"""Projects already-resolved graph entities into non-duplicated canonical collections."""

from __future__ import annotations

from ..knowledge_graph.graph_models import GraphNode, GraphNodeType, PersonRole
from .canonical_models import CanonicalDocument, CanonicalLocation, CanonicalPerson, CanonicalVehicle
from .fact_projection import project_fact


def project_entities(nodes: tuple[GraphNode, ...]):
    people = [node for node in nodes if node.node_type == GraphNodeType.PERSON]
    persons = tuple(CanonicalPerson(id=node.id, name=project_fact(node.label, node.provenance, f"graph.nodes[{node.id}].label"), roles=node.roles) for node in people)
    by_role = lambda role: tuple(person for person in persons if role in person.roles)
    vehicles = tuple(CanonicalVehicle(id=node.id, registration_number=project_fact(node.attributes.get("registration_number", node.label), node.provenance, f"graph.nodes[{node.id}].attributes.registration_number")) for node in nodes if node.node_type == GraphNodeType.VEHICLE)
    locations = tuple(CanonicalLocation(id=node.id, name=project_fact(node.label, node.provenance, f"graph.nodes[{node.id}].label")) for node in nodes if node.node_type == GraphNodeType.LOCATION)
    documents = tuple(CanonicalDocument(id=node.id, document_id=project_fact(node.attributes["document_id"], node.provenance, f"graph.nodes[{node.id}].attributes.document_id"), document_type=project_fact(node.attributes["document_type"], node.provenance, f"graph.nodes[{node.id}].attributes.document_type") if node.attributes.get("document_type") else None) for node in nodes if node.node_type == GraphNodeType.DOCUMENT)
    return {
        "complainants": by_role(PersonRole.COMPLAINANT),
        "victims": by_role(PersonRole.VICTIM), "accused": by_role(PersonRole.ACCUSED),
        "witnesses": by_role(PersonRole.WITNESS), "police_officers": by_role(PersonRole.POLICE_OFFICER),
        "doctors": by_role(PersonRole.DOCTOR), "vehicles": vehicles, "locations": locations,
        "documents": documents,
    }
