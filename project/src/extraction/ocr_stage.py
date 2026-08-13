"""Workflow stage that invokes OCR clients and attaches raw OCR artifacts."""

from __future__ import annotations

import time
from pathlib import Path
from uuid import UUID

from ..domain.documents import ExtractionState, ValidationStatus
from ..intake.checksum import calculate_sha256
from ..intake.storage_layout import CaseStorageLayout
from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .ocr_artifacts import OCRArtifactWriter
from .ocr_client import OCRClient


class OCRStage(WorkflowStage):
    name = "ocr"

    def __init__(self, storage_root: Path, client: OCRClient, artifact_writer: OCRArtifactWriter | None = None, *, resume: bool = False) -> None:
        self.storage_root = storage_root
        self.client = client
        self.artifact_writer = artifact_writer or OCRArtifactWriter(storage_root)
        self.resume = resume

    def can_run(self, context: WorkflowContext) -> bool:
        return any(
            document.validation_status == ValidationStatus.VALID
            and document.extraction_state == ExtractionState.PENDING
            and self.client.supports(document)
            for document in context.uploaded_documents
        )

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        results: list[ContextItem] = list(context.ocr_results)
        artifacts = list(context.generated_artifacts)
        updated_documents = []
        page_count = 0
        character_count = 0
        confidence_values: list[float] = []
        reused_count = 0

        for document in context.uploaded_documents:
            if (
                document.validation_status != ValidationStatus.VALID
                or document.extraction_state != ExtractionState.PENDING
                or not self.client.supports(document)
            ):
                updated_documents.append(document)
                continue
            source_path = self.storage_root / document.storage_key
            loaded = self._load_resume_artifact(document, source_path) if self.resume else None
            if loaded is not None:
                result, existing_artifacts = loaded
                artifacts.extend(existing_artifacts)
                reused_count += 1
            else:
                result = self.client.extract(document, source_path)
                artifacts.extend(self.artifact_writer.write(document, result))
            results.append(ContextItem(key=str(document.id), value=result))
            updated_documents.append(document.model_copy(update={"extraction_state": ExtractionState.COMPLETE}))
            page_count += result.page_count
            character_count += len(result.raw_text)
            if result.confidence is not None:
                confidence_values.append(result.confidence)

        return context.with_updates(
            uploaded_documents=tuple(updated_documents),
            ocr_results=tuple(results),
            generated_artifacts=tuple(artifacts),
            stage_metrics=context.stage_metrics + (
                ContextItem(
                    key=self.name,
                    value={
                        "execution_time_ms": (time.perf_counter() - started) * 1000,
                        "page_count": page_count,
                        "characters_extracted": character_count,
                        "confidence": (sum(confidence_values) / len(confidence_values) if confidence_values else None),
                        "token_usage": None,
                        "estimated_cost": None, "reused_ocr_results": reused_count,
                    },
                ),
            ),
            execution_metadata=context.execution_metadata + (
                ContextItem(key=self.name, value={"provider": type(self.client).__name__, "documents_processed": len(results) - len(context.ocr_results), "reused_ocr_results": reused_count}),
            ),
        )

    def _load_resume_artifact(self, document, source_path: Path):
        if self._matches_document_checksum(source_path, document.sha256):
            return self.artifact_writer.load(document)

        # A manifest can carry a regenerated document ID while the prior,
        # byte-identical original and its OCR artifacts remain in this case.
        # Reuse only after binding that candidate original to the current
        # document checksum and validating its own OCR artifact identity.
        layout = CaseStorageLayout(self.storage_root, document.case_id)
        expected_extension = Path(document.stored_filename or source_path.name).suffix.lower()
        try:
            candidates = tuple(layout.originals_directory.iterdir())
        except OSError:
            return None
        for candidate_path in candidates:
            if not candidate_path.is_file() or candidate_path.suffix.lower() != expected_extension:
                continue
            try:
                candidate_id = UUID(candidate_path.stem)
            except ValueError:
                continue
            if not self._matches_document_checksum(candidate_path, document.sha256):
                continue
            loaded = self.artifact_writer.load(document, artifact_document_id=candidate_id)
            if loaded is None:
                continue
            result, artifacts = loaded
            return result.model_copy(update={"document_id": document.id}), artifacts
        return None

    @staticmethod
    def _matches_document_checksum(path: Path, expected_checksum: str) -> bool:
        if not path.is_file():
            return False
        try:
            return calculate_sha256(path) == expected_checksum
        except OSError:
            return False
