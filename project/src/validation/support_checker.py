"""Checks that claim categories have an explicitly available source document."""

from __future__ import annotations

from ..normalization.canonical_models import CanonicalInvestigation
from .validation_models import IssueCategory, ValidationIssue, ValidationRules


class SupportChecker:
    def check(self, investigation: CanonicalInvestigation, rules: ValidationRules) -> tuple[ValidationIssue, ...]:
        document_types = {item.document_type.value for item in investigation.documents if item.document_type is not None}
        expected = (
            (bool(investigation.medical_findings), "medical_report", "medical_findings", "Medical findings exist but no medical-report document supports them."),
            (bool(investigation.forensic_findings), "fsl_report", "forensic_findings", "Forensic findings exist but no FSL-report document supports them."),
            (bool(investigation.recovered_property), "seizure_memo", "recovered_property", "Recovered property exists but no seizure-memo document supports it."),
        )
        return tuple(
            ValidationIssue(category=IssueCategory.DOCUMENT_SUPPORT, severity=rules.missing_document_severity, description=description, field_path=path)
            for present, document_type, path, description in expected if present and document_type not in document_types
        )
