"""Compatibility exports for the OCR port and future document-parser port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from ..domain.documents import SourceDocument
from .ocr_client import OCRClient
from .ocr_result import OCRResult


ParsedDocumentT = TypeVar("ParsedDocumentT", bound=BaseModel)
OCRExtractor = OCRClient


class DocumentParser(ABC, Generic[ParsedDocumentT]):
    """Reserved document-understanding port; Phase 5 will implement it."""

    @abstractmethod
    def parse(self, document: SourceDocument, ocr_result: OCRResult) -> ParsedDocumentT:
        """Convert OCR output into a typed document-specific representation."""
