"""Build retrieval metadata for RAG chunks."""

from __future__ import annotations

from typing import Any

from generator.rag.chunker import Chunk


class MetadataBuilder:
    """Attach case/document metadata to each chunk."""

    def build(self, chunk: Chunk) -> dict[str, Any]:
        return {
            "case_id": chunk.case_id,
            "document_type": chunk.document_type,
            "document_name": chunk.document_name,
            "chunk_id": chunk.chunk_id,
            "section": chunk.section,
            "source_file": chunk.metadata.get("source_file"),
            "entity_list": [],
            "timeline_reference": [],
            "evidence_reference": [],
        }
