"""Pydantic models for OCR extraction and evaluation results."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OCRExtractionResult(BaseModel):
    """Structured OCR extraction payload produced from a PDF."""

    document_type: str = Field(description="Document type inferred from the PDF.")
    extracted_data: dict[str, Any] = Field(default_factory=dict, description="Extracted content keyed by field name.")


class OCREvaluationMetrics(BaseModel):
    """Evaluation metrics comparing OCR output to ground truth."""

    entity_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_fields: int = Field(default=0, ge=0)
    incorrect_fields: int = Field(default=0, ge=0)
    precision: float = Field(default=0.0, ge=0.0, le=1.0)
    recall: float = Field(default=0.0, ge=0.0, le=1.0)
    f1: float = Field(default=0.0, ge=0.0, le=1.0)
    document_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)


class OCREvaluationResult(BaseModel):
    """Full OCR evaluation report for one case document."""

    document_type: str
    source_pdf: str
    extracted_json: str
    metrics: OCREvaluationMetrics
