"""Workflow stage for evidence-backed, non-final legal recommendations."""

from __future__ import annotations

import time
from pathlib import Path

from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .legal_artifacts import LegalArtifactWriter
from .legal_reasoner import LegalReasoner


class LegalReasoningStage(WorkflowStage):
    name = "legal_reasoning"
    def __init__(self, storage_root: Path, reasoner: LegalReasoner, artifact_writer: LegalArtifactWriter | None = None) -> None:
        self.reasoner, self.artifact_writer = reasoner, artifact_writer or LegalArtifactWriter(storage_root)
    def can_run(self, context: WorkflowContext) -> bool: return context.case_context is not None and context.legal_findings is None
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        if context.case_context is None: raise ValueError("Legal reasoning requires a CaseContext")
        findings = self.reasoner.reason(context.case_context)
        metrics = {"reasoning_duration_ms": (time.perf_counter() - started) * 1000, "findings": len(findings.findings), "supported_findings": sum(item.status.value == "supported" for item in findings.findings), "insufficient_findings": sum(item.status.value == "insufficient_evidence" for item in findings.findings), "conflicted_findings": sum(item.status.value == "conflicted" for item in findings.findings), "requiring_review": sum(item.review_required for item in findings.findings), "llm_retry_count": findings.retry_count}
        return context.with_updates(legal_findings=findings, generated_artifacts=context.generated_artifacts + self.artifact_writer.write(context.case_context, findings), stage_metrics=context.stage_metrics + (ContextItem(key=self.name, value=metrics),), execution_metadata=context.execution_metadata + (ContextItem(key=self.name, value={"review_required": findings.review_required}),))
