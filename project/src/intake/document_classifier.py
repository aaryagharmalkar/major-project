"""Deterministic filename and media-type classification; no AI is used here."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ..domain.common import ConfidenceLevel
from ..domain.documents import DocumentType


class ClassificationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    document_type: DocumentType
    confidence: ConfidenceLevel
    reason: str


class DeterministicDocumentClassifier:
    """Classifies known evidence categories using auditable filename keywords."""

    _KEYWORDS: tuple[tuple[DocumentType, tuple[str, ...]], ...] = (
        (DocumentType.POSTMORTEM_REPORT, ("postmortem", "post mortem", "autopsy")),
        (DocumentType.MEDICAL_REPORT, ("medical", "mlc", "injury", "hospital")),
        (DocumentType.FSL_REPORT, ("fsl", "forensic", "laboratory")),
        (DocumentType.WITNESS_STATEMENT, ("witness", "statement_161", "161 statement")),
        (DocumentType.CASE_DIARY, ("case diary", "case_diary", "diary")),
        (DocumentType.SEIZURE_MEMO, ("seizure", "recovery memo")),
        (DocumentType.ARREST_MEMO, ("arrest", "personal search")),
        (DocumentType.SPOT_PANCHNAMA, ("panchanama", "panchnama", "spot memo", "scene")),
        (DocumentType.VEHICLE_INSPECTION, ("vehicle inspection", "mechanical inspection", "vir")),
        (DocumentType.SITE_PLAN, ("site plan", "site_plan", "rough sketch")),
        (DocumentType.COMPLAINT, ("complaint", "application")),
        (DocumentType.FIR, ("fir", "first information report")),
    )

    def classify(self, filename: str, media_type: str | None) -> ClassificationResult:
        normalized_name = re.sub(r"[_-]+", " ", Path(filename).stem.lower())
        for document_type, keywords in self._KEYWORDS:
            if any(keyword in normalized_name for keyword in keywords):
                return ClassificationResult(
                    document_type=document_type,
                    confidence=ConfidenceLevel.HIGH,
                    reason="Matched deterministic filename keyword.",
                )

        if media_type and media_type.startswith("video/"):
            return ClassificationResult(
                document_type=DocumentType.CCTV_VIDEO,
                confidence=ConfidenceLevel.MEDIUM,
                reason="Classified from video MIME type.",
            )
        if media_type and media_type.startswith("image/"):
            return ClassificationResult(
                document_type=DocumentType.CCTV_IMAGE,
                confidence=ConfidenceLevel.LOW,
                reason="Classified from image MIME type; officer review required.",
            )
        return ClassificationResult(
            document_type=DocumentType.OTHER,
            confidence=ConfidenceLevel.LOW,
            reason="No deterministic classification rule matched.",
        )
