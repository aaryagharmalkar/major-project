"""CLI entry point for incident video simulation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .case_sources import load_incident_facts
from .comfy_client import ComfyUIClient, ComfyUIError
from .frame_utils import extract_last_frame
from .keyframe_generator import DEFAULT_KEYFRAME_WORKFLOW, generate_keyframe
from .prompt_builder import VideoScene, build_multi_scene_prompts, build_video_prompt
from .video_stitcher import _find_ffmpeg, stitch_clips
from .workflow_injector import (
    DEFAULT_I2V_MODEL,
    GenerationParams,
    WorkflowKind,
    build_api_prompt,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKFLOW = PACKAGE_ROOT / "workflows" / "wan_t2v_1.3b.json"
DEFAULT_I2V_WORKFLOW = PACKAGE_ROOT / "workflows" / "wan_i2v_vace_1.3b.json"


def _wan_frame_count(seconds: float, fps: int) -> int:
    """Snap frame count to Wan-compatible length (1 + 4n)."""
    raw = max(1, int(seconds * fps))
    snapped = 1 + 4 * max(0, round((raw - 1) / 4))
    return max(5, snapped)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an AI incident simulation video from case JSON using Wan 1.3B + ComfyUI.",
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to case_context.json or master_case.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=PACKAGE_ROOT / "output" / "incident_simulation.webp",
        help="Output video path (.webp, .webm, or .mp4)",
    )
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW, help="ComfyUI T2V workflow JSON")
    parser.add_argument(
        "--i2v-workflow",
        type=Path,
        default=DEFAULT_I2V_WORKFLOW,
        help="ComfyUI Wan VACE I2V workflow JSON",
    )
    parser.add_argument(
        "--keyframe-workflow",
        type=Path,
        default=DEFAULT_KEYFRAME_WORKFLOW,
        help="ComfyUI SD 1.5 keyframe workflow JSON",
    )
    parser.add_argument("--seconds", type=float, default=2.0, help="Clip length in seconds (single-scene mode)")
    parser.add_argument(
        "--scene-seconds",
        type=float,
        default=2.0,
        help="Seconds per scene in multi-scene mode (default 2.0; 5 scenes ≈ 10s total)",
    )
    parser.add_argument(
        "--multi-scene",
        action="store_true",
        help="Generate detailed multi-scene video from case timeline and stitch into one file",
    )
    parser.add_argument(
        "--pipeline",
        choices=("i2v", "t2v"),
        default="i2v",
        help="Multi-scene pipeline: i2v (keyframe + VACE I2V + frame chain) or t2v (legacy text-to-video)",
    )
    parser.add_argument(
        "--no-chain",
        action="store_true",
        help="Generate a fresh SD1.5 keyframe per scene instead of chaining last frames (less continuity)",
    )
    parser.add_argument(
        "--crossfade-ms",
        type=int,
        default=200,
        help="Crossfade duration between stitched scenes in milliseconds (0 = hard cut)",
    )
    parser.add_argument("--fps", type=int, default=15, help="Frames per second")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed (each scene adds +1)")
    parser.add_argument("--width", type=int, default=480, help="Video width")
    parser.add_argument("--height", type=int, default=480, help="Video height")
    parser.add_argument("--steps", type=int, default=30, help="Diffusion steps")
    parser.add_argument("--cfg", type=float, default=6.0, help="CFG scale")
    parser.add_argument(
        "--timeout-minutes",
        type=float,
        default=20.0,
        help="Max wait per scene in minutes (multi-scene can take ~5 min/scene on 6GB GPU)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print prompts and exit without generating")
    parser.add_argument(
        "--comfy-url",
        default=os.getenv("COMFYUI_URL", "http://127.0.0.1:8188"),
        help="ComfyUI server URL",
    )
    return parser


def _maybe_convert_to_mp4(source: Path, destination: Path) -> Path:
    if destination.suffix.lower() != ".mp4":
        return source
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        print("Warning: ffmpeg not found; keeping original format instead of MP4.")
        return source
    temp_mp4 = destination.with_suffix(".mp4")
    subprocess.run(
        [ffmpeg, "-y", "-i", str(source), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(temp_mp4)],
        check=True,
        capture_output=True,
    )
    return temp_mp4


def _generate_t2v_scene(
    client: ComfyUIClient,
    workflow: Path,
    scene: VideoScene,
    *,
    seed: int,
    frame_count: int,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    output_path: Path,
    timeout_seconds: float,
    fps: int,
) -> dict:
    params = GenerationParams(
        positive_prompt=scene.positive,
        negative_prompt=scene.negative,
        seed=seed,
        width=width,
        height=height,
        frame_count=frame_count,
        steps=steps,
        cfg=cfg,
        fps=fps,
    )
    prompt = build_api_prompt(workflow, params, kind=WorkflowKind.T2V)
    print(f"\n--- Scene: {scene.title} ({scene.time_label}) ---")
    print(scene.positive[:200] + ("..." if len(scene.positive) > 200 else ""))
    prompt_id = client.queue_prompt(prompt)
    print(f"Prompt ID: {prompt_id}. Waiting for ComfyUI...")
    history = client.wait_for_completion(prompt_id, timeout_seconds=timeout_seconds)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated = client.save_first_output(history, output_path)
    return {
        "scene_id": scene.scene_id,
        "title": scene.title,
        "time_label": scene.time_label,
        "event_text": scene.event_text,
        "positive_prompt": scene.positive,
        "negative_prompt": scene.negative,
        "seed": seed,
        "frames": frame_count,
        "comfy_prompt_id": prompt_id,
        "comfy_output_file": generated.filename,
        "output_path": str(output_path),
    }


def _generate_i2v_scene(
    client: ComfyUIClient,
    workflow: Path,
    scene: VideoScene,
    keyframe_path: Path,
    *,
    seed: int,
    frame_count: int,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    output_path: Path,
    timeout_seconds: float,
    fps: int,
) -> dict:
    uploaded_name = client.upload_image(keyframe_path)
    params = GenerationParams(
        positive_prompt=scene.motion_prompt,
        negative_prompt=scene.negative,
        seed=seed,
        width=width,
        height=height,
        frame_count=frame_count,
        steps=steps,
        cfg=cfg,
        model_file=DEFAULT_I2V_MODEL,
        input_image=uploaded_name,
        fps=fps,
    )
    prompt = build_api_prompt(workflow, params, kind=WorkflowKind.I2V)
    print(f"\n--- Scene: {scene.title} ({scene.time_label}) ---")
    print(f"Keyframe: {keyframe_path.name}")
    print(scene.motion_prompt[:200] + ("..." if len(scene.motion_prompt) > 200 else ""))
    prompt_id = client.queue_prompt(prompt)
    print(f"Prompt ID: {prompt_id}. Waiting for ComfyUI...")
    history = client.wait_for_completion(prompt_id, timeout_seconds=timeout_seconds)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated = client.save_first_output(history, output_path)
    return {
        "scene_id": scene.scene_id,
        "title": scene.title,
        "time_label": scene.time_label,
        "event_text": scene.event_text,
        "keyframe_prompt": scene.keyframe_prompt,
        "motion_prompt": scene.motion_prompt,
        "negative_prompt": scene.negative,
        "keyframe_path": str(keyframe_path),
        "seed": seed,
        "frames": frame_count,
        "comfy_prompt_id": prompt_id,
        "comfy_output_file": generated.filename,
        "output_path": str(output_path),
    }


def _print_multi_scene_plan(scenes: tuple[VideoScene, ...], args: argparse.Namespace, pipeline: str) -> None:
    total_seconds = args.scene_seconds * len(scenes)
    print("=== Multi-Scene Plan ===")
    print(json.dumps(
        {
            "pipeline": pipeline,
            "case_scenes": len(scenes),
            "seconds_per_scene": args.scene_seconds,
            "total_seconds": total_seconds,
            "fps": args.fps,
            "chain_frames": pipeline == "i2v" and not args.no_chain,
            "crossfade_ms": args.crossfade_ms,
        },
        indent=2,
    ))
    for index, scene in enumerate(scenes, 1):
        print(f"\n=== Scene {index}/{len(scenes)}: {scene.title} @ {scene.time_label} ===")
        print(f"Event: {scene.event_text}")
        if pipeline == "i2v":
            print(f"\nKeyframe prompt:\n{scene.keyframe_prompt}")
            print(f"\nMotion prompt:\n{scene.motion_prompt}")
        else:
            print(f"\nPositive:\n{scene.positive}")
        print(f"\nNegative:\n{scene.negative}")
    print(f"\nTotal: {total_seconds}s ({len(scenes)} scenes × {args.scene_seconds}s @ {args.fps}fps)")


def _finalize_multi_scene_output(
    args: argparse.Namespace,
    facts,
    scenes: tuple[VideoScene, ...],
    scene_records: list[dict],
    scene_clips: list[Path],
    pipeline: str,
) -> Path:
    output_path = args.output.expanduser().resolve()
    stitched_suffix = output_path.suffix.lower()
    if stitched_suffix not in {".mp4", ".webp", ".webm"}:
        stitched_path = output_path.with_suffix(".mp4")
    else:
        stitched_path = output_path

    if stitched_path.suffix.lower() == ".mp4":
        stitch_clips(
            scene_clips,
            stitched_path,
            crossfade_ms=args.crossfade_ms,
            fps=args.fps,
        )
        final_path = stitched_path
    else:
        mp4_path = output_path.with_suffix(".mp4")
        stitch_clips(scene_clips, mp4_path, crossfade_ms=args.crossfade_ms, fps=args.fps)
        final_path = mp4_path
        if output_path.suffix.lower() == ".webp":
            print(f"Stitched MP4 saved at {mp4_path} (use .mp4 output for best multi-scene results)")

    metadata = {
        "generated_by": "ai_simulation",
        "not_evidence": True,
        "model": DEFAULT_I2V_MODEL if pipeline == "i2v" else "wan-1.3b-q4_0",
        "mode": "multi_scene",
        "pipeline": pipeline,
        "source_file": facts.source_path,
        "source_kind": facts.source_kind.value,
        "case_id": facts.case_id,
        "scene_seconds": args.scene_seconds,
        "total_seconds": args.scene_seconds * len(scenes),
        "fps": args.fps,
        "crossfade_ms": args.crossfade_ms,
        "frame_chain": pipeline == "i2v" and not args.no_chain,
        "scenes": scene_records,
        "output_path": str(final_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = final_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    scenes_dir = final_path.parent / f"{final_path.stem}_scenes"
    prompts_path = scenes_dir / "prompts.json"
    prompts_path.write_text(json.dumps([asdict(scene) for scene in scenes], indent=2), encoding="utf-8")

    print(f"\nSaved stitched video: {final_path}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Scene clips: {scenes_dir}")
    return final_path


def _run_multi_scene_t2v(args: argparse.Namespace, facts) -> int:
    scenes = build_multi_scene_prompts(facts)
    frame_count = _wan_frame_count(args.scene_seconds, args.fps)
    total_seconds = args.scene_seconds * len(scenes)

    if args.dry_run:
        _print_multi_scene_plan(scenes, args, "t2v")
        return 0

    if not args.workflow.is_file():
        raise FileNotFoundError(f"Workflow not found: {args.workflow}")

    client = ComfyUIClient(args.comfy_url)
    client.check_server()
    timeout_seconds = args.timeout_minutes * 60.0

    output_path = args.output.expanduser().resolve()
    scenes_dir = output_path.parent / f"{output_path.stem}_scenes"
    scene_clips: list[Path] = []
    scene_records: list[dict] = []

    print(f"Generating {len(scenes)} T2V scenes ({args.scene_seconds}s each, ~{total_seconds}s total)...")
    print("Note: Each scene takes ~5 minutes on a 6GB GPU. Total run may take 25–30 minutes.")

    for index, scene in enumerate(scenes):
        clip_path = scenes_dir / f"scene_{index + 1:02d}_{scene.scene_id}.webp"
        record = _generate_t2v_scene(
            client,
            args.workflow,
            scene,
            seed=args.seed + index,
            frame_count=frame_count,
            width=args.width,
            height=args.height,
            steps=args.steps,
            cfg=args.cfg,
            output_path=clip_path,
            timeout_seconds=timeout_seconds,
            fps=args.fps,
        )
        scene_records.append(record)
        scene_clips.append(clip_path)
        print(f"Saved scene clip: {clip_path}")

    _finalize_multi_scene_output(args, facts, scenes, scene_records, scene_clips, "t2v")
    return 0


def _run_multi_scene_i2v(args: argparse.Namespace, facts) -> int:
    scenes = build_multi_scene_prompts(facts)
    frame_count = _wan_frame_count(args.scene_seconds, args.fps)
    total_seconds = args.scene_seconds * len(scenes)

    if args.dry_run:
        _print_multi_scene_plan(scenes, args, "i2v")
        return 0

    for workflow_path in (args.i2v_workflow, args.keyframe_workflow):
        if not workflow_path.is_file():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")

    client = ComfyUIClient(args.comfy_url)
    client.check_server()
    timeout_seconds = args.timeout_minutes * 60.0

    output_path = args.output.expanduser().resolve()
    scenes_dir = output_path.parent / f"{output_path.stem}_scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    keyframes_dir = scenes_dir / "keyframes"
    keyframes_dir.mkdir(parents=True, exist_ok=True)

    scene_clips: list[Path] = []
    scene_records: list[dict] = []
    chain_frames = not args.no_chain

    print(f"Generating {len(scenes)} I2V scenes ({args.scene_seconds}s each, ~{total_seconds}s total)...")
    print("Pipeline: SD1.5 keyframe → Wan VACE I2V → frame chain → crossfade stitch")
    print("Note: Each scene takes ~6–8 minutes on a 6GB GPU (keyframe + I2V). Total ~35–45 minutes.")

    previous_clip: Path | None = None
    for index, scene in enumerate(scenes):
        keyframe_path = keyframes_dir / f"keyframe_{index + 1:02d}_{scene.scene_id}.png"

        if index == 0 or not chain_frames:
            print(f"\nGenerating keyframe for scene {index + 1}...")
            generate_keyframe(
                client,
                args.keyframe_workflow,
                positive_prompt=scene.keyframe_prompt,
                seed=args.seed + index,
                output_path=keyframe_path,
                timeout_seconds=timeout_seconds,
            )
            print(f"Saved keyframe: {keyframe_path}")
        elif previous_clip is not None:
            print(f"\nChaining last frame from scene {index} as keyframe...")
            extract_last_frame(previous_clip, keyframe_path)
            print(f"Saved chained keyframe: {keyframe_path}")

        clip_path = scenes_dir / f"scene_{index + 1:02d}_{scene.scene_id}.webp"
        record = _generate_i2v_scene(
            client,
            args.i2v_workflow,
            scene,
            keyframe_path,
            seed=args.seed + index,
            frame_count=frame_count,
            width=args.width,
            height=args.height,
            steps=args.steps,
            cfg=args.cfg,
            output_path=clip_path,
            timeout_seconds=timeout_seconds,
            fps=args.fps,
        )
        scene_records.append(record)
        scene_clips.append(clip_path)
        previous_clip = clip_path
        print(f"Saved scene clip: {clip_path}")

    _finalize_multi_scene_output(args, facts, scenes, scene_records, scene_clips, "i2v")
    return 0


def _run_multi_scene(args: argparse.Namespace, facts) -> int:
    if args.pipeline == "i2v":
        return _run_multi_scene_i2v(args, facts)
    return _run_multi_scene_t2v(args, facts)


def _run_single_scene(args: argparse.Namespace, facts) -> int:
    video_prompt = build_video_prompt(facts)
    frame_count = _wan_frame_count(args.seconds, args.fps)

    if args.dry_run:
        print("=== Incident Facts ===")
        print(json.dumps(
            {
                "case_id": facts.case_id,
                "location": facts.location,
                "datetime": facts.datetime,
                "primary_narrative": facts.primary_narrative,
                "timeline_events": list(facts.timeline_events),
            },
            indent=2,
        ))
        print("\n=== Positive Prompt ===")
        print(video_prompt.positive)
        print("\n=== Negative Prompt ===")
        print(video_prompt.negative)
        print(f"\nFrames: {frame_count} ({args.seconds}s @ {args.fps}fps)")
        return 0

    if not args.workflow.is_file():
        raise FileNotFoundError(f"Workflow not found: {args.workflow}")

    client = ComfyUIClient(args.comfy_url)
    client.check_server()
    timeout_seconds = args.timeout_minutes * 60.0

    params = GenerationParams(
        positive_prompt=video_prompt.positive,
        negative_prompt=video_prompt.negative,
        seed=args.seed,
        width=args.width,
        height=args.height,
        frame_count=frame_count,
        steps=args.steps,
        cfg=args.cfg,
        fps=args.fps,
    )
    prompt = build_api_prompt(args.workflow, params, kind=WorkflowKind.T2V)

    print(f"Queueing generation ({frame_count} frames, seed={args.seed})...")
    prompt_id = client.queue_prompt(prompt)
    print(f"Prompt ID: {prompt_id}. Waiting for ComfyUI...")
    history = client.wait_for_completion(prompt_id, timeout_seconds=timeout_seconds)

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated = client.save_first_output(history, output_path)
    final_path = _maybe_convert_to_mp4(output_path, output_path)

    metadata = {
        "generated_by": "ai_simulation",
        "not_evidence": True,
        "model": "wan-1.3b-q4_0",
        "mode": "single_scene",
        "source_file": facts.source_path,
        "source_kind": facts.source_kind.value,
        "case_id": facts.case_id,
        "positive_prompt": video_prompt.positive,
        "negative_prompt": video_prompt.negative,
        "seed": args.seed,
        "frames": frame_count,
        "fps": args.fps,
        "seconds": args.seconds,
        "comfy_prompt_id": prompt_id,
        "comfy_output_file": generated.filename,
        "output_path": str(final_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = final_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved video: {final_path}")
    print(f"Saved metadata: {metadata_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    facts = load_incident_facts(args.input)
    if args.multi_scene:
        return _run_multi_scene(args, facts)
    return _run_single_scene(args, facts)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ComfyUIError, FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc

