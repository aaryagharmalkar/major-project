"""Embedding interface for RAG indexing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from generator.rag.chunker import Chunk


class BaseEmbedder(ABC):
    """Abstract contract for embedding providers."""

    @abstractmethod
    def embed(self, chunks: list[Chunk]) -> list[list[float]]:
        """Return embeddings for the provided chunks."""


class InlineEmbedder(BaseEmbedder):
    """Simple deterministic embedder used as a placeholder implementation."""

    def embed(self, chunks: list[Chunk]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for chunk in chunks:
            vector = [float(len(chunk.content)), float(len(chunk.section)), float(len(chunk.document_type))]
            embeddings.append(vector)
        return embeddings
