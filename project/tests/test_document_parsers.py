from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from src.domain.documents import DocumentType, ExtractionState, ParsingState
from src.domain.parsed_documents import Complaint, FIR
from src.extraction.ocr_result import OCRMetadata, OCRPage, OCRResult
from src.intake.upload_manager import IncomingUpload, UploadManager
from src.parsers.base_parser import GeminiParserClient, ParserClient
from src.parsers.fir_parser import FIRParser
from src.parsers.complaint_parser import ComplaintParser
from src.knowledge_graph.graph_builder import GraphBuilder
from src.normalization.canonical_builder import CanonicalBuilder
from src.parsers.parser_artifacts import ParsedDocumentArtifactWriter
from src.parsers.parser_registry import ParserRegistry, create_default_parser_registry
from src.parsers.parser_stage import ParserStage
from src.parsers.unknown_document_parser import UnknownDocumentParser
from src.workflow.context import ContextItem, WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import StageStatus, WorkflowState


class QueueParserClient(ParserClient):
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate_json(self, prompt: str):
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeGeminiModel:
    def generate_content(self, prompt, generation_config):
        self.prompt = prompt
        self.generation_config = generation_config
        return type("Response", (), {"text": json.dumps({"fir_number": "42/2026"})})()


def make_ocr_result(document_id):
    return OCRResult(
        document_id=document_id,
        pages=(OCRPage(page_number=1, text="FIR No. 42/2026", confidence=0.9),),
        raw_text="FIR No. 42/2026",
        confidence=0.9,
        language="en",
        metadata=OCRMetadata(
            provider="mock",
            model="mock-ocr",
            input_mime_type="application/pdf",
            processing_time_ms=1,
        ),
    )


class DocumentParserTests(unittest.TestCase):
    def _ocr(self, text: str) -> OCRResult:
        return OCRResult(
            document_id=uuid4(), pages=(OCRPage(page_number=1, text=text, confidence=0.9),), raw_text=text,
            confidence=0.9, language="en",
            metadata=OCRMetadata(provider="mock", model="mock-ocr", input_mime_type="application/pdf", processing_time_ms=1),
        )

    def _document_with_ocr(self, root: Path):
        source = root / "FIR.pdf"
        source.write_bytes(b"%PDF-1.4\nfixture")
        manager = UploadManager(root / "uploads")
        manifest = manager.ingest(uuid4(), (IncomingUpload(source_path=source, original_filename=source.name),))
        document = manifest.accepted_documents[0].model_copy(update={"extraction_state": ExtractionState.COMPLETE})
        return document, root / "uploads", make_ocr_result(document.id)

    def test_registry_selects_document_specific_parser(self) -> None:
        client = QueueParserClient([{"fir_number": "42/2026"}])
        registry = create_default_parser_registry(client)

        parser = registry.get(document_type=DocumentType.FIR)

        self.assertIsInstance(parser, FIRParser)

    def test_schema_validation_retries_then_returns_typed_model(self) -> None:
        document_id = uuid4()
        client = QueueParserClient(
            [
                {"registration_date": "not-a-date"},
                {"fir_number": "42/2026", "registration_date": "2026-01-02", "confidence": 0.8},
            ]
        )

        result = FIRParser(client).parse(make_ocr_result(document_id))

        self.assertIsInstance(result, FIR)
        self.assertEqual(result.fir_number, "42/2026")
        self.assertEqual(result.parse_metadata.retry_count, 1)
        self.assertEqual(len(client.prompts), 2)

    def test_mocked_gemini_client_returns_json_for_schema_validation(self) -> None:
        fake_model = FakeGeminiModel()
        client = GeminiParserClient(model_client=fake_model)

        payload = client.generate_json("schema constrained prompt")

        self.assertEqual(payload["fir_number"], "42/2026")
        self.assertEqual(fake_model.generation_config["response_mime_type"], "application/json")

    def test_parsed_artifact_is_generated(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root, ocr_result = self._document_with_ocr(Path(temp_dir))
            parsed = FIRParser(QueueParserClient([{"fir_number": "42/2026"}])).parse(ocr_result)

            artifact = ParsedDocumentArtifactWriter(storage_root).write(document, parsed)

            self.assertTrue((storage_root / artifact.storage_key).is_file())
            self.assertEqual(json.loads((storage_root / artifact.storage_key).read_text(encoding="utf-8"))["fir_number"], "42/2026")

    def test_parser_stage_integrates_with_workflow_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root, ocr_result = self._document_with_ocr(Path(temp_dir))
            registry = create_default_parser_registry(QueueParserClient([{"fir_number": "42/2026", "confidence": 0.9}]))
            context = WorkflowContext(
                case_id=document.case_id,
                uploaded_documents=(document,),
                ocr_results=(ContextItem(key=str(document.id), value=ocr_result),),
                execution_state=WorkflowState(case_id=document.case_id),
            )

            result = WorkflowEngine(StageRegistry([ParserStage(storage_root, registry)])).run(context)

            self.assertTrue(result.report.successful)
            self.assertEqual(result.context.uploaded_documents[0].parsing_state, ParsingState.COMPLETE)
            self.assertIsInstance(result.context.parsed_documents[0].value, FIR)
            self.assertEqual(result.context.stage_metrics[-1].value["documents_parsed"], 1)
            self.assertEqual(len(result.context.generated_artifacts), 1)

    def test_invalid_schema_failure_is_preserved_and_stage_retry_succeeds(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document, storage_root, ocr_result = self._document_with_ocr(Path(temp_dir))
            client = QueueParserClient([{"registration_date": "invalid-date"}, {"fir_number": "42/2026"}])
            registry = ParserRegistry(UnknownDocumentParser(client))
            registry.register(FIRParser(client, max_attempts=1))
            context = WorkflowContext(
                case_id=document.case_id,
                uploaded_documents=(document,),
                ocr_results=(ContextItem(key=str(document.id), value=ocr_result),),
                execution_state=WorkflowState(case_id=document.case_id),
            )
            engine = WorkflowEngine(StageRegistry([ParserStage(storage_root, registry)]))

            failed_run = engine.run(context)
            retried_run = engine.run(failed_run.context)

            self.assertEqual(failed_run.context.execution_state.record_for("document_parsing").status, StageStatus.FAILED)
            self.assertEqual(retried_run.context.execution_state.record_for("document_parsing").status, StageStatus.COMPLETED)
            self.assertEqual(retried_run.context.uploaded_documents[0].parsing_state, ParsingState.COMPLETE)

    def test_regression_fixture_entities_survive_parser_graph_and_canonical_projection(self) -> None:
        ocr_root = Path(__file__).parents[1] / "output" / "CASE_37e9a78cbf45553ebdbbf88e5e2ca761" / "processed" / "ocr"
        fir_ocr = self._ocr(json.loads((ocr_root / "FIR_d78b79f0_OCRResult.json").read_text(encoding="utf-8"))["raw_text"])
        complaint_ocr = self._ocr(json.loads((ocr_root / "complaint_553a46f3_OCRResult.json").read_text(encoding="utf-8"))["raw_text"])
        fir = FIRParser(QueueParserClient([{
            "complainant_name": "Neha Patil", "accused_names": ["Rohan Mehta"],
            "victim_names": ["Amit Kulkarni"], "vehicle_registrations": ["MH-12-AB-4821"],
        }])).parse(fir_ocr)
        complaint = ComplaintParser(QueueParserClient([{
            "complainant_name": "Neha Patil", "person_complained_against_names": ["Rohan Mehta"],
            "victim_names": ["Amit Kulkarni"], "vehicle_registrations": ["MH-12-AB-4821"],
        }])).parse(complaint_ocr)

        canonical = CanonicalBuilder().build(GraphBuilder(uuid4()).build((fir, complaint)))

        self.assertEqual(tuple(person.name.value for person in canonical.complainants), ("Neha Patil",))
        self.assertEqual(tuple(person.name.value for person in canonical.accused), ("Rohan Mehta",))
        self.assertEqual(tuple(person.name.value for person in canonical.victims), ("Amit Kulkarni",))
        self.assertEqual(tuple(vehicle.registration_number.value for vehicle in canonical.vehicles), ("MH-12-AB-4821",))

    def test_different_explicit_entities_are_projected_without_case_specific_logic(self) -> None:
        ocr = self._ocr(
            "FIR\nComplainant: Priya Sharma\nAccused: Raj Verma\nVictim: Sameer Khan\nVehicle: DL-01-AB-1234"
        )
        parsed = FIRParser(QueueParserClient([{
            "complainant_name": "Priya Sharma", "accused_names": ["Raj Verma"],
            "victim_names": ["Sameer Khan"], "vehicle_registrations": ["DL-01-AB-1234"],
        }])).parse(ocr)

        canonical = CanonicalBuilder().build(GraphBuilder(uuid4()).build((parsed,)))

        self.assertEqual(canonical.complainants[0].name.value, "Priya Sharma")
        self.assertEqual(canonical.accused[0].name.value, "Raj Verma")
        self.assertEqual(canonical.victims[0].name.value, "Sameer Khan")
        self.assertEqual(canonical.vehicles[0].registration_number.value, "DL-01-AB-1234")

    def test_absent_accused_is_not_invented_and_unsupported_entity_is_rejected(self) -> None:
        ocr = self._ocr("WRITTEN COMPLAINT\nComplainant: Priya Sharma\nVictim: Sameer Khan")
        parsed = ComplaintParser(QueueParserClient([{
            "complainant_name": "Priya Sharma", "victim_names": ["Sameer Khan"],
        }])).parse(ocr)
        canonical = CanonicalBuilder().build(GraphBuilder(uuid4()).build((parsed,)))
        self.assertFalse(canonical.accused)

        with self.assertRaises(Exception):
            ComplaintParser(QueueParserClient([{
                "complainant_name": "Priya Sharma", "person_complained_against_names": ["Raj Verma"],
            }])).parse(ocr)


if __name__ == "__main__":
    unittest.main()
