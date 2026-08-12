"""Registry for document-to-graph mapping functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeAlias

from ..domain.parsed_documents import ParsedDocument

if TYPE_CHECKING:
    from .graph_builder import GraphBuilder

GraphMapper: TypeAlias = Callable[["GraphBuilder", ParsedDocument, object], None]


class GraphRegistry:
    def __init__(self) -> None:
        self._mappers: dict[type[ParsedDocument], GraphMapper] = {}

    def register(self, document_class: type[ParsedDocument], mapper: GraphMapper) -> None:
        self._mappers[document_class] = mapper

    def map(self, builder: "GraphBuilder", document: ParsedDocument, document_node: object) -> None:
        mapper = self._mappers.get(type(document))
        if mapper is not None:
            mapper(builder, document, document_node)

