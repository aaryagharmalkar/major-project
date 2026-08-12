import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
import zipfile

from src.domain.documents import DocumentType, ValidationStatus
from src.intake.checksum import calculate_sha256
from src.intake.document_classifier import DeterministicDocumentClassifier
from src.intake.file_validator import FileValidator
from src.intake.storage_layout import CaseStorageLayout
from src.intake.upload_manager import IncomingUpload, UploadManager
from src.intake.upload_manifest import UploadEntryStatus
from src.intake.document_intake_stage import DocumentIntakeStage
from src.workflow.context import ContextItem, WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import WorkflowState


def write_pdf(path: Path, content: bytes = b"%PDF-1.4\nminimal evidence\n") -> None:
    path.write_bytes(content)


class DocumentIntakeTests(unittest.TestCase):
    def test_checksum_generation_is_sha256(self) -> None:
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "fir.pdf"
            content = b"%PDF-1.4\nFIR"
            file_path.write_bytes(content)

            self.assertEqual(calculate_sha256(file_path), hashlib.sha256(content).hexdigest())

    def test_classifier_uses_deterministic_filename_rules(self) -> None:
        result = DeterministicDocumentClassifier().classify("FIR_452_2024.pdf", "application/pdf")

        self.assertEqual(result.document_type, DocumentType.FIR)
        self.assertIn("deterministic", result.reason.lower())

    def test_validator_supports_each_declared_file_type(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            samples = {
                "file.pdf": b"%PDF-1.4\n",
                "file.jpg": b"\xff\xd8\xff\xe0jpeg",
                "file.jpeg": b"\xff\xd8\xff\xe0jpeg",
                "file.png": b"\x89PNG\r\n\x1a\ncontent",
                "file.mp4": b"\x00\x00\x00\x18ftypisommore",
                "file.mov": b"\x00\x00\x00\x18ftypqt  more",
                "file.wav": b"RIFF\x00\x00\x00\x00WAVEfmt ",
            }
            for filename, content in samples.items():
                (root / filename).write_bytes(content)
            with zipfile.ZipFile(root / "file.docx", "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types />")
                archive.writestr("word/document.xml", "<w:document />")

            validator = FileValidator()
            for path in root.iterdir():
                with self.subTest(path=path.name):
                    self.assertTrue(validator.validate(path).is_valid)

    def test_invalid_extension_is_rejected_and_not_stored(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "notes.exe"
            source.write_bytes(b"not an executable")
            manager = UploadManager(root / "uploads")
            manifest = manager.ingest(uuid4(), (IncomingUpload(source_path=source, original_filename=source.name),))

            entry = manifest.entries[0]
            self.assertEqual(entry.status, UploadEntryStatus.REJECTED)
            self.assertEqual(entry.source_document.validation_status, ValidationStatus.INVALID)
            self.assertIsNone(entry.source_document.stored_filename)

    def test_duplicate_upload_is_recorded_once_without_second_copy(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "fir.pdf"
            write_pdf(source)
            manager = UploadManager(root / "uploads")
            case_id = uuid4()
            upload = IncomingUpload(source_path=source, original_filename="fir.pdf")

            manifest = manager.ingest(case_id, (upload, upload))

            self.assertEqual([entry.status for entry in manifest.entries], [UploadEntryStatus.ACCEPTED, UploadEntryStatus.DUPLICATE])
            self.assertEqual(len(list(CaseStorageLayout(root / "uploads", case_id).originals_directory.iterdir())), 1)

    def test_manifest_and_storage_layout_are_created(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "medical_report.pdf"
            write_pdf(source)
            case_id = uuid4()
            manager = UploadManager(root / "uploads")
            manifest = manager.ingest(case_id, (IncomingUpload(source_path=source, original_filename=source.name),))
            manifest_path = manager.write_manifest(manifest)
            layout = CaseStorageLayout(root / "uploads", case_id)

            self.assertTrue(layout.originals_directory.is_dir())
            self.assertTrue(layout.processed_directory.is_dir())
            self.assertTrue(layout.thumbnails_directory.is_dir())
            self.assertTrue(manifest_path.is_file())
            self.assertEqual(manifest.accepted_documents[0].detected_type, DocumentType.MEDICAL_REPORT)

    def test_document_intake_stage_integrates_with_workflow_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "complaint.pdf"
            write_pdf(source)
            case_id = uuid4()
            context = WorkflowContext(
                case_id=case_id,
                pending_uploads=(ContextItem(key="complaint", value=IncomingUpload(source_path=source, original_filename=source.name)),),
                execution_state=WorkflowState(case_id=case_id),
            )
            stage = DocumentIntakeStage(root / "uploads")
            result = WorkflowEngine(StageRegistry([stage])).run(context)

            self.assertTrue(result.report.successful)
            self.assertEqual(len(result.context.uploaded_documents), 1)
            self.assertEqual(result.context.pending_uploads, ())
            self.assertEqual(result.context.stage_metrics[-1].value["accepted"], 1)
            self.assertEqual(result.context.generated_artifacts[-1].name, "upload_manifest")


if __name__ == "__main__":
    unittest.main()
