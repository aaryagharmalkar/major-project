"""Immutable models for deterministic evidence-quality evaluation."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from ..domain.common import DomainModel, SourceReference


class IssueCategory(StrEnum):
    COMPLETENESS = "completeness"
    DOCUMENT_SUPPORT = "document_support"
    CONFLICT = "conflict"
    TIMELINE = "timeline"
    PROVENANCE = "provenance"
    ENTITY = "entity"
    UNSUPPORTED_FACT = "unsupported_fact"
    LOW_CONFIDENCE = "low_confidence"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueStatus(StrEnum):
    OPEN = "open"
    REVIEW_REQUIRED = "review_required"


class ValidationDisposition(StrEnum):
    DRAFT_ALLOWED = "draft_allowed"
    REVIEW_REQUIRED = "review_required"
    FINAL_BLOCKED = "final_blocked"


class ValidationIssue(DomainModel):
    issue_id: UUID = Field(default_factory=uuid4)
    category: IssueCategory
    severity: IssueSeverity
    description: str
    field_path: str
    source_references: tuple[SourceReference, ...] = ()
    related_entity_ids: tuple[UUID, ...] = ()
    status: IssueStatus = IssueStatus.OPEN


class ValidationRules(DomainModel):
    """Case-specific policy; defaults avoid assuming every case has every document."""

    require_fir_number: bool = False
    require_police_station: bool = False
    require_occurrence_details: bool = False
    missing_document_severity: IssueSeverity = IssueSeverity.WARNING
    missing_required_severity: IssueSeverity = IssueSeverity.ERROR
    low_confidence_threshold: float = Field(default=0.4, ge=0, le=1)


class ValidationReport(DomainModel):
    errors: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    missing_documents: tuple[ValidationIssue, ...] = ()
    missing_information: tuple[ValidationIssue, ...] = ()
    conflicts: tuple[ValidationIssue, ...] = ()
    unresolved_entities: tuple[ValidationIssue, ...] = ()
    unsupported_facts: tuple[ValidationIssue, ...] = ()
    low_confidence_facts: tuple[ValidationIssue, ...] = ()
    timeline_issues: tuple[ValidationIssue, ...] = ()
    completeness_score: float = Field(ge=0, le=1)
    critical_failure: bool
    review_required: bool
    disposition: ValidationDisposition
