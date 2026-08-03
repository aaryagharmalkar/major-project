"""Master case schema for the charge sheet dataset generation pipeline.

This module defines the complete source-of-truth data model used to generate
all downstream documents, ground-truth artifacts, and evaluation outputs.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


NonEmptyString = Annotated[str, Field(min_length=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class SchemaBaseModel(BaseModel):
	"""Base model with strict, production-friendly validation settings."""

	model_config = ConfigDict(
		extra="forbid",
		populate_by_name=True,
		str_strip_whitespace=True,
		validate_assignment=True,
	)


class CaseInformation(SchemaBaseModel):
	"""Core case-level identifiers and incident metadata."""

	case_id: NonEmptyString = Field(description="Unique identifier for the case.")
	crime_category: NonEmptyString = Field(description="High-level crime category.")
	offence_description: NonEmptyString = Field(
		description="Narrative description of the alleged offence."
	)
	police_station: NonEmptyString = Field(description="Investigating police station.")
	district: NonEmptyString = Field(description="District where the case is registered.")
	state: NonEmptyString = Field(description="State where the case is registered.")
	FIR_number: NonEmptyString = Field(description="FIR reference number.")
	FIR_date: date = Field(description="Date on which the FIR was registered.")
	incident_date: date = Field(description="Date on which the incident occurred.")
	incident_time: time = Field(description="Approximate time of the incident.")
	location: NonEmptyString = Field(description="Primary incident location.")


class Person(SchemaBaseModel):
	"""Reusable base model for people involved in the case."""

	person_id: NonEmptyString = Field(description="Unique identifier for the person.")
	full_name: NonEmptyString = Field(description="Legal or known full name.")
	age: NonNegativeInt = Field(ge=0, le=120, description="Age in years.")
	gender: NonEmptyString = Field(description="Gender as captured in the source case data.")
	occupation: NonEmptyString = Field(description="Occupation or role of the person.")
	address: NonEmptyString = Field(description="Residential address or location description.")
	phone: str | None = Field(default=None, description="Optional contact number.")


class Injury(SchemaBaseModel):
	"""Medical injury record associated with the victim or examination subject."""

	body_part: NonEmptyString = Field(description="Injured body part.")
	injury_type: NonEmptyString = Field(description="Clinical or descriptive injury type.")
	severity: NonEmptyString = Field(description="Severity classification of the injury.")


class Victim(Person):
	"""Victim profile used across FIR, medical, and witness narratives."""

	injuries: list[Injury] = Field(
		default_factory=list,
		description="Observed injuries linked to the victim.",
	)
	statement_summary: str | None = Field(
		default=None,
		description="Optional summary of the victim's version of events.",
	)
	relationship_to_accused: str | None = Field(
		default=None,
		description="Optional relationship, if any, between victim and accused.",
	)


class Accused(Person):
	"""Accused person profile used throughout the investigation record."""

	alias_names: list[NonEmptyString] = Field(
		default_factory=list,
		description="Known aliases or other names used by the accused.",
	)
	charges: list[NonEmptyString] = Field(
		default_factory=list,
		description="Case-specific allegations or charge labels linked to this person.",
	)
	custody_status: str | None = Field(
		default=None,
		description="Optional custody or bail status.",
	)


class Witness(Person):
	"""Witness profile used for statements, diary entries, and annexures."""

	statement_summary: str | None = Field(
		default=None,
		description="Optional summary of the witness statement.",
	)
	relationship_to_case: str | None = Field(
		default=None,
		description="Optional relationship of the witness to the incident or parties.",
	)
	is_hostile: bool = Field(
		default=False,
		description="Whether the witness is recorded as hostile or uncooperative.",
	)


class InvestigatingOfficer(SchemaBaseModel):
	"""Investigating officer assigned to the case."""

	name: NonEmptyString = Field(description="Name of the investigating officer.")
	rank: NonEmptyString = Field(description="Rank or designation of the officer.")
	buckle_number: NonEmptyString = Field(description="Service or buckle number.")
	police_station: NonEmptyString = Field(description="Police station of posting.")
	phone: str | None = Field(default=None, description="Optional officer contact number.")


class TimelineEvent(SchemaBaseModel):
	"""Chronological event used to reconstruct the case timeline."""

	timestamp: datetime = Field(description="Date and time of the event.")
	event_type: NonEmptyString = Field(description="Type or stage of the event.")
	description: NonEmptyString = Field(description="Short narrative of the event.")
	related_people: list[NonEmptyString] = Field(
		default_factory=list,
		description="Person identifiers associated with the event.",
	)
	related_evidence: list[NonEmptyString] = Field(
		default_factory=list,
		description="Evidence identifiers associated with the event.",
	)


class Evidence(SchemaBaseModel):
	"""Physical or documentary evidence recorded in the investigation."""

	evidence_id: NonEmptyString = Field(description="Unique identifier for the evidence item.")
	evidence_type: NonEmptyString = Field(description="Category of evidence item.")
	description: NonEmptyString = Field(description="Narrative description of the evidence.")
	recovered_from: NonEmptyString = Field(description="Location or person from whom it was recovered.")
	seizure_date: date = Field(description="Date on which the evidence was seized.")
	forensic_required: bool = Field(
		default=False,
		description="Whether the item requires forensic examination.",
	)


class MedicalReport(SchemaBaseModel):
	"""Medical examination summary for the victim or another examined person."""

	report_id: NonEmptyString = Field(description="Unique identifier for the medical report.")
	subject_person_id: NonEmptyString = Field(description="Person identifier of the examined subject.")
	hospital_name: NonEmptyString = Field(description="Hospital or medical facility name.")
	doctor_name: NonEmptyString = Field(description="Examining doctor or medical officer.")
	examination_datetime: datetime = Field(description="Date and time of examination.")
	injuries: list[Injury] = Field(
		default_factory=list,
		description="Injuries documented during the medical examination.",
	)
	medical_opinion: str | None = Field(
		default=None,
		description="Optional medical opinion or diagnosis summary.",
	)
	fit_for_statement: bool | None = Field(
		default=None,
		description="Optional fitness assessment for giving a statement.",
	)
	fit_for_arrest: bool | None = Field(
		default=None,
		description="Optional fitness assessment relevant to arrest procedures.",
	)
	remarks: str | None = Field(default=None, description="Additional medical remarks.")


class FSLReport(SchemaBaseModel):
	"""Forensic Science Laboratory report linked to seized evidence."""

	report_id: NonEmptyString = Field(description="Unique identifier for the FSL report.")
	laboratory_name: NonEmptyString = Field(description="Name of the forensic laboratory.")
	report_date: date = Field(description="Date on which the FSL report was issued.")
	examined_evidence_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="Evidence identifiers covered by the forensic analysis.",
	)
	examination_summary: str | None = Field(
		default=None,
		description="Summary of the analysis performed by the laboratory.",
	)
	findings: str | None = Field(default=None, description="Key findings from the report.")
	conclusion: str | None = Field(default=None, description="Final forensic conclusion.")
	remarks: str | None = Field(default=None, description="Additional forensic remarks.")


class ArrestDetails(SchemaBaseModel):
	"""Arrest record tied to one or more accused persons."""

	arrest_id: NonEmptyString = Field(description="Unique identifier for the arrest record.")
	arrested_person_id: NonEmptyString = Field(description="Identifier of the arrested person.")
	arrest_datetime: datetime = Field(description="Date and time of arrest.")
	arrest_location: NonEmptyString = Field(description="Place where the arrest occurred.")
	grounds_of_arrest: NonEmptyString = Field(description="Brief grounds recorded for the arrest.")
	arresting_officer_name: NonEmptyString = Field(description="Name of the arresting officer.")
	arresting_officer_buckle_number: NonEmptyString = Field(
		description="Buckle number of the arresting officer."
	)
	memo_number: NonEmptyString = Field(description="Arrest memo number.")
	witness_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="Witness identifiers present during arrest.",
	)
	remarks: str | None = Field(default=None, description="Additional arrest remarks.")


class SeizureDetails(SchemaBaseModel):
	"""Seizure record describing recovered items and supporting witnesses."""

	seizure_id: NonEmptyString = Field(description="Unique identifier for the seizure record.")
	memo_number: NonEmptyString = Field(description="Seizure memo number.")
	seizure_datetime: datetime = Field(description="Date and time of the seizure.")
	seizure_location: NonEmptyString = Field(description="Place where the seizure occurred.")
	seizing_officer_name: NonEmptyString = Field(description="Name of the officer who seized the items.")
	seizing_officer_buckle_number: NonEmptyString = Field(
		description="Buckle number of the seizing officer."
	)
	witness_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="Witness identifiers associated with the seizure.",
	)
	evidence_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="Evidence identifiers covered by this seizure.",
	)
	inventory_reference: str | None = Field(
		default=None,
		description="Optional reference to the seizure inventory or annexure.",
	)
	remarks: str | None = Field(default=None, description="Additional seizure remarks.")


class SpotPanchanama(SchemaBaseModel):
	"""Spot panchanama capturing observations from the incident location."""

	panchanama_id: NonEmptyString = Field(description="Unique identifier for the panchanama.")
	prepared_by: NonEmptyString = Field(description="Name of the officer who prepared it.")
	prepared_at: datetime = Field(description="Date and time the panchanama was prepared.")
	location: NonEmptyString = Field(description="Exact or descriptive spot location.")
	observation_summary: NonEmptyString = Field(description="Summary of observations at the scene.")
	attesting_witness_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="Witness identifiers attesting the spot panchanama.",
	)
	sketch_reference: str | None = Field(
		default=None,
		description="Optional reference to a scene sketch or diagram.",
	)
	photograph_references: list[NonEmptyString] = Field(
		default_factory=list,
		description="Optional photograph or media references.",
	)


class CaseDiaryEntry(SchemaBaseModel):
	"""Single investigative diary entry recorded by the investigating officer."""

	entry_number: NonNegativeInt = Field(description="Sequential case diary entry number.")
	timestamp: datetime = Field(description="Date and time of the diary entry.")
	author_name: NonEmptyString = Field(description="Name of the entry author.")
	content: NonEmptyString = Field(description="Diary entry text.")
	related_people_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="People identifiers mentioned in the entry.",
	)
	related_evidence_ids: list[NonEmptyString] = Field(
		default_factory=list,
		description="Evidence identifiers mentioned in the entry.",
	)


class BNSSection(SchemaBaseModel):
	"""Single Bharatiya Nyaya Sanhita section applicable to the case."""

	section_code: NonEmptyString = Field(description="Official section code.")
	section_title: NonEmptyString = Field(description="Short title of the section.")
	description: NonEmptyString = Field(description="Human-readable section description.")
	applicability_notes: str | None = Field(
		default=None,
		description="Optional case-specific notes on applicability.",
	)


class ApplicableBNSSections(SchemaBaseModel):
	"""Container for the legal sections relevant to the case."""

	sections: list[BNSSection] = Field(
		default_factory=list,
		description="List of applicable BNS sections.",
	)


class GeneratedDocumentMetadata(SchemaBaseModel):
	"""Metadata for a generated downstream document."""

	document_type: NonEmptyString = Field(description="Type of generated document.")
	template_name: NonEmptyString = Field(description="Template used to render the document.")
	output_file_name: NonEmptyString = Field(description="Target output file name.")
	output_format: NonEmptyString = Field(description="Output format such as PDF or JSON.")
	version: NonEmptyString = Field(description="Document version or revision label.")
	generated_at: datetime | None = Field(
		default=None,
		description="Optional timestamp when the document was generated.",
	)
	notes: str | None = Field(default=None, description="Optional metadata notes.")


class GeneratedDocumentsMetadata(SchemaBaseModel):
	"""Container for metadata about all derived documents for the case."""

	documents: list[GeneratedDocumentMetadata] = Field(
		default_factory=list,
		description="Metadata entries for each generated case document.",
	)


class MasterCase(SchemaBaseModel):
	"""Root source-of-truth model for a complete criminal investigation case."""

	case_information: CaseInformation = Field(description="Case-level information and incident metadata.")
	victim: Victim = Field(description="Primary victim profile.")
	accused: list[Accused] = Field(
		default_factory=list,
		description="Accused persons linked to the case.",
	)
	witnesses: list[Witness] = Field(
		default_factory=list,
		description="Witnesses associated with the case.",
	)
	investigating_officer: InvestigatingOfficer = Field(
		description="Investigating officer responsible for the case."
	)
	timeline: list[TimelineEvent] = Field(
		default_factory=list,
		description="Chronological sequence of investigation events.",
	)
	evidence: list[Evidence] = Field(
		default_factory=list,
		description="Evidence items collected in the case.",
	)
	medical_report: MedicalReport | None = Field(
		default=None,
		description="Optional medical report for the victim or subject.",
	)
	fsl_report: FSLReport | None = Field(
		default=None,
		description="Optional forensic laboratory report.",
	)
	arrest_details: list[ArrestDetails] = Field(
		default_factory=list,
		description="Arrest records associated with the case.",
	)
	seizure_details: list[SeizureDetails] = Field(
		default_factory=list,
		description="Seizure records associated with the case.",
	)
	spot_panchanama: SpotPanchanama | None = Field(
		default=None,
		description="Optional spot panchanama for the incident scene.",
	)
	case_diary_entries: list[CaseDiaryEntry] = Field(
		default_factory=list,
		description="Case diary entries maintained by the investigating officer.",
	)
	applicable_bns_sections: ApplicableBNSSections = Field(
		default_factory=ApplicableBNSSections,
		description="Relevant BNS sections for the case.",
	)
	generated_documents_metadata: GeneratedDocumentsMetadata = Field(
		default_factory=GeneratedDocumentsMetadata,
		description="Metadata for all generated documents derived from this master case.",
	)
