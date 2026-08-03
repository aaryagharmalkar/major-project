"""Generate charge sheet Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.chargesheet_renderer import ChargeSheetRenderer
from generator.schemas.documents._base import CaseSummary, EvidenceReference, LegalSectionReference, OfficerReference, PersonReference, WitnessReference
from generator.schemas.documents.chargesheet_schema import ChargeSheetDocument, ChargeSheetFinding
from generator.schemas.master_case_schema import MasterCase


class ChargeSheetDocumentGenerator(BaseDocumentGenerator[ChargeSheetDocument]):
    """Generate a charge sheet from the case data."""

    document_schema_model = ChargeSheetDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=ChargeSheetRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        case = self._master_case
        accused = [
            PersonReference(
                person_id=person.person_id,
                full_name=person.full_name,
                age=person.age,
                gender=person.gender,
                occupation=person.occupation,
                address=person.address,
                phone=person.phone,
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
        sections = [
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
                "case_summary": CaseSummary(
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
                ),
                "investigating_officer": OfficerReference(
                    name=case.investigating_officer.name,
                    rank=case.investigating_officer.rank,
                    buckle_number=case.investigating_officer.buckle_number,
                    police_station=case.investigating_officer.police_station,
                    phone=case.investigating_officer.phone,
                ),
                "accused": accused,
                "victim": PersonReference(
                    person_id=case.victim.person_id,
                    full_name=case.victim.full_name,
                    age=case.victim.age,
                    gender=case.victim.gender,
                    occupation=case.victim.occupation,
                    address=case.victim.address,
                    phone=case.victim.phone,
                ),
                "witnesses": witnesses,
                "evidence": evidence,
                "applicable_sections": sections,
                "findings": [
                    ChargeSheetFinding(
                        heading="Summary of Offence",
                        text=case.case_information.offence_description,
                    )
                ],
                "final_status": "Charge sheet prepared",
                "prayer": "Prayer for appropriate trial proceedings.",
                "annexure_notes": "Annexure list to be appended.",
            }
        ]

    def _output_filename(self, document: ChargeSheetDocument, index: int) -> str:
        return "chargesheet.md"
