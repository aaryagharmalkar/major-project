"""Errors specific to raw-text OCR, with no document-understanding semantics."""


class OCRException(RuntimeError):
    """Base exception for OCR processing."""


class UnsupportedOCRDocumentError(OCRException):
    """Raised when a source document is not currently accepted by the OCR layer."""


class OCRProviderError(OCRException):
    """Raised when a provider cannot return an OCR response."""


class OCRResponseError(OCRException):
    """Raised when a provider response is missing the raw OCR contract."""
