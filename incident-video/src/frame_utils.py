"""Extract frames from generated clips for scene chaining."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .video_stitcher import _find_ffmpeg


def extract_last_frame(video_path: Path, output_path: Path) -> Path:
    """Save the last frame of a video/animated-webp clip as a PNG."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to extract frames for scene chaining.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-sseof",
            "-0.05",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    if not output_path.is_file():
        raise RuntimeError(f"Failed to extract last frame from {video_path}")
    return output_path

