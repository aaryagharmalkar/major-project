"""Workflow adapter for the otherwise transport-agnostic upload manager."""

from __future__ import annotations

from pathlib import Path

from ..workflow.context import ContextItem, GeneratedArtifact, WorkflowContext
from ..workflow.stage import WorkflowStage
from .upload_manager import IncomingUpload, UploadManager
from .upload_manifest import UploadManifest


class DocumentIntakeStage(WorkflowStage):
    name = "document_intake"

    def __init__(self, storage_root: Path, manager: UploadManager | None = None) -> None:
        self.manager = manager or UploadManager(storage_root)

    def can_run(self, context: WorkflowContext) -> bool:
        return bool(context.pending_uploads)

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        uploads = tuple(self._as_upload(item) for item in context.pending_uploads)
        existing_manifest = context.upload_manifest
        if existing_manifest is not None and not isinstance(existing_manifest, UploadManifest):
            raise TypeError("WorkflowContext.upload_manifest must be an UploadManifest")

        manifest = self.manager.ingest(context.case_id, uploads, existing_manifest)
        manifest_path = self.manager.write_manifest(manifest)
        accepted_count = len(manifest.accepted_documents)
        rejected_count = sum(entry.status.value == "rejected" for entry in manifest.entries)
        duplicate_count = sum(entry.status.value == "duplicate" for entry in manifest.entries)

        return context.with_updates(
            pending_uploads=(),
            uploaded_documents=manifest.accepted_documents,
            upload_manifest=manifest,
            generated_artifacts=context.generated_artifacts + (
                GeneratedArtifact(
                    name="upload_manifest",
                    storage_key=CaseStorageKey.from_path(self.manager.storage_root, manifest_path),
                    media_type="application/json",
                ),
            ),
            stage_metrics=context.stage_metrics + (
                ContextItem(key=self.name, value={"accepted": accepted_count, "rejected": rejected_count, "duplicate": duplicate_count}),
            ),
            execution_metadata=context.execution_metadata + (
                ContextItem(key=self.name, value={"manifest_entries": len(manifest.entries)}),
            ),
        )

    @staticmethod
    def _as_upload(item: ContextItem) -> IncomingUpload:
        if not isinstance(item.value, IncomingUpload):
            raise TypeError("pending_uploads values must be IncomingUpload instances")
        return item.value


class CaseStorageKey:
    """Keeps artifact paths relative to the configured storage root."""

    @staticmethod
    def from_path(storage_root: Path, path: Path) -> str:
        return path.relative_to(storage_root).as_posix()
