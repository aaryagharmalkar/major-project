from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4

from src.chargesheet.chargesheet_populator import ChargeSheetPopulator
from src.chargesheet.chargesheet_stage import ChargeSheetStage
from src.chargesheet.form_if5_schema import ChargeSheetField, FieldStatus
from src.context.case_context import CaseContext
from src.domain.common import SourceReference
from src.knowledge_graph.graph_models import GraphProvenance
from src.legal.legal_findings import EvidenceMapping, EvidenceStrength, LegalFinding, LegalFindingStatus, LegalFindings
from src.normalization.canonical_models import CanonicalEvidence, CanonicalFact, CanonicalPerson
from src.rendering.if5_renderer import IF5Renderer
from src.review.review_models import ReviewStatus
from src.workflow.context import WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import StageStatus, WorkflowState


def fact(value: str) -> CanonicalFact:
    document_id = uuid4()
    provenance = GraphProvenance(document_id=document_id, confidence=0.8, parser_name="fixture", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), source_reference=SourceReference(document_id=document_id))
    return CanonicalFact(value=value, source_document_ids=(document_id,), references=(provenance,), source_path="fixture.path", confidence=0.8, extraction_method="fixture", timestamp=provenance.timestamp)


def context(disposition="draft_allowed") -> CaseContext:
    case_id = uuid4(); victim_fact = fact("Asha Devi"); evidence_fact = fact("CCTV recording")
    return CaseContext(case_id=case_id, case_metadata=(fact("42/2026"),), police_station=fact("Central PS"), court=fact("Sessions Court"), victims=(CanonicalPerson(id=uuid4(), name=victim_fact),), evidence=(CanonicalEvidence(evidence_id=uuid4(), type="digital", description=evidence_fact, source_documents=(evidence_fact.source_document_ids[0],), confidence=0.8),), medical_findings=(fact("Documented injury"),), validation_disposition=disposition)


def findings(disposition="draft_allowed", status=LegalFindingStatus.SUPPORTED) -> LegalFindings:
    reference = SourceReference(document_id=uuid4())
    mapping = EvidenceMapping(source_document_id=reference.document_id, field_path="evidence[0]", description="CCTV recording", source_references=(reference,))
    return LegalFindings(findings=(LegalFinding(legal_reference_id=uuid4(), offence="Fixture offence", proposed_section="S-1", description="Fixture", supporting_evidence=(mapping,), evidence_strength=EvidenceStrength.HIGH, confidence=0.8, status=status, review_required=False, source_references=(reference,)),), review_required=False, validation_disposition=disposition, retry_count=0)


class ChargeSheetTests(TestCase):
    def test_populator_preserves_sources_and_leaves_unsupported_narrative_unavailable(self):
        data = ChargeSheetPopulator().populate(context(), findings())
        self.assertEqual(data.case_number.value, "42/2026")
        self.assertTrue(data.case_number.source_references)
        self.assertEqual(data.case_summary.status, FieldStatus.UNAVAILABLE)
        self.assertEqual(data.legal_sections[0].value, "S-1")

    def test_schema_rejects_populated_value_without_provenance(self):
        with self.assertRaises(ValueError):
            ChargeSheetField(value="unsupported", status=FieldStatus.POPULATED)

    def test_unsupported_legal_finding_is_not_rendered_as_a_section(self):
        data = ChargeSheetPopulator().populate(context(), findings(status=LegalFindingStatus.INSUFFICIENT_EVIDENCE))
        self.assertEqual(data.legal_sections[0].status, FieldStatus.UNAVAILABLE)
        self.assertIsNone(data.legal_sections[0].value)

    def test_renderer_creates_a_readable_pdf(self):
        data = ChargeSheetPopulator().populate(context(), findings())
        with TemporaryDirectory() as directory:
            output = IF5Renderer().render(data, Path(directory) / "charge_sheet.pdf")
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)

    def test_workflow_writes_data_and_pdf_artifacts(self):
        case_context = context(); workflow = WorkflowContext(case_id=case_context.case_id, case_context=case_context, legal_findings=findings(), execution_state=WorkflowState(case_id=case_context.case_id))
        with TemporaryDirectory() as directory:
            result = WorkflowEngine(StageRegistry([ChargeSheetStage(Path(directory))])).run(workflow)
            self.assertEqual(result.context.execution_state.record_for("chargesheet_population").status, StageStatus.COMPLETED)
            self.assertIsNotNone(result.context.chargesheet_data)
            self.assertIsNotNone(result.context.officer_review)
            self.assertEqual(result.context.officer_review.status, ReviewStatus.REVIEW_REQUIRED)
            self.assertEqual({item.name for item in result.context.generated_artifacts}, {"chargesheet_data", "chargesheet_draft", "chargesheet_review_state"})
            for artifact in result.context.generated_artifacts:
                self.assertTrue((Path(directory) / artifact.storage_key).is_file())

    def test_final_blocked_writes_json_but_not_pdf(self):
        case_context = context("final_blocked"); workflow = WorkflowContext(case_id=case_context.case_id, case_context=case_context, legal_findings=findings("final_blocked"), execution_state=WorkflowState(case_id=case_context.case_id))
        with TemporaryDirectory() as directory:
            result = WorkflowEngine(StageRegistry([ChargeSheetStage(Path(directory))])).run(workflow)
            self.assertTrue(result.report.successful)
            self.assertEqual([item.name for item in result.context.generated_artifacts], ["chargesheet_data"])


if __name__ == "__main__":
    main()
