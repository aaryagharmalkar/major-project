"""Run OCR across PDFs inside a case folder and persist extracted JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from generator.ocr.gemini_ocr import GeminiOCRClient
from generator.ocr.ocr_result import OCRExtractionResult

logger = logging.getLogger(__name__)


class OCRPipeline:
    """Process PDFs in a case folder and save structured OCR outputs."""

    def __init__(self, ocr_client: GeminiOCRClient | None = None) -> None:
        self._ocr_client = ocr_client or GeminiOCRClient()

    def run(self, case_directory: str | Path) -> list[Path]:
        case_path = Path(case_directory).expanduser().resolve()
        pdf_directory = case_path / "pdfs"
        output_directory = case_path / "ocr"
        output_directory.mkdir(parents=True, exist_ok=True)

        outputs: list[Path] = []
        if not pdf_directory.exists():
            return outputs

        for pdf_path in sorted(pdf_directory.glob("*.pdf")):
            result = self._ocr_client.extract(pdf_path)
            output_path = output_directory / f"{pdf_path.stem}.json"
            output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            outputs.append(output_path)

        return outputs
