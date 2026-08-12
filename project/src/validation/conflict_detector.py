"""Surfaces Phase 7 conflicts without resolving or changing them."""

from __future__ import annotations

from ..normalization.canonical_models import CanonicalInvestigation, ConflictSeverity
from .validation_models import IssueCategory, IssueSeverity, IssueStatus, ValidationIssue


class ConflictDetector:
    def detect(self, investigation: CanonicalInvestigation) -> tuple[ValidationIssue, ...]:
        severity = {ConflictSeverity.LOW: IssueSeverity.WARNING, ConflictSeverity.MEDIUM: IssueSeverity.ERROR, ConflictSeverity.HIGH: IssueSeverity.CRITICAL}
        return tuple(ValidationIssue(category=IssueCategory.CONFLICT, severity=severity[item.severity], description=f"Unresolved conflict at {item.field_path}.", field_path=item.field_path, source_references=item.source_references, status=IssueStatus.REVIEW_REQUIRED) for item in investigation.conflicts if item.status.value == "unresolved")
