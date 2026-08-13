"""Download Wan 1.3B GGUF and SD 1.5 keyframe models into ComfyUI model directories."""

from __future__ import annotations

import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

WAN_REPO = "calcuis/wan-1.3b-gguf"
SD15_REPO = "runwayml/stable-diffusion-v1-5"

WAN_FILES = {
    "wan2.1_t2v_1.3b-q4_0.gguf": "models/diffusion_models",
    "wan2.1-vace-1.3b-q4_0.gguf": "models/diffusion_models",
    "umt5-xxl-encoder-q4_k_m.gguf": "models/text_encoders",
    "pig_wan_vae_fp32-f16.gguf": "models/vae",
}

SD15_FILES = {
    "v1-5-pruned-emaonly.safetensors": "models/checkpoints",
}


def _download_file(repo: str, filename: str, target_dir: Path) -> None:
    target = target_dir / filename
    target_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"Already exists: {target}")
        return
    print(f"Downloading {filename} -> {target_dir}")
    downloaded = Path(hf_hub_download(repo_id=repo, filename=filename, local_dir=str(target_dir)))
    if downloaded.resolve() != target.resolve() and downloaded.exists():
        downloaded.replace(target)
    print(f"Saved: {target}")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: python {Path(__file__).name} <comfyui_root>", file=sys.stderr)
        return 2

    comfy_root = Path(sys.argv[1]).expanduser().resolve()
    if not comfy_root.is_dir():
        print(f"ComfyUI directory not found: {comfy_root}", file=sys.stderr)
        return 1

    for filename, relative_dir in WAN_FILES.items():
        _download_file(WAN_REPO, filename, comfy_root / relative_dir)

    for filename, relative_dir in SD15_FILES.items():
        _download_file(SD15_REPO, filename, comfy_root / relative_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
