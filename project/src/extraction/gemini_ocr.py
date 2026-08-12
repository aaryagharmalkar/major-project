"""Gemini adapter for raw OCR only; it does not infer document fields or facts."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..domain.documents import SourceDocument
from .ocr_client import OCRClient
from .ocr_exceptions import OCRProviderError, OCRResponseError, UnsupportedOCRDocumentError
from .ocr_result import OCRMetadata, OCRPage, OCRResult


class GeminiOCRClient(OCRClient):
    """Raw-OCR adapter backed by the current Google Gen AI SDK."""

    supported_mime_types = frozenset({"application/pdf", "image/png", "image/jpeg"})
    OCR_PROMPT = """You are an OCR transcription service. Transcribe the supplied document exactly.
Do not summarize, classify, identify people, extract fields, or infer facts.
Return only JSON with this exact shape:
{
  "pages": [{"page_number": 1, "text": "verbatim page text", "confidence": 0.0}],
  "language": "detected language or null",
  "warnings": ["any transcription warnings"]
}
For multi-page PDFs, return one entry per page in page order."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-flash-latest", *, model_client: Any | None = None) -> None:
        self.model_name = model
        self._injected_client = model_client is not None
        if model_client is not None:
            self._model = model_client
            return
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini OCR")
        try:
            from google import genai

            self._model = genai.Client(api_key=api_key)
        except ImportError as exc:
            raise ImportError("google-genai package is required for Gemini OCR") from exc

    def extract(self, document: SourceDocument, source_path: Path) -> OCRResult:
        if not self.supports(document):
            raise UnsupportedOCRDocumentError(f"OCR does not support '{document.media_type}' yet")
        if not source_path.is_file():
            raise OCRProviderError(f"Stored source document was not found: {source_path}")

        started = time.perf_counter()
        try:
            response = self._generate(source_path, document.media_type)
            response_text = getattr(response, "text", "") or ""
        except Exception as exc:
            raise OCRProviderError(f"Gemini OCR request failed: {exc}") from exc

        processing_time_ms = (time.perf_counter() - started) * 1000
        payload = self._parse_payload(response_text)
        pages = self._build_pages(payload)
        confidence_values = [page.confidence for page in pages if page.confidence is not None]
        usage = getattr(response, "usage_metadata", None)
        token_usage = getattr(usage, "total_token_count", None) if usage else None

        return OCRResult(
            document_id=document.id,
            pages=pages,
            raw_text="\n\n".join(page.text for page in pages),
            confidence=(sum(confidence_values) / len(confidence_values) if confidence_values else None),
            warnings=tuple(str(warning) for warning in payload.get("warnings", ())),
            language=payload.get("language"),
            metadata=OCRMetadata(
                provider="gemini",
                model=self.model_name,
                input_mime_type=document.media_type,
                processing_time_ms=processing_time_ms,
                token_usage=token_usage,
            ),
        )

    def _generate(self, source_path: Path, mime_type: str) -> Any:
        """Use Files API for PDFs; retain simple injectable test-client compatibility."""
        config = {"temperature": 0, "response_mime_type": "application/json"}
        if self._injected_client and hasattr(self._model, "generate_content"):
            return self._model.generate_content(
                [self.OCR_PROMPT, {"mime_type": mime_type, "data": source_path.read_bytes()}],
                generation_config=config,
            )
        if mime_type == "application/pdf":
            uploaded = self._model.files.upload(file=str(source_path), config={"mime_type": mime_type})
            try:
                uploaded = self._wait_for_uploaded_file(uploaded)
                return self._model.models.generate_content(model=self.model_name, contents=[self.OCR_PROMPT, uploaded], config=config)
            finally:
                self._model.files.delete(name=uploaded.name)
        from google.genai import types
        image = types.Part.from_bytes(data=source_path.read_bytes(), mime_type=mime_type)
        return self._model.models.generate_content(model=self.model_name, contents=[self.OCR_PROMPT, image], config=config)

    def _wait_for_uploaded_file(self, uploaded: Any) -> Any:
        """Wait only when the SDK reports asynchronous PDF processing."""
        state = self._file_state(uploaded)
        for _ in range(30):
            if state != "PROCESSING":
                break
            time.sleep(1)
            uploaded = self._model.files.get(name=uploaded.name)
            state = self._file_state(uploaded)
        if state == "PROCESSING":
            raise OCRProviderError("Gemini PDF processing did not become ready in time")
        if state == "FAILED":
            raise OCRProviderError("Gemini failed to process the uploaded PDF")
        return uploaded

    @staticmethod
    def _file_state(uploaded: Any) -> str | None:
        state = getattr(uploaded, "state", None)
        return (getattr(state, "value", state) or "").upper() or None

    @staticmethod
    def _parse_payload(response_text: str) -> dict[str, Any]:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise OCRResponseError("Gemini OCR did not return valid JSON") from exc
        if not isinstance(payload, dict):
            raise OCRResponseError("Gemini OCR response must be a JSON object")
        return payload

    @staticmethod
    def _build_pages(payload: dict[str, Any]) -> tuple[OCRPage, ...]:
        raw_pages = payload.get("pages")
        if not isinstance(raw_pages, list) or not raw_pages:
            raise OCRResponseError("Gemini OCR response must include at least one page")
        try:
            return tuple(
                OCRPage(
                    page_number=item["page_number"],
                    text=item["text"],
                    confidence=item.get("confidence"),
                )
                for item in raw_pages
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise OCRResponseError("Gemini OCR pages do not match the OCR contract") from exc
