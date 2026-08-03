"""Generate seizure memo Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.seizure_renderer import SeizureRenderer
from generator.schemas.documents._base import CaseSummary, EvidenceReference, OfficerReference, WitnessReference
from generator.schemas.documents.seizure_schema import SeizureMemoDocument
from generator.schemas.master_case_schema import MasterCase


class SeizureDocumentGenerator(BaseDocumentGenerator[SeizureMemoDocument]):
    """Generate a seizure memo from the case's seizure data."""

    document_schema_model = SeizureMemoDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=SeizureRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []
        for entry in self._master_case.seizure_details:
            case_summary = CaseSummary(
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
            )
            witnesses = [
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
            evidence = [
                EvidenceReference(
                    evidence_id=item.evidence_id,
                    evidence_type=item.evidence_type,
                    description=item.description,
                    recovered_from=item.recovered_from,
                    seizure_date=item.seizure_date,
                    forensic_required=item.forensic_required,
                )
                for item in self._master_case.evidence
            ]
            documents.append(
                {
                    "case_summary": case_summary,
                    "memo_number": entry.memo_number,
                    "seizure_datetime": entry.seizure_datetime,
                    "seizure_location": entry.seizure_location,
                    "seizing_officer": OfficerReference(
                        name=self._master_case.investigating_officer.name,
                        rank=self._master_case.investigating_officer.rank,
                        buckle_number=self._master_case.investigating_officer.buckle_number,
                        police_station=self._master_case.investigating_officer.police_station,
                        phone=self._master_case.investigating_officer.phone,
                    ),
                    "witnesses": witnesses,
                    "evidence": evidence,
                    "inventory_reference": entry.inventory_reference,
                    "remarks": entry.remarks,
                }
            )
        return documents

    def _output_filename(self, document: SeizureMemoDocument, index: int) -> str:
        return f"seizure_{index:02d}.md"
