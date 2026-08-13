"""Deterministic projection from Phase 9 outputs; this module never infers facts."""

from __future__ import annotations

from ..context.case_context import CaseContext
from ..legal.legal_findings import LegalFindings, LegalFindingStatus
from ..normalization.canonical_models import CanonicalFact
from .form_if5_schema import ChargeSheetData, ChargeSheetField, FieldStatus, IF5Row


class ChargeSheetPopulator:
    def _unavailable(self) -> ChargeSheetField:
        return ChargeSheetField(status=FieldStatus.UNAVAILABLE, review_required=True)

    def _field(self, fact: CanonicalFact | None, review: bool) -> ChargeSheetField:
        if fact is None:
            return self._unavailable()
        return ChargeSheetField(
            value=str(fact.value),
            status=FieldStatus.REVIEW_REQUIRED if review else FieldStatus.POPULATED,
            confidence=fact.confidence,
            source_references=tuple(item.source_reference for item in fact.references),
            review_required=review,
        )

    def _rows(self, facts: tuple[CanonicalFact, ...], review: bool) -> tuple[IF5Row, ...]:
        return tuple(IF5Row(serial=index, description=self._field(fact, review), exhibit=self._unavailable()) for index, fact in enumerate(facts, 1))

    def populate(self, context: CaseContext, findings: LegalFindings) -> ChargeSheetData:
        review = context.validation_disposition != "draft_allowed" or findings.review_required
        people = lambda values: tuple(IF5Row(serial=index, description=self._field(person.name, review), exhibit=self._unavailable()) for index, person in enumerate(values, 1))
        timeline = tuple(IF5Row(serial=index, description=self._field(event.description, review or event.status.value == "review_required"), exhibit=self._unavailable()) for index, event in enumerate(context.relevant_timeline, 1))
        evidence = tuple(IF5Row(serial=index, description=self._field(item.description, review), exhibit=self._unavailable()) for index, item in enumerate(context.evidence, 1))
        recovered = tuple(IF5Row(serial=index, description=self._field(item.description, review), exhibit=self._unavailable()) for index, item in enumerate(context.recovered_property, 1))
        legal_sections = tuple(self._legal_field(item) for item in findings.findings)
        return ChargeSheetData(
            case_id=context.case_id,
            disposition=context.validation_disposition,
            case_number=self._field(context.case_metadata[0] if context.case_metadata else None, review),
            police_station=self._field(context.police_station, review),
            court=self._field(context.court, review),
            case_summary=self._unavailable(),
            detailed_facts=self._unavailable(),
            investigation_conducted=self._unavailable(),
            evidence_analysis=self._unavailable(),
            complainants=people(context.complainants), victims=people(context.victims), accused=people(context.accused), witnesses=people(context.witnesses),
            timeline=timeline, documentary_evidence=evidence, material_evidence=recovered,
            medical_findings=tuple(self._field(item, review) for item in context.medical_findings),
            forensic_findings=tuple(self._field(item, review) for item in context.forensic_findings),
            vehicle_findings=tuple(self._field(item.registration_number, review) for item in context.vehicles),
            legal_sections=legal_sections,
            final_opinion=self._unavailable(), signature=self._unavailable(),
        )

    def _legal_field(self, finding) -> ChargeSheetField:
        if finding.status != LegalFindingStatus.SUPPORTED:
            return ChargeSheetField(status=FieldStatus.UNAVAILABLE, review_required=True)
        return ChargeSheetField(value=finding.proposed_section or finding.offence, status=FieldStatus.REVIEW_REQUIRED if finding.review_required else FieldStatus.POPULATED, confidence=finding.confidence, source_references=finding.source_references, review_required=finding.review_required)
