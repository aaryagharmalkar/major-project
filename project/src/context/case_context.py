"""Compact, provenance-preserving view for legal analysis—not a source of truth."""

from __future__ import annotations

from uuid import UUID

from ..domain.common import DomainModel, SourceReference
from ..normalization.canonical_models import (
    CanonicalConflict, CanonicalDocument, CanonicalEvidence, CanonicalFact,
    CanonicalLocation, CanonicalPerson, CanonicalTimelineEvent, CanonicalVehicle,
    MissingInformation,
)
from ..validation.validation_models import ValidationIssue, ValidationReport


class CaseContext(DomainModel):
    case_id: UUID
    case_metadata: tuple[CanonicalFact, ...] = ()
    fir_details: tuple[CanonicalFact, ...] = ()
    police_station: CanonicalFact | None = None
    court: CanonicalFact | None = None
    occurrence_details: tuple[CanonicalTimelineEvent, ...] = ()
    complainants: tuple[CanonicalPerson, ...] = ()
    victims: tuple[CanonicalPerson, ...] = ()
    accused: tuple[CanonicalPerson, ...] = ()
    witnesses: tuple[CanonicalPerson, ...] = ()
    police_officers: tuple[CanonicalPerson, ...] = ()
    doctors: tuple[CanonicalPerson, ...] = ()
    locations: tuple[CanonicalLocation, ...] = ()
    relevant_timeline: tuple[CanonicalTimelineEvent, ...] = ()
    evidence: tuple[CanonicalEvidence, ...] = ()
    medical_findings: tuple[CanonicalFact, ...] = ()
    forensic_findings: tuple[CanonicalFact, ...] = ()
    vehicles: tuple[CanonicalVehicle, ...] = ()
    recovered_property: tuple[CanonicalEvidence, ...] = ()
    investigation_actions: tuple[CanonicalFact, ...] = ()
    documents: tuple[CanonicalDocument, ...] = ()
    legal_section_references: tuple[CanonicalFact, ...] = ()
    validation_issues: tuple[ValidationIssue, ...] = ()
    conflicts: tuple[ValidationIssue, ...] = ()
    missing_information: tuple[ValidationIssue, ...] = ()
    canonical_conflicts: tuple[CanonicalConflict, ...] = ()
    canonical_missing_information: tuple[MissingInformation, ...] = ()
    source_references: tuple[SourceReference, ...] = ()
    validation_disposition: str
