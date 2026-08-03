"""Index chunk payloads into a local Qdrant-like JSON store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class QdrantIndexer:
    """Persist indexable records locally for later ingestion into Qdrant."""

    def __init__(self, *, output_directory: str | Path | None = None) -> None:
        self._output_directory = Path(output_directory or "./rag_output").expanduser().resolve()
        self._output_directory.mkdir(parents=True, exist_ok=True)

    def index(self, case_id: str, chunks: list[dict[str, Any]], embeddings: list[list[float]], metadata: list[dict[str, Any]]) -> dict[str, Any]:
        records = []
        for chunk, embedding, item_metadata in zip(chunks, embeddings, metadata, strict=False):
            records.append(
                {
                    "id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "embedding": embedding,
                    "metadata": item_metadata,
                }
            )

        output_path = self._output_directory / f"{case_id}_index.json"
        output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "case_id": case_id,
            "record_count": len(records),
            "output_path": str(output_path),
        }
