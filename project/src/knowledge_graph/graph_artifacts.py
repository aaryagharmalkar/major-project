"""Writes the Phase 6 graph and its independently consumable node/edge artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import GeneratedArtifact
from .graph_models import InvestigationKnowledgeGraph


class GraphArtifactWriter:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def write(self, graph: InvestigationKnowledgeGraph) -> tuple[GeneratedArtifact, ...]:
        layout = CaseStorageLayout(self.storage_root, graph.case_id).ensure_exists()
        directory = layout.processed_directory / "graph"
        directory.mkdir(parents=True, exist_ok=True)
        payloads = {
            "investigation_graph.json": graph.model_dump(mode="json"),
            "nodes.json": [node.model_dump(mode="json") for node in graph.nodes],
            "edges.json": [edge.model_dump(mode="json") for edge in graph.edges],
        }
        artifacts = []
        for filename, payload in payloads.items():
            path = directory / filename
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            artifacts.append(GeneratedArtifact(name=filename.removesuffix(".json"), storage_key=layout.relative_key(path), media_type="application/json"))
        return tuple(artifacts)
