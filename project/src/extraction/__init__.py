"""Raw OCR interfaces and adapters; document understanding is deferred."""

from .base import DocumentParser, OCRExtractor
from .gemini_ocr import GeminiOCRClient
from .ocr_client import OCRClient
from .ocr_result import OCRResult
from .ocr_stage import OCRStage

__all__ = ["DocumentParser", "GeminiOCRClient", "OCRClient", "OCRExtractor", "OCRResult", "OCRStage"]
