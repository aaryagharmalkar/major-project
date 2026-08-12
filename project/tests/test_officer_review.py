from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from src.chargesheet.chargesheet_populator import ChargeSheetPopulator
from src.review.review_models import ReviewEventType, ReviewStatus
from src.review.review_service import ReviewLifecycleError, ReviewService

from test_chargesheet import context, findings


class OfficerReviewTests(TestCase):
    def setUp(self):
        self.service = ReviewService()
        self.data = ChargeSheetPopulator().populate(context(), findings())

    def submitted(self):
        return self.service.submit_for_review(self.service.create_draft(self.data), self.data)

    def approved(self):
        return self.service.approve(self.submitted(), self.data, reviewer_id="officer-1", reviewer_name="Officer One")

    def test_draft_creation_is_versioned_and_audited(self):
        review = self.service.create_draft(self.data)
        self.assertEqual(review.status, ReviewStatus.DRAFT)
        self.assertEqual(review.data_version, 1)
        self.assertEqual(review.data_content_hash, self.data.content_hash)
        self.assertEqual(review.events[-1].event_type, ReviewEventType.DRAFT_CREATED)

    def test_submission_requires_draft_and_sets_review_required(self):
        review = self.submitted()
        self.assertEqual(review.status, ReviewStatus.REVIEW_REQUIRED)
        self.assertEqual(review.events[-1].event_type, ReviewEventType.SUBMITTED_FOR_REVIEW)

    def test_officer_can_approve_review_required_version(self):
        review = self.approved()
        self.assertEqual(review.status, ReviewStatus.APPROVED)
        self.assertEqual(review.approved_version, self.data.version)
        self.assertEqual(review.approved_content_hash, self.data.content_hash)

    def test_officer_can_reject_and_reason_is_retained(self):
        review = self.service.reject(self.submitted(), self.data, reviewer_id="officer-1", rejection_reason="Missing signed annexure")
        self.assertEqual(review.status, ReviewStatus.REJECTED)
        self.assertEqual(review.rejection_reason, "Missing signed annexure")

    def test_officer_can_request_revision(self):
        review = self.service.request_revision(self.submitted(), self.data, reviewer_id="officer-1", comments="Clarify annexure reference")
        self.assertEqual(review.status, ReviewStatus.DRAFT)
        self.assertEqual(review.events[-1].event_type, ReviewEventType.REVISION_REQUESTED)

    def test_final_blocked_cannot_be_approved_or_finalized(self):
        blocked = self.data.model_copy(update={"disposition": "final_blocked"})
        review = self.service.submit_for_review(self.service.create_draft(blocked), blocked)
        with self.assertRaises(ReviewLifecycleError):
            self.service.approve(review, blocked, reviewer_id="officer-1")
        with self.assertRaises(ReviewLifecycleError):
            self.service.finalize(review, blocked, storage_root=Path("."))

    def test_draft_and_rejected_cannot_be_finalized(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ReviewLifecycleError):
                self.service.finalize(self.service.create_draft(self.data), self.data, storage_root=Path(directory))
            rejected = self.service.reject(self.submitted(), self.data, reviewer_id="officer-1", rejection_reason="Rejected")
            with self.assertRaises(ReviewLifecycleError):
                self.service.finalize(rejected, self.data, storage_root=Path(directory))

    def test_approved_version_finalizes_once_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            finalized = self.service.finalize(self.approved(), self.data, storage_root=Path(directory))
            self.assertEqual(finalized.status, ReviewStatus.FINALIZED)
            self.assertTrue((Path(directory) / finalized.final_artifact_reference).is_file())
            self.assertEqual(self.service.finalize(finalized, self.data, storage_root=Path(directory)), finalized)

    def test_changed_data_invalidates_approval_and_requires_new_review(self):
        approved = self.approved()
        changed = self.data.model_copy(update={"version": 2})
        revision = self.service.replace_data(approved, changed)
        self.assertEqual(revision.status, ReviewStatus.DRAFT)
        self.assertIsNone(revision.approved_version)
        with TemporaryDirectory() as directory:
            with self.assertRaises(ReviewLifecycleError):
                self.service.finalize(approved, changed, storage_root=Path(directory))
        self.assertEqual(self.service.submit_for_review(revision, changed).status, ReviewStatus.REVIEW_REQUIRED)

    def test_wrong_version_or_content_hash_cannot_finalize(self):
        approved = self.approved()
        wrong_version = self.data.model_copy(update={"version": 2})
        with TemporaryDirectory() as directory:
            with self.assertRaises(ReviewLifecycleError):
                self.service.finalize(approved, wrong_version, storage_root=Path(directory))
            forged = approved.model_copy(update={"data_content_hash": "0" * 64})
            with self.assertRaises(ReviewLifecycleError):
                self.service.finalize(forged, self.data, storage_root=Path(directory))

    def test_finalized_record_cannot_transition(self):
        with TemporaryDirectory() as directory:
            finalized = self.service.finalize(self.approved(), self.data, storage_root=Path(directory))
            with self.assertRaises(ReviewLifecycleError):
                self.service.request_revision(finalized, self.data, reviewer_id="officer-1", comments="No")

    def test_draft_and_final_artifacts_are_separate(self):
        with TemporaryDirectory() as directory:
            draft = Path(directory) / "draft" / "ChargeSheet_v1_review.pdf"
            from src.rendering.if5_renderer import IF5Renderer
            IF5Renderer().render(self.data, draft)
            finalized = self.service.finalize(self.approved(), self.data, storage_root=Path(directory))
            self.assertNotEqual(draft, Path(directory) / finalized.final_artifact_reference)
            self.assertTrue(draft.is_file())

    def test_lifecycle_events_are_recorded(self):
        finalized = None
        with TemporaryDirectory() as directory:
            finalized = self.service.finalize(self.approved(), self.data, storage_root=Path(directory))
        self.assertEqual([event.event_type for event in finalized.events], [ReviewEventType.DRAFT_CREATED, ReviewEventType.SUBMITTED_FOR_REVIEW, ReviewEventType.APPROVED, ReviewEventType.FINALIZED])


if __name__ == "__main__":
    main()
