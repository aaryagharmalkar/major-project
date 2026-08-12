from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from src.domain.common import SourceReference
from src.knowledge_graph.graph_models import GraphProvenance, PersonRole
from src.normalization.canonical_models import (CanonicalCaseMetadata, CanonicalConflict, CanonicalDocument, CanonicalEvidence, CanonicalInvestigation, CanonicalPerson, CanonicalTimelineEvent, ConfidenceSummary)
from src.validation.evidence_validator import EvidenceValidator
from src.validation.validation_models import ValidationDisposition, ValidationRules
from src.validation.validation_stage import EvidenceValidationStage
from src.workflow.context import WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import WorkflowState


def fact(value, confidence=0.8):
    doc_id = uuid4()
    provenance = GraphProvenance(document_id=doc_id, confidence=confidence, parser_name="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), source_reference=SourceReference(document_id=doc_id))
    from src.normalization.canonical_models import CanonicalFact
    return CanonicalFact(value=value, source_document_ids=(doc_id,), references=(provenance,), source_path="fixture.path", confidence=confidence, extraction_method="fixture", timestamp=provenance.timestamp)


def investigation(**updates):
    canonical = CanonicalInvestigation(
        case_metadata=CanonicalCaseMetadata(case_id=uuid4(), fir_number=fact("42/2026")), police_station=fact("Central PS"),
        timeline=(CanonicalTimelineEvent(event_id=uuid4(), timestamp=fact(datetime(2026, 1, 2, tzinfo=timezone.utc)), description=fact("Incident occurrence")),),
        documents=(CanonicalDocument(id=uuid4(), document_id=fact(str(uuid4())), document_type=fact("fir")),),
        confidence_summary=ConfidenceSummary(average=0.8, fact_count=4),
    )
    return canonical.model_copy(update=updates)


class EvidenceValidationTests(unittest.TestCase):
    def test_complete_valid_case(self):
        report = EvidenceValidator(ValidationRules(require_fir_number=True, require_police_station=True, require_occurrence_details=True)).validate(investigation())
        self.assertEqual(report.disposition, ValidationDisposition.DRAFT_ALLOWED)
        self.assertEqual(report.completeness_score, 1)

    def test_missing_fir_data(self):
        report = EvidenceValidator(ValidationRules(require_fir_number=True)).validate(investigation(case_metadata=CanonicalCaseMetadata(case_id=uuid4())))
        self.assertTrue(report.missing_information)
        self.assertEqual(report.disposition, ValidationDisposition.REVIEW_REQUIRED)

    def test_missing_expected_medical_evidence(self):
        report = EvidenceValidator().validate(investigation(medical_findings=(fact("Abrasion"),)))
        self.assertEqual(len(report.missing_documents), 1)
        self.assertEqual(report.disposition, ValidationDisposition.DRAFT_ALLOWED)

    def test_conflicting_names(self):
        conflict = CanonicalConflict(field_path="persons.name", competing_values=(fact("Rahul"), fact("Rohan")), source_references=(SourceReference(document_id=uuid4()),))
        report = EvidenceValidator().validate(investigation(conflicts=(conflict,)))
        self.assertEqual(report.conflicts[0].field_path, "persons.name")

    def test_conflicting_dates(self):
        conflict = CanonicalConflict(field_path="timeline.timestamp", competing_values=(fact("2026-01-01"), fact("2026-01-02")), source_references=(SourceReference(document_id=uuid4()),))
        report = EvidenceValidator().validate(investigation(conflicts=(conflict,)))
        self.assertEqual(report.conflicts[0].status.value, "review_required")

    def test_impossible_chronology(self):
        events = (
            CanonicalTimelineEvent(event_id=uuid4(), timestamp=fact(datetime(2026, 1, 2, tzinfo=timezone.utc)), description=fact("Incident occurrence")),
            CanonicalTimelineEvent(event_id=uuid4(), timestamp=fact(datetime(2026, 1, 1, tzinfo=timezone.utc)), description=fact("Arrest memo")),
        )
        report = EvidenceValidator().validate(investigation(timeline=events))
        self.assertEqual(len(report.timeline_issues), 1)

    def test_missing_provenance_is_unsupported(self):
        invalid = fact("Unsupported")
        invalid = invalid.model_construct(value="Unsupported", source_document_ids=(), references=(), source_path="unsupported", confidence=0.8, extraction_method="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
        report = EvidenceValidator().validate(investigation(medical_findings=(invalid,)))
        self.assertEqual(len(report.unsupported_facts), 1)

    def test_unsupported_fact_blocks_final(self):
        invalid = fact("Unsupported").model_construct(value="Unsupported", source_document_ids=(), references=(), source_path="unsupported", confidence=0.8, extraction_method="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
        report = EvidenceValidator().validate(investigation(medical_findings=(invalid,)))
        self.assertEqual(report.disposition, ValidationDisposition.FINAL_BLOCKED)

    def test_low_confidence_evidence(self):
        evidence = CanonicalEvidence(evidence_id=uuid4(), type="evidence", description=fact("Knife", 0.1), source_documents=(uuid4(),), confidence=0.1)
        report = EvidenceValidator(ValidationRules(low_confidence_threshold=0.4)).validate(investigation(evidence=(evidence,)))
        self.assertTrue(report.low_confidence_facts)

    def test_unresolved_entity(self):
        person = CanonicalPerson(id=uuid4(), name=fact("Unknown"), roles=frozenset({PersonRole.WITNESS}))
        report = EvidenceValidator().validate(investigation(witnesses=(person,)))
        self.assertEqual(len(report.unresolved_entities), 1)

    def test_draft_allowed_with_warnings(self):
        report = EvidenceValidator().validate(investigation(medical_findings=(fact("Abrasion"),)))
        self.assertFalse(report.critical_failure)
        self.assertEqual(report.disposition, ValidationDisposition.DRAFT_ALLOWED)

    def test_final_blocked_with_critical_error(self):
        invalid = fact("Unsupported").model_construct(value="Unsupported", source_document_ids=(), references=(), source_path="unsupported", confidence=0.8, extraction_method="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
        report = EvidenceValidator().validate(investigation(forensic_findings=(invalid,)))
        self.assertTrue(report.critical_failure)

    def test_workflow_integration(self):
        canonical = investigation()
        context = WorkflowContext(case_id=canonical.case_metadata.case_id, canonical_investigation=canonical, execution_state=WorkflowState(case_id=canonical.case_metadata.case_id))
        with TemporaryDirectory() as temp_dir:
            result = WorkflowEngine(StageRegistry([EvidenceValidationStage(Path(temp_dir))])).run(context)
        self.assertTrue(result.report.successful)
        self.assertIsNotNone(result.context.validation_report)

    def test_artifact_generation(self):
        canonical = investigation()
        context = WorkflowContext(case_id=canonical.case_metadata.case_id, canonical_investigation=canonical, execution_state=WorkflowState(case_id=canonical.case_metadata.case_id))
        with TemporaryDirectory() as temp_dir:
            result = WorkflowEngine(StageRegistry([EvidenceValidationStage(Path(temp_dir))])).run(context)
            paths = [Path(temp_dir) / artifact.storage_key for artifact in result.context.generated_artifacts]
            self.assertEqual(len(paths), 3)
            self.assertTrue(all(path.is_file() for path in paths))
            self.assertIn("disposition", json.loads(next(path for path in paths if path.name == "validation_report.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
