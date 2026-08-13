"""Typed, non-inferential case-level representation produced in Phase 7."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from ..domain.common import DomainModel, SourceReference
from ..knowledge_graph.graph_models import GraphProvenance, PersonRole


class CanonicalFact(DomainModel):
    value: Any
    source_document_ids: tuple[UUID, ...] = Field(min_length=1)
    references: tuple[GraphProvenance, ...] = Field(min_length=1)
    source_path: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    extraction_method: str = Field(min_length=1)
    timestamp: datetime


class ConflictSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConflictStatus(StrEnum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    ACCEPTED_VARIANT = "accepted_variant"
    REVIEW_REQUIRED = "review_required"


class CanonicalConflict(DomainModel):
    conflict_id: UUID = Field(default_factory=uuid4)
    field_path: str
    competing_values: tuple[CanonicalFact, ...] = Field(min_length=2)
    source_references: tuple[SourceReference, ...] = Field(min_length=1)
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    status: ConflictStatus = ConflictStatus.UNRESOLVED
    resolution: str | None = None
    resolved_by: str | None = None
    resolution_timestamp: datetime | None = None


class CanonicalPerson(DomainModel):
    id: UUID
    name: CanonicalFact
    roles: frozenset[PersonRole] = frozenset()


class CanonicalVehicle(DomainModel):
    id: UUID
    registration_number: CanonicalFact


class CanonicalLocation(DomainModel):
    id: UUID
    name: CanonicalFact


class CanonicalDocument(DomainModel):
    id: UUID
    document_id: CanonicalFact
    document_type: CanonicalFact | None = None


class CanonicalEvidence(DomainModel):
    evidence_id: UUID
    type: str
    description: CanonicalFact
    source_documents: tuple[UUID, ...]
    collection_details: tuple[CanonicalFact, ...] = ()
    custody_information: tuple[CanonicalFact, ...] = ()
    related_person_ids: tuple[UUID, ...] = ()
    related_vehicle_ids: tuple[UUID, ...] = ()
    related_event_ids: tuple[UUID, ...] = ()
    confidence: float | None = Field(default=None, ge=0, le=1)


class TimelineStatus(StrEnum):
    NORMAL = "normal"
    REVIEW_REQUIRED = "review_required"


class CanonicalTimelineEvent(DomainModel):
    event_id: UUID
    timestamp: CanonicalFact | None = None
    description: CanonicalFact
    location_id: UUID | None = None
    participant_ids: tuple[UUID, ...] = ()
    supporting_documents: tuple[UUID, ...] = ()
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: TimelineStatus = TimelineStatus.NORMAL


class MissingInformation(DomainModel):
    field_path: str
    description: str


class ConfidenceSummary(DomainModel):
    average: float | None = Field(default=None, ge=0, le=1)
    fact_count: int = Field(ge=0)


class CanonicalCaseMetadata(DomainModel):
    case_id: UUID
    fir_number: CanonicalFact | None = None
    registration_date: CanonicalFact | None = None


class CanonicalInvestigation(DomainModel):
    case_metadata: CanonicalCaseMetadata
    fir_details: tuple[CanonicalFact, ...] = ()
    jurisdiction: CanonicalFact | None = None
    police_station: CanonicalFact | None = None
    court: CanonicalFact | None = None
    offences: tuple[CanonicalFact, ...] = ()
    complainants: tuple[CanonicalPerson, ...] = ()
    victims: tuple[CanonicalPerson, ...] = ()
    accused: tuple[CanonicalPerson, ...] = ()
    witnesses: tuple[CanonicalPerson, ...] = ()
    police_officers: tuple[CanonicalPerson, ...] = ()
    doctors: tuple[CanonicalPerson, ...] = ()
    vehicles: tuple[CanonicalVehicle, ...] = ()
    locations: tuple[CanonicalLocation, ...] = ()
    evidence: tuple[CanonicalEvidence, ...] = ()
    medical_findings: tuple[CanonicalFact, ...] = ()
    forensic_findings: tuple[CanonicalFact, ...] = ()
    timeline: tuple[CanonicalTimelineEvent, ...] = ()
    investigation_actions: tuple[CanonicalFact, ...] = ()
    recovered_property: tuple[CanonicalEvidence, ...] = ()
    documents: tuple[CanonicalDocument, ...] = ()
    conflicts: tuple[CanonicalConflict, ...] = ()
    missing_information: tuple[MissingInformation, ...] = ()
    source_references: tuple[SourceReference, ...] = ()
    confidence_summary: ConfidenceSummary
