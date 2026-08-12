"""Deterministic, read-only evidence validation for canonical investigations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel

from ..normalization.canonical_models import CanonicalFact, CanonicalInvestigation
from .completeness_checker import CompletenessChecker
from .conflict_detector import ConflictDetector
from .support_checker import SupportChecker
from .timeline_validator import TimelineValidator
from .validation_models import (
    IssueCategory, IssueSeverity, IssueStatus, ValidationDisposition,
    ValidationIssue, ValidationReport, ValidationRules,
)


class EvidenceValidator:
    def __init__(self, rules: ValidationRules | None = None) -> None:
        self.rules = rules or ValidationRules()
        self.completeness_checker = CompletenessChecker()
        self.support_checker = SupportChecker()
        self.conflict_detector = ConflictDetector()
        self.timeline_validator = TimelineValidator()

    def validate(self, investigation: CanonicalInvestigation) -> ValidationReport:
        missing = self.completeness_checker.check(investigation, self.rules)
        missing_documents = self.support_checker.check(investigation, self.rules)
        conflicts = self.conflict_detector.detect(investigation)
        timeline_issues = self.timeline_validator.validate(investigation)
        unsupported, low_confidence = self._validate_facts(investigation)
        unresolved = self._unresolved_entities(investigation)
        all_issues = missing + missing_documents + conflicts + timeline_issues + unsupported + low_confidence + unresolved
        errors = tuple(item for item in all_issues if item.severity in {IssueSeverity.ERROR, IssueSeverity.CRITICAL})
        warnings = tuple(item for item in all_issues if item.severity == IssueSeverity.WARNING)
        critical = any(item.severity == IssueSeverity.CRITICAL for item in all_issues)
        review = critical or bool(errors) or bool(conflicts) or bool(timeline_issues) or bool(unresolved)
        disposition = ValidationDisposition.FINAL_BLOCKED if critical else ValidationDisposition.REVIEW_REQUIRED if review else ValidationDisposition.DRAFT_ALLOWED
        configured_required = sum((self.rules.require_fir_number, self.rules.require_police_station, self.rules.require_occurrence_details))
        completeness_score = max(0.0, 1 - len(missing) / max(1, configured_required + len(investigation.missing_information)))
        return ValidationReport(errors=errors, warnings=warnings, missing_documents=missing_documents, missing_information=missing, conflicts=conflicts, unresolved_entities=unresolved, unsupported_facts=unsupported, low_confidence_facts=low_confidence, timeline_issues=timeline_issues, completeness_score=completeness_score, critical_failure=critical, review_required=review, disposition=disposition)

    def _validate_facts(self, investigation: CanonicalInvestigation) -> tuple[tuple[ValidationIssue, ...], tuple[ValidationIssue, ...]]:
        unsupported, low = [], []
        for fact in self._facts(investigation):
            valid_references = bool(fact.source_document_ids and fact.references) and all(reference.document_id in fact.source_document_ids and reference.source_reference.document_id == reference.document_id for reference in fact.references)
            if not valid_references:
                unsupported.append(ValidationIssue(category=IssueCategory.UNSUPPORTED_FACT, severity=IssueSeverity.CRITICAL, description="Canonical fact cannot be traced to a valid source document and graph provenance.", field_path=fact.source_path, status=IssueStatus.REVIEW_REQUIRED))
            elif fact.confidence is not None and fact.confidence < self.rules.low_confidence_threshold:
                low.append(ValidationIssue(category=IssueCategory.LOW_CONFIDENCE, severity=IssueSeverity.WARNING, description="Canonical fact confidence is below the configured review threshold.", field_path=fact.source_path, source_references=tuple(reference.source_reference for reference in fact.references), status=IssueStatus.REVIEW_REQUIRED))
        return tuple(unsupported), tuple(low)

    @staticmethod
    def _facts(value: Any) -> Iterator[CanonicalFact]:
        if isinstance(value, CanonicalFact):
            yield value
        elif isinstance(value, BaseModel):
            for field_name in value.__class__.model_fields:
                yield from EvidenceValidator._facts(getattr(value, field_name))
        elif isinstance(value, (tuple, list)):
            for item in value:
                yield from EvidenceValidator._facts(item)

    @staticmethod
    def _unresolved_entities(investigation: CanonicalInvestigation) -> tuple[ValidationIssue, ...]:
        entities = investigation.victims + investigation.accused + investigation.witnesses + investigation.police_officers + investigation.doctors
        return tuple(ValidationIssue(category=IssueCategory.ENTITY, severity=IssueSeverity.WARNING, description="Entity remains unidentified or ambiguous.", field_path=f"persons[{entity.id}].name", source_references=tuple(reference.source_reference for reference in entity.name.references), related_entity_ids=(entity.id,), status=IssueStatus.REVIEW_REQUIRED) for entity in entities if str(entity.name.value).casefold() in {"unknown", "unidentified", "ambiguous"})
