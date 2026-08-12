"""Writes legal recommendations and their allowed evidence mappings."""

from __future__ import annotations

import json
from pathlib import Path

from ..context.case_context import CaseContext
from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .evidence_mapper import EvidenceMapper
from .legal_findings import LegalFindings


class LegalArtifactWriter:
    def __init__(self, storage_root: Path) -> None: self.storage_root = storage_root
    def write(self, context: CaseContext, findings: LegalFindings) -> tuple[GeneratedArtifact, ...]:
        layout = CaseStorageLayout(self.storage_root, context.case_id).ensure_exists()
        directory = layout.processed_directory / "legal"; directory.mkdir(parents=True, exist_ok=True)
        artifacts = []
        for name, payload in (("legal_findings.json", findings.model_dump(mode="json")), ("evidence_mapping.json", [item.model_dump(mode="json") for item in EvidenceMapper().available(context)])):
            path = directory / name; path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            artifacts.append(GeneratedArtifact(name=name.removesuffix(".json"), storage_key=layout.relative_key(path), media_type="application/json"))
        return tuple(artifacts)
