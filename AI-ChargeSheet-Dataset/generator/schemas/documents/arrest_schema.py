"""Pydantic schema for arrest memo documents."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import CaseSummary, DocumentSchemaBase, OfficerReference, PersonReference, WitnessReference


class ArrestMemoDocument(DocumentSchemaBase):
    """Structured arrest memo document ready for Markdown rendering."""

    document_type: Literal["Arrest Memo"] = "Arrest Memo"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    arrest_id: str = Field(description="Arrest record identifier.")
    arrested_person: PersonReference = Field(description="Arrested person's profile.")
    arrest_datetime: datetime = Field(description="Date and time of arrest.")
    arrest_location: str = Field(description="Location where the arrest occurred.")
    grounds_of_arrest: str = Field(description="Recorded grounds for arrest.")
    arresting_officer: OfficerReference = Field(description="Officer who conducted the arrest.")
    witnesses: list[WitnessReference] = Field(default_factory=list, description="Witnesses present during arrest.")
    memo_number: str = Field(description="Arrest memo number.")
    remarks: str | None = Field(default=None, description="Additional arrest remarks.")
