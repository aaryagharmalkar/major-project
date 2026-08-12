"""Projects graph evidence nodes and their explicit graph links."""

from __future__ import annotations

from ..knowledge_graph.graph_models import GraphEdge, GraphNode, GraphNodeType, GraphRelationshipType
from .canonical_models import CanonicalEvidence
from .fact_projection import project_fact


def project_evidence(nodes: tuple[GraphNode, ...], edges: tuple[GraphEdge, ...]) -> tuple[CanonicalEvidence, ...]:
    node_by_id = {node.id: node for node in nodes}
    projected = []
    for node in nodes:
        if node.node_type not in {GraphNodeType.EVIDENCE, GraphNodeType.RECOVERED_PROPERTY}:
            continue
        related = [edge for edge in edges if edge.source_node_id == node.id]
        related_ids = lambda relationship: tuple(edge.target_node_id for edge in related if edge.relationship_type == relationship)
        collection = tuple(project_fact(node_by_id[target].label, node.provenance, f"graph.edges[{edge.id}]") for edge in related if edge.relationship_type == GraphRelationshipType.COLLECTED_BY for target in (edge.target_node_id,))
        custody = tuple(project_fact(node_by_id[target].label, node.provenance, f"graph.edges[{edge.id}]") for edge in related if edge.relationship_type == GraphRelationshipType.RECOVERED_FROM for target in (edge.target_node_id,))
        confidences = [item.confidence for item in node.provenance if item.confidence is not None]
        projected.append(CanonicalEvidence(
            evidence_id=node.id, type=node.node_type.value, description=project_fact(node.label, node.provenance, f"graph.nodes[{node.id}].label"),
            source_documents=tuple(dict.fromkeys(item.document_id for item in node.provenance)), collection_details=collection, custody_information=custody,
            related_person_ids=related_ids(GraphRelationshipType.COLLECTED_BY), related_vehicle_ids=(), related_event_ids=(),
            confidence=sum(confidences) / len(confidences) if confidences else None,
        ))
    return tuple(projected)
