"""Generate FIR Markdown documents from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.schemas.documents._base import (
    CaseSummary,
    EvidenceReference,
    LegalSectionReference,
    OfficerReference,
    PersonReference,
    WitnessReference,
)
from generator.schemas.documents.fir_schema import (
    FIRAccused,
    FIRAttachments,
    FIRComplainant,
    FIRDocument,
    FIRHeader,
    FIRInvestigationDetails,
    FIRNarrative,
    FIRRegistrationDetails,
)
from generator.schemas.master_case_schema import MasterCase


class FIRDocumentGenerator(BaseDocumentGenerator[FIRDocument]):
    """Generate a layout-driven FIR document from MasterCase data."""

    document_schema_model = FIRDocument

    def _build_documents(self) -> list[dict[str, Any]]:
        """Build a single FIR document payload from the validated MasterCase."""

        case = self._master_case
        case_summary = CaseSummary(
            case_id=case.case_information.case_id,
            crime_category=case.case_information.crime_category,
            FIR_number=case.case_information.FIR_number,
            FIR_date=case.case_information.FIR_date,
            incident_date=case.case_information.incident_date,
            incident_time=case.case_information.incident_time,
            police_station=case.case_information.police_station,
            district=case.case_information.district,
            state=case.case_information.state,
            location=case.case_information.location,
        )

        complainant = PersonReference(
            person_id=case.victim.person_id,
            full_name=case.victim.full_name,
            age=case.victim.age,
            gender=case.victim.gender,
            occupation=case.victim.occupation,
            address=case.victim.address,
            phone=case.victim.phone,
        )

        accused = [
            FIRAccused(
                person=PersonReference(
                    person_id=person.person_id,
                    full_name=person.full_name,
                    age=person.age,
                    gender=person.gender,
                    occupation=person.occupation,
                    address=person.address,
                    phone=person.phone,
                ),
                aliases=person.alias_names,
                charges=person.charges,
            )
            for person in case.accused
        ]

        witnesses = [
            WitnessReference(
                person_id=person.person_id,
                full_name=person.full_name,
                age=person.age,
                gender=person.gender,
                occupation=person.occupation,
                address=person.address,
                phone=person.phone,
                relationship_to_case=person.relationship_to_case,
                statement_summary=person.statement_summary,
                is_hostile=person.is_hostile,
            )
            for person in case.witnesses
        ]

        investigating_officer = OfficerReference(
            name=case.investigating_officer.name,
            rank=case.investigating_officer.rank,
            buckle_number=case.investigating_officer.buckle_number,
            police_station=case.investigating_officer.police_station,
            phone=case.investigating_officer.phone,
        )

        evidence = [
            EvidenceReference(
                evidence_id=item.evidence_id,
                evidence_type=item.evidence_type,
                description=item.description,
                recovered_from=item.recovered_from,
                seizure_date=item.seizure_date,
                forensic_required=item.forensic_required,
            )
            for item in case.evidence
        ]

        legal_sections = [
            LegalSectionReference(
                section_code=section.section_code,
                section_title=section.section_title,
                description=section.description,
                applicability_notes=section.applicability_notes,
            )
            for section in case.applicable_bns_sections.sections
        ]

        return [
            {
                "case_summary": case_summary,
                "header": FIRHeader(
                    fir_number=case.case_information.FIR_number,
                    registration_date=case.case_information.FIR_date.isoformat(),
                    police_station=case.case_information.police_station,
                    district=case.case_information.district,
                    state=case.case_information.state,
                ),
                "registration_details": FIRRegistrationDetails(
                    crime_category=case.case_information.crime_category,
                    offence_description=case.case_information.offence_description,
                    incident_date=case.case_information.incident_date.isoformat(),
                    incident_time=case.case_information.incident_time.isoformat(),
                    place_of_occurrence=case.case_information.location,
                ),
                "complainant": FIRComplainant(person=complainant),
                "accused": accused,
                "investigation_details": FIRInvestigationDetails(
                    officer=investigating_officer,
                    witnesses=witnesses,
                    evidence=evidence,
                    applicable_sections=legal_sections,
                ),
                "narrative": FIRNarrative(
                    complaint_summary=self._build_complaint_summary(case_summary, complainant),
                    occurrence_narrative=case.case_information.offence_description,
                    registration_notes=self._build_registration_notes(case_summary, investigating_officer),
                ),
                "attachments": FIRAttachments(
                    continuation_notes=self._build_continuation_notes(case_summary),
                    signatures=self._build_signature_block(investigating_officer),
                ),
            }
        ]

    def _output_filename(self, document: FIRDocument, index: int) -> str:
        """Return the fixed FIR Markdown filename."""

        return "fir.md"

    @staticmethod
    def _build_complaint_summary(case_summary: CaseSummary, complainant: PersonReference) -> str:
        """Build a deterministic complaint summary from case data."""

        return (
            f"{complainant.full_name} reported the incident registered as {case_summary.FIR_number} "
            f"at {case_summary.police_station}, {case_summary.district}, {case_summary.state}, "
            f"concerning a {case_summary.crime_category.lower()} allegation at {case_summary.location}."
        )

    @staticmethod
    def _build_registration_notes(case_summary: CaseSummary, investigating_officer: OfficerReference) -> str:
        """Build deterministic registration notes for the FIR."""

        return (
            f"The FIR was registered on {case_summary.FIR_date.isoformat()} under the supervision of "
            f"{investigating_officer.name}, {investigating_officer.rank}, at {case_summary.police_station}."
        )

    @staticmethod
    def _build_continuation_notes(case_summary: CaseSummary) -> str:
        """Build placeholder continuation notes from case data."""

        return (
            f"Continuation for FIR {case_summary.FIR_number}. "
            f"Additional narrative details may be attached as required."
        )

    @staticmethod
    def _build_signature_block(investigating_officer: OfficerReference) -> str:
        """Build a signature block from officer metadata."""

        return (
            f"Prepared by {investigating_officer.name}, {investigating_officer.rank}. "
            f"Buckle number: {investigating_officer.buckle_number}."
        )
