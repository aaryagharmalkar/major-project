"""Coordinates validation, deterministic classification, storage, and manifesting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from ..domain.documents import ClassificationStatus, ExtractionState, ProcessingCapability, SourceDocument, ValidationStatus
from .checksum import calculate_sha256
from .document_classifier import DeterministicDocumentClassifier
from .exceptions import UploadSourceNotFoundError
from .file_validator import FileValidator
from .storage_layout import CaseStorageLayout
from .upload_manifest import UploadEntryStatus, UploadManifest, UploadManifestEntry


class IncomingUpload(BaseModel):
    """Local upload request supplied by a transport/UI adapter in a future layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_path: Path
    original_filename: str = Field(min_length=1)


class UploadManager:
    def __init__(
        self,
        storage_root: Path,
        *,
        validator: FileValidator | None = None,
        classifier: DeterministicDocumentClassifier | None = None,
        max_case_size_bytes: int | None = None,
    ) -> None:
        self.storage_root = storage_root
        self.validator = validator or FileValidator()
        self.classifier = classifier or DeterministicDocumentClassifier()
        self.max_case_size_bytes = max_case_size_bytes

    def ingest(
        self,
        case_id: UUID,
        uploads: tuple[IncomingUpload, ...],
        existing_manifest: UploadManifest | None = None,
    ) -> UploadManifest:
        if existing_manifest is not None and existing_manifest.case_id != case_id:
            raise ValueError("Existing manifest belongs to a different case")

        layout = CaseStorageLayout(self.storage_root, case_id).ensure_exists()
        existing_entries = existing_manifest.entries if existing_manifest else ()
        known_checksums = {
            entry.source_document.sha256: entry.source_document.id
            for entry in existing_entries
            if entry.status == UploadEntryStatus.ACCEPTED
        }
        entries = list(existing_entries)
        total_size = sum(entry.source_document.size_bytes for entry in existing_entries if entry.status == UploadEntryStatus.ACCEPTED)

        for upload in uploads:
            self._validate_upload_name(upload.original_filename)
            if not upload.source_path.is_file():
                raise UploadSourceNotFoundError(f"Upload source does not exist: {upload.source_path}")
            validation = self.validator.validate(upload.source_path)
            if validation.is_valid and self.max_case_size_bytes is not None and total_size + validation.size_bytes > self.max_case_size_bytes:
                validation = validation.model_copy(update={"is_valid": False, "errors": validation.errors + ("Case upload size limit exceeded.",)})
            checksum = calculate_sha256(upload.source_path)
            classification = self.classifier.classify(upload.original_filename, validation.detected_mime_type)
            capability = self._capability(validation.detected_mime_type)
            document_id = uuid4()
            duplicate_of = known_checksums.get(checksum)

            if not validation.is_valid:
                status = UploadEntryStatus.REJECTED
                validation_status = ValidationStatus.INVALID
                storage_key = f"CASE_{case_id.hex}/rejected/{document_id}{validation.extension}"
                stored_filename = None
            elif duplicate_of:
                status = UploadEntryStatus.DUPLICATE
                validation_status = ValidationStatus.DUPLICATE
                storage_key = f"CASE_{case_id.hex}/duplicates/{document_id}{validation.extension}"
                stored_filename = None
            else:
                stored_path = layout.copy_original(upload.source_path, document_id, validation.extension)
                status = UploadEntryStatus.ACCEPTED
                validation_status = ValidationStatus.VALID
                storage_key = layout.relative_key(stored_path)
                stored_filename = stored_path.name
                known_checksums[checksum] = document_id
                total_size += validation.size_bytes

            document = SourceDocument(
                id=document_id,
                case_id=case_id,
                original_filename=Path(upload.original_filename).name,
                stored_filename=stored_filename,
                storage_key=storage_key,
                media_type=validation.detected_mime_type or "application/octet-stream",
                sha256=checksum,
                size_bytes=validation.size_bytes,
                declared_type=classification.document_type,
                detected_type=classification.document_type,
                classification_confidence=classification.confidence,
                validation_status=validation_status,
                classification_status=(ClassificationStatus.CLASSIFIED if classification.document_type.value != "other" else ClassificationStatus.UNKNOWN),
                extraction_state=ExtractionState.PENDING if capability == ProcessingCapability.OCR_SUPPORTED else ExtractionState.DEFERRED,
                processing_capability=capability,
                uploaded_at=datetime.now(timezone.utc),
            )
            entries.append(
                UploadManifestEntry(
                    source_document=document,
                    validation=validation,
                    classification=classification,
                    status=status,
                    duplicate_of_document_id=duplicate_of,
                )
            )

        return UploadManifest(case_id=case_id, entries=tuple(entries))

    @staticmethod
    def _validate_upload_name(name: str) -> None:
        candidate = Path(name)
        if candidate.name != name or "\\" in name or name.startswith(("/", "\\")) or ":" in name:
            raise ValueError("Unsafe uploaded filename")

    @staticmethod
    def _capability(media_type: str | None) -> ProcessingCapability:
        if media_type in {"application/pdf", "image/jpeg", "image/png"}:
            return ProcessingCapability.OCR_SUPPORTED
        if media_type in {"video/mp4", "video/quicktime", "audio/wav"}:
            return ProcessingCapability.MEDIA_PROCESSING_REQUIRED
        return ProcessingCapability.UNSUPPORTED

    def write_manifest(self, manifest: UploadManifest) -> Path:
        layout = CaseStorageLayout(self.storage_root, manifest.case_id).ensure_exists()
        output_path = layout.processed_directory / "upload_manifest.json"
        output_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_path
