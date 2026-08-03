"""Layout-driven Pydantic schema for FIR documents derived from a MasterCase."""

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


class FIRHeader(DocumentSchemaBase):
    """Header block for the FIR form."""

    fir_number: str = Field(description="Official FIR number.")
    registration_date: str = Field(description="Date of FIR registration.")
    police_station: str = Field(description="Police station handling the FIR.")
    district: str = Field(description="District where the FIR was registered.")
    state: str = Field(description="State where the FIR was registered.")


class FIRRegistrationDetails(DocumentSchemaBase):
    """Core registration and incident metadata."""

    crime_category: str = Field(description="Crime category or offence heading.")
    offence_description: str = Field(description="Narrative description of the offence.")
    incident_date: str = Field(description="Date of the incident.")
    incident_time: str = Field(description="Time of the incident.")
    place_of_occurrence: str = Field(description="Place where the incident occurred.")


class FIRComplainant(DocumentSchemaBase):
    """Complainant details captured in the FIR."""

    person: PersonReference = Field(description="Complainant reference data.")


class FIRAccused(DocumentSchemaBase):
    """Accused details captured in the FIR."""

    person: PersonReference = Field(description="Accused reference data.")
    aliases: list[str] = Field(default_factory=list, description="Known aliases for the accused person.")
    charges: list[str] = Field(default_factory=list, description="Charges or allegations recorded.")


class FIRNarrative(DocumentSchemaBase):
    """Narrative body of the FIR."""

    complaint_summary: str = Field(description="Short complaint summary.")
    occurrence_narrative: str = Field(description="Full narrative text as recorded in the FIR.")
    registration_notes: str | None = Field(default=None, description="Notes about FIR registration.")


class FIRInvestigationDetails(DocumentSchemaBase):
    """Investigation facts attached to the FIR."""

    officer: OfficerReference = Field(description="Investigating officer details.")
    witnesses: list[WitnessReference] = Field(default_factory=list, description="Witnesses mentioned in the FIR.")
    evidence: list[EvidenceReference] = Field(default_factory=list, description="Evidence referenced in the FIR.")
    applicable_sections: list[LegalSectionReference] = Field(
        default_factory=list,
        description="Legal sections referenced in the FIR.",
    )


class FIRAttachments(DocumentSchemaBase):
    """Attachment / continuation notes section."""

    continuation_notes: str | None = Field(default=None, description="Continuation or attachment notes.")
    signatures: str | None = Field(default=None, description="Officer signature or attestation line.")


class FIRDocument(DocumentSchemaBase):
    """Structured FIR document data ready for Markdown rendering."""

    document_type: Literal["First Information Report"] = "First Information Report"
    case_summary: CaseSummary = Field(description="Case identifiers and incident metadata.")
    header: FIRHeader = Field(description="Header block for the FIR form.")
    registration_details: FIRRegistrationDetails = Field(description="Registration and occurrence metadata.")
    complainant: FIRComplainant = Field(description="Complainant details.")
    accused: list[FIRAccused] = Field(default_factory=list, description="Known accused persons.")
    investigation_details: FIRInvestigationDetails = Field(description="Investigation-related details.")
    narrative: FIRNarrative = Field(description="Narrative block.")
    attachments: FIRAttachments = Field(description="Attachment and signature notes.")
