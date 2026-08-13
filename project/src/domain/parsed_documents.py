"""Typed, document-local outputs produced from OCR text without case-level reasoning."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from .common import DomainModel
from .documents import DocumentType


class ParseMetadata(DomainModel):
    parser_name: str
    parse_duration_ms: float = Field(ge=0)
    validation_success: bool = True
    retry_count: int = Field(ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: tuple[str, ...] = ()


class ParsedDocument(DomainModel):
    document_id: UUID
    document_type: DocumentType
    ocr_text_sha256: str = Field(pattern=r"^[A-Fa-f0-9]{64}$")
    parse_metadata: ParseMetadata


class FIR(ParsedDocument):
    document_type: Literal[DocumentType.FIR] = DocumentType.FIR
    fir_number: str | None = None
    crime_number: str | None = None
    registration_date: date | None = None
    police_station: str | None = None
    complainant_name: str | None = None
    accused_names: tuple[str, ...] = ()
    victim_names: tuple[str, ...] = ()
    vehicle_registrations: tuple[str, ...] = ()
    occurrence_datetime: datetime | None = None
    occurrence_location: str | None = None
    jurisdiction: str | None = None
    court: str | None = None
    reported_sections: tuple[str, ...] = ()
    narrative_text: str | None = None


class Complaint(ParsedDocument):
    document_type: Literal[DocumentType.COMPLAINT] = DocumentType.COMPLAINT
    complaint_date: date | None = None
    complainant_name: str | None = None
    complainant_address: str | None = None
    person_complained_against_names: tuple[str, ...] = ()
    victim_names: tuple[str, ...] = ()
    vehicle_registrations: tuple[str, ...] = ()
    complaint_text: str | None = None


class MedicalReport(ParsedDocument):
    document_type: Literal[DocumentType.MEDICAL_REPORT] = DocumentType.MEDICAL_REPORT
    report_number: str | None = None
    report_date: date | None = None
    patient_name: str | None = None
    doctor_name: str | None = None
    hospital_name: str | None = None
    observations: tuple[str, ...] = ()
    opinion_text: str | None = None


class PostmortemReport(ParsedDocument):
    document_type: Literal[DocumentType.POSTMORTEM_REPORT] = DocumentType.POSTMORTEM_REPORT
    report_number: str | None = None
    examination_date: date | None = None
    deceased_name: str | None = None
    doctor_name: str | None = None
    findings: tuple[str, ...] = ()
    opinion_text: str | None = None


class FSLReport(ParsedDocument):
    document_type: Literal[DocumentType.FSL_REPORT] = DocumentType.FSL_REPORT
    report_number: str | None = None
    report_date: date | None = None
    laboratory_name: str | None = None
    examined_items: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    opinion_text: str | None = None


class WitnessStatement(ParsedDocument):
    document_type: Literal[DocumentType.WITNESS_STATEMENT] = DocumentType.WITNESS_STATEMENT
    statement_date: date | None = None
    witness_name: str | None = None
    witness_address: str | None = None
    recorded_by: str | None = None
    statement_text: str | None = None


class CaseDiaryEntry(DomainModel):
    entry_number: str | None = None
    entry_datetime: datetime | None = None
    text: str | None = None


class CaseDiary(ParsedDocument):
    document_type: Literal[DocumentType.CASE_DIARY] = DocumentType.CASE_DIARY
    diary_number: str | None = None
    officer_name: str | None = None
    entries: tuple[CaseDiaryEntry, ...] = ()


class ArrestMemo(ParsedDocument):
    document_type: Literal[DocumentType.ARREST_MEMO] = DocumentType.ARREST_MEMO
    memo_number: str | None = None
    arrest_datetime: datetime | None = None
    arrested_person_name: str | None = None
    arrest_location: str | None = None
    arresting_officer_name: str | None = None


class SeizureItem(DomainModel):
    description: str | None = None
    exhibit_mark: str | None = None


class SeizureMemo(ParsedDocument):
    document_type: Literal[DocumentType.SEIZURE_MEMO] = DocumentType.SEIZURE_MEMO
    memo_number: str | None = None
    seizure_datetime: datetime | None = None
    seizure_location: str | None = None
    seized_items: tuple[SeizureItem, ...] = ()
    prepared_by: str | None = None


class SpotPanchnama(ParsedDocument):
    document_type: Literal[DocumentType.SPOT_PANCHNAMA] = DocumentType.SPOT_PANCHNAMA
    memo_number: str | None = None
    inspection_datetime: datetime | None = None
    location: str | None = None
    observations: tuple[str, ...] = ()
    witnesses: tuple[str, ...] = ()


class VehicleInspection(ParsedDocument):
    document_type: Literal[DocumentType.VEHICLE_INSPECTION] = DocumentType.VEHICLE_INSPECTION
    report_number: str | None = None
    inspection_date: date | None = None
    vehicle_registration: str | None = None
    inspected_by: str | None = None
    observations: tuple[str, ...] = ()


class SitePlan(ParsedDocument):
    document_type: Literal[DocumentType.SITE_PLAN] = DocumentType.SITE_PLAN
    plan_number: str | None = None
    plan_date: date | None = None
    location: str | None = None
    prepared_by: str | None = None
    annotations: tuple[str, ...] = ()


class CCTVMetadata(ParsedDocument):
    document_type: Literal[DocumentType.CCTV_IMAGE] = DocumentType.CCTV_IMAGE
    camera_identifier: str | None = None
    recording_datetime: datetime | None = None
    location: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0)
    metadata_text: str | None = None


class UnknownDocument(ParsedDocument):
    document_type: Literal[DocumentType.OTHER] = DocumentType.OTHER
    raw_text: str
