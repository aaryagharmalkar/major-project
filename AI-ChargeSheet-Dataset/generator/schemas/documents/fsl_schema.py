"""Pydantic schema for FSL report documents."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import CaseSummary, DocumentSchemaBase, EvidenceReference


class FSLReportDocument(DocumentSchemaBase):
    """Structured forensic laboratory report ready for Markdown rendering."""

    document_type: Literal["FSL Report"] = "FSL Report"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    report_id: str = Field(description="Forensic report identifier.")
    laboratory_name: str = Field(description="Name of the forensic laboratory.")
    report_date: date = Field(description="Date on which the FSL report was issued.")
    examined_evidence: list[EvidenceReference] = Field(default_factory=list, description="Evidence items examined by the FSL.")
    examination_summary: str | None = Field(default=None, description="Summary of the examination process.")
    findings: str | None = Field(default=None, description="Key findings from the FSL report.")
    conclusion: str | None = Field(default=None, description="Final forensic conclusion.")
    remarks: str | None = Field(default=None, description="Additional forensic remarks.")
