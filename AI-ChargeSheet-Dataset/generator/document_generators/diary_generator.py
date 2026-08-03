"""Generate case diary Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.diary_renderer import DiaryRenderer
from generator.schemas.documents._base import CaseDiaryEntryReference, CaseSummary, OfficerReference
from generator.schemas.documents.diary_schema import CaseDiaryDocument
from generator.schemas.master_case_schema import MasterCase


class DiaryDocumentGenerator(BaseDocumentGenerator[CaseDiaryDocument]):
    """Generate a case diary from the case's chronological diary entries."""

    document_schema_model = CaseDiaryDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=DiaryRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        entries = [
            CaseDiaryEntryReference(
                entry_number=item.entry_number,
                timestamp=item.timestamp,
                author_name=item.author_name,
                content=item.content,
                related_people_ids=item.related_people_ids,
                related_evidence_ids=item.related_evidence_ids,
            )
            for item in self._master_case.case_diary_entries
        ]
        return [
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
                "investigating_officer": OfficerReference(
                    name=self._master_case.investigating_officer.name,
                    rank=self._master_case.investigating_officer.rank,
                    buckle_number=self._master_case.investigating_officer.buckle_number,
                    police_station=self._master_case.investigating_officer.police_station,
                    phone=self._master_case.investigating_officer.phone,
                ),
                "entries": entries,
                "remarks": "Diary generated from master case chronology.",
            }
        ]

    def _output_filename(self, document: CaseDiaryDocument, index: int) -> str:
        return "case_diary.md"
