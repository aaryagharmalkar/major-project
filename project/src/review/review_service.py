"""Human-only review transitions and guarded IF-5 finalization."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from ..chargesheet.form_if5_schema import ChargeSheetData
from ..intake.storage_layout import CaseStorageLayout
from ..rendering.if5_renderer import IF5Renderer
from ..validation.validation_models import ValidationDisposition
from .review_models import ChargeSheetReview, ReviewEvent, ReviewEventType, ReviewStatus


class ReviewLifecycleError(ValueError):
    """Raised when an attempted officer-review transition is unsafe."""


class ReviewService:
    """Pure service boundary; callers retain the immutable review record they receive."""

    def create_draft(self, data: ChargeSheetData, *, charge_sheet_id=None) -> ChargeSheetReview:
        review = ChargeSheetReview(
            case_id=data.case_id,
            charge_sheet_id=charge_sheet_id,
            status=ReviewStatus.DRAFT,
            data_version=data.version,
            data_content_hash=data.content_hash,
        ) if charge_sheet_id else ChargeSheetReview(
            case_id=data.case_id,
            status=ReviewStatus.DRAFT,
            data_version=data.version,
            data_content_hash=data.content_hash,
        )
        return self._event(review, ReviewEventType.DRAFT_CREATED)

    def submit_for_review(self, review: ChargeSheetReview, data: ChargeSheetData) -> ChargeSheetReview:
        self._ensure_status(review, ReviewStatus.DRAFT)
        self._ensure_data_matches(review, data)
        return self._event(review.model_copy(update={"status": ReviewStatus.REVIEW_REQUIRED}), ReviewEventType.SUBMITTED_FOR_REVIEW)

    def approve(self, review: ChargeSheetReview, data: ChargeSheetData, *, reviewer_id: str, reviewer_name: str | None = None, comments: str | None = None) -> ChargeSheetReview:
        self._ensure_status(review, ReviewStatus.REVIEW_REQUIRED)
        self._ensure_data_matches(review, data)
        if data.disposition == ValidationDisposition.FINAL_BLOCKED.value:
            raise ReviewLifecycleError("FINAL_BLOCKED charge sheets cannot be approved")
        now = datetime.now(timezone.utc)
        approved = review.model_copy(update={"status": ReviewStatus.APPROVED, "reviewer_id": reviewer_id, "reviewer_name": reviewer_name, "review_timestamp": now, "decision": "approved", "comments": comments, "rejection_reason": None, "approved_version": data.version, "approved_content_hash": data.content_hash})
        return self._event(approved, ReviewEventType.APPROVED, actor_id=reviewer_id)

    def reject(self, review: ChargeSheetReview, data: ChargeSheetData, *, reviewer_id: str, rejection_reason: str, comments: str | None = None) -> ChargeSheetReview:
        self._ensure_status(review, ReviewStatus.REVIEW_REQUIRED)
        self._ensure_data_matches(review, data)
        if not rejection_reason.strip():
            raise ReviewLifecycleError("A rejection reason is required")
        rejected = review.model_copy(update={"status": ReviewStatus.REJECTED, "reviewer_id": reviewer_id, "review_timestamp": datetime.now(timezone.utc), "decision": "rejected", "comments": comments, "rejection_reason": rejection_reason})
        return self._event(rejected, ReviewEventType.REJECTED, actor_id=reviewer_id)

    def request_revision(self, review: ChargeSheetReview, data: ChargeSheetData, *, reviewer_id: str, comments: str) -> ChargeSheetReview:
        self._ensure_status(review, ReviewStatus.REVIEW_REQUIRED)
        self._ensure_data_matches(review, data)
        if not comments.strip():
            raise ReviewLifecycleError("Revision comments are required")
        revised = review.model_copy(update={"status": ReviewStatus.DRAFT, "reviewer_id": reviewer_id, "review_timestamp": datetime.now(timezone.utc), "decision": "revision_requested", "comments": comments})
        return self._event(revised, ReviewEventType.REVISION_REQUESTED, actor_id=reviewer_id)

    def replace_data(self, review: ChargeSheetReview, data: ChargeSheetData) -> ChargeSheetReview:
        """Invalidate any prior approval when a new deterministic data version arrives."""

        if review.status == ReviewStatus.FINALIZED:
            raise ReviewLifecycleError("FINALIZED charge sheets are immutable")
        if data.case_id != review.case_id:
            raise ReviewLifecycleError("Replacement data belongs to a different case")
        if data.version <= review.data_version:
            raise ReviewLifecycleError("Revised ChargeSheetData must use a higher version")
        replacement = review.model_copy(update={"status": ReviewStatus.DRAFT, "data_version": data.version, "data_content_hash": data.content_hash, "reviewer_id": None, "reviewer_name": None, "review_timestamp": None, "decision": None, "comments": None, "rejection_reason": None, "approved_version": None, "approved_content_hash": None})
        return self._event(replacement, ReviewEventType.DRAFT_CREATED, metadata={"supersedes_version": str(review.data_version)})

    def finalize(self, review: ChargeSheetReview, data: ChargeSheetData, *, storage_root: Path) -> ChargeSheetReview:
        if review.status == ReviewStatus.FINALIZED:
            self._ensure_data_matches(review, data)
            return review
        self._ensure_status(review, ReviewStatus.APPROVED)
        self._ensure_data_matches(review, data)
        if data.disposition == ValidationDisposition.FINAL_BLOCKED.value:
            raise ReviewLifecycleError("FINAL_BLOCKED charge sheets cannot be finalized")
        if review.approved_version != data.version or review.approved_content_hash != data.content_hash:
            raise ReviewLifecycleError("Approval does not authorize this ChargeSheetData version")
        layout = CaseStorageLayout(storage_root, data.case_id).ensure_exists()
        final_path = layout.processed_directory / "chargesheet" / "final" / f"ChargeSheet_v{data.version}_final.pdf"
        if final_path.exists():
            raise ReviewLifecycleError("A finalized artifact already exists and will not be overwritten")
        IF5Renderer().render(data, final_path, final=True)
        finalized = review.model_copy(update={"status": ReviewStatus.FINALIZED, "finalized_at": datetime.now(timezone.utc), "final_artifact_reference": layout.relative_key(final_path)})
        finalized = self._event(finalized, ReviewEventType.FINALIZED, actor_id=review.reviewer_id or "system")
        state_path = layout.processed_directory / "chargesheet" / "review_state.json"
        state_path.write_text(json.dumps(finalized.model_dump(mode="json"), indent=2), encoding="utf-8")
        return finalized

    def _ensure_status(self, review: ChargeSheetReview, expected: ReviewStatus) -> None:
        if review.status == ReviewStatus.FINALIZED:
            raise ReviewLifecycleError("FINALIZED charge sheets are immutable")
        if review.status != expected:
            raise ReviewLifecycleError(f"Expected review status {expected.value}, got {review.status.value}")

    def _ensure_data_matches(self, review: ChargeSheetReview, data: ChargeSheetData) -> None:
        if review.case_id != data.case_id or review.data_version != data.version or review.data_content_hash != data.content_hash:
            raise ReviewLifecycleError("ChargeSheetData does not match the review version and content hash")

    def _event(self, review: ChargeSheetReview, event_type: ReviewEventType, *, actor_id: str = "system", metadata: dict[str, str] | None = None) -> ChargeSheetReview:
        event = ReviewEvent(event_type=event_type, case_id=review.case_id, charge_sheet_id=review.charge_sheet_id, version=review.data_version, actor_id=actor_id, metadata=metadata or {})
        return review.model_copy(update={"events": review.events + (event,)})
