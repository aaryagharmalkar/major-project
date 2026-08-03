"""Pydantic schema for spot panchanama documents."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from generator.schemas.documents._base import CaseSummary, DocumentSchemaBase


class SpotPanchanamaDocument(DocumentSchemaBase):
    """Structured spot panchanama document ready for Markdown rendering."""

    document_type: Literal["Spot Panchanama"] = "Spot Panchanama"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    panchanama_id: str = Field(description="Unique panchanama identifier.")
    prepared_by: str = Field(description="Name of the officer who prepared the document.")
    prepared_at: datetime = Field(description="Date and time when the panchanama was prepared.")
    location: str = Field(description="Location of the spot observation.")
    observation_summary: str = Field(description="Observation summary for the spot panchanama.")
    attesting_witness_ids: list[str] = Field(default_factory=list, description="Witness identifiers attesting the spot panchanama.")
    sketch_reference: str | None = Field(default=None, description="Optional sketch reference.")
    photograph_references: list[str] = Field(default_factory=list, description="Photograph references associated with the panchanama.")
