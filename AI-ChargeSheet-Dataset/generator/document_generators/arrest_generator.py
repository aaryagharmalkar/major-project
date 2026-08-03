"""Generate arrest memo Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.arrest_renderer import ArrestRenderer
from generator.schemas.documents._base import CaseSummary, OfficerReference, PersonReference, WitnessReference
from generator.schemas.documents.arrest_schema import ArrestMemoDocument
from generator.schemas.master_case_schema import MasterCase


class ArrestDocumentGenerator(BaseDocumentGenerator[ArrestMemoDocument]):
    """Generate an arrest memo from the case's arrest data."""

    document_schema_model = ArrestMemoDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=ArrestRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []
        for entry in self._master_case.arrest_details:
            arrested = next((person for person in self._master_case.accused if person.person_id == entry.arrested_person_id), None)
            if arrested is None:
                continue
            witness_refs = [
                WitnessReference(
                    person_id=self._master_case.witnesses[index].person_id if index < len(self._master_case.witnesses) else "",
                    full_name=self._master_case.witnesses[index].full_name if index < len(self._master_case.witnesses) else "",
                    age=self._master_case.witnesses[index].age if index < len(self._master_case.witnesses) else 0,
                    gender=self._master_case.witnesses[index].gender if index < len(self._master_case.witnesses) else "",
                    occupation=self._master_case.witnesses[index].occupation if index < len(self._master_case.witnesses) else "",
                    address=self._master_case.witnesses[index].address if index < len(self._master_case.witnesses) else "",
                    phone=self._master_case.witnesses[index].phone if index < len(self._master_case.witnesses) else None,
                    relationship_to_case=self._master_case.witnesses[index].relationship_to_case if index < len(self._master_case.witnesses) else None,
                    statement_summary=self._master_case.witnesses[index].statement_summary if index < len(self._master_case.witnesses) else None,
                    is_hostile=self._master_case.witnesses[index].is_hostile if index < len(self._master_case.witnesses) else False,
                )
                for index in range(len(self._master_case.witnesses))
            ]
            documents.append(
                {
                    "case_summary": CaseSummary(
                        case_id=self._master_case.case_information.case_id,
                        crime_category=self._master_case.case_information.crime_category,
                        FIR_number=self._master_case.case_information.FIR_number,
                        FIR_date=self._master_case.case_information.FIR_date,
                        incident_date=self._master_case.case_information.incident_date,
                        incident_time=self._master_case.case_information.incident_time,
                        police_station=self._master_case.case_information.police_station,
                        district=self._master_case.case_information.district,
                        state=self._master_case.case_information.state,
                        location=self._master_case.case_information.location,
                    ),
                    "arrest_id": entry.arrest_id,
                    "arrested_person": PersonReference(
                        person_id=arrested.person_id,
                        full_name=arrested.full_name,
                        age=arrested.age,
                        gender=arrested.gender,
                        occupation=arrested.occupation,
                        address=arrested.address,
                        phone=arrested.phone,
                    ),
                    "arrest_datetime": entry.arrest_datetime,
                    "arrest_location": entry.arrest_location,
                    "grounds_of_arrest": entry.grounds_of_arrest,
                    "arresting_officer": OfficerReference(
                        name=self._master_case.investigating_officer.name,
                        rank=self._master_case.investigating_officer.rank,
                        buckle_number=self._master_case.investigating_officer.buckle_number,
                        police_station=self._master_case.investigating_officer.police_station,
                        phone=self._master_case.investigating_officer.phone,
                    ),
                    "witnesses": witness_refs,
                    "memo_number": entry.memo_number,
                    "remarks": entry.remarks,
                }
            )
        return documents

    def _output_filename(self, document: ArrestMemoDocument, index: int) -> str:
        return f"arrest_{index:02d}.md"
