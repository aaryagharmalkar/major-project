"""Persists one validated typed-document artifact per source document."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..domain.documents import SourceDocument
from ..domain.parsed_documents import ParsedDocument
from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact


class ParsedDocumentArtifactWriter:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def write(self, source_document: SourceDocument, parsed_document: ParsedDocument) -> GeneratedArtifact:
        layout = CaseStorageLayout(self.storage_root, source_document.case_id).ensure_exists()
        parsed_directory = layout.processed_directory / "parsed"
        parsed_directory.mkdir(parents=True, exist_ok=True)
        stem = re.sub(r"[^A-Za-z0-9]+", "_", Path(source_document.original_filename).stem).strip("_") or "document"
        output_path = parsed_directory / f"{stem}_{source_document.id.hex[:8]}.json"
        output_path.write_text(
            json.dumps(parsed_document.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return GeneratedArtifact(
            name="parsed_document",
            storage_key=layout.relative_key(output_path),
            media_type="application/json",
        )
