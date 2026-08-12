"""Evidence-backed data contract for the supplied charge-sheet sample."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from ..domain.common import DomainModel, SourceReference


class FieldStatus(StrEnum):
    POPULATED = "populated"
    UNAVAILABLE = "unavailable"
    CONFLICT = "conflict"
    REVIEW_REQUIRED = "review_required"
    NOT_APPLICABLE = "not_applicable"


class ChargeSheetField(DomainModel):
    value: str | None = None
    status: FieldStatus
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_references: tuple[SourceReference, ...] = ()
    review_required: bool = False

    @model_validator(mode="after")
    def populated_values_require_provenance(self) -> "ChargeSheetField":
        if self.status in {FieldStatus.POPULATED, FieldStatus.REVIEW_REQUIRED}:
            if not self.value or not self.source_references:
                raise ValueError("Rendered charge-sheet values require source references")
        if self.status in {FieldStatus.UNAVAILABLE, FieldStatus.NOT_APPLICABLE} and self.value:
            raise ValueError("Unavailable fields cannot contain an unsupported value")
        return self

    @property
    def rendered(self) -> str:
        return self.value if self.value else "Not Available in Investigation Records"


class IF5Row(DomainModel):
    serial: int = Field(ge=1)
    description: ChargeSheetField
    exhibit: ChargeSheetField


class ChargeSheetData(DomainModel):
    case_id: UUID
    disposition: str
    version: int = Field(default=1, ge=1)
    case_number: ChargeSheetField
    police_station: ChargeSheetField
    court: ChargeSheetField
    case_summary: ChargeSheetField
    detailed_facts: ChargeSheetField
    investigation_conducted: ChargeSheetField
    evidence_analysis: ChargeSheetField
    complainants: tuple[IF5Row, ...] = ()
    victims: tuple[IF5Row, ...] = ()
    accused: tuple[IF5Row, ...] = ()
    witnesses: tuple[IF5Row, ...] = ()
    timeline: tuple[IF5Row, ...] = ()
    documentary_evidence: tuple[IF5Row, ...] = ()
    material_evidence: tuple[IF5Row, ...] = ()
    medical_findings: tuple[ChargeSheetField, ...] = ()
    forensic_findings: tuple[ChargeSheetField, ...] = ()
    vehicle_findings: tuple[ChargeSheetField, ...] = ()
    legal_sections: tuple[ChargeSheetField, ...] = ()
    annexures: tuple[IF5Row, ...] = ()
    final_opinion: ChargeSheetField
    signature: ChargeSheetField

    @property
    def content_hash(self) -> str:
        """Stable identity for the exact charge-sheet content and version."""

        payload = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
