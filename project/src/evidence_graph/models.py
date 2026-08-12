"""Typed, storage-agnostic Investigation Knowledge Graph (IKG) primitives."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from ..domain.common import DomainEntity, SourceReference


class NodeType(StrEnum):
    PERSON = "person"
    VEHICLE = "vehicle"
    EVIDENCE = "evidence"
    TIMELINE_EVENT = "timeline_event"
    DOCUMENT = "document"
    RECOVERED_PROPERTY = "recovered_property"
    MEDICAL_FINDING = "medical_finding"
    FORENSIC_FINDING = "forensic_finding"
    LEGAL_REFERENCE = "legal_reference"


class RelationshipType(StrEnum):
    SUPPORTED_BY = "supported_by"
    ASSERTED_BY = "asserted_by"
    RELATES_TO = "relates_to"
    COLLECTED_BY = "collected_by"
    OWNED_BY = "owned_by"
    DRIVEN_BY = "driven_by"
    OCCURRED_BEFORE = "occurred_before"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    CUSTODY_OF = "custody_of"


class GraphNode(DomainEntity):
    node_type: NodeType
    attributes: dict[str, Any] = Field(default_factory=dict)
    source_references: tuple[SourceReference, ...] = ()


class Relationship(DomainEntity):
    source_node_id: UUID
    target_node_id: UUID
    relationship_type: RelationshipType
    source_references: tuple[SourceReference, ...] = ()


class InvestigationKnowledgeGraph(DomainEntity):
    case_id: UUID
    nodes: tuple[GraphNode, ...] = ()
    relationships: tuple[Relationship, ...] = ()
