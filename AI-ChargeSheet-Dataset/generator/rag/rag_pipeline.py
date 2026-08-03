"""Orchestrate OCR-derived chunking, embedding, and indexing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from generator.rag.chunker import Chunker
from generator.rag.embedder import BaseEmbedder, InlineEmbedder
from generator.rag.metadata_builder import MetadataBuilder
from generator.rag.qdrant_indexer import QdrantIndexer


class RAGPipeline:
    """Build retrieval-ready artifacts from OCR JSON."""

    def __init__(self, *, chunker: Chunker | None = None, embedder: BaseEmbedder | None = None, metadata_builder: MetadataBuilder | None = None, indexer: QdrantIndexer | None = None) -> None:
        self._chunker = chunker or Chunker()
        self._embedder = embedder or InlineEmbedder()
        self._metadata_builder = metadata_builder or MetadataBuilder()
        self._indexer = indexer or QdrantIndexer()

    def run(self, case_directory: str | Path, ocr_json_path: str | Path, *, output_directory: str | Path | None = None) -> dict[str, Any]:
        case_path = Path(case_directory).expanduser().resolve()
        ocr_path = Path(ocr_json_path).expanduser().resolve()
        if not case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {case_path}")
        if not ocr_path.exists():
            raise FileNotFoundError(f"OCR JSON not found: {ocr_path}")

        chunks = self._chunker.chunk(case_path, ocr_path)
        embeddings = self._embedder.embed(chunks)
        metadata = [self._metadata_builder.build(chunk) for chunk in chunks]

        payload = [
            {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "section": chunk.section,
                "metadata": metadata_item,
            }
            for chunk, metadata_item in zip(chunks, metadata, strict=False)
        ]

        rag_directory = Path(output_directory or case_path / "rag").expanduser().resolve()
        rag_directory.mkdir(parents=True, exist_ok=True)

        chunks_path = rag_directory / "chunks.json"
        chunks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        embeddings_path = rag_directory / "embeddings.json"
        embeddings_path.write_text(json.dumps(embeddings, ensure_ascii=False, indent=2), encoding="utf-8")

        metadata_path = rag_directory / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        index_report = self._indexer.index(case_path.name, payload, embeddings, metadata)
        report_path = rag_directory / "index_report.json"
        report_path.write_text(json.dumps(index_report, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "case_id": case_path.name,
            "chunk_count": len(payload),
            "embedding_count": len(embeddings),
            "rag_directory": str(rag_directory),
            "index_report": index_report,
        }
