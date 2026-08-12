"""Models describing originals uploaded into an investigation workspace."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from .common import ConfidenceLevel, DomainEntity


class DocumentType(StrEnum):
    FIR = "fir"
    COMPLAINT = "complaint"
    WITNESS_STATEMENT = "witness_statement"
    MEDICAL_REPORT = "medical_report"
    POSTMORTEM_REPORT = "postmortem_report"
    FSL_REPORT = "fsl_report"
    ARREST_MEMO = "arrest_memo"
    SEIZURE_MEMO = "seizure_memo"
    SPOT_PANCHNAMA = "spot_panchnama"
    VEHICLE_INSPECTION = "vehicle_inspection"
    SITE_PLAN = "site_plan"
    CASE_DIARY = "case_diary"
    CCTV_IMAGE = "cctv_image"
    CCTV_VIDEO = "cctv_video"
    PHOTOGRAPH = "photograph"
    AUDIO = "audio"
    OTHER = "other"


class ExtractionState(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"
    DEFERRED = "deferred"


class ProcessingCapability(StrEnum):
    OCR_SUPPORTED = "ocr_supported"
    MEDIA_PROCESSING_REQUIRED = "media_processing_required"
    UNSUPPORTED = "unsupported"


class ParsingState(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"


class ClassificationStatus(StrEnum):
    PENDING = "pending"
    CLASSIFIED = "classified"
    UNKNOWN = "unknown"


class SourceDocument(DomainEntity):
    """Immutable metadata for an original uploaded file; never stores its content."""

    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    original_filename: str = Field(min_length=1)
    stored_filename: str | None = None
    storage_key: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[A-Fa-f0-9]{64}$")
    size_bytes: int = Field(ge=0)
    declared_type: DocumentType = DocumentType.OTHER
    detected_type: DocumentType = DocumentType.OTHER
    classification_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    validation_status: ValidationStatus = ValidationStatus.PENDING
    classification_status: ClassificationStatus = ClassificationStatus.PENDING
    extraction_state: ExtractionState = ExtractionState.PENDING
    processing_capability: ProcessingCapability = ProcessingCapability.UNSUPPORTED
    parsing_state: ParsingState = ParsingState.PENDING
    uploaded_at: datetime

    @field_validator("original_filename")
    @classmethod
    def filename_must_not_include_path(cls, value: str) -> str:
        if PurePosixPath(value).name != value or "\\" in value:
            raise ValueError("original_filename must not include a path")
        return value
