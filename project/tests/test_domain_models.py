from datetime import datetime
import unittest
from uuid import uuid4

from pydantic import ValidationError

from src.domain.common import ConfidenceLevel, SourceReference
from src.domain.documents import DocumentType, SourceDocument
from src.domain.investigation import CanonicalInvestigation, CaseMetadata


class DomainModelTests(unittest.TestCase):
    def test_source_document_rejects_non_hash_value(self) -> None:
        with self.assertRaises(ValidationError):
            SourceDocument(
                case_id=uuid4(),
                original_filename="fir.pdf",
                storage_key="cases/1/fir.pdf",
                media_type="application/pdf",
                sha256="not-a-sha256",
                size_bytes=1,
                uploaded_at=datetime.now(),
            )


    def test_source_document_rejects_paths_in_original_filename(self) -> None:
        with self.assertRaises(ValidationError):
            SourceDocument(
                case_id=uuid4(),
                original_filename="../fir.pdf",
                storage_key="cases/1/fir.pdf",
                media_type="application/pdf",
                sha256="a" * 64,
                size_bytes=1,
                uploaded_at=datetime.now(),
            )


    def test_canonical_investigation_is_immutable(self) -> None:
        case_id = uuid4()
        investigation = CanonicalInvestigation(
            case_metadata=CaseMetadata(case_id=case_id, fir_number="452/2024"),
            source_document_ids=(),
        )

        self.assertEqual(investigation.case_metadata.fir_number, "452/2024")
        with self.assertRaises(ValidationError):
            investigation.legal_sections = ("Section 281 BNS",)


    def test_source_reference_preserves_confidence(self) -> None:
        reference = SourceReference(document_id=uuid4(), confidence=ConfidenceLevel.HIGH)

        self.assertIs(reference.confidence, ConfidenceLevel.HIGH)
