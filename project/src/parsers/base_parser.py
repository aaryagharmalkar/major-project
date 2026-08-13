"""Schema-constrained parsing primitives for independent OCR documents."""

from __future__ import annotations

import hashlib
import json
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import ValidationError

from ..domain.documents import DocumentType
from ..domain.parsed_documents import ParseMetadata, ParsedDocument
from ..extraction.ocr_result import OCRResult


class ParserError(RuntimeError):
    """Base error for a parser that cannot return a validated typed document."""


class ParserValidationError(ParserError):
    """Raised only after all schema-validation attempts have failed."""


class ParserClient(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> dict[str, Any]:
        """Return a JSON object; transport providers must reject invalid JSON."""


class GeminiParserClient(ParserClient):
    """Small Gemini JSON adapter, injectable so parser tests never call the API."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-flash-latest", *, model_client: Any | None = None) -> None:
        self.model_name = model
        self._injected_client = model_client is not None
        if model_client is not None:
            self._model = model_client
            return
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini document parsing")
        try:
            from google import genai

            self._model = genai.Client(api_key=api_key)
        except ImportError as exc:
            raise ImportError("google-genai package is required for Gemini parsing") from exc

    def generate_json(self, prompt: str) -> dict[str, Any]:
        try:
            config = {"temperature": 0, "response_mime_type": "application/json"}
            response = self._model.generate_content(prompt, generation_config=config) if self._injected_client and hasattr(self._model, "generate_content") else self._model.models.generate_content(model=self.model_name, contents=prompt, config=config)
            payload = json.loads(getattr(response, "text", "") or "")
        except (json.JSONDecodeError, Exception) as exc:
            raise ParserError(f"Gemini parser request failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise ParserError("Gemini parser response must be a JSON object")
        return payload


ParsedDocumentT = TypeVar("ParsedDocumentT", bound=ParsedDocument)


class BaseDocumentParser(ABC, Generic[ParsedDocumentT]):
    document_type: DocumentType
    model_type: type[ParsedDocumentT]
    supported_entity_fields: tuple[str, ...] = ()

    def __init__(self, client: ParserClient, *, max_attempts: int = 2) -> None:
        self.client = client
        self.max_attempts = max_attempts

    @property
    def name(self) -> str:
        return type(self).__name__

    def parse(self, ocr_result: OCRResult) -> ParsedDocumentT:
        started = time.perf_counter()
        validation_errors: list[str] = []
        for attempt in range(self.max_attempts):
            try:
                payload = self.client.generate_json(self._build_prompt(ocr_result))
                return self._validate_payload(
                    payload,
                    ocr_result,
                    parse_duration_ms=(time.perf_counter() - started) * 1000,
                    retry_count=attempt,
                )
            except (ParserError, ValidationError) as exc:
                validation_errors.append(str(exc))
        raise ParserValidationError(
            f"{self.name} could not produce a valid {self.model_type.__name__} after "
            f"{self.max_attempts} attempts: {validation_errors[-1] if validation_errors else 'unknown error'}"
        )

    def _validate_payload(
        self,
        payload: dict[str, Any],
        ocr_result: OCRResult,
        *,
        parse_duration_ms: float,
        retry_count: int,
    ) -> ParsedDocumentT:
        controlled_payload = dict(payload)
        self._validate_explicit_entities(controlled_payload, ocr_result)
        controlled_payload.update(
            {
                "document_id": ocr_result.document_id,
                "document_type": self.document_type,
                "ocr_text_sha256": hashlib.sha256(ocr_result.raw_text.encode("utf-8")).hexdigest(),
                "parse_metadata": ParseMetadata(
                    parser_name=self.name,
                    parse_duration_ms=parse_duration_ms,
                    retry_count=retry_count,
                    confidence=controlled_payload.pop("confidence", None),
                    warnings=tuple(controlled_payload.pop("warnings", ())),
                ),
            }
        )
        return self.model_type.model_validate(controlled_payload)

    def _validate_explicit_entities(self, payload: dict[str, Any], ocr_result: OCRResult) -> None:
        """Reject role/entity values that are not present in the supplied OCR text."""

        normalized_ocr = self._normalize_for_support(ocr_result.raw_text)
        for field in self.supported_entity_fields:
            value = payload.get(field)
            values = value if isinstance(value, (list, tuple)) else (value,)
            for item in values:
                if item is None:
                    continue
                if not isinstance(item, str) or not self._normalize_for_support(item) or self._normalize_for_support(item) not in normalized_ocr:
                    raise ParserError(f"{self.name} returned {field} value that is not explicitly present in the OCR transcription")

    @staticmethod
    def _normalize_for_support(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.casefold())

    def _build_prompt(self, ocr_result: OCRResult) -> str:
        schema = json.dumps(self.model_type.model_json_schema(), ensure_ascii=False)
        return (
            "Convert only explicitly stated information from the OCR transcription into the JSON schema below. "
            "Do not infer, summarize, classify evidence, identify legal sections, or add facts. "
            "Use null for unavailable scalar fields and [] for unavailable lists. "
            f"{self._document_specific_instructions()} "
            "Return only a valid JSON object matching this schema.\n\n"
            f"Schema: {schema}\n\nOCR transcription (preserve its meaning; do not add information):\n{ocr_result.raw_text}"
        )

    def _document_specific_instructions(self) -> str:
        return ""


class UnknownDocumentParser(BaseDocumentParser[ParsedDocumentT]):
    """Fallback parser that retains raw OCR text exactly, without interpretation."""

    def parse(self, ocr_result: OCRResult) -> ParsedDocumentT:
        from ..domain.parsed_documents import UnknownDocument

        started = time.perf_counter()
        return UnknownDocument(
            document_id=ocr_result.document_id,
            ocr_text_sha256=hashlib.sha256(ocr_result.raw_text.encode("utf-8")).hexdigest(),
            raw_text=ocr_result.raw_text,
            parse_metadata=ParseMetadata(
                parser_name=self.name,
                parse_duration_ms=(time.perf_counter() - started) * 1000,
                retry_count=0,
                warnings=("No document-specific parser is registered for this document type.",),
            ),
        )  # type: ignore[return-value]
