"""Gemini-backed OCR extraction adapter."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from generator.llm.gemini import GeminiClient, GeminiClientError
from generator.ocr.ocr_result import OCRExtractionResult

logger = logging.getLogger(__name__)


class GeminiOCRClient:
    """Thin adapter that sends a PDF to Gemini and returns structured OCR JSON."""

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client

    def extract(self, pdf_path: Path) -> OCRExtractionResult:
        """Extract structured content from a PDF using Gemini."""

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if self._client is None:
            logger.warning("No Gemini client configured; returning an empty extraction result for %s", pdf_path)
            return OCRExtractionResult(document_type=pdf_path.stem, extracted_data={})

        prompt = (
            "You are performing OCR extraction on a generated investigation PDF. "
            "Return JSON with a document_type string and an extracted_data object. "
            "Do not invent facts. Only extract from the provided document."
        )
        try:
            raw_response = self._client.send_prompt(prompt + f"\nPDF path: {pdf_path}")
        except GeminiClientError as exc:
            logger.warning("Gemini OCR request failed for %s: %s", pdf_path, exc)
            return OCRExtractionResult(document_type=pdf_path.stem, extracted_data={})

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            payload = {"document_type": pdf_path.stem, "extracted_data": {}}

        return OCRExtractionResult.model_validate(payload)

    def extract(self, pdf_path: Path) -> OCRExtractionResult:
        """Extract structured content from a PDF using Gemini."""

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        prompt = (
            "You are performing OCR extraction on a generated investigation PDF. "
            "Return JSON with a document_type string and an extracted_data object. "
            "Do not invent facts. Only extract from the provided document."
        )
        try:
            raw_response = self._client.send_prompt(prompt + f"\nPDF path: {pdf_path}")
        except GeminiClientError as exc:
            logger.warning("Gemini OCR request failed for %s: %s", pdf_path, exc)
            return OCRExtractionResult(document_type=pdf_path.stem, extracted_data={})

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            payload = {"document_type": pdf_path.stem, "extracted_data": {}}

        return OCRExtractionResult.model_validate(payload)
