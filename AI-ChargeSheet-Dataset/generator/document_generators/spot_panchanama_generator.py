"""Generate spot panchanama Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.spot_panchanama_renderer import SpotPanchanamaRenderer
from generator.schemas.documents._base import CaseSummary
from generator.schemas.documents.spot_panchanama_schema import SpotPanchanamaDocument
from generator.schemas.master_case_schema import MasterCase


class SpotPanchanamaDocumentGenerator(BaseDocumentGenerator[SpotPanchanamaDocument]):
    """Generate a spot panchanama document from the case's scene details."""

    document_schema_model = SpotPanchanamaDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=SpotPanchanamaRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        if self._master_case.spot_panchanama is None:
            return []
        case = self._master_case.spot_panchanama
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
                "panchanama_id": case.panchanama_id,
                "prepared_by": case.prepared_by,
                "prepared_at": case.prepared_at,
                "location": case.location,
                "observation_summary": case.observation_summary,
                "attesting_witness_ids": case.attesting_witness_ids,
                "sketch_reference": case.sketch_reference,
                "photograph_references": case.photograph_references,
            }
        ]

    def _output_filename(self, document: SpotPanchanamaDocument, index: int) -> str:
        return "spot_panchanama.md"
