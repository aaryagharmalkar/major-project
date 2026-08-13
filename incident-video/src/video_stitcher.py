"""Stitch multiple scene clips into one longer video."""

from __future__ import annotations

import shutil
import subprocess
import os
from pathlib import Path


def _find_ffmpeg() -> str | None:
    """Return ffmpeg executable path, including common Windows install locations."""
    found = shutil.which("ffmpeg")
    if found:
        return found

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        winget_link = Path(local_app_data) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
        if winget_link.is_file():
            return str(winget_link)

    return None


def stitch_clips(clips: list[Path], output: Path, *, crossfade_ms: int = 200, fps: int = 15) -> Path:
    """Concatenate scene clips into a single MP4, optionally with crossfade transitions."""
    if not clips:
        raise ValueError("No clips provided for stitching")
    if len(clips) == 1:
        shutil.copy2(clips[0], output)
        return output

    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg is required to stitch multi-scene videos. "
            "Install with: winget install Gyan.FFmpeg — then restart your terminal."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output.parent / "_stitch_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    segment_paths: list[Path] = []
    try:
        for index, clip in enumerate(clips, 1):
            segment = temp_dir / f"segment_{index:02d}.mp4"
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(clip),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    str(fps),
                    str(segment),
                ],
                check=True,
                capture_output=True,
            )
            segment_paths.append(segment)

        if crossfade_ms <= 0 or len(segment_paths) < 2:
            list_file = temp_dir / "concat.txt"
            list_file.write_text(
                "\n".join(f"file '{path.resolve().as_posix()}'" for path in segment_paths),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_file),
                    "-c",
                    "copy",
                    str(output),
                ],
                check=True,
                capture_output=True,
            )
        else:
            _stitch_with_crossfade(ffmpeg, segment_paths, output, crossfade_ms, fps)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output


def _probe_duration(ffmpeg: str, path: Path) -> float:
    result = subprocess.run(
        [
            ffmpeg,
            "-i",
            str(path),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            time_part = line.split("Duration:")[1].split(",")[0].strip()
            hours, minutes, seconds = time_part.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    raise RuntimeError(f"Could not probe duration for {path}")


def _stitch_with_crossfade(
    ffmpeg: str,
    segments: list[Path],
    output: Path,
    crossfade_ms: int,
    fps: int,
) -> None:
    crossfade_s = crossfade_ms / 1000.0
    durations = [_probe_duration(ffmpeg, segment) for segment in segments]

    inputs: list[str] = []
    for segment in segments:
        inputs.extend(["-i", str(segment)])

    parts: list[str] = []
    cumulative = durations[0]
    prev = "0:v"
    for index in range(1, len(segments)):
        out_label = "vout" if index == len(segments) - 1 else f"vx{index}"
        offset = max(0.0, cumulative - crossfade_s)
        parts.append(
            f"[{prev}][{index}:v]xfade=transition=fade:duration={crossfade_s:.3f}:offset={offset:.3f}[{out_label}]"
        )
        cumulative += durations[index] - crossfade_s
        prev = out_label

    filter_complex = ";".join(parts)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            str(output),
        ],
        check=True,
        capture_output=True,
    )
