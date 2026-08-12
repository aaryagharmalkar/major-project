"""Workflow stage for non-mutating canonical evidence validation."""

from __future__ import annotations

import time
from pathlib import Path

from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .evidence_validator import EvidenceValidator
from .validation_artifacts import ValidationArtifactWriter


class EvidenceValidationStage(WorkflowStage):
    name = "evidence_validation"

    def __init__(self, storage_root: Path, validator: EvidenceValidator | None = None, artifact_writer: ValidationArtifactWriter | None = None) -> None:
        self.validator = validator or EvidenceValidator()
        self.artifact_writer = artifact_writer or ValidationArtifactWriter(storage_root)

    def can_run(self, context: WorkflowContext) -> bool:
        return context.canonical_investigation is not None and context.validation_report is None

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        canonical = context.canonical_investigation
        if canonical is None:
            raise ValueError("Evidence validation requires a CanonicalInvestigation")
        report = self.validator.validate(canonical)
        metrics = {"total_checks": len(report.errors) + len(report.warnings), "errors": len(report.errors), "warnings": len(report.warnings), "critical_issues": sum(item.severity.value == "critical" for item in report.errors), "missing_documents": len(report.missing_documents), "conflicts": len(report.conflicts), "unsupported_facts": len(report.unsupported_facts), "low_confidence_facts": len(report.low_confidence_facts), "completeness_score": report.completeness_score, "validation_duration_ms": (time.perf_counter() - started) * 1000}
        return context.with_updates(validation_report=report, generated_artifacts=context.generated_artifacts + self.artifact_writer.write(context.case_id, report), stage_metrics=context.stage_metrics + (ContextItem(key=self.name, value=metrics),), execution_metadata=context.execution_metadata + (ContextItem(key=self.name, value={"disposition": report.disposition.value}),))
