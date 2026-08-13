from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from src.domain.documents import ExtractionState, SourceDocument, ValidationStatus
from src.extraction.gemini_ocr import GeminiOCRClient
from src.extraction.ocr_artifacts import OCRArtifactWriter
from src.extraction.ocr_client import OCRClient
from src.extraction.ocr_result import OCRMetadata, OCRPage, OCRResult
from src.extraction.ocr_stage import OCRStage
from src.intake.upload_manager import IncomingUpload, UploadManager
from src.workflow.context import WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import StageStatus, WorkflowState


def write_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\nOCR fixture\n")


class FakeGeminiResponse:
    def __init__(self, payload: dict | None = None, *, text: str | None = None, parsed=None) -> None:
        self.text = json.dumps(payload) if text is None else text
        self.parsed = parsed
        self.usage_metadata = type("Usage", (), {"total_token_count": 42})()


class FakeGeminiModel:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests: list[tuple] = []

    def generate_content(self, contents, generation_config):
        self.requests.append((contents, generation_config))
        return FakeGeminiResponse(self.payload)


class FakeGenAIClient:
    """Current SDK-shaped client proving PDFs use Files API and are cleaned up."""
    def __init__(self, payload: dict) -> None:
        self.files = self.Files()
        self.models = self.Models(payload)

    class Files:
        def __init__(self): self.uploads, self.deleted = [], []
        def upload(self, *, file, config):
            self.uploads.append((file, config))
            return type("Uploaded", (), {"name": "files/fixture"})()
        def delete(self, *, name): self.deleted.append(name)

    class Models:
        def __init__(self, payload): self.payload, self.requests = payload, []
        def generate_content(self, *, model, contents, config):
            self.requests.append((model, contents, config))
            return FakeGeminiResponse(self.payload)


class MockOCRClient(OCRClient):
    supported_mime_types = frozenset({"application/pdf"})

    def __init__(self, *, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.calls = 0

    def extract(self, document: SourceDocument, source_path: Path) -> OCRResult:
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise RuntimeError("temporary provider failure")
        pages = (
            OCRPage(page_number=1, text="first page", confidence=0.95),
            OCRPage(page_number=2, text="second page", confidence=0.85),
        )
        return OCRResult(
            document_id=document.id,
            pages=pages,
            raw_text="first page\n\nsecond page",
            confidence=0.9,
            warnings=(),
            language="en",
            metadata=OCRMetadata(
                provider="mock",
                model="mock-ocr",
                input_mime_type=document.media_type,
                processing_time_ms=5,
            ),
        )


class OCRLayerTests(unittest.TestCase):
    def _ingested_document(self, root: Path) -> tuple[SourceDocument, Path]:
        source = root / "FIR.pdf"
        write_pdf(source)
        manager = UploadManager(root / "uploads")
        manifest = manager.ingest(uuid4(), (IncomingUpload(source_path=source, original_filename=source.name),))
        document = manifest.accepted_documents[0]
        return document, root / "uploads"

    def _ingested_image(self, root: Path) -> tuple[SourceDocument, Path]:
        source = root / "scene.png"
        source.write_bytes(b"\x89PNG\r\n\x1a\nimage fixture")
        manager = UploadManager(root / "uploads")
        manifest = manager.ingest(uuid4(), (IncomingUpload(source_path=source, original_filename=source.name),))
        document = manifest.accepted_documents[0]
        return document, root / "uploads"

    def test_mocked_gemini_adapter_returns_multipage_raw_ocr(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_document(Path(temp_dir))
            fake_model = FakeGeminiModel(
                {
                    "pages": [
                        {"page_number": 1, "text": "Page one", "confidence": 0.9},
                        {"page_number": 2, "text": "Page two", "confidence": 0.8},
                    ],
                    "language": "en",
                    "warnings": ["Low contrast on page 2"],
                }
            )
            client = GeminiOCRClient(model_client=fake_model)

            result = client.extract(document, storage_root / document.storage_key)

            self.assertEqual(result.page_count, 2)
            self.assertEqual(result.raw_text, "Page one\n\nPage two")
            self.assertEqual(result.metadata.token_usage, 42)
            self.assertEqual(result.warnings, ("Low contrast on page 2",))
            self.assertEqual(len(fake_model.requests), 1)
            self.assertEqual(fake_model.requests[0][1]["response_mime_type"], "application/json")
            self.assertEqual(fake_model.requests[0][1]["response_json_schema"], GeminiOCRClient.RESPONSE_SCHEMA)
            self.assertNotIn('"pages"', GeminiOCRClient.OCR_PROMPT)
            self.assertFalse(hasattr(result, "accused"))

    def test_current_sdk_pdf_path_uploads_and_deletes_the_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_document(Path(temp_dir))
            client_backend = FakeGenAIClient({"pages": [{"page_number": 1, "text": "Page one"}]})
            result = GeminiOCRClient(model_client=client_backend).extract(document, storage_root / document.storage_key)
            self.assertEqual(result.raw_text, "Page one")
            self.assertEqual(client_backend.files.uploads[0][1], {"mime_type": "application/pdf"})
            self.assertEqual(client_backend.files.deleted, ["files/fixture"])

    def test_current_sdk_image_path_uses_an_inline_image_part(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_image(Path(temp_dir))
            client_backend = FakeGenAIClient({"pages": [{"page_number": 1, "text": "Image text"}], "language": "en", "warnings": []})

            result = GeminiOCRClient(model_client=client_backend).extract(document, storage_root / document.storage_key)

            request = client_backend.models.requests[0]
            part = request[1][1]
            self.assertEqual(result.raw_text, "Image text")
            self.assertEqual(part.inline_data.mime_type, "image/png")
            self.assertFalse(client_backend.files.uploads)

    def test_sdk_parsed_response_is_used_when_response_text_is_not_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_document(Path(temp_dir))
            backend = FakeGeminiModel({})
            backend.generate_content = lambda contents, generation_config: FakeGeminiResponse(
                text="not JSON", parsed={"pages": [{"page_number": 1, "text": "Structured text"}], "language": "en", "warnings": []}
            )

            result = GeminiOCRClient(model_client=backend).extract(document, storage_root / document.storage_key)

            self.assertEqual(result.raw_text, "Structured text")

    def test_fenced_json_is_accepted_but_malformed_output_has_safe_diagnostics(self) -> None:
        fenced = "```json\n{\"pages\":[{\"page_number\":1,\"text\":\"Fenced text\"}],\"language\":null,\"warnings\":[]}\n```"
        payload = GeminiOCRClient._parse_payload(fenced)
        self.assertEqual(payload["pages"][0]["text"], "Fenced text")
        with self.assertRaisesRegex(Exception, r"received 9 characters"):
            GeminiOCRClient._parse_payload("not json!")

    def test_ocr_artifacts_are_written_without_parsing_text(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_document(Path(temp_dir))
            result = MockOCRClient().extract(document, storage_root / document.storage_key)

            artifacts = OCRArtifactWriter(storage_root).write(document, result)

            self.assertEqual(len(artifacts), 3)
            self.assertTrue(all((storage_root / artifact.storage_key).is_file() for artifact in artifacts))
            raw_text_artifact = next(artifact for artifact in artifacts if artifact.name == "ocr_raw_text")
            self.assertEqual((storage_root / raw_text_artifact.storage_key).read_text(encoding="utf-8"), result.raw_text)

    def test_ocr_stage_attaches_results_artifacts_and_metrics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_document(Path(temp_dir))
            context = WorkflowContext(
                case_id=document.case_id,
                uploaded_documents=(document,),
                execution_state=WorkflowState(case_id=document.case_id),
            )
            result = WorkflowEngine(StageRegistry([OCRStage(storage_root, MockOCRClient())])).run(context)

            self.assertTrue(result.report.successful)
            self.assertEqual(result.context.uploaded_documents[0].extraction_state, ExtractionState.COMPLETE)
            self.assertEqual(len(result.context.ocr_results), 1)
            self.assertEqual(len(result.context.generated_artifacts), 3)
            self.assertEqual(result.context.stage_metrics[-1].value["page_count"], 2)
            self.assertEqual(result.context.stage_metrics[-1].value["characters_extracted"], 23)

    def test_failed_ocr_stage_can_be_retried_with_preserved_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root = self._ingested_document(Path(temp_dir))
            context = WorkflowContext(
                case_id=document.case_id,
                uploaded_documents=(document,),
                execution_state=WorkflowState(case_id=document.case_id),
            )
            client = MockOCRClient(fail_first=True)
            engine = WorkflowEngine(StageRegistry([OCRStage(storage_root, client)]))

            failed_run = engine.run(context)
            retried_run = engine.run(failed_run.context)

            self.assertEqual(failed_run.context.execution_state.record_for("ocr").status, StageStatus.FAILED)
            self.assertEqual(retried_run.context.execution_state.record_for("ocr").status, StageStatus.COMPLETED)
            self.assertEqual(client.calls, 2)
            self.assertTrue(retried_run.report.successful)


if __name__ == "__main__":
    unittest.main()
