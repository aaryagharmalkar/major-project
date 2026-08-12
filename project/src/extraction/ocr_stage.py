"""Workflow stage that invokes OCR clients and attaches raw OCR artifacts."""

from __future__ import annotations

import time
from pathlib import Path

from ..domain.documents import ExtractionState, ValidationStatus
from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .ocr_artifacts import OCRArtifactWriter
from .ocr_client import OCRClient


class OCRStage(WorkflowStage):
    name = "ocr"

    def __init__(self, storage_root: Path, client: OCRClient, artifact_writer: OCRArtifactWriter | None = None) -> None:
        self.storage_root = storage_root
        self.client = client
        self.artifact_writer = artifact_writer or OCRArtifactWriter(storage_root)

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

        for document in context.uploaded_documents:
            if (
                document.validation_status != ValidationStatus.VALID
                or document.extraction_state != ExtractionState.PENDING
                or not self.client.supports(document)
            ):
                updated_documents.append(document)
                continue
            source_path = self.storage_root / document.storage_key
            result = self.client.extract(document, source_path)
            results.append(ContextItem(key=str(document.id), value=result))
            artifacts.extend(self.artifact_writer.write(document, result))
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
                        "estimated_cost": None,
                    },
                ),
            ),
            execution_metadata=context.execution_metadata + (
                ContextItem(key=self.name, value={"provider": type(self.client).__name__, "documents_processed": len(results) - len(context.ocr_results)}),
            ),
        )
