"""Workflow stage producing the compact CaseContext view."""

from __future__ import annotations

import time
from pathlib import Path

from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .case_context_builder import CaseContextBuilder
from .context_artifacts import ContextArtifactWriter


class CaseContextStage(WorkflowStage):
    name = "case_context"
    def __init__(self, storage_root: Path, builder: CaseContextBuilder | None = None, artifact_writer: ContextArtifactWriter | None = None) -> None:
        self.builder, self.artifact_writer = builder or CaseContextBuilder(), artifact_writer or ContextArtifactWriter(storage_root)
    def can_run(self, context: WorkflowContext) -> bool:
        return context.canonical_investigation is not None and context.validation_report is not None and context.case_context is None
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        if context.canonical_investigation is None or context.validation_report is None: raise ValueError("Case context requires canonical investigation and validation report")
        case_context = self.builder.build(context.canonical_investigation, context.validation_report)
        metrics = {"selected_facts": len(case_context.case_metadata) + len(case_context.medical_findings) + len(case_context.forensic_findings), "documents_referenced": len(case_context.source_references), "conflicts_included": len(case_context.conflicts), "validation_issues_included": len(case_context.validation_issues), "duration_ms": (time.perf_counter() - started) * 1000}
        return context.with_updates(case_context=case_context, generated_artifacts=context.generated_artifacts + (self.artifact_writer.write(case_context),), stage_metrics=context.stage_metrics + (ContextItem(key=self.name, value=metrics),), execution_metadata=context.execution_metadata + (ContextItem(key=self.name, value={"validation_disposition": case_context.validation_disposition}),))
