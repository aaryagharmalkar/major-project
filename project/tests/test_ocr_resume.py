from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import uuid4

from src.domain.documents import ExtractionState
from src.domain.parsed_documents import FIR
from src.extraction.ocr_client import OCRClient
from src.extraction.ocr_result import OCRMetadata, OCRPage, OCRResult
from src.extraction.ocr_stage import OCRStage
from src.intake.document_intake_stage import DocumentIntakeStage
from src.intake.upload_manager import IncomingUpload, UploadManager
from src.parsers.base_parser import ParserClient, ParserError
from src.parsers.fir_parser import FIRParser
from src.parsers.parser_registry import ParserRegistry
from src.parsers.parser_stage import ParserStage
from src.workflow.context import WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.production import create_workflow_context
from src.workflow.registry import StageRegistry
from src.workflow.state import StageStatus, WorkflowState


class CountingOCR(OCRClient):
    supported_mime_types = frozenset({"application/pdf"})

    def __init__(self):
        self.calls = 0

    def extract(self, document, source_path):
        self.calls += 1
        text = f"OCR for {document.id}"
        return OCRResult(
            document_id=document.id, pages=(OCRPage(page_number=1, text=text, confidence=.9),), raw_text=text,
            confidence=.9, language="en",
            metadata=OCRMetadata(provider="mock", model="mock-ocr", input_mime_type=document.media_type, processing_time_ms=1),
        )


class FixedParserClient(ParserClient):
    def __init__(self, *, fail: bool = False):
        self.fail = fail

    def generate_json(self, prompt):
        if self.fail:
            raise ParserError("simulated parser quota failure")
        return {"fir_number": "42/2026"}


class OCRResumeTests(TestCase):
    def _uploads(self, root: Path, names=("fir.pdf",)):
        uploads = []
        for index, name in enumerate(names):
            path = root / name
            path.write_bytes(b"%PDF-1.4\nresume fixture " + str(index).encode())
            uploads.append(IncomingUpload(source_path=path, original_filename=name))
        return tuple(uploads)

    def _initial_ocr(self, root: Path, names=("fir.pdf",)):
        storage, case_id = root / "storage", uuid4()
        uploads = self._uploads(root, names)
        manifest = UploadManager(storage).ingest(case_id, uploads)
        UploadManager(storage).write_manifest(manifest)
        client = CountingOCR()
        context = WorkflowContext(case_id=case_id, uploaded_documents=manifest.accepted_documents, upload_manifest=manifest, execution_state=WorkflowState(case_id=case_id))
        result = WorkflowEngine(StageRegistry((OCRStage(storage, client),))).run(context)
        self.assertTrue(result.report.successful)
        return storage, case_id, uploads, manifest, result.context

    @staticmethod
    def _pending(context):
        return context.with_updates(
            uploaded_documents=tuple(document.model_copy(update={"extraction_state": ExtractionState.PENDING}) for document in context.uploaded_documents),
            ocr_results=(), execution_state=WorkflowState(case_id=context.case_id), stage_metrics=(), execution_metadata=(),
        )

    def test_valid_artifacts_are_reused_without_an_ocr_call(self):
        with TemporaryDirectory() as directory:
            storage, _, _, _, initial = self._initial_ocr(Path(directory))
            client = CountingOCR()
            resumed = WorkflowEngine(StageRegistry((OCRStage(storage, client, resume=True),))).run(self._pending(initial))
            self.assertTrue(resumed.report.successful)
            self.assertEqual(client.calls, 0)
            self.assertEqual(resumed.context.stage_metrics[-1].value["reused_ocr_results"], 1)

    def test_checksum_mismatch_or_missing_or_invalid_artifact_requires_fresh_ocr(self):
        with TemporaryDirectory() as directory:
            storage, _, _, _, initial = self._initial_ocr(Path(directory))
            mismatched = self._pending(initial).with_updates(uploaded_documents=(initial.uploaded_documents[0].model_copy(update={"sha256": "f" * 64, "extraction_state": ExtractionState.PENDING}),))
            client = CountingOCR()
            WorkflowEngine(StageRegistry((OCRStage(storage, client, resume=True),))).run(mismatched)
            self.assertEqual(client.calls, 1)

            result_path = next(storage / artifact.storage_key for artifact in initial.generated_artifacts if artifact.name == "ocr_result")
            result_path.unlink()
            client = CountingOCR()
            WorkflowEngine(StageRegistry((OCRStage(storage, client, resume=True),))).run(self._pending(initial))
            self.assertEqual(client.calls, 1)

            result_path.write_text("{}", encoding="utf-8")
            client = CountingOCR()
            WorkflowEngine(StageRegistry((OCRStage(storage, client, resume=True),))).run(self._pending(initial))
            self.assertEqual(client.calls, 1)

    def test_mixed_artifacts_reuse_only_valid_documents_and_non_resume_stays_fresh(self):
        with TemporaryDirectory() as directory:
            storage, _, _, _, initial = self._initial_ocr(Path(directory), ("fir.pdf", "complaint.pdf"))
            second_result = [storage / artifact.storage_key for artifact in initial.generated_artifacts if artifact.name == "ocr_result"][1]
            second_result.unlink()
            client = CountingOCR()
            resumed = WorkflowEngine(StageRegistry((OCRStage(storage, client, resume=True),))).run(self._pending(initial))
            self.assertEqual(client.calls, 1)
            self.assertEqual(resumed.context.stage_metrics[-1].value["reused_ocr_results"], 1)

            client = CountingOCR()
            WorkflowEngine(StageRegistry((OCRStage(storage, client, resume=False),))).run(self._pending(initial))
            self.assertEqual(client.calls, 2)

    def test_resume_after_parser_failure_reuses_ocr_and_retries_parser(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            storage, case_id = root / "storage", uuid4()
            uploads = self._uploads(root)
            failing_registry = ParserRegistry(FIRParser(FixedParserClient(fail=True)))
            failing_registry.register(FIRParser(FixedParserClient(fail=True)))
            first = create_workflow_context(case_id, uploads)
            first_run = WorkflowEngine(StageRegistry((
                DocumentIntakeStage(storage), OCRStage(storage, CountingOCR()), ParserStage(storage, failing_registry),
            ))).run(first)
            self.assertEqual(first_run.context.execution_state.record_for("ocr").status, StageStatus.COMPLETED)
            self.assertEqual(first_run.context.execution_state.record_for("document_parsing").status, StageStatus.FAILED)

            parser_registry = ParserRegistry(FIRParser(FixedParserClient()))
            parser_registry.register(FIRParser(FixedParserClient()))
            resumed = create_workflow_context(case_id, uploads, resume=True, storage_root=storage)
            ocr = CountingOCR()
            resumed_run = WorkflowEngine(StageRegistry((
                DocumentIntakeStage(storage, resume=True), OCRStage(storage, ocr, resume=True), ParserStage(storage, parser_registry),
            ))).run(resumed)
            self.assertTrue(resumed_run.report.successful)
            self.assertEqual(ocr.calls, 0)
            self.assertIsInstance(resumed_run.context.parsed_documents[0].value, FIR)
