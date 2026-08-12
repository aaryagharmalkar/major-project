from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4

from src.domain.common import SourceReference
from src.extraction.ocr_client import OCRClient
from src.extraction.ocr_result import OCRMetadata, OCRPage, OCRResult
from src.intake.upload_manager import IncomingUpload
from src.legal.legal_rules import LegalJurisdiction, LegalReference, LegalReferenceProvider, LegalReferenceSource
from src.parsers.base_parser import ParserClient, ParserError
from src.validation.evidence_validator import EvidenceValidator
from src.validation.validation_models import ValidationDisposition, ValidationReport
from src.workflow.production import STAGE_ORDER, create_production_registry, create_workflow_context
from src.workflow.engine import WorkflowEngine
from src.workflow.state import StageStatus


class FixtureOCRClient(OCRClient):
    supported_mime_types = frozenset({"application/pdf"})

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def extract(self, document, source_path: Path) -> OCRResult:
        if self.fail:
            raise RuntimeError("fixture OCR failure")
        return OCRResult(
            document_id=document.id,
            pages=(OCRPage(page_number=1, text="Medical report: documented injury", confidence=0.9),),
            raw_text="Medical report: documented injury",
            confidence=0.9,
            metadata=OCRMetadata(provider="fixture", model="fixture-ocr", input_mime_type=document.media_type, processing_time_ms=1),
        )


class FixtureParserClient(ParserClient):
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def generate_json(self, prompt: str) -> dict:
        if self.fail:
            raise ParserError("fixture parser failure")
        return {"report_number": "MLC-1", "patient_name": "Asha Devi", "doctor_name": "Dr. Sen", "observations": ["documented injury"], "confidence": 0.9}


class FixtureLegalProvider(LegalReferenceProvider):
    def references_for(self, context):
        return (LegalReference(section_id=uuid4(), section_number="S-1", offence_name="Fixture offence", description="Fixture offence supported by documented injury", required_elements=("documented injury",), jurisdiction=LegalJurisdiction.INDIA, effective_from=date(2024, 7, 1), source=LegalReferenceSource(publisher="Fixture", citation="Fixture reference", uri="https://example.test/reference"), version="fixture-v1", source_reference=SourceReference(document_id=uuid4())),)


class FailingLegalProvider(LegalReferenceProvider):
    def references_for(self, context):
        raise RuntimeError("fixture legal provider failure")


class FinalBlockedValidator(EvidenceValidator):
    def validate(self, investigation) -> ValidationReport:
        return ValidationReport(completeness_score=0, critical_failure=True, review_required=True, disposition=ValidationDisposition.FINAL_BLOCKED)


class EndToEndPipelineTests(TestCase):
    def _workflow(self, root: Path, *, ocr=None, parser=None, provider=None, validator=None):
        source = root / "medical_report.pdf"
        source.write_bytes(b"%PDF-1.4\nfixture medical report\n")
        case_id = uuid4()
        context = create_workflow_context(case_id, (IncomingUpload(source_path=source, original_filename=source.name),))
        registry = create_production_registry(root / "artifacts", ocr_client=ocr or FixtureOCRClient(), parser_client=parser or FixtureParserClient(), legal_reference_provider=provider or FixtureLegalProvider(), evidence_validator=validator)
        return WorkflowEngine(registry).run(context), registry, root / "artifacts"

    def test_fixture_case_travels_through_every_typed_stage(self):
        with TemporaryDirectory() as directory:
            result, registry, root = self._workflow(Path(directory))
            self.assertEqual(tuple(stage.name for stage in registry.stages), STAGE_ORDER)
            self.assertTrue(result.report.successful)
            self.assertEqual(tuple(record.status for record in result.report.stage_records), (StageStatus.COMPLETED,) * len(STAGE_ORDER))
            self.assertIsNotNone(result.context.chargesheet_data)
            self.assertEqual(result.context.validation_report.disposition, ValidationDisposition.DRAFT_ALLOWED)
            self.assertTrue(any(artifact.name == "chargesheet_draft" for artifact in result.context.generated_artifacts))
            self.assertTrue(all((root / artifact.storage_key).is_file() for artifact in result.context.generated_artifacts))

    def test_ocr_failure_stops_the_workflow_without_pdf(self):
        with TemporaryDirectory() as directory:
            result, _, _ = self._workflow(Path(directory), ocr=FixtureOCRClient(fail=True))
            self.assertEqual(result.context.execution_state.record_for("ocr").status, StageStatus.FAILED)
            self.assertFalse(any(artifact.media_type == "application/pdf" for artifact in result.context.generated_artifacts))

    def test_parser_failure_stops_the_workflow_without_pdf(self):
        with TemporaryDirectory() as directory:
            result, _, _ = self._workflow(Path(directory), parser=FixtureParserClient(fail=True))
            self.assertEqual(result.context.execution_state.record_for("document_parsing").status, StageStatus.FAILED)
            self.assertFalse(any(artifact.media_type == "application/pdf" for artifact in result.context.generated_artifacts))

    def test_legal_provider_failure_stops_the_workflow_without_pdf(self):
        with TemporaryDirectory() as directory:
            result, _, _ = self._workflow(Path(directory), provider=FailingLegalProvider())
            self.assertEqual(result.context.execution_state.record_for("legal_reasoning").status, StageStatus.FAILED)
            self.assertFalse(any(artifact.media_type == "application/pdf" for artifact in result.context.generated_artifacts))

    def test_final_blocked_case_writes_data_but_not_pdf(self):
        with TemporaryDirectory() as directory:
            result, _, _ = self._workflow(Path(directory), validator=FinalBlockedValidator())
            self.assertTrue(result.report.successful)
            self.assertEqual(result.context.validation_report.disposition, ValidationDisposition.FINAL_BLOCKED)
            self.assertIsNotNone(result.context.chargesheet_data)
            self.assertFalse(any(artifact.media_type == "application/pdf" for artifact in result.context.generated_artifacts))

    def test_production_cli_module_has_no_legacy_charge_sheet_imports(self):
        main_source = (Path(__file__).parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        for forbidden in ("loader", "PromptBuilder", "PDFGenerator", "get_llm_client", "FixtureLegalReferenceProvider"):
            self.assertNotIn(forbidden, main_source)


if __name__ == "__main__":
    main()
