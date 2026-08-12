"""Immutable, provenance-preserving models for the Phase 6 knowledge graph."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from ..domain.common import DomainModel, SourceReference


class GraphNodeType(StrEnum):
    PERSON = "person"
    VEHICLE = "vehicle"
    EVIDENCE = "evidence"
    TIMELINE_EVENT = "timeline_event"
    DOCUMENT = "document"
    MEDICAL_FINDING = "medical_finding"
    FSL_FINDING = "fsl_finding"
    RECOVERED_PROPERTY = "recovered_property"
    LOCATION = "location"


class PersonRole(StrEnum):
    VICTIM = "victim"
    ACCUSED = "accused"
    WITNESS = "witness"
    POLICE_OFFICER = "police_officer"
    DOCTOR = "doctor"


class GraphRelationshipType(StrEnum):
    SUPPORTED_BY = "supported_by"
    ASSERTED_BY = "asserted_by"
    RELATES_TO = "relates_to"
    TREATED_AT = "treated_at"
    DRIVES = "drives"
    OWNS = "owns"
    RECOVERED_FROM = "recovered_from"
    COLLECTED_BY = "collected_by"
    EXAMINED_BY = "examined_by"
    PART_OF = "part_of"
    MENTIONS = "mentions"
    OCCURRED_BEFORE = "occurred_before"
    OCCURRED_AFTER = "occurred_after"
    CONTRADICTS = "contradicts"


class GraphProvenance(DomainModel):
    """The extraction context required to audit a graph fact."""

    document_id: UUID
    page: int | None = Field(default=None, ge=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    parser_name: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_reference: SourceReference


class GraphNode(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    node_type: GraphNodeType
    label: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    roles: frozenset[PersonRole] = frozenset()
    provenance: tuple[GraphProvenance, ...] = Field(min_length=1)


class GraphEdge(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    source_node_id: UUID
    target_node_id: UUID
    relationship_type: GraphRelationshipType
    provenance: tuple[GraphProvenance, ...] = Field(min_length=1)


class InvestigationKnowledgeGraph(DomainModel):
    case_id: UUID
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()

