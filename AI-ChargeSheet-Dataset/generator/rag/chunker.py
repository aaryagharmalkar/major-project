"""Chunk OCR JSON content into semantic sections for retrieval indexing."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Chunk(BaseModel):
    """A semantic chunk derived from OCR output."""

    chunk_id: str
    case_id: str
    document_type: str
    document_name: str
    section: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chunker:
    """Split OCR JSON payloads into semantic chunks."""

    def __init__(self, *, chunk_size: int = 400) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self._chunk_size = chunk_size

    def chunk(self, case_directory: str | Path, ocr_json_path: str | Path) -> list[Chunk]:
        case_path = Path(case_directory).expanduser().resolve()
        ocr_path = Path(ocr_json_path).expanduser().resolve()
        if not ocr_path.exists():
            raise FileNotFoundError(f"OCR JSON not found: {ocr_path}")

        payload = json.loads(ocr_path.read_text(encoding="utf-8"))
        extracted_data = payload.get("extracted_data", {})
        document_type = payload.get("document_type", ocr_path.stem)
        case_id = case_path.name
        document_name = ocr_path.stem

        chunks: list[Chunk] = []
        sections = self._build_sections(extracted_data)
        for section_name, section_text in sections.items():
            if not section_text.strip():
                continue
            text = section_text.strip()
            for start in range(0, len(text), self._chunk_size):
                chunk_text = text[start : start + self._chunk_size]
                chunk_id = f"{case_id}:{document_name}:{section_name}:{len(chunks) + 1}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        case_id=case_id,
                        document_type=document_type,
                        document_name=document_name,
                        section=section_name,
                        content=chunk_text,
                        metadata={"source_file": ocr_path.name},
                    )
                )

        if not chunks:
            chunks.append(
                Chunk(
                    chunk_id=f"{case_id}:{document_name}:full:1",
                    case_id=case_id,
                    document_type=document_type,
                    document_name=document_name,
                    section="full",
                    content=json.dumps(extracted_data, ensure_ascii=False),
                    metadata={"source_file": ocr_path.name},
                )
            )

        return chunks

    def _build_sections(self, extracted_data: dict[str, Any]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in extracted_data.items():
            if isinstance(value, str):
                normalized[key] = value
            elif isinstance(value, (dict, list)):
                normalized[key] = json.dumps(value, ensure_ascii=False)
            else:
                normalized[key] = str(value)

        if not normalized:
            return {"full": ""}

        if "narrative" in normalized:
            return {"narrative": normalized["narrative"], "other": "\n".join(value for key, value in normalized.items() if key != "narrative")}

        if "witness" in normalized:
            return {"witness": normalized["witness"], "other": "\n".join(value for key, value in normalized.items() if key != "witness")}

        if "medical" in normalized:
            return {"medical": normalized["medical"], "other": "\n".join(value for key, value in normalized.items() if key != "medical")}

        if "evidence" in normalized:
            return {"evidence": normalized["evidence"], "other": "\n".join(value for key, value in normalized.items() if key != "evidence")}

        if "investigation" in normalized:
            return {"investigation": normalized["investigation"], "other": "\n".join(value for key, value in normalized.items() if key != "investigation")}

        return {"full": "\n".join(normalized.values())}
