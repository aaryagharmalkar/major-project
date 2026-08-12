"""Writes the derived context separately from canonical data."""

from __future__ import annotations

import json
from pathlib import Path

from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .case_context import CaseContext


class ContextArtifactWriter:
    def __init__(self, storage_root: Path) -> None: self.storage_root = storage_root
    def write(self, context: CaseContext) -> GeneratedArtifact:
        layout = CaseStorageLayout(self.storage_root, context.case_id).ensure_exists()
        path = layout.processed_directory / "context" / "case_context.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(context.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8")
        return GeneratedArtifact(name="case_context", storage_key=layout.relative_key(path), media_type="application/json")
