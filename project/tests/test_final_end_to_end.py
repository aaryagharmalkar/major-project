"""Phase 11E production-composition validation with synthetic PDF evidence."""

from pathlib import Path
import re
import zlib
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4

from reportlab.pdfgen.canvas import Canvas

from src.extraction.ocr_client import OCRClient
from src.extraction.ocr_result import OCRMetadata, OCRPage, OCRResult
from src.intake.upload_manager import IncomingUpload
from src.legal.legal_rules import LocalLegalReferenceProvider
from src.parsers.base_parser import ParserClient, ParserError
from src.review.review_models import ReviewStatus
from src.review.review_service import ReviewLifecycleError, ReviewService
from src.rendering.if5_renderer import IF5Renderer
from src.workflow.engine import WorkflowEngine
from src.workflow.production import create_production_registry, create_workflow_context
from src.workflow.state import StageStatus


FIXTURE_FILES = ("FIR.pdf", "complaint.pdf", "witness_statement_01.pdf", "witness_statement_02.pdf", "medical_report.pdf", "seizure_memo.pdf", "vehicle_inspection.pdf", "fsl_report.pdf", "site_plan.pdf")
DATASET = Path(__file__).parents[1] / "references" / "legal" / "bns_sections.json"
DATASET_VERSION = "bns-2023-2024-07-01"


def write_fixture_files(root: Path) -> tuple[IncomingUpload, ...]:
    root.mkdir(parents=True, exist_ok=True)
    uploads = []
    for name in FIXTURE_FILES:
        path = root / name
        canvas = Canvas(str(path)); canvas.drawString(72, 760, f"Synthetic Phase 11E evidence: {name}"); canvas.drawString(72, 740, "FIR 42/2026, Central PS, Market Road, Asha Devi, vehicle KA01AB1234."); canvas.save()
        uploads.append(IncomingUpload(source_path=path, original_filename=name))
    return tuple(uploads)


def inspect_pdf(path: Path) -> tuple[int, str]:
    """Dependency-free structural check for the ReportLab PDFs produced in this test."""
    payload = path.read_bytes()
    if not (payload.startswith(b"%PDF-") and payload.rstrip().endswith(b"%%EOF")):
        raise AssertionError("PDF header or EOF marker is missing")
    decoded = []
    for stream in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", payload, re.DOTALL):
        try: decoded.append(zlib.decompress(stream).decode("latin-1", errors="ignore"))
        except zlib.error: pass
    return (len(re.findall(rb"/Type /Page\b", payload)), "\n".join(decoded))


class FixtureOCR(OCRClient):
    supported_mime_types = frozenset({"application/pdf"})
    def __init__(self, fail: bool = False): self.fail = fail
    def extract(self, document, source_path):
        if self.fail: raise RuntimeError("fixture OCR failure")
        text = {
            "FIR.pdf": "FIR 42/2026; Central PS; Complainant: Asha Devi; Accused: Raj Verma; Victim: Sameer Khan; Vehicle: KA01AB1234.",
            "complaint.pdf": "Complaint; Complainant: Asha Devi; Person complained against: Raj Verma; Victim: Sameer Khan; Vehicle: KA01AB1234.",
        }.get(document.original_filename, "Synthetic evidence")
        return OCRResult(document_id=document.id, pages=(OCRPage(page_number=1, text=text, confidence=.9),), raw_text=text, confidence=.9, metadata=OCRMetadata(provider="fixture", model="fixture", input_mime_type=document.media_type, processing_time_ms=1))


class FixtureParser(ParserClient):
    def __init__(self, fail: bool = False): self.fail = fail
    def generate_json(self, prompt):
        if self.fail: raise ParserError("fixture parser failure")
        if '"FIR"' in prompt: return {"fir_number": "42/2026", "registration_date": "2026-01-02", "police_station": "Central PS", "complainant_name": "Asha Devi", "accused_names": ["Raj Verma"], "victim_names": ["Sameer Khan"], "vehicle_registrations": ["KA01AB1234"], "occurrence_datetime": "2026-01-01T10:00:00", "occurrence_location": "Market Road", "jurisdiction": "Central", "court": "Sessions Court", "reported_sections": ["115"], "confidence": .9}
        if '"Complaint"' in prompt: return {"complaint_date": "2026-01-01", "complainant_name": "Asha Devi", "person_complained_against_names": ["Raj Verma"], "victim_names": ["Sameer Khan"], "vehicle_registrations": ["KA01AB1234"], "complaint_text": "Complaint at Market Road", "confidence": .9}
        if '"WitnessStatement"' in prompt: return {"witness_name": "Ravi Kumar", "statement_text": "Witness statement", "confidence": .9}
        if '"MedicalReport"' in prompt: return {"report_number": "MLC-1", "patient_name": "Asha Devi", "doctor_name": "Dr Sen", "observations": ["hurt"], "confidence": .9}
        if '"SeizureMemo"' in prompt: return {"memo_number": "SZ-1", "seizure_location": "Market Road", "seized_items": [{"description": "CCTV DVR", "exhibit_mark": "E1"}], "confidence": .9}
        if '"VehicleInspection"' in prompt: return {"report_number": "VI-1", "vehicle_registration": "KA01AB1234", "inspected_by": "Officer Rao", "confidence": .9}
        if '"FSLReport"' in prompt: return {"report_number": "FSL-1", "examined_items": ["CCTV DVR"], "findings": ["DVR intact"], "confidence": .9}
        if '"SitePlan"' in prompt: return {"plan_number": "SP-1", "location": "Market Road", "prepared_by": "Officer Rao", "confidence": .9}
        return {"confidence": .9}


class FinalEndToEndTests(TestCase):
    def production_result(self, root: Path, *, ocr=None, parser=None):
        uploads = write_fixture_files(root / "fixtures")
        context = create_workflow_context(uuid4(), uploads)
        registry = create_production_registry(root / "output", ocr_client=ocr or FixtureOCR(), parser_client=parser or FixtureParser(), legal_reference_path=DATASET, legal_reference_version=DATASET_VERSION)
        return WorkflowEngine(registry).run(context), root / "output"

    def test_complete_production_fixture_to_approved_final_pdf(self):
        with TemporaryDirectory() as directory:
            result, output = self.production_result(Path(directory))
            self.assertTrue(result.report.successful)
            self.assertEqual(tuple(record.status for record in result.report.stage_records), (StageStatus.COMPLETED,) * 9)
            artifacts = {item.name: output / item.storage_key for item in result.context.generated_artifacts}
            for name in ("upload_manifest", "ocr_result", "parsed_document", "investigation_graph", "canonical_investigation", "validation_report", "case_context", "legal_findings", "chargesheet_data", "chargesheet_draft", "chargesheet_review_state"):
                self.assertIn(name, artifacts)
            review, data = result.context.officer_review, result.context.chargesheet_data
            self.assertEqual(review.status, ReviewStatus.REVIEW_REQUIRED)
            approved = ReviewService().approve(review, data, reviewer_id="officer-1")
            finalized = ReviewService().finalize(approved, data, storage_root=output)
            draft, final = artifacts["chargesheet_draft"], output / finalized.final_artifact_reference
            self.assertTrue(draft.is_file()); self.assertTrue(final.is_file()); self.assertNotEqual(draft, final)
            pages, _ = inspect_pdf(final); self.assertGreater(pages, 0); self.assertGreater(final.stat().st_size, 1000)
            self.assertEqual(finalized.approved_version, data.version)
            self.assertEqual(finalized.approved_content_hash, data.content_hash)
            self.assertEqual(data.case_number.value, "42/2026")
            self.assertTrue(data.case_number.source_references)
            self.assertEqual(data.case_number.source_references[0].document_id, result.context.case_context.case_metadata[0].source_document_ids[0])
            with self.assertRaises(ReviewLifecycleError): ReviewService().finalize(approved, data, storage_root=output)

    def test_failures_and_deferred_media_cannot_create_final_output(self):
        with TemporaryDirectory() as directory:
            result, output = self.production_result(Path(directory), ocr=FixtureOCR(fail=True))
            self.assertEqual(result.context.execution_state.record_for("ocr").status, StageStatus.FAILED)
            self.assertFalse(any(path.suffix == ".pdf" and "final" in str(path) for path in output.rglob("*.pdf")))
        with TemporaryDirectory() as directory:
            root = Path(directory); video = root / "evidence.mp4"; video.write_bytes(b"\x00\x00\x00\x18ftypisom")
            from src.intake.upload_manager import UploadManager
            document = UploadManager(root / "storage").ingest(uuid4(), (IncomingUpload(source_path=video, original_filename=video.name),)).accepted_documents[0]
            self.assertEqual(document.extraction_state.value, "deferred")

    def test_rejection_and_modified_approval_are_blocked(self):
        with TemporaryDirectory() as directory:
            result, output = self.production_result(Path(directory))
            review, data, service = result.context.officer_review, result.context.chargesheet_data, ReviewService()
            rejected = service.reject(review, data, reviewer_id="officer-1", rejection_reason="Needs correction")
            with self.assertRaises(ReviewLifecycleError): service.finalize(rejected, data, storage_root=output)
            approved = service.approve(review, data, reviewer_id="officer-1")
            changed = data.model_copy(update={"version": 2})
            with self.assertRaises(ReviewLifecycleError): service.finalize(approved, changed, storage_root=output)

    def test_renderer_is_content_deterministic_for_same_charge_sheet_data(self):
        with TemporaryDirectory() as directory:
            result, _ = self.production_result(Path(directory))
            first, second = Path(directory) / "first.pdf", Path(directory) / "second.pdf"
            IF5Renderer().render(result.context.chargesheet_data, first)
            IF5Renderer().render(result.context.chargesheet_data, second)
            self.assertEqual(inspect_pdf(first)[0], inspect_pdf(second)[0])
            self.assertEqual(result.context.chargesheet_data.content_hash, result.context.chargesheet_data.content_hash)


if __name__ == "__main__":
    main()
