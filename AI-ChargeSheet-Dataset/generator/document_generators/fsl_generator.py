"""Generate FSL report Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.fsl_renderer import FSLRenderer
from generator.schemas.documents._base import CaseSummary, EvidenceReference
from generator.schemas.documents.fsl_schema import FSLReportDocument
from generator.schemas.master_case_schema import MasterCase


class FSLDocumentGenerator(BaseDocumentGenerator[FSLReportDocument]):
    """Generate an FSL report from the case's forensic representation."""

    document_schema_model = FSLReportDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=FSLRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        case = self._master_case
        if case.fsl_report is None:
            return []

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
                "report_id": case.fsl_report.report_id,
                "laboratory_name": case.fsl_report.laboratory_name,
                "report_date": case.fsl_report.report_date,
                "examined_evidence": evidence,
                "examination_summary": case.fsl_report.examination_summary,
                "findings": case.fsl_report.findings,
                "conclusion": case.fsl_report.conclusion,
                "remarks": case.fsl_report.remarks,
            }
        ]

    def _output_filename(self, document: FSLReportDocument, index: int) -> str:
        return "fsl_report.md"
