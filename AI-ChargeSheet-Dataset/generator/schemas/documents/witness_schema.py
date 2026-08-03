"""Pydantic schema for witness statement documents."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import (
    CaseSummary,
    DocumentSchemaBase,
    EvidenceReference,
    OfficerReference,
    PersonReference,
    WitnessReference,
)


class WitnessStatementBody(DocumentSchemaBase):
    """The body of a witness statement document."""

    statement_title: str = Field(description="Human-readable title for the witness statement.")
    statement_text: str = Field(description="Complete witness statement text.")
    relationship_context: str | None = Field(default=None, description="Relationship context for the witness.")
    observed_events: list[str] = Field(default_factory=list, description="Observed events mentioned by the witness.")


class WitnessStatementDocument(DocumentSchemaBase):
    """Structured witness statement document ready for Markdown rendering."""

    document_type: Literal["Witness Statement"] = "Witness Statement"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    witness: WitnessReference = Field(description="Witness providing the statement.")
    recorded_by: OfficerReference = Field(description="Officer who recorded the statement.")
    statement: WitnessStatementBody = Field(description="Statement body.")
    mentioned_people: list[PersonReference] = Field(default_factory=list, description="People mentioned in the statement.")
    mentioned_evidence: list[EvidenceReference] = Field(default_factory=list, description="Evidence items mentioned in the statement.")
    statement_index: int = Field(ge=1, description="Ordinal index of the witness statement within the case.")
