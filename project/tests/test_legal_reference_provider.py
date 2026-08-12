from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4

from src.context.case_context import CaseContext
from src.domain.common import SourceReference
from src.extraction.ocr_client import OCRClient
from src.knowledge_graph.graph_models import GraphProvenance
from src.legal.evidence_mapper import EvidenceMapper
from src.legal.legal_findings import EvidenceStrength, LegalFinding, LegalFindingStatus, LegalFindings
from src.legal.legal_reasoner import LegalReasoner, LegalReasoningClient
from src.legal.legal_rules import LegalReferenceConfigurationError, LocalLegalReferenceProvider
from src.normalization.canonical_models import CanonicalFact
from src.parsers.base_parser import ParserClient
from src.validation.validation_models import ValidationDisposition
from src.workflow.production import create_production_registry


DATASET_PATH = Path(__file__).parents[1] / "references" / "legal" / "bns_sections.json"
DATASET_VERSION = "bns-2023-2024-07-01"


def fact(value: str) -> CanonicalFact:
    document_id = uuid4()
    provenance = GraphProvenance(document_id=document_id, confidence=0.8, parser_name="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), source_reference=SourceReference(document_id=document_id))
    return CanonicalFact(value=value, source_document_ids=(document_id,), references=(provenance,), source_path="fixture.hurt", confidence=0.8, extraction_method="fixture", timestamp=provenance.timestamp)


def context(disposition: ValidationDisposition = ValidationDisposition.DRAFT_ALLOWED) -> CaseContext:
    return CaseContext(case_id=uuid4(), medical_findings=(fact("hurt"),), validation_disposition=disposition.value)


class QueueClient(LegalReasoningClient):
    def __init__(self, payloads): self.payloads = list(payloads)
    def generate_json(self, prompt): return self.payloads.pop(0)


class NoopOCRClient(OCRClient):
    def extract(self, document, source_path): raise AssertionError("not invoked during registry construction")


class NoopParserClient(ParserClient):
    def generate_json(self, prompt): raise AssertionError("not invoked during registry construction")


class LegalReferenceProviderTests(TestCase):
    def test_versioned_dataset_loads_and_looks_up_known_section(self):
        provider = LocalLegalReferenceProvider.load(DATASET_PATH, DATASET_VERSION)
        section = provider.lookup("115")
        self.assertEqual(provider.dataset.version, DATASET_VERSION)
        self.assertIsNotNone(section)
        self.assertEqual(section.offence_name, "Voluntarily causing hurt")
        self.assertEqual(section.version, DATASET_VERSION)
        self.assertEqual(section.source.publisher, "India Code")

    def test_unknown_section_lookup_returns_none(self):
        provider = LocalLegalReferenceProvider.load(DATASET_PATH, DATASET_VERSION)
        self.assertIsNone(provider.lookup("9999"))

    def test_missing_or_mismatched_configuration_fails_safely(self):
        with self.assertRaises(LegalReferenceConfigurationError):
            LocalLegalReferenceProvider.load(None, DATASET_VERSION)
        with self.assertRaises(LegalReferenceConfigurationError):
            LocalLegalReferenceProvider.load(DATASET_PATH, "wrong-version")

    def test_invalid_dataset_version_metadata_is_rejected(self):
        with TemporaryDirectory() as directory:
            payload = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
            payload["references"][0]["version"] = "different-version"
            path = Path(directory) / "invalid.json"; path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(LegalReferenceConfigurationError):
                LocalLegalReferenceProvider.load(path, DATASET_VERSION)

    def test_production_registry_loads_configured_provider_and_rejects_missing_configuration(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(LegalReferenceConfigurationError):
                create_production_registry(Path(directory))
            registry = create_production_registry(Path(directory), ocr_client=NoopOCRClient(), parser_client=NoopParserClient(), legal_reference_path=DATASET_PATH, legal_reference_version=DATASET_VERSION)
            legal_stage = next(stage for stage in registry.stages if stage.name == "legal_reasoning")
            self.assertIsInstance(legal_stage.reasoner.reference_provider, LocalLegalReferenceProvider)

    def test_configured_reference_can_produce_supported_finding_with_evidence(self):
        provider = LocalLegalReferenceProvider.load(DATASET_PATH, DATASET_VERSION)
        result = LegalReasoner(provider).reason(context())
        self.assertEqual(result.findings[0].proposed_section, "115")
        self.assertEqual(result.findings[0].status, LegalFindingStatus.SUPPORTED)
        self.assertEqual(result.findings[0].legal_reference_id, provider.lookup("115").section_id)
        self.assertTrue(result.findings[0].supporting_evidence)

    def test_llm_unknown_section_and_missing_evidence_become_review_required(self):
        provider = LocalLegalReferenceProvider.load(DATASET_PATH, DATASET_VERSION)
        mapping = EvidenceMapper().available(context())[0]
        unknown = LegalFindings(findings=(LegalFinding(legal_reference_id=uuid4(), offence="Unknown", proposed_section="9999", description="Unknown", supporting_evidence=(mapping,), evidence_strength=EvidenceStrength.LOW, confidence=.1, status=LegalFindingStatus.REVIEW_REQUIRED, review_required=True, source_references=mapping.source_references),), review_required=True, validation_disposition=ValidationDisposition.DRAFT_ALLOWED.value, retry_count=0).model_dump(mode="json")
        missing_evidence = json.loads(json.dumps(unknown)); missing_evidence["findings"][0]["legal_reference_id"] = str(provider.lookup("115").section_id); missing_evidence["findings"][0]["proposed_section"] = "115"; missing_evidence["findings"][0]["supporting_evidence"] = []
        result = LegalReasoner(provider, QueueClient([unknown, missing_evidence])).reason(context())
        self.assertFalse(result.findings)
        self.assertTrue(result.review_required)
        self.assertEqual(result.retry_count, 2)

    def test_final_blocked_never_returns_legal_findings(self):
        provider = LocalLegalReferenceProvider.load(DATASET_PATH, DATASET_VERSION)
        result = LegalReasoner(provider).reason(context(ValidationDisposition.FINAL_BLOCKED))
        self.assertFalse(result.findings)
        self.assertTrue(result.review_required)


if __name__ == "__main__":
    main()
