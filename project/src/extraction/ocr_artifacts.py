"""Writes OCR output files without interpreting their contents."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..domain.documents import SourceDocument
from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .ocr_result import OCRMetadata, OCRResult


class OCRArtifactWriter:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def write(self, document: SourceDocument, result: OCRResult) -> tuple[GeneratedArtifact, ...]:
        layout = CaseStorageLayout(self.storage_root, document.case_id).ensure_exists()
        ocr_directory = layout.processed_directory / "ocr"
        ocr_directory.mkdir(parents=True, exist_ok=True)
        base_name = self._artifact_base_name(document)
        raw_text_path = ocr_directory / f"{base_name}_raw.txt"
        metadata_path = ocr_directory / f"{base_name}_metadata.json"
        result_path = ocr_directory / f"{base_name}_OCRResult.json"
        raw_text_path.write_text(result.raw_text, encoding="utf-8")
        metadata_path.write_text(
            json.dumps(result.metadata.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        result_path.write_text(
            json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return (
            GeneratedArtifact(name="ocr_raw_text", storage_key=layout.relative_key(raw_text_path), media_type="text/plain"),
            GeneratedArtifact(name="ocr_metadata", storage_key=layout.relative_key(metadata_path), media_type="application/json"),
            GeneratedArtifact(name="ocr_result", storage_key=layout.relative_key(result_path), media_type="application/json"),
        )

    def load(self, document: SourceDocument) -> tuple[OCRResult, tuple[GeneratedArtifact, ...]] | None:
        """Load an existing OCR result only when all deterministic artifacts validate."""

        layout = CaseStorageLayout(self.storage_root, document.case_id)
        ocr_directory = layout.processed_directory / "ocr"
        base_name = self._artifact_base_name(document)
        raw_text_path = ocr_directory / f"{base_name}_raw.txt"
        metadata_path = ocr_directory / f"{base_name}_metadata.json"
        result_path = ocr_directory / f"{base_name}_OCRResult.json"
        if not all(path.is_file() for path in (raw_text_path, metadata_path, result_path)):
            return None
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            page_count = payload.pop("page_count", None)
            result = OCRResult.model_validate(payload)
            metadata = OCRMetadata.model_validate(json.loads(metadata_path.read_text(encoding="utf-8")))
            raw_text = raw_text_path.read_text(encoding="utf-8")
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None
        if (
            result.document_id != document.id
            or page_count != result.page_count
            or result.raw_text != raw_text
            or result.metadata != metadata
            or result.raw_text != "\n\n".join(page.text for page in result.pages)
        ):
            return None
        return result, (
            GeneratedArtifact(name="ocr_raw_text", storage_key=layout.relative_key(raw_text_path), media_type="text/plain"),
            GeneratedArtifact(name="ocr_metadata", storage_key=layout.relative_key(metadata_path), media_type="application/json"),
            GeneratedArtifact(name="ocr_result", storage_key=layout.relative_key(result_path), media_type="application/json"),
        )

    @staticmethod
    def _artifact_base_name(document: SourceDocument) -> str:
        stem = re.sub(r"[^A-Za-z0-9]+", "_", Path(document.original_filename).stem).strip("_") or "document"
        return f"{stem}_{document.id.hex[:8]}"
