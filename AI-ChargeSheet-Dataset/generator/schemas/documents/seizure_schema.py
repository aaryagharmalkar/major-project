"""Pydantic schema for seizure memo documents."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import (
    CaseSummary,
    DocumentSchemaBase,
    EvidenceReference,
    OfficerReference,
    WitnessReference,
)


class SeizureMemoDocument(DocumentSchemaBase):
    """Structured seizure memo document ready for Markdown rendering."""

    document_type: Literal["Seizure Memo"] = "Seizure Memo"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    memo_number: str = Field(description="Seizure memo number.")
    seizure_datetime: datetime = Field(description="Date and time of the seizure.")
    seizure_location: str = Field(description="Location where the seizure occurred.")
    seizing_officer: OfficerReference = Field(description="Officer who conducted the seizure.")
    witnesses: list[WitnessReference] = Field(default_factory=list, description="Witnesses present during seizure.")
    evidence: list[EvidenceReference] = Field(default_factory=list, description="Evidence items seized.")
    inventory_reference: str | None = Field(default=None, description="Reference to the seizure inventory.")
    remarks: str | None = Field(default=None, description="Additional seizure remarks.")
