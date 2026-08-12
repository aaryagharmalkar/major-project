"""Persistence ports for dependency-injected application services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ..domain.documents import SourceDocument
from ..domain.investigation import CanonicalInvestigation


class DocumentRepository(ABC):
    @abstractmethod
    def save(self, document: SourceDocument) -> None:
        """Persist immutable source-document metadata."""

    @abstractmethod
    def get(self, document_id: UUID) -> SourceDocument | None:
        """Return a source document by ID, when it exists."""

    @abstractmethod
    def list_for_case(self, case_id: UUID) -> tuple[SourceDocument, ...]:
        """Return all source documents recorded for a case."""


class CaseRepository(ABC):
    @abstractmethod
    def save(self, investigation: CanonicalInvestigation) -> None:
        """Persist a canonical investigation snapshot."""

    @abstractmethod
    def get(self, case_id: UUID) -> CanonicalInvestigation | None:
        """Return the latest canonical investigation snapshot for a case."""
