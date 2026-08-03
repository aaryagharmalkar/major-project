"""Generate complaint Markdown documents from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.schemas.documents._base import PersonReference
from generator.schemas.documents.complaint_schema import ComplaintDocument
from generator.schemas.master_case_schema import MasterCase
from generator.renderers.complaint_renderer import ComplaintRenderer


class ComplaintDocumentGenerator(BaseDocumentGenerator[ComplaintDocument]):
    """Generate a complaint document from MasterCase data."""

    document_schema_model = ComplaintDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=ComplaintRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        case = self._master_case
        complainant = PersonReference(
            person_id=case.victim.person_id,
            full_name=case.victim.full_name,
            age=case.victim.age,
            gender=case.victim.gender,
            occupation=case.victim.occupation,
            address=case.victim.address,
            phone=case.victim.phone,
        )
        accused_details = ", ".join(person.full_name for person in case.accused)
        return [
            {
                "complaint_number": case.case_information.FIR_number,
                "complainant": complainant,
                "incident_date": case.case_information.incident_date.isoformat(),
                "location": case.case_information.location,
                "offence_description": case.case_information.offence_description,
                "narrative": case.case_information.offence_description,
                "accused_details": accused_details or "None",
                "signature": f"Prepared by {case.investigating_officer.name}",
            }
        ]

    def _output_filename(self, document: ComplaintDocument, index: int) -> str:
        return "complaint.md"
