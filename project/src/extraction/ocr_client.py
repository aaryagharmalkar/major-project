"""Swappable OCR client port; providers return transcription only."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain.documents import SourceDocument
from .ocr_result import OCRResult


class OCRClient(ABC):
    supported_mime_types: frozenset[str] = frozenset()

    def supports(self, document: SourceDocument) -> bool:
        """Whether this provider can transcribe the document without interpretation."""
        return document.media_type in self.supported_mime_types

    @abstractmethod
    def extract(self, document: SourceDocument, source_path: Path) -> OCRResult:
        """Transcribe one supported source document into raw per-page text."""
