"""Configurable, non-legal completeness checks for canonical case data."""

from __future__ import annotations

from ..normalization.canonical_models import CanonicalInvestigation
from .validation_models import IssueCategory, IssueSeverity, ValidationIssue, ValidationRules


class CompletenessChecker:
    def check(self, investigation: CanonicalInvestigation, rules: ValidationRules) -> tuple[ValidationIssue, ...]:
        missing = []
        checks = (
            (rules.require_fir_number and investigation.case_metadata.fir_number is None, "case_metadata.fir_number", "FIR/case number is required by the configured validation rule."),
            (rules.require_police_station and investigation.police_station is None, "police_station", "Police station is required by the configured validation rule."),
            (rules.require_occurrence_details and not investigation.timeline, "timeline", "Occurrence details are required by the configured validation rule."),
        )
        for absent, path, description in checks:
            if absent:
                missing.append(ValidationIssue(category=IssueCategory.COMPLETENESS, severity=rules.missing_required_severity, description=description, field_path=path))
        for item in investigation.missing_information:
            missing.append(ValidationIssue(category=IssueCategory.COMPLETENESS, severity=IssueSeverity.WARNING, description=item.description, field_path=item.field_path))
        return tuple(missing)
