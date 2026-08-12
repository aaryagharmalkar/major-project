"""Registers explicit or safely comparable conflicts; never resolves them."""

from __future__ import annotations

from ..knowledge_graph.graph_models import GraphEdge, GraphNode, GraphRelationshipType
from .canonical_models import CanonicalConflict
from .fact_projection import project_fact


class ConflictRegistry:
    def find(self, nodes: tuple[GraphNode, ...], edges: tuple[GraphEdge, ...]) -> tuple[CanonicalConflict, ...]:
        by_id = {node.id: node for node in nodes}
        conflicts = []
        for edge in edges:
            if edge.relationship_type != GraphRelationshipType.CONTRADICTS:
                continue
            left, right = by_id[edge.source_node_id], by_id[edge.target_node_id]
            conflicts.append(CanonicalConflict(
                field_path=f"graph.nodes[{left.id}]<->graph.nodes[{right.id}]",
                competing_values=(project_fact(left.label, left.provenance, f"graph.nodes[{left.id}].label"), project_fact(right.label, right.provenance, f"graph.nodes[{right.id}].label")),
                source_references=tuple(item.source_reference for item in edge.provenance),
            ))
        # Equal descriptions with different explicit timestamps are alternatives for
        # the same stated event; preserve both rather than choosing one.
        events = [node for node in nodes if node.attributes.get("description") and node.attributes.get("occurred_at")]
        for position, left in enumerate(events):
            for right in events[position + 1:]:
                if left.attributes["description"] == right.attributes["description"] and left.attributes["occurred_at"] != right.attributes["occurred_at"]:
                    conflicts.append(CanonicalConflict(
                        field_path="timeline.timestamp",
                        competing_values=(project_fact(left.attributes["occurred_at"], left.provenance, f"graph.nodes[{left.id}].attributes.occurred_at"), project_fact(right.attributes["occurred_at"], right.provenance, f"graph.nodes[{right.id}].attributes.occurred_at")),
                        source_references=tuple(item.source_reference for item in left.provenance + right.provenance),
                    ))
        return tuple(conflicts)
