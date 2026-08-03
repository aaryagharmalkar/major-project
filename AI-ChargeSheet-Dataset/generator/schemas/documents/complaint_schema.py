"""Pydantic schema for complaint documents derived from a MasterCase."""

from __future__ import annotations

from pydantic import Field

from generator.schemas.documents._base import DocumentSchemaBase, PersonReference


class ComplaintDocument(DocumentSchemaBase):
    """Structured complaint document data ready for Markdown rendering."""

    complaint_number: str = Field(description="Complaint reference number.")
    complainant: PersonReference = Field(description="Complainant profile.")
    incident_date: str = Field(description="Date of the incident.")
    location: str = Field(description="Place of occurrence.")
    offence_description: str = Field(description="Offence description.")
    narrative: str = Field(description="Summary of the complaint narrative.")
    accused_details: str = Field(description="Accused details summary.")
    signature: str = Field(description="Officer signature or endorsement line.")
