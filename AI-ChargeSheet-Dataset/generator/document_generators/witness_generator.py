"""Generate witness statement Markdown documents from a validated MasterCase."""

from __future__ import annotations

from typing import Any

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.schemas.documents._base import (
    CaseSummary,
    EvidenceReference,
    OfficerReference,
    PersonReference,
    WitnessReference,
)
from generator.schemas.documents.witness_schema import WitnessStatementBody, WitnessStatementDocument
from generator.schemas.master_case_schema import MasterCase
from generator.renderers.witness_renderer import WitnessRenderer


class WitnessDocumentGenerator(BaseDocumentGenerator[WitnessStatementDocument]):
    """Generate one witness statement Markdown document per witness in MasterCase."""

    document_schema_model = WitnessStatementDocument

    def __init__(self, master_case: MasterCase, output_directory: str | None = None) -> None:
        super().__init__(master_case, output_directory or ".", renderer=WitnessRenderer())

    def _build_documents(self) -> list[dict[str, Any]]:
        """Build a witness statement payload for every witness in the case."""

        case = self._master_case
        case_summary = CaseSummary(
            case_id=case.case_information.case_id,
            crime_category=case.case_information.crime_category,
            FIR_number=case.case_information.FIR_number,
            FIR_date=case.case_information.FIR_date,
            incident_date=case.case_information.incident_date,
            incident_time=case.case_information.incident_time,
            police_station=case.case_information.police_station,
            district=case.case_information.district,
            state=case.case_information.state,
            location=case.case_information.location,
        )

        recorded_by = OfficerReference(
            name=case.investigating_officer.name,
            rank=case.investigating_officer.rank,
            buckle_number=case.investigating_officer.buckle_number,
            police_station=case.investigating_officer.police_station,
            phone=case.investigating_officer.phone,
        )

        accused_people = [
            PersonReference(
                person_id=person.person_id,
                full_name=person.full_name,
                age=person.age,
                gender=person.gender,
                occupation=person.occupation,
                address=person.address,
                phone=person.phone,
            )
            for person in case.accused
        ]

        evidence_items = [
            EvidenceReference(
                evidence_id=item.evidence_id,
                evidence_type=item.evidence_type,
                description=item.description,
                recovered_from=item.recovered_from,
                seizure_date=item.seizure_date,
                forensic_required=item.forensic_required,
            )
            for item in case.evidence
        ]

        documents: list[dict[str, Any]] = []
        for index, witness in enumerate(case.witnesses, start=1):
            witness_reference = WitnessReference(
                person_id=witness.person_id,
                full_name=witness.full_name,
                age=witness.age,
                gender=witness.gender,
                occupation=witness.occupation,
                address=witness.address,
                phone=witness.phone,
                relationship_to_case=witness.relationship_to_case,
                statement_summary=witness.statement_summary,
                is_hostile=witness.is_hostile,
            )

            statement_body = WitnessStatementBody(
                statement_title=self._build_statement_title(index, witness_reference),
                statement_text=self._build_statement_text(case_summary, witness_reference),
                relationship_context=witness_reference.relationship_to_case,
                observed_events=self._build_observed_events(case, witness_reference),
            )

            documents.append(
                {
                    "case_summary": case_summary,
                    "witness": witness_reference,
                    "recorded_by": recorded_by,
                    "statement": statement_body,
                    "mentioned_people": accused_people,
                    "mentioned_evidence": evidence_items,
                    "statement_index": index,
                }
            )

        return documents

    def _output_filename(self, document: WitnessStatementDocument, index: int) -> str:
        """Return the filename for a witness statement document."""

        return f"witness_{index:02d}.md"

    @staticmethod
    def _build_statement_title(index: int, witness: WitnessReference) -> str:
        """Build a deterministic title for a witness statement."""

        return f"Witness Statement {index:02d} - {witness.full_name}"

    @staticmethod
    def _build_statement_text(case_summary: CaseSummary, witness: WitnessReference) -> str:
        """Build the witness statement body from existing MasterCase facts."""

        summary = witness.statement_summary or "described the events recorded in the case timeline."
        return (
            f"{witness.full_name} stated that they are connected to the case as {witness.relationship_to_case or 'a witness'} "
            f"and provided the following account for FIR {case_summary.FIR_number}: {summary}"
        )

    @staticmethod
    def _build_observed_events(case: MasterCase, witness: WitnessReference) -> list[str]:
        """Build a list of timeline event summaries associated with the witness."""

        observed_events: list[str] = []
        for event in case.timeline:
            if witness.person_id in event.related_people:
                observed_events.append(event.description)
        return observed_events
