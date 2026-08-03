"""Generate medical report Markdown from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.renderers.medical_renderer import MedicalRenderer
from generator.schemas.documents._base import CaseSummary, InjuryReference, OfficerReference, PersonReference
from generator.schemas.documents.medical_schema import MedicalExamination, MedicalReportDocument
from generator.schemas.master_case_schema import MasterCase


class MedicalDocumentGenerator(BaseDocumentGenerator[MedicalReportDocument]):
    """Generate a medical report from the case's medical data."""

    document_schema_model = MedicalReportDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=MedicalRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        case = self._master_case
        if case.medical_report is None:
            return []

        patient = PersonReference(
            person_id=case.victim.person_id,
            full_name=case.victim.full_name,
            age=case.victim.age,
            gender=case.victim.gender,
            occupation=case.victim.occupation,
            address=case.victim.address,
            phone=case.victim.phone,
        )
        examining_officer = OfficerReference(
            name=case.medical_report.doctor_name,
            rank="Doctor",
            buckle_number="",
            police_station=case.case_information.police_station,
            phone=None,
        )
        injuries = [
            InjuryReference(
                body_part=item.body_part,
                injury_type=item.injury_type,
                severity=item.severity,
                notes=None,
            )
            for item in case.victim.injuries
        ]
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
        return [
            {
                "case_summary": case_summary,
                "patient": patient,
                "examining_officer": examining_officer,
                "examination": MedicalExamination(
                    hospital_name=case.medical_report.hospital_name,
                    doctor_name=case.medical_report.doctor_name,
                    examination_datetime=case.medical_report.examination_datetime,
                    medical_opinion=case.medical_report.medical_opinion,
                    fit_for_statement=case.medical_report.fit_for_statement,
                    fit_for_arrest=case.medical_report.fit_for_arrest,
                    remarks=case.medical_report.remarks,
                ),
                "injuries": injuries,
            }
        ]

    def _output_filename(self, document: MedicalReportDocument, index: int) -> str:
        return "medical_report.md"
