from __future__ import annotations

import time
import json
from pathlib import Path

from ..intake.storage_layout import CaseStorageLayout
from ..rendering.if5_renderer import IF5Renderer
from ..review.review_service import ReviewService
from ..workflow.context import ContextItem, GeneratedArtifact, WorkflowContext
from ..workflow.stage import WorkflowStage
from .chargesheet_artifacts import ChargeSheetArtifactWriter
from .chargesheet_populator import ChargeSheetPopulator
from .chargesheet_validator import ChargeSheetValidator


class ChargeSheetStage(WorkflowStage):
    name = "chargesheet_population"

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root
        self.populator = ChargeSheetPopulator()
        self.validator = ChargeSheetValidator()
        self.artifact_writer = ChargeSheetArtifactWriter(storage_root)
        self.renderer = IF5Renderer()
        self.review_service = ReviewService()

    def can_run(self, context: WorkflowContext) -> bool:
        return context.case_context is not None and context.legal_findings is not None and context.chargesheet_data is None

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.case_context is None or context.legal_findings is None:
            raise ValueError("Charge-sheet generation requires CaseContext and LegalFindings")
        started = time.perf_counter()
        data = self.populator.populate(context.case_context, context.legal_findings)
        validation = self.validator.validate(data)
        if validation.errors:
            raise ValueError("; ".join(validation.errors))
        artifacts = (self.artifact_writer.write(data),)
        review = None
        if data.disposition != "final_blocked":
            layout = CaseStorageLayout(self.storage_root, data.case_id).ensure_exists()
            path = self.renderer.render(data, layout.processed_directory / "chargesheet" / "draft" / f"ChargeSheet_v{data.version}_review.pdf")
            artifacts += (GeneratedArtifact(name="chargesheet_draft", storage_key=layout.relative_key(path), media_type="application/pdf"),)
            review = self.review_service.submit_for_review(self.review_service.create_draft(data), data)
            review_path = layout.processed_directory / "chargesheet" / "review_state.json"
            review_path.write_text(json.dumps(review.model_dump(mode="json"), indent=2), encoding="utf-8")
            artifacts += (GeneratedArtifact(name="chargesheet_review_state", storage_key=layout.relative_key(review_path), media_type="application/json"),)
        metrics = {"review_required": validation.review_required, "pdf_generated": data.disposition != "final_blocked", "duration_ms": (time.perf_counter() - started) * 1000}
        return context.with_updates(chargesheet_data=data, officer_review=review, generated_artifacts=context.generated_artifacts + artifacts, stage_metrics=context.stage_metrics + (ContextItem(key=self.name, value=metrics),), execution_metadata=context.execution_metadata + (ContextItem(key=self.name, value={"validation_disposition": data.disposition, "review_required": validation.review_required}),))
