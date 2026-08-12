from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4
from datetime import date

from src.domain.documents import ExtractionState, ProcessingCapability
from src.intake.file_validator import FileValidator
from src.intake.upload_manager import IncomingUpload, UploadManager
from src.workflow.production import create_production_registry
from src.legal.legal_rules import LegalReferenceConfigurationError
from src.extraction.ocr_client import OCRClient
from src.parsers.base_parser import ParserClient
from src.domain.documents import DocumentType
from src.domain.parsed_documents import FIR, Complaint, ParseMetadata
from src.knowledge_graph.graph_builder import GraphBuilder
from src.normalization.canonical_builder import CanonicalBuilder


class NoopOCR(OCRClient):
    def extract(self, document, source_path): raise AssertionError("not called")


class NoopParser(ParserClient):
    def generate_json(self, prompt): raise AssertionError("not called")


class ProductionHardeningTests(TestCase):
    def _pdf(self, root: Path, name: str = "fir.pdf") -> Path:
        path = root / name
        path.write_bytes(b"%PDF-1.4\nfixture")
        return path

    def test_path_traversal_filenames_are_rejected(self):
        with TemporaryDirectory() as directory:
            source = self._pdf(Path(directory))
            for name in ("../file.pdf", "..\\file.pdf", "C:\\file.pdf", "\\\\server\\file.pdf"):
                with self.assertRaises(ValueError):
                    UploadManager(Path(directory) / "storage").ingest(uuid4(), (IncomingUpload(source_path=source, original_filename=name),))

    def test_uploads_are_isolated_and_use_uuid_storage_names(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); case_id = uuid4()
            manifest = UploadManager(root / "storage").ingest(case_id, (IncomingUpload(source_path=self._pdf(root), original_filename="fir.pdf"),))
            document = manifest.accepted_documents[0]
            stored = root / "storage" / document.storage_key
            self.assertTrue(stored.is_relative_to(root / "storage" / f"CASE_{case_id.hex}"))
            self.assertNotIn("fir.pdf", document.storage_key)

    def test_file_size_and_signature_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); oversized = self._pdf(root)
            self.assertFalse(FileValidator(max_size_bytes=4).validate(oversized).is_valid)
            corrupt = root / "corrupt.pdf"; corrupt.write_bytes(b"not-a-pdf")
            self.assertFalse(FileValidator().validate(corrupt).is_valid)

    def test_case_total_limit_rejects_later_upload(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); first, second = self._pdf(root, "a.pdf"), self._pdf(root, "b.pdf")
            manifest = UploadManager(root / "storage", max_case_size_bytes=first.stat().st_size).ingest(uuid4(), (IncomingUpload(source_path=first, original_filename="a.pdf"), IncomingUpload(source_path=second, original_filename="b.pdf")))
            self.assertEqual(len(manifest.accepted_documents), 1)

    def test_media_is_preserved_but_explicitly_deferred(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); video = root / "cctv.mp4"; video.write_bytes(b"\x00\x00\x00\x18ftypisom")
            document = UploadManager(root / "storage").ingest(uuid4(), (IncomingUpload(source_path=video, original_filename="cctv.mp4"),)).accepted_documents[0]
            self.assertEqual(document.processing_capability, ProcessingCapability.MEDIA_PROCESSING_REQUIRED)
            self.assertEqual(document.extraction_state, ExtractionState.DEFERRED)

    def test_production_clients_require_gemini_configuration_when_not_injected(self):
        with TemporaryDirectory() as directory:
            dataset = Path(__file__).parents[1] / "references" / "legal" / "bns_sections.json"
            with self.assertRaises(ValueError):
                create_production_registry(Path(directory), legal_reference_path=dataset, legal_reference_version="bns-2023-2024-07-01")
            registry = create_production_registry(Path(directory), ocr_client=NoopOCR(), parser_client=NoopParser(), legal_reference_path=dataset, legal_reference_version="bns-2023-2024-07-01")
            self.assertEqual(registry.stages[1].client.__class__, NoopOCR)

    def test_fir_metadata_and_complaint_provenance_reach_canonical_graph(self):
        document_id, case_id = uuid4(), uuid4()
        metadata = ParseMetadata(parser_name="fixture", parse_duration_ms=1, retry_count=0, confidence=.8)
        fir = FIR(document_id=document_id, ocr_text_sha256="a" * 64, parse_metadata=metadata, fir_number="42/2026", crime_number="C-42", registration_date=date(2026, 1, 2), police_station="Central PS", occurrence_location="Market Road", jurisdiction="Central", court="Sessions Court", reported_sections=("115",))
        complaint = Complaint(document_id=uuid4(), ocr_text_sha256="b" * 64, parse_metadata=metadata, complainant_name="Asha Devi", complaint_text="Complaint assertion")
        canonical = CanonicalBuilder().build(GraphBuilder(case_id).build((fir, complaint)))
        self.assertEqual(canonical.case_metadata.fir_number.value, "42/2026")
        self.assertEqual(canonical.police_station.value, "Central PS")
        self.assertEqual(canonical.court.value, "Sessions Court")
        self.assertEqual(canonical.offences[0].value, "115")
        self.assertTrue(any(reference.document_id == complaint.document_id for reference in canonical.victims[0].name.references))


if __name__ == "__main__":
    main()
