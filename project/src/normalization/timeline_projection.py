"""Chronological projection of explicit graph events without forcing reconciliation."""

from __future__ import annotations

from ..knowledge_graph.graph_models import GraphEdge, GraphNode, GraphNodeType, GraphRelationshipType
from .canonical_models import CanonicalTimelineEvent
from .fact_projection import project_fact


def project_timeline(nodes: tuple[GraphNode, ...], edges: tuple[GraphEdge, ...]) -> tuple[CanonicalTimelineEvent, ...]:
    events = []
    for node in nodes:
        if node.node_type != GraphNodeType.TIMELINE_EVENT:
            continue
        outgoing = [edge for edge in edges if edge.source_node_id == node.id]
        location = next((edge.target_node_id for edge in outgoing if edge.relationship_type == GraphRelationshipType.RELATES_TO), None)
        event_time = node.attributes.get("occurred_at")
        events.append(CanonicalTimelineEvent(
            event_id=node.id,
            timestamp=project_fact(event_time, node.provenance, f"graph.nodes[{node.id}].attributes.occurred_at") if event_time else None,
            description=project_fact(node.attributes.get("description", node.label), node.provenance, f"graph.nodes[{node.id}].attributes.description"),
            location_id=location,
            supporting_documents=tuple(dict.fromkeys(item.document_id for item in node.provenance)),
            confidence=project_fact(node.label, node.provenance, f"graph.nodes[{node.id}].label").confidence,
        ))
    return tuple(sorted(events, key=lambda item: (item.timestamp is None, item.timestamp.value if item.timestamp else item.event_id.hex)))
