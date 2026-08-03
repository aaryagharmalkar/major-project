"""Pydantic schema for charge sheet documents."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import (
    CaseSummary,
    DocumentSchemaBase,
    EvidenceReference,
    LegalSectionReference,
    OfficerReference,
    PersonReference,
    WitnessReference,
)


class ChargeSheetFinding(DocumentSchemaBase):
    """Single finding or conclusion section within a charge sheet."""

    heading: str = Field(description="Heading for the finding section.")
    text: str = Field(description="Narrative text for the finding.")


class ChargeSheetDocument(DocumentSchemaBase):
    """Structured charge sheet document ready for Markdown rendering."""

    document_type: Literal["Charge Sheet"] = "Charge Sheet"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    investigating_officer: OfficerReference = Field(description="Investigating officer who prepared the charge sheet.")
    accused: list[PersonReference] = Field(default_factory=list, description="Accused persons in the charge sheet.")
    victim: PersonReference = Field(description="Victim profile.")
    witnesses: list[WitnessReference] = Field(default_factory=list, description="Witnesses supporting the prosecution case.")
    evidence: list[EvidenceReference] = Field(default_factory=list, description="Evidence relied on in the charge sheet.")
    applicable_sections: list[LegalSectionReference] = Field(
        default_factory=list,
        description="Applicable legal sections.",
    )
    findings: list[ChargeSheetFinding] = Field(default_factory=list, description="Narrative findings and conclusions.")
    final_status: str = Field(description="Final investigation status.")
    prayer: str | None = Field(default=None, description="Final prosecution prayer or request.")
    annexure_notes: str | None = Field(default=None, description="Notes about annexures and supporting records.")
