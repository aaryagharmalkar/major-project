"""The sole controlled data carrier passed to and returned by every stage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..domain.documents import SourceDocument
from ..normalization.canonical_models import CanonicalInvestigation
from ..knowledge_graph.graph_models import InvestigationKnowledgeGraph
from ..validation.validation_models import ValidationReport
from ..context.case_context import CaseContext
from ..legal.legal_findings import LegalFindings
from ..chargesheet.form_if5_schema import ChargeSheetData
from ..review.review_models import ChargeSheetReview
from .state import WorkflowState


class ContextItem(BaseModel):
    """A named future-stage value retained without leaking unrelated arguments."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    key: str = Field(min_length=1)
    value: Any


class GeneratedArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    storage_key: str
    media_type: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowContext(BaseModel):
    """Immutable snapshot containing all state shared by workflow stages."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    case_id: UUID
    resume: bool = False
    pending_uploads: tuple[ContextItem, ...] = ()
    uploaded_documents: tuple[SourceDocument, ...] = ()
    upload_manifest: Any | None = None
    ocr_results: tuple[ContextItem, ...] = ()
    parsed_documents: tuple[ContextItem, ...] = ()
    investigation_knowledge_graph: InvestigationKnowledgeGraph | None = None
    canonical_investigation: CanonicalInvestigation | None = None
    validation_report: ValidationReport | None = None
    case_context: CaseContext | None = None
    legal_findings: LegalFindings | None = None
    chargesheet_data: ChargeSheetData | None = None
    officer_review: ChargeSheetReview | None = None
    generated_artifacts: tuple[GeneratedArtifact, ...] = ()
    stage_metrics: tuple[ContextItem, ...] = ()
    execution_metadata: tuple[ContextItem, ...] = ()
    metadata: tuple[ContextItem, ...] = ()
    execution_state: WorkflowState

    def with_updates(self, **updates: Any) -> "WorkflowContext":
        """Return a validated replacement snapshot; never mutate stage context."""

        unknown_fields = set(updates) - set(self.__class__.model_fields)
        if unknown_fields:
            raise ValueError(f"Unsupported WorkflowContext fields: {sorted(unknown_fields)}")
        # Read attributes directly so arbitrary typed stage payloads (for example
        # IncomingUpload) survive a controlled context transition unchanged.
        values = {
            field_name: getattr(self, field_name)
            for field_name in self.__class__.model_fields
        }
        values.update(updates)
        return self.__class__.model_validate(values)


class WorkflowRunResult(BaseModel):
    """Engine output that always retains the latest context and execution report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    context: WorkflowContext
    report: "WorkflowExecutionReport"


from .state import WorkflowExecutionReport  # noqa: E402  # Resolve Pydantic forward reference.

WorkflowRunResult.model_rebuild()
