"""Shared immutable value objects used by the new domain layer."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DomainModel(BaseModel):
    """Base model that prevents accidental mutation of investigation facts."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FieldStatus(StrEnum):
    POPULATED = "populated"
    UNAVAILABLE = "unavailable"
    CONFLICT = "conflict"
    REVIEW_REQUIRED = "review_required"


class ReviewFlag(StrEnum):
    NONE = "none"
    LOW_CONFIDENCE = "low_confidence"
    CONFLICT = "conflict"
    MISSING_EVIDENCE = "missing_evidence"
    OFFICER_REVIEW_REQUIRED = "officer_review_required"


class SourceLocation(DomainModel):
    """A precise location within an uploaded source document or media file."""

    page_number: int | None = Field(default=None, ge=1)
    frame_number: int | None = Field(default=None, ge=0)
    timestamp_seconds: float | None = Field(default=None, ge=0)
    extraction_key: str | None = None


class SourceReference(DomainModel):
    """Provenance linking a normalized fact to an uploaded source."""

    document_id: UUID
    location: SourceLocation = Field(default_factory=SourceLocation)
    excerpt: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class ProvenancedValue(DomainModel):
    """A value whose reliability and origin are preserved through the workflow."""

    value: Any
    status: FieldStatus = FieldStatus.POPULATED
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    sources: tuple[SourceReference, ...] = ()
    review_flag: ReviewFlag = ReviewFlag.NONE


class DomainEntity(DomainModel):
    """Base identity for graph nodes and normalized investigation entities."""

    id: UUID = Field(default_factory=uuid4)
