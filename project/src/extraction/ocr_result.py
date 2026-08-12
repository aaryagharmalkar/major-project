"""Typed raw OCR output. These models deliberately contain no case semantics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class OCRPage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    page_number: int = Field(ge=1)
    text: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class OCRMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    model: str
    input_mime_type: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = Field(ge=0)
    token_usage: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class OCRResult(BaseModel):
    """A provenance-ready text transcription, not a parsed investigation document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: UUID
    pages: tuple[OCRPage, ...]
    raw_text: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: tuple[str, ...] = ()
    language: str | None = None
    metadata: OCRMetadata

    @computed_field
    @property
    def page_count(self) -> int:
        return len(self.pages)
