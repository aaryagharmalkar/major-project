"""Immutable, auditable output of one or more document-ingestion operations."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..domain.documents import SourceDocument
from .document_classifier import ClassificationResult
from .file_validator import FileValidationResult


class UploadEntryStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class UploadManifestEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_document: SourceDocument
    validation: FileValidationResult
    classification: ClassificationResult
    status: UploadEntryStatus
    duplicate_of_document_id: UUID | None = None


class UploadManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: UUID
    entries: tuple[UploadManifestEntry, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def accepted_documents(self) -> tuple[SourceDocument, ...]:
        return tuple(entry.source_document for entry in self.entries if entry.status == UploadEntryStatus.ACCEPTED)
