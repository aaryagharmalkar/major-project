"""Workflow stage that independently parses completed OCR results by registry lookup."""

from __future__ import annotations

import time
from pathlib import Path
from uuid import UUID

from ..domain.documents import ExtractionState, ParsingState
from ..extraction.ocr_result import OCRResult
from ..workflow.context import ContextItem, WorkflowContext
from ..workflow.stage import WorkflowStage
from .parser_artifacts import ParsedDocumentArtifactWriter
from .parser_registry import ParserRegistry


class ParserStage(WorkflowStage):
    name = "document_parsing"

    def __init__(self, storage_root: Path, registry: ParserRegistry, artifact_writer: ParsedDocumentArtifactWriter | None = None) -> None:
        self.registry = registry
        self.artifact_writer = artifact_writer or ParsedDocumentArtifactWriter(storage_root)

    def can_run(self, context: WorkflowContext) -> bool:
        result_ids = {self._ocr_result(item).document_id for item in context.ocr_results if self._is_ocr_result(item)}
        return any(
            document.extraction_state == ExtractionState.COMPLETE
            and document.parsing_state == ParsingState.PENDING
            and document.id in result_ids
            for document in context.uploaded_documents
        )

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        started = time.perf_counter()
        ocr_results = {
            self._ocr_result(item).document_id: self._ocr_result(item)
            for item in context.ocr_results
            if self._is_ocr_result(item)
        }
        parsed_items = list(context.parsed_documents)
        artifacts = list(context.generated_artifacts)
        updated_documents = []
        retry_count = 0
        confidence_values: list[float] = []
        warnings: list[str] = []

        for document in context.uploaded_documents:
            result = ocr_results.get(document.id)
            if (
                document.extraction_state != ExtractionState.COMPLETE
                or document.parsing_state != ParsingState.PENDING
                or result is None
            ):
                updated_documents.append(document)
                continue

            parser = self.registry.get(document.detected_type)
            parsed_document = parser.parse(result)
            parsed_items.append(ContextItem(key=str(document.id), value=parsed_document))
            artifacts.append(self.artifact_writer.write(document, parsed_document))
            updated_documents.append(document.model_copy(update={"parsing_state": ParsingState.COMPLETE}))
            retry_count += parsed_document.parse_metadata.retry_count
            if parsed_document.parse_metadata.confidence is not None:
                confidence_values.append(parsed_document.parse_metadata.confidence)
            warnings.extend(parsed_document.parse_metadata.warnings)

        parsed_count = len(parsed_items) - len(context.parsed_documents)
        return context.with_updates(
            uploaded_documents=tuple(updated_documents),
            parsed_documents=tuple(parsed_items),
            generated_artifacts=tuple(artifacts),
            stage_metrics=context.stage_metrics + (
                ContextItem(
                    key=self.name,
                    value={
                        "parse_duration_ms": (time.perf_counter() - started) * 1000,
                        "validation_success": True,
                        "retry_count": retry_count,
                        "confidence": (sum(confidence_values) / len(confidence_values) if confidence_values else None),
                        "warnings": tuple(warnings),
                        "documents_parsed": parsed_count,
                    },
                ),
            ),
            execution_metadata=context.execution_metadata + (
                ContextItem(key=self.name, value={"documents_parsed": parsed_count}),
            ),
        )

    @staticmethod
    def _is_ocr_result(item: ContextItem) -> bool:
        return isinstance(item.value, OCRResult)

    @staticmethod
    def _ocr_result(item: ContextItem) -> OCRResult:
        if not isinstance(item.value, OCRResult):
            raise TypeError("OCR result context item must contain OCRResult")
        return item.value
