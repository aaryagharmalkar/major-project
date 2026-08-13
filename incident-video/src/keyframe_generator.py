"""Generate still keyframe images via ComfyUI SD 1.5 workflow."""

from __future__ import annotations

from pathlib import Path

from .comfy_client import ComfyUIClient
from .prompt_builder import KEYFRAME_NEGATIVE
from .workflow_injector import KeyframeParams, WorkflowKind, build_api_prompt

DEFAULT_KEYFRAME_WORKFLOW = Path(__file__).resolve().parent.parent / "workflows" / "sd15_keyframe.json"


def generate_keyframe(
    client: ComfyUIClient,
    workflow: Path,
    *,
    positive_prompt: str,
    seed: int,
    output_path: Path,
    width: int = 512,
    height: int = 512,
    steps: int = 25,
    cfg: float = 7.0,
    timeout_seconds: float = 600.0,
) -> Path:
    """Generate a PNG keyframe and save it to output_path."""
    params = KeyframeParams(
        positive_prompt=positive_prompt,
        negative_prompt=KEYFRAME_NEGATIVE,
        seed=seed,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
    )
    prompt = build_api_prompt(workflow, params, kind=WorkflowKind.KEYFRAME)
    prompt_id = client.queue_prompt(prompt)
    history = client.wait_for_completion(prompt_id, timeout_seconds=timeout_seconds)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    client.save_first_output(history, output_path)
    return output_path

