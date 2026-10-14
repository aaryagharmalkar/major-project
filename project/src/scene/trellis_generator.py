"""
TRELLIS 3D Asset Generation Service.

Provides an automated pipeline to generate textured 3D GLB mesh assets from:
1. Case Evidence Descriptions / FIR Entities (Text-to-3D)
2. Forensic Crime Scene / Vehicle Photos (Image-to-3D)
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("TrellisAssetGenerator")


class TrellisAssetGenerator:
    """
    Manages 3D asset generation requests for the Byomkesh Reconstruction System.
    """

    def __init__(
        self,
        output_dir: str | Path = "frontend/public/assets/generated",
        hf_token: Optional[str] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.hf_token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

    def get_asset_filename(self, identifier: str) -> str:
        clean_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in identifier.lower())
        return f"{clean_id}.glb"

    def is_asset_cached(self, identifier: str) -> bool:
        target_path = self.output_dir / self.get_asset_filename(identifier)
        return target_path.exists() and target_path.stat().st_size > 0

    def generate_from_text(
        self,
        prompt: str,
        asset_id: str,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Generates a 3D .glb mesh from text by first synthesizing a canonical viewpoint
        and executing the TRELLIS SLAT flow reconstruction.
        """
        target_file = self.output_dir / self.get_asset_filename(asset_id)
        rel_path = f"/assets/generated/{target_file.name}"

        if target_file.exists() and target_file.stat().st_size > 0:
            logger.info(f"Using cached 3D asset: {target_file}")
            return {
                "success": True,
                "asset_id": asset_id,
                "file_path": str(target_file),
                "public_path": rel_path,
                "cached": True,
            }

        logger.info(f"Connecting to TRELLIS 3D generator for prompt: '{prompt}'...")

        try:
            from gradio_client import Client, handle_file

            client = Client("prithivMLmods/TRELLIS.2-Text-to-3D", token=self.hf_token)
            
            # Step 1: Text to Image
            img_path = client.predict(prompt=prompt, api_name="/generate_txt2img")
            
            # Step 2: Preprocess Image
            preprocessed_img = client.predict(input=handle_file(img_path), api_name="/preprocess_image")

            # Step 3: Run TRELLIS 3D Generation
            res = client.predict(
                image=handle_file(preprocessed_img),
                seed=seed,
                resolution="512",
                decimation_target=100000,
                texture_size=1024,
                ss_guidance_strength=7.5,
                ss_guidance_rescale=0.7,
                ss_sampling_steps=12,
                ss_rescale_t=5.0,
                shape_guidance=7.5,
                shape_rescale=0.5,
                shape_steps=12,
                shape_rescale_t=3.0,
                tex_guidance=1.0,
                tex_rescale=0.0,
                tex_steps=12,
                tex_rescale_t=3.0,
                api_name="/generate_3d"
            )

            # res is tuple: (rerun_viewer_data, glb_filepath)
            downloaded_glb = None
            if isinstance(res, (list, tuple)):
                for item in reversed(res):
                    if isinstance(item, str) and item.endswith(".glb") and os.path.exists(item):
                        downloaded_glb = item
                        break
                    elif isinstance(item, dict) and item.get("path", "").endswith(".glb"):
                        downloaded_glb = item["path"]
                        break
            elif isinstance(res, str) and res.endswith(".glb"):
                downloaded_glb = res

            if downloaded_glb and os.path.exists(downloaded_glb):
                with open(downloaded_glb, "rb") as src, open(target_file, "wb") as dst:
                    dst.write(src.read())

                logger.info(f"Successfully generated 3D asset: {target_file}")
                return {
                    "success": True,
                    "asset_id": asset_id,
                    "file_path": str(target_file),
                    "public_path": rel_path,
                    "cached": False,
                }
            else:
                return {
                    "success": False,
                    "error": f"No valid .glb file returned. Got: {res}",
                    "fallback_path": "/assets/vehicles/bajaj_pulsar_150.glb",
                }

        except Exception as e:
            logger.warning(f"TRELLIS generation exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_path": "/assets/vehicles/bajaj_pulsar_150.glb",
            }
