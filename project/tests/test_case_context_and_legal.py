from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from src.context.case_context import CaseContext
from src.context.case_context_builder import CaseContextBuilder
from src.context.context_stage import CaseContextStage
from src.domain.common import SourceReference
from src.knowledge_graph.graph_models import GraphProvenance
from src.legal.evidence_mapper import EvidenceMapper
from src.legal.legal_findings import EvidenceStrength, LegalFinding, LegalFindingStatus, LegalFindings
from src.legal.legal_reasoner import LegalReasoner, LegalReasoningClient
from src.legal.legal_rules import FixtureLegalReferenceProvider, LegalReference
from src.legal.legal_stage import LegalReasoningStage
from src.normalization.canonical_models import CanonicalCaseMetadata, CanonicalEvidence, CanonicalInvestigation, ConfidenceSummary
from src.validation.validation_models import ValidationDisposition, ValidationIssue, IssueCategory, IssueSeverity, ValidationReport
from src.workflow.context import WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import WorkflowState


def fact(value, confidence=0.8):
    from src.normalization.canonical_models import CanonicalFact
    document_id = uuid4(); provenance = GraphProvenance(document_id=document_id, confidence=confidence, parser_name="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), source_reference=SourceReference(document_id=document_id))
    return CanonicalFact(value=value, source_document_ids=(document_id,), references=(provenance,), source_path="fixture.path", confidence=confidence, extraction_method="fixture", timestamp=provenance.timestamp)


def report(disposition=ValidationDisposition.DRAFT_ALLOWED, issues=()):
    return ValidationReport(errors=tuple(issue for issue in issues if issue.severity in {IssueSeverity.ERROR, IssueSeverity.CRITICAL}), warnings=tuple(issue for issue in issues if issue.severity == IssueSeverity.WARNING), completeness_score=1, critical_failure=disposition == ValidationDisposition.FINAL_BLOCKED, review_required=disposition != ValidationDisposition.DRAFT_ALLOWED, disposition=disposition)


def canonical():
    case_id = uuid4(); evidence = CanonicalEvidence(evidence_id=uuid4(), type="evidence", description=fact("CCTV recording"), source_documents=(), confidence=.8)
    return CanonicalInvestigation(case_metadata=CanonicalCaseMetadata(case_id=case_id, fir_number=fact("42/2026")), police_station=fact("Central PS"), evidence=(evidence,), medical_findings=(fact("injury"),), confidence_summary=ConfidenceSummary(average=.8, fact_count=3))


def reference():
    from datetime import date
    from src.legal.legal_rules import LegalJurisdiction, LegalReferenceSource
    return LegalReference(section_id=uuid4(), section_number="S-1", offence_name="Fixture offence", description="Fixture legal reference", required_elements=("injury",), jurisdiction=LegalJurisdiction.INDIA, effective_from=date(2024, 7, 1), source=LegalReferenceSource(publisher="Fixture", citation="Fixture reference", uri="https://example.test/reference"), version="fixture-v1", source_reference=SourceReference(document_id=uuid4()))


class QueueClient(LegalReasoningClient):
    def __init__(self, responses): self.responses = list(responses)
    def generate_json(self, prompt):
        response = self.responses.pop(0)
        if isinstance(response, Exception): raise response
        return response


class CaseContextAndLegalTests(unittest.TestCase):
    def test_case_context_generation_and_filtering(self):
        context = CaseContextBuilder().build(canonical(), report())
        self.assertEqual(context.police_station.value, "Central PS")
        self.assertEqual(context.documents, canonical().documents)

    def test_context_preserves_provenance_and_validation_issues(self):
        issue = ValidationIssue(category=IssueCategory.COMPLETENESS, severity=IssueSeverity.WARNING, description="Missing", field_path="fir")
        context = CaseContextBuilder().build(canonical(), report(issues=(issue,)))
        self.assertEqual(context.medical_findings[0].references[0].parser_name, "fixture")
        self.assertEqual(context.validation_issues[0].issue_id, issue.issue_id)

    def test_empty_context_retains_missing_information(self):
        source = canonical().model_copy(update={"medical_findings": (), "evidence": ()})
        context = CaseContextBuilder().build(source, report())
        self.assertFalse(context.evidence)

    def test_legal_finding_schema_and_evidence_mapping(self):
        context = CaseContextBuilder().build(canonical(), report())
        mappings = EvidenceMapper().available(context)
        findings = LegalReasoner(FixtureLegalReferenceProvider((reference(),))).reason(context)
        self.assertTrue(mappings)
        self.assertIsInstance(findings.findings[0], LegalFinding)
        self.assertEqual(findings.findings[0].status, LegalFindingStatus.SUPPORTED)

    def test_insufficient_evidence_and_missing_legal_reference(self):
        context = CaseContextBuilder().build(canonical(), report())
        insufficient_ref = reference().model_copy(update={"required_elements": ("missing element",)})
        finding = LegalReasoner(FixtureLegalReferenceProvider((insufficient_ref,))).reason(context).findings[0]
        self.assertEqual(finding.status, LegalFindingStatus.INSUFFICIENT_EVIDENCE)
        empty = LegalReasoner(FixtureLegalReferenceProvider()).reason(context)
        self.assertFalse(empty.findings)
        self.assertTrue(empty.review_required)

    def test_conflicted_evidence_requires_review(self):
        issue = ValidationIssue(category=IssueCategory.CONFLICT, severity=IssueSeverity.ERROR, description="Conflict", field_path="evidence")
        validation = report(ValidationDisposition.REVIEW_REQUIRED, (issue,)).model_copy(update={"conflicts": (issue,)})
        context = CaseContextBuilder().build(canonical(), validation)
        finding = LegalReasoner(FixtureLegalReferenceProvider((reference(),))).reason(context).findings[0]
        self.assertEqual(finding.status, LegalFindingStatus.CONFLICTED)

    def test_mocked_llm_output_and_invalid_retry(self):
        context = CaseContextBuilder().build(canonical(), report())
        mapping = EvidenceMapper().available(context)[0]
        legal_reference = reference()
        valid = LegalFindings(findings=(LegalFinding(legal_reference_id=legal_reference.section_id, offence="Fixture offence", proposed_section="S-1", description="Mock", supporting_evidence=(mapping,), evidence_strength=EvidenceStrength.MEDIUM, confidence=.7, status=LegalFindingStatus.SUPPORTED, review_required=False, source_references=mapping.source_references),), review_required=False, validation_disposition=context.validation_disposition, retry_count=0).model_dump(mode="json")
        forged = json.loads(json.dumps(valid))
        forged["findings"][0]["supporting_evidence"][0]["source_document_id"] = str(uuid4())
        result = LegalReasoner(FixtureLegalReferenceProvider((legal_reference,)), QueueClient([forged, valid])).reason(context)
        self.assertEqual(result.retry_count, 1)

    def test_final_blocked_and_review_required_behavior(self):
        blocked = CaseContextBuilder().build(canonical(), report(ValidationDisposition.FINAL_BLOCKED))
        result = LegalReasoner(FixtureLegalReferenceProvider((reference(),))).reason(blocked)
        self.assertFalse(result.findings)
        reviewed = CaseContextBuilder().build(canonical(), report(ValidationDisposition.REVIEW_REQUIRED))
        self.assertTrue(LegalReasoner(FixtureLegalReferenceProvider((reference(),))).reason(reviewed).review_required)

    def test_workflow_integration_and_artifacts(self):
        source = canonical(); validation = report(); workflow = WorkflowContext(case_id=source.case_metadata.case_id, canonical_investigation=source, validation_report=validation, execution_state=WorkflowState(case_id=source.case_metadata.case_id))
        with TemporaryDirectory() as temp_dir:
            context_run = WorkflowEngine(StageRegistry([CaseContextStage(Path(temp_dir))])).run(workflow)
            legal_run = WorkflowEngine(StageRegistry([LegalReasoningStage(Path(temp_dir), LegalReasoner(FixtureLegalReferenceProvider((reference(),))))])).run(context_run.context)
            paths = [Path(temp_dir) / artifact.storage_key for artifact in legal_run.context.generated_artifacts]
            self.assertTrue(legal_run.report.successful)
            self.assertIsNotNone(legal_run.context.legal_findings)
            self.assertTrue(any(path.name == "case_context.json" for path in paths))
            self.assertTrue(any(path.name == "legal_findings.json" for path in paths))
            self.assertTrue(any(path.name == "evidence_mapping.json" for path in paths))


if __name__ == "__main__": unittest.main()
