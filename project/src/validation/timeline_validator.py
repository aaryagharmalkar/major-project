"""Flags suspicious explicit chronology; it never reorders canonical events."""

from __future__ import annotations

from ..normalization.canonical_models import CanonicalInvestigation
from .validation_models import IssueCategory, IssueSeverity, IssueStatus, ValidationIssue


class TimelineValidator:
    def validate(self, investigation: CanonicalInvestigation) -> tuple[ValidationIssue, ...]:
        dated = [(event, event.timestamp.value) for event in investigation.timeline if event.timestamp is not None]
        occurrence_times = [time for event, time in dated if "occurrence" in str(event.description.value).casefold() or "incident" in str(event.description.value).casefold()]
        if not occurrence_times:
            return ()
        occurrence = min(occurrence_times)
        issues = []
        for event, timestamp in dated:
            text = str(event.description.value).casefold()
            if timestamp < occurrence and any(word in text for word in ("arrest", "seizure", "medical examination", "medical exam")):
                issues.append(ValidationIssue(category=IssueCategory.TIMELINE, severity=IssueSeverity.ERROR, description="Event precedes the explicitly recorded occurrence time.", field_path=f"timeline[{event.event_id}].timestamp", source_references=tuple(reference.source_reference for reference in event.timestamp.references), related_entity_ids=(event.event_id,), status=IssueStatus.REVIEW_REQUIRED))
        return tuple(issues)
