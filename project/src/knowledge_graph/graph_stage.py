"""Workflow stage that transforms all parsed documents into one graph."""

from __future__ import annotations

import time
from pathlib import Path

from ..domain.parsed_documents import ParsedDocument
from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .graph_artifacts import GraphArtifactWriter
from .graph_builder import GraphBuilder


class GraphStage(WorkflowStage):
    name = "investigation_knowledge_graph"

    def __init__(self, storage_root: Path, artifact_writer: GraphArtifactWriter | None = None) -> None:
        self.artifact_writer = artifact_writer or GraphArtifactWriter(storage_root)

    def can_run(self, context: WorkflowContext) -> bool:
        return context.investigation_knowledge_graph is None and any(isinstance(item.value, ParsedDocument) for item in context.parsed_documents)

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        parsed_documents = tuple(item.value for item in context.parsed_documents if isinstance(item.value, ParsedDocument))
        builder = GraphBuilder(context.case_id)
        graph = builder.build(parsed_documents)
        confidences = [provenance.confidence for node in graph.nodes for provenance in node.provenance if provenance.confidence is not None]
        metrics = {
            "entities": len(graph.nodes),
            "relationships": len(graph.edges),
            "duplicates_merged": builder.duplicates_merged,
            "conflicts": 0,
            "confidence": sum(confidences) / len(confidences) if confidences else None,
            "duration_ms": (time.perf_counter() - started) * 1000,
        }
        return context.with_updates(
            investigation_knowledge_graph=graph,
            generated_artifacts=context.generated_artifacts + self.artifact_writer.write(graph),
            stage_metrics=context.stage_metrics + (ContextItem(key=self.name, value=metrics),),
            execution_metadata=context.execution_metadata + (ContextItem(key=self.name, value={"documents_graphed": len(parsed_documents)}),),
        )
