"""Pydantic schema for medical report documents."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import (
    CaseSummary,
    DocumentSchemaBase,
    InjuryReference,
    OfficerReference,
    PersonReference,
)


class MedicalExamination(DocumentSchemaBase):
    """Medical examination metadata and findings."""

    hospital_name: str = Field(description="Hospital or medical facility name.")
    doctor_name: str = Field(description="Name of the examining doctor.")
    examination_datetime: datetime = Field(description="Date and time of the medical examination.")
    medical_opinion: str | None = Field(default=None, description="Medical opinion or diagnosis summary.")
    fit_for_statement: bool | None = Field(default=None, description="Fitness for giving a statement.")
    fit_for_arrest: bool | None = Field(default=None, description="Fitness relevant to arrest procedures.")
    remarks: str | None = Field(default=None, description="Additional medical remarks.")


class MedicalReportDocument(DocumentSchemaBase):
    """Structured medical report document ready for Markdown rendering."""

    document_type: Literal["Medical Report"] = "Medical Report"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    patient: PersonReference = Field(description="Patient or victim examined in the medical report.")
    examining_officer: OfficerReference = Field(description="Medical officer or doctor reference.")
    examination: MedicalExamination = Field(description="Medical examination details.")
    injuries: list[InjuryReference] = Field(default_factory=list, description="Injuries documented during examination.")
