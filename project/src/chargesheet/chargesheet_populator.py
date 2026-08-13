"""Deterministic projection from Phase 9 outputs; this module never infers facts."""

from __future__ import annotations

from ..context.case_context import CaseContext
from ..legal.legal_findings import LegalFindings, LegalFindingStatus
from ..normalization.canonical_models import CanonicalFact
from .form_if5_schema import ChargeSheetData, ChargeSheetField, ChargeSheetLegalFinding, ChargeSheetReviewItem, FieldStatus, IF5Row
from .presentation import document_action_statement, format_inline, format_value, is_temporal_value, label, sentence, unique_lines


class ChargeSheetPopulator:
    def _unavailable(self) -> ChargeSheetField:
        return ChargeSheetField(status=FieldStatus.UNAVAILABLE, review_required=True)

    def _field(self, fact: CanonicalFact | None, review: bool) -> ChargeSheetField:
        if fact is None:
            return self._unavailable()
        rendered = format_value(fact.value)
        if not rendered:
            return self._unavailable()
        return ChargeSheetField(
            value=rendered,
            status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED,
            confidence=fact.confidence,
            source_references=tuple(item.source_reference for item in fact.references),
            review_required=review,
        )

    def _rows(self, facts: tuple[CanonicalFact, ...], review: bool) -> tuple[IF5Row, ...]:
        return tuple(IF5Row(serial=index, description=self._field(fact, review), exhibit=self._unavailable()) for index, fact in enumerate(facts, 1))

    def _joined_field(self, facts: tuple[CanonicalFact, ...], review: bool) -> ChargeSheetField:
        facts = tuple(fact for fact in facts if fact.value is not None and format_value(fact.value) != "Not Available")
        if not facts:
            return self._unavailable()
        references = tuple(dict.fromkeys(reference for fact in facts for reference in (item.source_reference for item in fact.references)))
        confidences = [fact.confidence for fact in facts if fact.confidence is not None]
        return ChargeSheetField(
            value=unique_lines([format_value(fact.value) for fact in facts]),
            status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED,
            confidence=sum(confidences) / len(confidences) if confidences else None,
            source_references=references,
            review_required=review,
        )

    def _document_rows(self, context: CaseContext, review: bool) -> tuple[IF5Row, ...]:
        rows = []
        for index, document in enumerate(context.documents, 1):
            facts = tuple(item for item in (document.document_type, document.document_id, *document.attributes.values()) if item is not None)
            if not facts:
                continue
            document_type = label(str(document.document_type.value)) if document.document_type else "Source document"
            details = [f"Document ID: {format_inline(document.document_id.value)}"]
            details.extend(
                f"{key.replace('_', ' ').capitalize()}: {format_value(fact.value)}"
                for key, fact in document.attributes.items()
                if fact.value is not None
            )
            field = self._joined_field(facts, review).model_copy(update={"value": f"{document_type}:\n" + "\n".join(details)})
            rows.append(IF5Row(serial=index, description=field, exhibit=self._unavailable()))
        return tuple(rows)

    def _labelled_field(self, entries: tuple[tuple[str, tuple[CanonicalFact, ...]], ...], review: bool) -> ChargeSheetField:
        facts = tuple(fact for _, group in entries for fact in group)
        if not facts:
            return self._unavailable()
        lines = [f"{heading}: {unique_lines([format_value(fact.value) for fact in group])}" for heading, group in entries if group]
        return self._joined_field(facts, review).model_copy(update={"value": unique_lines(lines)})

    def _case_summary(self, context: CaseContext, review: bool) -> ChargeSheetField:
        facts = [*context.fir_details, *(event.timestamp for event in context.occurrence_details if event.timestamp), *(event.description for event in context.occurrence_details), *(location.name for location in context.locations), *(item.name for item in context.complainants), *(item.name for item in context.accused), *(item.name for item in context.victims), *(item.registration_number for item in context.vehicles)]
        if not facts:
            return self._unavailable()
        occurrence = [format_inline(event.timestamp.value) for event in context.occurrence_details if event.timestamp]
        occurrence.extend(
            format_inline(fact.value) for fact in context.fir_details
            if is_temporal_value(fact.value)
        )
        locations = [format_inline(item.name.value) for item in context.locations]
        people = (("complainant", context.complainants), ("accused", context.accused), ("victim", context.victims))
        lines = []
        if occurrence or locations:
            detail = "The records describe an occurrence"
            if occurrence:
                detail += f" on {'; '.join(dict.fromkeys(occurrence))}"
            if locations:
                detail += f" at {'; '.join(dict.fromkeys(locations))}"
            lines.append(sentence(detail))
        descriptions = [format_inline(event.description.value) for event in context.occurrence_details if event.description.value]
        if descriptions:
            first_sentence = descriptions[0].split(".", 1)[0].strip()
            if first_sentence:
                lines.append(sentence(f"Recorded incident: {first_sentence}"))
        for role, persons in people:
            names = unique_lines([format_inline(person.name.value) for person in persons]).replace("\n", "; ")
            if names:
                lines.append(sentence(f"Recorded {role}{'s' if len(persons) != 1 else ''}: {names}"))
        vehicles = unique_lines([format_inline(item.registration_number.value) for item in context.vehicles]).replace("\n", "; ")
        if vehicles:
            lines.append(sentence(f"Vehicle reference{'s' if len(context.vehicles) != 1 else ''}: {vehicles}"))
        return self._joined_field(tuple(facts), review).model_copy(update={"value": unique_lines(lines)})

    def _investigation_field(self, context: CaseContext, review: bool) -> ChargeSheetField:
        statements, facts = [], []
        for document in context.documents:
            if document.document_type is None:
                continue
            statement = document_action_statement(str(document.document_type.value), {key: fact.value for key, fact in document.attributes.items()})
            if statement:
                statements.append(statement)
                facts.extend((document.document_type, *document.attributes.values()))
        return self._joined_field(tuple(facts), review).model_copy(update={"value": unique_lines(statements)}) if statements else self._joined_field(context.investigation_actions, review)

    def _evidence_analysis(self, context: CaseContext, review: bool) -> ChargeSheetField:
        groups = (("Documentary Evidence", tuple(item.description for item in context.evidence)), ("Physical/Material Evidence", tuple(item.description for item in context.recovered_property)), ("Medical Evidence", context.medical_findings), ("Forensic Evidence", context.forensic_findings), ("Vehicle Evidence", tuple(item.registration_number for item in context.vehicles)), ("Witness Evidence", tuple(item.name for item in context.witnesses)))
        facts = tuple(fact for _, group in groups for fact in group)
        for item in (*context.evidence, *context.recovered_property):
            facts += (*item.collection_details, *item.custody_information)
        if not facts:
            return self._unavailable()
        lines, rendered_evidence = [], set()
        for heading, group in groups:
            values = [line.lstrip("- ").strip() for fact in group for line in format_value(fact.value).splitlines() if line.strip()]
            values = [value for value in values if value not in rendered_evidence]
            if values:
                lines.append(f"{heading}:")
                lines.extend(f"- {sentence(value)}" for value in values)
                rendered_evidence.update(values)
        for item in (*context.evidence, *context.recovered_property):
            details = [format_inline(fact.value) for fact in (*item.collection_details, *item.custody_information) if fact.value is not None]
            if details:
                lines.extend(f"- Collection/custody detail: {sentence(detail)}" for detail in details)
        return self._joined_field(facts, review).model_copy(update={"value": unique_lines(lines)})

    def populate(self, context: CaseContext, findings: LegalFindings) -> ChargeSheetData:
        review = context.validation_disposition != "draft_allowed" or findings.review_required
        people = lambda values: tuple(IF5Row(serial=index, description=self._field(person.name, review), exhibit=self._unavailable()) for index, person in enumerate(values, 1))
        timeline = tuple(IF5Row(serial=index, description=self._field(event.description, review or event.status.value == "review_required"), exhibit=self._unavailable()) for index, event in enumerate(context.relevant_timeline, 1))
        evidence = tuple(IF5Row(serial=index, description=self._field(item.description, review), exhibit=self._unavailable()) for index, item in enumerate(context.evidence, 1))
        recovered = tuple(IF5Row(serial=index, description=self._field(item.description, review), exhibit=self._unavailable()) for index, item in enumerate(context.recovered_property, 1))
        legal_sections = tuple(self._legal_field(item) for item in findings.findings)
        finding_rows = tuple(self._legal_finding(item) for item in findings.findings)
        conflict_items = tuple(
            ChargeSheetReviewItem(category="conflict", description=issue.description, source_references=issue.source_references)
            for issue in context.conflicts
        ) + tuple(
            ChargeSheetReviewItem(category="conflict", description=f"Unresolved conflict at {item.field_path}.", source_references=item.source_references)
            for item in context.canonical_conflicts if item.status.value != "resolved"
        )
        missing_items = tuple(
            ChargeSheetReviewItem(category="missing_information", description=item.description, source_references=item.source_references)
            for item in context.missing_information
        ) + tuple(
            ChargeSheetReviewItem(category="missing_information", description=item.description)
            for item in context.canonical_missing_information
        )
        return ChargeSheetData(
            case_id=context.case_id,
            disposition=context.validation_disposition,
            case_number=self._field(context.case_metadata[0] if context.case_metadata else None, review),
            police_station=self._field(context.police_station, review),
            court=self._field(context.court, review),
            case_summary=self._case_summary(context, review),
            detailed_facts=self._joined_field(tuple(event.description for event in context.occurrence_details), review),
            investigation_conducted=self._investigation_field(context, review),
            evidence_analysis=self._evidence_analysis(context, review),
            complainants=people(context.complainants), victims=people(context.victims), accused=people(context.accused), witnesses=people(context.witnesses),
            timeline=timeline, documentary_evidence=evidence, material_evidence=recovered,
            medical_findings=tuple(self._field(item, review) for item in context.medical_findings),
            forensic_findings=tuple(self._field(item, review) for item in context.forensic_findings),
            vehicle_findings=tuple(self._field(item.registration_number, review) for item in context.vehicles),
            legal_sections=legal_sections, legal_findings=finding_rows, conflicts=conflict_items, missing_information=missing_items,
            annexures=self._document_rows(context, review),
            final_opinion=self._unavailable(), signature=self._unavailable(),
        )

    def _legal_field(self, finding) -> ChargeSheetField:
        review = finding.review_required or finding.status != LegalFindingStatus.SUPPORTED
        return ChargeSheetField(value=finding.proposed_section or finding.offence, status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED, confidence=finding.confidence, source_references=finding.source_references, review_required=review)

    def _legal_finding(self, finding) -> ChargeSheetLegalFinding:
        review = finding.review_required or finding.status != LegalFindingStatus.SUPPORTED
        evidence = tuple(
            ChargeSheetField(value=format_value(item.description) or "Evidence reference recorded; description unavailable.", status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED, source_references=item.source_references, review_required=review)
            for item in finding.supporting_evidence
        )
        contradicting = tuple(
            ChargeSheetField(value=format_value(item.description) or "Evidence reference recorded; description unavailable.", status=FieldStatus.REVIEW_REQUIRED, source_references=item.source_references, review_required=True)
            for item in finding.contradicting_evidence
        )
        return ChargeSheetLegalFinding(
            offence=ChargeSheetField(value=finding.offence, status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED, confidence=finding.confidence, source_references=finding.source_references, review_required=review),
            proposed_section=self._legal_field(finding),
            description=ChargeSheetField(value=finding.description, status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED, confidence=finding.confidence, source_references=finding.source_references, review_required=review),
            status=finding.status.value, evidence_strength=finding.evidence_strength.value, review_required=review,
            supporting_evidence=evidence, contradicting_evidence=contradicting,
        )
