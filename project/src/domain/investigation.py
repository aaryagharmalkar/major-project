"""Canonical, provenance-preserving representation of an investigation."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from .common import ConfidenceLevel, DomainEntity, SourceReference


class PersonRole(StrEnum):
    VICTIM = "victim"
    ACCUSED = "accused"
    WITNESS = "witness"
    POLICE_OFFICER = "police_officer"
    DOCTOR = "doctor"
    PANCH_WITNESS = "panch_witness"
    OTHER = "other"


class Person(DomainEntity):
    roles: frozenset[PersonRole] = frozenset()
    full_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    address: str | None = None
    contact: str | None = None
    source_references: tuple[SourceReference, ...] = ()


class Vehicle(DomainEntity):
    registration_number: str | None = None
    vehicle_type: str | None = None
    make_model: str | None = None
    owner_id: UUID | None = None
    driver_id: UUID | None = None
    source_references: tuple[SourceReference, ...] = ()


class EvidenceKind(StrEnum):
    MEDICAL = "medical"
    FORENSIC = "forensic"
    DIGITAL = "digital"
    PHOTOGRAPH = "photograph"
    PHYSICAL = "physical"
    DOCUMENTARY = "documentary"
    RECOVERED_PROPERTY = "recovered_property"
    OTHER = "other"


class EvidenceItem(DomainEntity):
    kind: EvidenceKind
    description: str
    exhibit_mark: str | None = None
    collected_at: datetime | None = None
    collected_by_id: UUID | None = None
    custody_document_ids: tuple[UUID, ...] = ()
    source_references: tuple[SourceReference, ...] = ()


class TimelineEvent(DomainEntity):
    occurred_at: datetime | None = None
    occurred_on: date | None = None
    description: str
    related_person_ids: tuple[UUID, ...] = ()
    related_evidence_ids: tuple[UUID, ...] = ()
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source_references: tuple[SourceReference, ...] = ()


class InvestigationConflict(DomainEntity):
    fact_path: str
    description: str
    conflicting_sources: tuple[SourceReference, ...]
    resolved: bool = False


class MissingInformation(DomainEntity):
    field_path: str
    description: str
    blocking: bool = False


class CaseMetadata(DomainEntity):
    case_id: UUID
    fir_number: str | None = None
    police_station: str | None = None
    jurisdiction: str | None = None
    court_name: str | None = None
    registration_date: date | None = None
    source_references: tuple[SourceReference, ...] = ()


class CanonicalInvestigation(DomainEntity):
    """Single source of truth assembled from the IKG after normalization."""

    case_metadata: CaseMetadata
    persons: tuple[Person, ...] = ()
    vehicles: tuple[Vehicle, ...] = ()
    evidence_items: tuple[EvidenceItem, ...] = ()
    timeline: tuple[TimelineEvent, ...] = ()
    legal_sections: tuple[str, ...] = ()
    investigation_notes: tuple[str, ...] = ()
    conflicts: tuple[InvestigationConflict, ...] = ()
    missing_information: tuple[MissingInformation, ...] = ()
    source_document_ids: tuple[UUID, ...] = ()
