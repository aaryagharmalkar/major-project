"""Creates the Phase 7 canonical view from an existing knowledge graph."""

from __future__ import annotations

from ..knowledge_graph.graph_models import GraphNodeType, InvestigationKnowledgeGraph
from .canonical_models import CanonicalCaseMetadata, CanonicalInvestigation, ConfidenceSummary, MissingInformation
from .conflict_registry import ConflictRegistry
from .entity_projection import project_entities
from .evidence_projection import project_evidence
from .fact_projection import project_fact
from .timeline_projection import project_timeline


class CanonicalBuilder:
    def __init__(self, conflict_registry: ConflictRegistry | None = None) -> None:
        self.conflict_registry = conflict_registry or ConflictRegistry()

    def build(self, graph: InvestigationKnowledgeGraph) -> CanonicalInvestigation:
        entities = project_entities(graph.nodes)
        evidence = project_evidence(graph.nodes, graph.edges)
        timeline = project_timeline(graph.nodes, graph.edges)
        conflicts = self.conflict_registry.find(graph.nodes, graph.edges)
        medical = tuple(project_fact(node.label, node.provenance, f"graph.nodes[{node.id}].label") for node in graph.nodes if node.node_type == GraphNodeType.MEDICAL_FINDING)
        forensic = tuple(project_fact(node.label, node.provenance, f"graph.nodes[{node.id}].label") for node in graph.nodes if node.node_type == GraphNodeType.FSL_FINDING)
        all_facts = [person.name for group in (entities["victims"], entities["accused"], entities["witnesses"], entities["police_officers"], entities["doctors"]) for person in group]
        all_facts += [vehicle.registration_number for vehicle in entities["vehicles"]] + list(medical) + list(forensic)
        confidences = [fact.confidence for fact in all_facts if fact.confidence is not None]
        sources = tuple(dict.fromkeys(reference.source_reference for node in graph.nodes for reference in node.provenance))
        fir_nodes = tuple(node for node in graph.nodes if node.node_type == GraphNodeType.DOCUMENT and node.attributes.get("document_type") == "fir")
        fir = fir_nodes[0] if fir_nodes else None
        def fir_fact(field):
            value = fir.attributes.get(field) if fir else None
            return project_fact(value, fir.provenance, f"fir.{field}") if value is not None else None
        fir_number = fir_fact("fir_number") or fir_fact("crime_number")
        registration_date = fir_fact("registration_date")
        police_station, jurisdiction, court = fir_fact("police_station"), fir_fact("jurisdiction"), fir_fact("court")
        fir_details = tuple(item for item in (fir_fact("occurrence_datetime"), fir_fact("occurrence_location")) if item is not None)
        offences = tuple(project_fact(value, fir.provenance, "fir.reported_sections") for value in (fir.attributes.get("reported_sections", ()) if fir else ()))
        missing = () if graph.nodes else (MissingInformation(field_path="investigation_knowledge_graph", description="No graph entities are available for canonical projection."),)
        return CanonicalInvestigation(
            case_metadata=CanonicalCaseMetadata(case_id=graph.case_id, fir_number=fir_number, registration_date=registration_date),
            fir_details=fir_details, jurisdiction=jurisdiction, police_station=police_station, court=court, offences=offences,
            victims=entities["victims"], accused=entities["accused"], witnesses=entities["witnesses"], police_officers=entities["police_officers"], doctors=entities["doctors"],
            vehicles=entities["vehicles"], locations=entities["locations"], evidence=tuple(item for item in evidence if item.type == GraphNodeType.EVIDENCE.value),
            recovered_property=tuple(item for item in evidence if item.type == GraphNodeType.RECOVERED_PROPERTY.value), medical_findings=medical, forensic_findings=forensic,
            timeline=timeline, documents=entities["documents"], conflicts=conflicts, missing_information=missing, source_references=sources,
            confidence_summary=ConfidenceSummary(average=sum(confidences) / len(confidences) if confidences else None, fact_count=len(all_facts)),
        )
