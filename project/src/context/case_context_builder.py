"""Selects legal-relevant canonical facts while retaining their original provenance."""

from __future__ import annotations

from ..normalization.canonical_models import CanonicalInvestigation
from ..validation.validation_models import ValidationReport
from .case_context import CaseContext


class CaseContextBuilder:
    def build(self, canonical: CanonicalInvestigation, validation: ValidationReport) -> CaseContext:
        metadata = tuple(item for item in (canonical.case_metadata.fir_number, canonical.case_metadata.registration_date, canonical.jurisdiction) if item is not None)
        all_issues = validation.errors + validation.warnings
        return CaseContext(
            case_id=canonical.case_metadata.case_id, case_metadata=metadata, fir_details=canonical.fir_details,
            police_station=canonical.police_station, court=canonical.court,
            occurrence_details=tuple(event for event in canonical.timeline if "occurrence" in str(event.description.value).casefold() or "incident" in str(event.description.value).casefold()),
            complainants=canonical.complainants, victims=canonical.victims, accused=canonical.accused, witnesses=canonical.witnesses,
            police_officers=canonical.police_officers, doctors=canonical.doctors, locations=canonical.locations,
            relevant_timeline=canonical.timeline, evidence=canonical.evidence, medical_findings=canonical.medical_findings,
            forensic_findings=canonical.forensic_findings, vehicles=canonical.vehicles,
            recovered_property=canonical.recovered_property, investigation_actions=canonical.investigation_actions,
            documents=canonical.documents,
            legal_section_references=canonical.offences, validation_issues=all_issues, conflicts=validation.conflicts,
            missing_information=validation.missing_information, canonical_conflicts=canonical.conflicts,
            canonical_missing_information=canonical.missing_information, source_references=canonical.source_references,
            validation_disposition=validation.disposition.value,
        )
