"""
CLI Test script to verify TRELLIS 3D Asset Generation pipeline.
Usage:
    python project/src/test_trellis.py --mode text --prompt "country-made 9mm pistol on table"
    python project/src/test_trellis.py --mode image --image path/to/evidence.jpg
"""

import os
import sys
import argparse
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

from scene.trellis_generator import TrellisAssetGenerator


def test_generation():
    parser = argparse.ArgumentParser(description="Test TRELLIS 3D Asset Generator")
    parser.add_argument("--mode", choices=["text", "image", "status"], default="status")
    parser.add_argument("--prompt", type=str, default="A crashed blue hatchback car")
    parser.add_argument("--image", type=str, default=None)
    parser.add_argument("--id", type=str, default="test_asset")

    args = parser.parse_args()

    hf_token = os.getenv("HF_TOKEN")
    print(f"[*] HF_TOKEN detected: {'Yes (' + hf_token[:6] + '...)' if hf_token else 'No (using public mode)'}")

    generator = TrellisAssetGenerator(
        output_dir=Path(__file__).parent.parent.parent / "frontend/public/assets/generated",
        hf_token=hf_token,
    )

    if args.mode == "status":
        print("[+] TrellisAssetGenerator initialized successfully.")
        print(f"[+] Output Directory: {generator.output_dir.resolve()}")
        print("[+] Cached assets:", [f.name for f in generator.output_dir.glob("*.glb")])
        print("\nTo test generating a real 3D model, run:")
        print('  python project/src/test_trellis.py --mode text --prompt "broken wooden door lock" --id "door_lock"')
        return

    if args.mode == "text":
        print(f"[*] Triggering Text-to-3D for prompt: '{args.prompt}' (ID: {args.id})")
        result = generator.generate_from_text(prompt=args.prompt, asset_id=args.id)
        print("[*] Result:", result)

    elif args.mode == "image":
        if not args.image:
            print("[-] Error: --image path required for image mode.")
            return
        print(f"[*] Triggering Image-to-3D for image: {args.image} (ID: {args.id})")
        result = generator.generate_from_image(image_path=args.image, asset_id=args.id)
        print("[*] Result:", result)


if __name__ == "__main__":
    test_generation()
