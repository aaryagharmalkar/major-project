"""Persists canonical output without replacing any previous-stage artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .canonical_models import CanonicalInvestigation


class CanonicalArtifactWriter:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def write(self, canonical: CanonicalInvestigation) -> tuple[GeneratedArtifact, ...]:
        layout = CaseStorageLayout(self.storage_root, canonical.case_metadata.case_id).ensure_exists()
        directory = layout.processed_directory / "canonical"
        directory.mkdir(parents=True, exist_ok=True)
        payloads = {"canonical_investigation.json": canonical.model_dump(mode="json"), "conflicts.json": [item.model_dump(mode="json") for item in canonical.conflicts], "timeline.json": [item.model_dump(mode="json") for item in canonical.timeline], "evidence.json": [item.model_dump(mode="json") for item in canonical.evidence + canonical.recovered_property]}
        artifacts = []
        for filename, payload in payloads.items():
            path = directory / filename
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            artifacts.append(GeneratedArtifact(name=filename.removesuffix(".json"), storage_key=layout.relative_key(path), media_type="application/json"))
        return tuple(artifacts)
