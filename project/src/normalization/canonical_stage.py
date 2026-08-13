"""Workflow integration for Phase 7 canonical investigation projection."""

from __future__ import annotations

import time
from pathlib import Path

from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .canonical_artifacts import CanonicalArtifactWriter
from .canonical_builder import CanonicalBuilder


class CanonicalInvestigationStage(WorkflowStage):
    name = "canonical_investigation"

    def __init__(self, storage_root: Path, builder: CanonicalBuilder | None = None, artifact_writer: CanonicalArtifactWriter | None = None) -> None:
        self.builder = builder or CanonicalBuilder()
        self.artifact_writer = artifact_writer or CanonicalArtifactWriter(storage_root)

    def can_run(self, context: WorkflowContext) -> bool:
        return context.investigation_knowledge_graph is not None and context.canonical_investigation is None

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        graph = context.investigation_knowledge_graph
        if graph is None:
            raise ValueError("Canonical investigation requires an Investigation Knowledge Graph")
        canonical = self.builder.build(graph)
        metrics = {
            "canonical_persons": sum(len(group) for group in (canonical.complainants, canonical.victims, canonical.accused, canonical.witnesses, canonical.police_officers, canonical.doctors)),
            "vehicles": len(canonical.vehicles), "evidence_items": len(canonical.evidence) + len(canonical.recovered_property),
            "timeline_events": len(canonical.timeline), "conflicts": len(canonical.conflicts),
            "unresolved_conflicts": sum(item.status.value == "unresolved" for item in canonical.conflicts),
            "missing_fields": len(canonical.missing_information), "average_confidence": canonical.confidence_summary.average,
            "duration_ms": (time.perf_counter() - started) * 1000,
        }
        return context.with_updates(
            canonical_investigation=canonical,
            generated_artifacts=context.generated_artifacts + self.artifact_writer.write(canonical),
            stage_metrics=context.stage_metrics + (ContextItem(key=self.name, value=metrics),),
            execution_metadata=context.execution_metadata + (ContextItem(key=self.name, value={"graph_case_id": str(graph.case_id)}),),
        )
