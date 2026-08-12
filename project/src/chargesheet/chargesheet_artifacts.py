from __future__ import annotations

import json
from pathlib import Path

from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .form_if5_schema import ChargeSheetData


class ChargeSheetArtifactWriter:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def write(self, data: ChargeSheetData) -> GeneratedArtifact:
        layout = CaseStorageLayout(self.storage_root, data.case_id).ensure_exists()
        path = layout.processed_directory / "chargesheet" / "draft" / f"ChargeSheet_v{data.version}_data.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8")
        return GeneratedArtifact(name="chargesheet_data", storage_key=layout.relative_key(path), media_type="application/json")
