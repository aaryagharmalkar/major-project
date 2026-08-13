"""Builds one case graph from typed, document-local parser outputs only."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from ..domain.common import SourceReference
from ..domain.parsed_documents import (
    ArrestMemo, CaseDiary, CCTVMetadata, Complaint, FSLReport, FIR, MedicalReport,
    ParsedDocument, PostmortemReport, SeizureMemo, SitePlan, SpotPanchnama,
    VehicleInspection, WitnessStatement,
)
from .entity_resolver import EntityResolver
from .graph_models import (
    GraphEdge, GraphNode, GraphNodeType, GraphProvenance,
    GraphRelationshipType, InvestigationKnowledgeGraph, PersonRole,
)
from .graph_registry import GraphRegistry


class GraphBuilder:
    """A deterministic builder that records only values exposed by parser models."""

    def __init__(self, case_id: UUID, registry: GraphRegistry | None = None) -> None:
        self.case_id = case_id
        self.registry = registry or self._default_registry()
        self.resolver = EntityResolver()
        self._nodes: list[GraphNode] = []
        self._edges: list[GraphEdge] = []
        self._identity_index: dict[str, UUID] = {}
        self._duplicates_merged = 0

    @property
    def duplicates_merged(self) -> int:
        return self._duplicates_merged

    def build(self, documents: tuple[ParsedDocument, ...]) -> InvestigationKnowledgeGraph:
        for document in documents:
            document_node = self.add_node(
                GraphNodeType.DOCUMENT,
                f"{document.document_type.value}:{document.document_id}",
                document,
                attributes=self._document_attributes(document),
            )
            self.registry.map(self, document, document_node)
        return InvestigationKnowledgeGraph(case_id=self.case_id, nodes=tuple(self._nodes), edges=tuple(self._edges))

    def add_node(
        self, node_type: GraphNodeType, label: str | None, document: ParsedDocument,
        *, attributes: dict[str, object] | None = None, roles: frozenset[PersonRole] = frozenset(),
        document_node: GraphNode | None = None,
    ) -> GraphNode | None:
        if not label:
            return None
        provenance = self._provenance(document)
        key = self.resolver.identity_key(node_type, label)
        existing_id = self._identity_index.get(key)
        if node_type == GraphNodeType.PERSON and existing_id is None:
            matches = [node for node in self._nodes if node.node_type == node_type and self.resolver.person_matches(node.label, label)]
            if len(matches) == 1:
                existing_id = matches[0].id
        if existing_id is not None:
            node = next(node for node in self._nodes if node.id == existing_id)
            index = self._nodes.index(node)
            self._nodes[index] = node.model_copy(update={
                "roles": node.roles | roles,
                "provenance": node.provenance + (provenance,),
            })
            self._duplicates_merged += 1
            node = self._nodes[index]
        else:
            node = GraphNode(node_type=node_type, label=label, attributes=attributes or {}, roles=roles, provenance=(provenance,))
            self._nodes.append(node)
            self._identity_index[key] = node.id
        if document_node is not None and node.id != document_node.id:
            self.add_edge(document_node, node, GraphRelationshipType.MENTIONS, document)
            self.add_edge(node, document_node, GraphRelationshipType.ASSERTED_BY, document)
        return node

    def add_edge(self, source: GraphNode | None, target: GraphNode | None, relationship_type: GraphRelationshipType, document: ParsedDocument) -> None:
        if source is None or target is None:
            return
        provenance = self._provenance(document)
        for index, edge in enumerate(self._edges):
            if edge.source_node_id == source.id and edge.target_node_id == target.id and edge.relationship_type == relationship_type:
                self._edges[index] = edge.model_copy(update={"provenance": edge.provenance + (provenance,)})
                return
        self._edges.append(GraphEdge(source_node_id=source.id, target_node_id=target.id, relationship_type=relationship_type, provenance=(provenance,)))

    @staticmethod
    def _provenance(document: ParsedDocument) -> GraphProvenance:
        confidence = document.parse_metadata.confidence
        return GraphProvenance(
            document_id=document.document_id,
            confidence=confidence,
            parser_name=document.parse_metadata.parser_name,
            timestamp=datetime.now(timezone.utc),
            source_reference=SourceReference(document_id=document.document_id),
        )

    @staticmethod
    def _document_attributes(document: ParsedDocument) -> dict[str, object]:
        attributes: dict[str, object] = {"document_id": str(document.document_id), "document_type": document.document_type.value}
        if isinstance(document, FIR):
            for field in ("fir_number", "crime_number", "registration_date", "police_station", "occurrence_datetime", "occurrence_location", "jurisdiction", "court", "reported_sections"):
                value = getattr(document, field)
                if value not in (None, (), ""):
                    attributes[field] = value
        return attributes

    @staticmethod
    def _default_registry() -> GraphRegistry:
        registry = GraphRegistry()
        registry.register(FIR, GraphBuilder._map_fir)
        registry.register(Complaint, GraphBuilder._map_complaint)
        registry.register(MedicalReport, GraphBuilder._map_medical)
        registry.register(PostmortemReport, GraphBuilder._map_postmortem)
        registry.register(FSLReport, GraphBuilder._map_fsl)
        registry.register(WitnessStatement, GraphBuilder._map_witness)
        registry.register(CaseDiary, GraphBuilder._map_diary)
        registry.register(ArrestMemo, GraphBuilder._map_arrest)
        registry.register(SeizureMemo, GraphBuilder._map_seizure)
        registry.register(SpotPanchnama, GraphBuilder._map_spot)
        registry.register(VehicleInspection, GraphBuilder._map_vehicle)
        registry.register(SitePlan, GraphBuilder._map_site_plan)
        registry.register(CCTVMetadata, GraphBuilder._map_cctv)
        return registry

    @staticmethod
    def _person(builder: "GraphBuilder", name: str | None, role: PersonRole, doc: ParsedDocument, document_node: GraphNode) -> GraphNode | None:
        return builder.add_node(GraphNodeType.PERSON, name, doc, roles=frozenset({role}), document_node=document_node)

    @staticmethod
    def _location(builder: "GraphBuilder", label: str | None, doc: ParsedDocument, document_node: GraphNode) -> GraphNode | None:
        return builder.add_node(GraphNodeType.LOCATION, label, doc, document_node=document_node)

    @staticmethod
    def _map_fir(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, FIR) and isinstance(document_node, GraphNode)
        GraphBuilder._person(builder, doc.complainant_name, PersonRole.COMPLAINANT, doc, document_node)
        for name in doc.accused_names:
            GraphBuilder._person(builder, name, PersonRole.ACCUSED, doc, document_node)
        for name in doc.victim_names:
            GraphBuilder._person(builder, name, PersonRole.VICTIM, doc, document_node)
        for registration in doc.vehicle_registrations:
            builder.add_node(GraphNodeType.VEHICLE, registration, doc, attributes={"registration_number": registration}, document_node=document_node)
        if doc.occurrence_datetime or doc.narrative_text:
            event = builder.add_node(GraphNodeType.TIMELINE_EVENT, f"FIR occurrence {doc.document_id}", doc, attributes={"occurred_at": doc.occurrence_datetime, "description": doc.narrative_text}, document_node=document_node)
            builder.add_edge(event, document_node, GraphRelationshipType.SUPPORTED_BY, doc)
        GraphBuilder._location(builder, doc.occurrence_location, doc, document_node)

    @staticmethod
    def _map_complaint(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, Complaint) and isinstance(document_node, GraphNode)
        GraphBuilder._person(builder, doc.complainant_name, PersonRole.COMPLAINANT, doc, document_node)
        for name in doc.person_complained_against_names:
            GraphBuilder._person(builder, name, PersonRole.ACCUSED, doc, document_node)
        for name in doc.victim_names:
            GraphBuilder._person(builder, name, PersonRole.VICTIM, doc, document_node)
        for registration in doc.vehicle_registrations:
            builder.add_node(GraphNodeType.VEHICLE, registration, doc, attributes={"registration_number": registration}, document_node=document_node)

    @staticmethod
    def _map_medical(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, MedicalReport) and isinstance(document_node, GraphNode)
        patient = GraphBuilder._person(builder, doc.patient_name, PersonRole.VICTIM, doc, document_node)
        doctor = GraphBuilder._person(builder, doc.doctor_name, PersonRole.DOCTOR, doc, document_node)
        hospital = GraphBuilder._location(builder, doc.hospital_name, doc, document_node)
        builder.add_edge(patient, hospital, GraphRelationshipType.TREATED_AT, doc)
        builder.add_edge(patient, doctor, GraphRelationshipType.EXAMINED_BY, doc)
        for finding in doc.observations:
            finding_node = builder.add_node(GraphNodeType.MEDICAL_FINDING, finding, doc, document_node=document_node)
            builder.add_edge(finding_node, document_node, GraphRelationshipType.PART_OF, doc)

    @staticmethod
    def _map_postmortem(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, PostmortemReport) and isinstance(document_node, GraphNode)
        deceased = GraphBuilder._person(builder, doc.deceased_name, PersonRole.VICTIM, doc, document_node)
        doctor = GraphBuilder._person(builder, doc.doctor_name, PersonRole.DOCTOR, doc, document_node)
        builder.add_edge(deceased, doctor, GraphRelationshipType.EXAMINED_BY, doc)
        for finding in doc.findings:
            node = builder.add_node(GraphNodeType.MEDICAL_FINDING, finding, doc, document_node=document_node)
            builder.add_edge(node, document_node, GraphRelationshipType.PART_OF, doc)

    @staticmethod
    def _map_fsl(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, FSLReport) and isinstance(document_node, GraphNode)
        for finding in doc.findings:
            node = builder.add_node(GraphNodeType.FSL_FINDING, finding, doc, document_node=document_node)
            builder.add_edge(node, document_node, GraphRelationshipType.PART_OF, doc)
        for item in doc.examined_items:
            evidence = builder.add_node(GraphNodeType.EVIDENCE, item, doc, document_node=document_node)
            builder.add_edge(evidence, document_node, GraphRelationshipType.EXAMINED_BY, doc)

    @staticmethod
    def _map_witness(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, WitnessStatement) and isinstance(document_node, GraphNode)
        GraphBuilder._person(builder, doc.witness_name, PersonRole.WITNESS, doc, document_node)
        GraphBuilder._person(builder, doc.recorded_by, PersonRole.POLICE_OFFICER, doc, document_node)

    @staticmethod
    def _map_diary(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, CaseDiary) and isinstance(document_node, GraphNode)
        GraphBuilder._person(builder, doc.officer_name, PersonRole.POLICE_OFFICER, doc, document_node)
        for entry in doc.entries:
            if entry.entry_datetime or entry.text:
                builder.add_node(GraphNodeType.TIMELINE_EVENT, f"Diary {entry.entry_number or 'entry'} {doc.document_id}", doc, attributes={"occurred_at": entry.entry_datetime, "description": entry.text}, document_node=document_node)

    @staticmethod
    def _map_arrest(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, ArrestMemo) and isinstance(document_node, GraphNode)
        accused = GraphBuilder._person(builder, doc.arrested_person_name, PersonRole.ACCUSED, doc, document_node)
        officer = GraphBuilder._person(builder, doc.arresting_officer_name, PersonRole.POLICE_OFFICER, doc, document_node)
        location = GraphBuilder._location(builder, doc.arrest_location, doc, document_node)
        builder.add_edge(accused, officer, GraphRelationshipType.RELATES_TO, doc)
        builder.add_edge(accused, location, GraphRelationshipType.RECOVERED_FROM, doc)

    @staticmethod
    def _map_seizure(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, SeizureMemo) and isinstance(document_node, GraphNode)
        officer = GraphBuilder._person(builder, doc.prepared_by, PersonRole.POLICE_OFFICER, doc, document_node)
        location = GraphBuilder._location(builder, doc.seizure_location, doc, document_node)
        for item in doc.seized_items:
            property_node = builder.add_node(GraphNodeType.RECOVERED_PROPERTY, item.description, doc, attributes={"exhibit_mark": item.exhibit_mark}, document_node=document_node)
            builder.add_edge(property_node, location, GraphRelationshipType.RECOVERED_FROM, doc)
            builder.add_edge(property_node, officer, GraphRelationshipType.COLLECTED_BY, doc)

    @staticmethod
    def _map_spot(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, SpotPanchnama) and isinstance(document_node, GraphNode)
        GraphBuilder._location(builder, doc.location, doc, document_node)
        for witness in doc.witnesses:
            GraphBuilder._person(builder, witness, PersonRole.WITNESS, doc, document_node)

    @staticmethod
    def _map_vehicle(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, VehicleInspection) and isinstance(document_node, GraphNode)
        vehicle = builder.add_node(GraphNodeType.VEHICLE, doc.vehicle_registration, doc, attributes={"registration_number": doc.vehicle_registration}, document_node=document_node)
        officer = GraphBuilder._person(builder, doc.inspected_by, PersonRole.POLICE_OFFICER, doc, document_node)
        builder.add_edge(vehicle, officer, GraphRelationshipType.EXAMINED_BY, doc)

    @staticmethod
    def _map_site_plan(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, SitePlan) and isinstance(document_node, GraphNode)
        GraphBuilder._location(builder, doc.location, doc, document_node)
        GraphBuilder._person(builder, doc.prepared_by, PersonRole.POLICE_OFFICER, doc, document_node)

    @staticmethod
    def _map_cctv(builder: "GraphBuilder", doc: ParsedDocument, document_node: object) -> None:
        assert isinstance(doc, CCTVMetadata) and isinstance(document_node, GraphNode)
        location = GraphBuilder._location(builder, doc.location, doc, document_node)
        event = builder.add_node(GraphNodeType.TIMELINE_EVENT, f"CCTV {doc.camera_identifier or doc.document_id}", doc, attributes={"occurred_at": doc.recording_datetime, "description": doc.metadata_text}, document_node=document_node)
        builder.add_edge(event, location, GraphRelationshipType.RELATES_TO, doc)
