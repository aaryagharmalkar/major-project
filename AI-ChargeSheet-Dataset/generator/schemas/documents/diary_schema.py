"""Pydantic schema for case diary documents."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import CaseDiaryEntryReference, CaseSummary, DocumentSchemaBase, OfficerReference


class CaseDiaryDocument(DocumentSchemaBase):
    """Structured case diary document ready for Markdown rendering."""

    document_type: Literal["Case Diary"] = "Case Diary"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    investigating_officer: OfficerReference = Field(description="Investigating officer maintaining the diary.")
    entries: list[CaseDiaryEntryReference] = Field(default_factory=list, description="Chronological diary entries.")
    remarks: str | None = Field(default=None, description="Additional diary remarks.")
