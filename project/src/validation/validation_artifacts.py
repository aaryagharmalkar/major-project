"""Persists validation artifacts without altering canonical or graph outputs."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .validation_models import ValidationReport


class ValidationArtifactWriter:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def write(self, case_id: UUID, report: ValidationReport) -> tuple[GeneratedArtifact, ...]:
        layout = CaseStorageLayout(self.storage_root, case_id).ensure_exists()
        directory = layout.processed_directory / "validation"
        directory.mkdir(parents=True, exist_ok=True)
        payloads = {"validation_report.json": report.model_dump(mode="json"), "conflicts.json": [item.model_dump(mode="json") for item in report.conflicts], "missing_information.json": [item.model_dump(mode="json") for item in report.missing_information]}
        artifacts = []
        for filename, payload in payloads.items():
            path = directory / filename
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            artifacts.append(GeneratedArtifact(name=filename.removesuffix(".json"), storage_key=layout.relative_key(path), media_type="application/json"))
        return tuple(artifacts)
