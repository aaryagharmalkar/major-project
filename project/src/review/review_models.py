"""Immutable, non-sensitive review lifecycle contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from ..domain.common import DomainModel


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    FINALIZED = "finalized"


class ReviewEventType(StrEnum):
    DRAFT_CREATED = "draft_created"
    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    FINALIZED = "finalized"


class ReviewEvent(DomainModel):
    event_type: ReviewEventType
    case_id: UUID
    charge_sheet_id: UUID
    version: int = Field(ge=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str = "system"
    metadata: dict[str, str] = Field(default_factory=dict)


class ChargeSheetReview(DomainModel):
    case_id: UUID
    charge_sheet_id: UUID = Field(default_factory=uuid4)
    status: ReviewStatus
    data_version: int = Field(ge=1)
    data_content_hash: str = Field(min_length=64, max_length=64)
    reviewer_id: str | None = None
    reviewer_name: str | None = None
    review_timestamp: datetime | None = None
    decision: str | None = None
    comments: str | None = None
    rejection_reason: str | None = None
    approved_version: int | None = Field(default=None, ge=1)
    approved_content_hash: str | None = Field(default=None, min_length=64, max_length=64)
    finalized_at: datetime | None = None
    final_artifact_reference: str | None = None
    events: tuple[ReviewEvent, ...] = ()
