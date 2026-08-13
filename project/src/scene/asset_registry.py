"""
3D asset registry.

Maps semantic scene entities to GLB/GLTF assets.

The Scene Projector decides WHAT exists.
The Asset Registry decides WHICH 3D model represents it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


# ============================================================
# ASSET DEFINITION
# ============================================================

@dataclass(frozen=True)
class AssetDefinition:
    asset_id: str
    path: str

    # Useful when an exact model isn't available.
    category: str

    keywords: tuple[str, ...] = ()


# ============================================================
# REGISTRY
# ============================================================

class AssetRegistry:

    def __init__(self, asset_root: str | Path = "assets"):

        self.asset_root = Path(asset_root)

        self.assets: list[AssetDefinition] = [

            # ------------------------------------------------
            # VEHICLES
            # ------------------------------------------------

            AssetDefinition(
                asset_id="bajaj_pulsar_220f",
                path="vehicles/bajaj_pulsar_220f.glb",
                category="vehicle",
                keywords=(
                    "bajaj",
                    "pulsar",
                    "pulsar 220f",
                    "motorcycle",
                    "bike",
                ),
            ),

            AssetDefinition(
                asset_id="honda_activa_6g",
                path="vehicles/honda_activa_6g.glb",
                category="vehicle",
                keywords=(
                    "honda",
                    "activa",
                    "activa 6g",
                    "scooter",
                ),
            ),

            # ------------------------------------------------
            # PEOPLE
            # ------------------------------------------------

            AssetDefinition(
                asset_id="generic_male",
                path="people/generic_male.glb",
                category="person",
                keywords=(
                    "male",
                    "man",
                    "person",
                ),
            ),

            AssetDefinition(
                asset_id="generic_female",
                path="people/generic_female.glb",
                category="person",
                keywords=(
                    "female",
                    "woman",
                    "person",
                ),
            ),

            # ------------------------------------------------
            # ENVIRONMENT
            # ------------------------------------------------

            AssetDefinition(
                asset_id="road",
                path="environment/road.glb",
                category="environment",
                keywords=("road",),

            ),

            AssetDefinition(
                asset_id="street_light",
                path="environment/street_light.glb",
                category="environment",
                keywords=("street light", "lamp", "light"),
            ),

            AssetDefinition(
                asset_id="traffic_signal",
                path="environment/traffic_signal.glb",
                category="environment",
                keywords=("traffic signal", "signal"),
            ),

            # ------------------------------------------------
            # FALLBACK
            # ------------------------------------------------

            AssetDefinition(
                asset_id="generic_vehicle",
                path="fallback/generic_vehicle.glb",
                category="vehicle",
                keywords=("vehicle", "car", "bike"),
            ),

            AssetDefinition(
                asset_id="generic_person",
                path="fallback/generic_person.glb",
                category="person",
                keywords=("person", "human"),
            ),
        ]

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize(text: str | None) -> str:

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ========================================================
    # SEARCH
    # ========================================================

    def find(
        self,
        query: str,
        category: str | None = None,
    ) -> AssetDefinition | None:

        normalized_query = self._normalize(query)

        best_asset = None
        best_score = 0

        for asset in self.assets:

            if category and asset.category != category:
                continue

            score = 0

            for keyword in asset.keywords:

                normalized_keyword = self._normalize(keyword)

                if normalized_keyword in normalized_query:
                    score += len(normalized_keyword)

            if score > best_score:
                best_score = score
                best_asset = asset

        return best_asset

    # ========================================================
    # RESOLVE
    # ========================================================

    def resolve_vehicle(
        self,
        make: str | None,
        model: str | None,
    ) -> AssetDefinition:

        query = " ".join(
            value
            for value in [make, model]
            if value
        )

        asset = self.find(
            query,
            category="vehicle",
        )

        if asset:
            return asset

        return self.find(
            "generic vehicle",
            category="vehicle",
        )

    # ========================================================

    def resolve_person(
        self,
        role: str | None,
    ) -> AssetDefinition:

        asset = self.find(
            role or "person",
            category="person",
        )

        if asset:
            return asset

        return self.find(
            "generic person",
            category="person",
        )

    # ========================================================
    # ABSOLUTE PATH
    # ========================================================

    def absolute_path(
        self,
        asset: AssetDefinition,
    ) -> str:

        return str(
            self.asset_root / asset.path
        )