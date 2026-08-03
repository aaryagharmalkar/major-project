"""Shared base models for document-specific schemas.

These models are intentionally small and reusable so document schemas can stay
focused on the content they carry while still validating against consistent
reference structures.
"""

from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class DocumentSchemaBase(BaseModel):
    """Common Pydantic configuration for document schemas."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class CaseSummary(DocumentSchemaBase):
    """Minimal case identifiers shared by every derived document."""

    case_id: str = Field(description="Unique identifier for the case.")
    crime_category: str = Field(description="Crime category of the case.")
    FIR_number: str = Field(description="FIR reference number.")
    FIR_date: date = Field(description="Date on which the FIR was registered.")
    incident_date: date = Field(description="Date on which the incident occurred.")
    incident_time: time = Field(description="Approximate time of the incident.")
    police_station: str = Field(description="Police station handling the case.")
    district: str = Field(description="District where the case is registered.")
    state: str = Field(description="State where the case is registered.")
    location: str = Field(description="Primary incident location.")


class PersonReference(DocumentSchemaBase):
    """Reusable profile for a person referenced by a document."""

    person_id: str = Field(description="Unique person identifier.")
    full_name: str = Field(description="Full name of the person.")
    age: int = Field(ge=0, le=120, description="Age in years.")
    gender: str = Field(description="Gender recorded in the case data.")
    occupation: str = Field(description="Occupation or role of the person.")
    address: str = Field(description="Address associated with the person.")
    phone: str | None = Field(default=None, description="Optional contact number.")


class OfficerReference(DocumentSchemaBase):
    """Reusable profile for a police officer referenced by a document."""

    name: str = Field(description="Officer name.")
    rank: str = Field(description="Officer rank or designation.")
    buckle_number: str = Field(description="Service or buckle number.")
    police_station: str = Field(description="Officer posting location.")
    phone: str | None = Field(default=None, description="Optional officer contact number.")


class WitnessReference(PersonReference):
    """Reusable witness profile with statement context."""

    relationship_to_case: str | None = Field(
        default=None,
        description="Relationship of the witness to the case or parties.",
    )
    statement_summary: str | None = Field(
        default=None,
        description="Short summary of the witness statement.",
    )
    is_hostile: bool = Field(default=False, description="Whether the witness is hostile.")


class EvidenceReference(DocumentSchemaBase):
    """Reusable evidence profile for document rendering."""

    evidence_id: str = Field(description="Unique evidence identifier.")
    evidence_type: str = Field(description="Type of evidence item.")
    description: str = Field(description="Evidence description.")
    recovered_from: str = Field(description="Location or person from whom the evidence was recovered.")
    seizure_date: date | None = Field(default=None, description="Date of seizure.")
    forensic_required: bool = Field(default=False, description="Whether forensic testing is required.")


class LegalSectionReference(DocumentSchemaBase):
    """Reusable legal section profile for documents."""

    section_code: str = Field(description="Official legal section code.")
    section_title: str = Field(description="Short title of the legal section.")
    description: str = Field(description="Readable description of the legal section.")
    applicability_notes: str | None = Field(
        default=None,
        description="Optional notes on why the section applies.",
    )


class InjuryReference(DocumentSchemaBase):
    """Reusable injury profile for medical reporting."""

    body_part: str = Field(description="Affected body part.")
    injury_type: str = Field(description="Type of injury.")
    severity: str = Field(description="Severity classification.")
    notes: str | None = Field(default=None, description="Optional descriptive notes.")


class TimelineEntryReference(DocumentSchemaBase):
    """Reusable timeline entry for diary-style documents."""

    timestamp: datetime = Field(description="Event timestamp.")
    event_type: str = Field(description="Event category.")
    description: str = Field(description="Event description.")
    related_people: list[str] = Field(default_factory=list, description="Related person IDs.")
    related_evidence: list[str] = Field(default_factory=list, description="Related evidence IDs.")


class CaseDiaryEntryReference(DocumentSchemaBase):
    """Reusable case diary entry for the diary document."""

    entry_number: int = Field(ge=0, description="Sequential diary entry number.")
    timestamp: datetime = Field(description="Diary entry timestamp.")
    author_name: str = Field(description="Name of the diary entry author.")
    content: str = Field(description="Diary entry text.")
    related_people_ids: list[str] = Field(default_factory=list, description="Related person IDs.")
    related_evidence_ids: list[str] = Field(default_factory=list, description="Related evidence IDs.")
