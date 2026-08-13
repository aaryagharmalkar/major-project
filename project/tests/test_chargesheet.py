from datetime import date, datetime, timezone
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4

from src.chargesheet.chargesheet_populator import ChargeSheetPopulator
from src.chargesheet.chargesheet_stage import ChargeSheetStage
from src.chargesheet.form_if5_schema import ChargeSheetField, ChargeSheetLegalFinding, FieldStatus, IF5Row
from src.chargesheet.presentation import document_action_statement, format_value, unique_lines
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
    def test_populator_preserves_sources_and_projects_available_summary(self):
        data = ChargeSheetPopulator().populate(context(), findings())
        self.assertEqual(data.case_number.value, "42/2026")
        self.assertTrue(data.case_number.source_references)
        self.assertEqual(data.case_summary.status, FieldStatus.POPULATED)
        self.assertIn("Recorded victim", data.case_summary.value)
        self.assertEqual(data.legal_sections[0].value, "S-1")

    def test_generic_value_formatter_handles_nested_values_without_python_repr(self):
        value = {
            "description": "Vehicle seized: ZX-92",
            "exhibit_mark": None,
            "metadata": {"ignored": "detail"},
        }
        self.assertIn("Description: Vehicle seized: ZX-92", format_value(value))
        self.assertIn("Exhibit mark: Not Available", format_value(value))
        self.assertEqual(format_value(datetime(2027, 3, 4, 9, 5)), "04 March 2027, 09:05")
        self.assertEqual(format_value(date(2027, 3, 4)), "04 March 2027")
        nested = format_value(("first", {"item": ["second", None]}, None))
        self.assertIn("- first", nested)
        self.assertIn("Item:", nested)
        self.assertIn("Not Available", nested)
        self.assertEqual(format_value(None), "Not Available")
        self.assertNotIn("{'", format_value({"item": ["first", "second"]}))

    def test_formatter_handles_realistic_nested_document_attributes_after_json_reload(self):
        value = ({"description": "Seized object", "exhibit_mark": None}, {"observations": ("lane marking", ["impact point", None])})
        rendered = format_value(value)
        self.assertIn("Description: Seized object", rendered)
        self.assertIn("Exhibit mark: Not Available", rendered)
        self.assertIn("Observations:", rendered)
        self.assertIn("- lane marking", rendered)
        self.assertIn("- impact point", rendered)
        self.assertEqual(format_value("2028-09-10T00:00:00+00:00"), "10 September 2028")
        self.assertEqual(format_value("2028-09-10T15:45:00+00:00"), "10 September 2028, 15:45")

    def test_generic_activity_and_evidence_projection_is_grouped_and_distinct(self):
        case_context = context()
        data = ChargeSheetPopulator().populate(case_context, findings())
        self.assertEqual(data.investigation_conducted.status, FieldStatus.UNAVAILABLE)
        self.assertIn("Documentary Evidence:", data.evidence_analysis.value)
        self.assertNotIn("CCTV recording", data.case_summary.value)
        self.assertEqual(unique_lines(["same", "same\nnext"]), "same\nnext")
        self.assertEqual(document_action_statement("field_note", {"observed_at": "Bridge"}), "The field note record was examined: Observed at: Bridge.")
        self.assertNotIn("Narrative text", document_action_statement("fir", {"narrative_text": "Incident facts", "fir_number": "X-1"}))

    def test_schema_rejects_populated_value_without_provenance(self):
        with self.assertRaises(ValueError):
            ChargeSheetField(value="unsupported", status=FieldStatus.POPULATED)

    def test_insufficient_legal_finding_is_retained_as_review_required(self):
        data = ChargeSheetPopulator().populate(context(), findings(status=LegalFindingStatus.INSUFFICIENT_EVIDENCE))
        self.assertEqual(data.legal_sections[0].status, FieldStatus.REVIEW_REQUIRED)
        self.assertEqual(data.legal_sections[0].value, "S-1")
        self.assertEqual(data.legal_findings[0].status, LegalFindingStatus.INSUFFICIENT_EVIDENCE)
        self.assertTrue(data.legal_findings[0].review_required)

    def test_renderer_creates_a_readable_pdf(self):
        data = ChargeSheetPopulator().populate(context(), findings())
        with TemporaryDirectory() as directory:
            output = IF5Renderer().render(data, Path(directory) / "charge_sheet.pdf")
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)

    def test_renderer_paginates_oversized_legal_finding_without_truncation(self):
        data = ChargeSheetPopulator().populate(context(), findings())
        source = SourceReference(document_id=uuid4())
        evidence = tuple(
            ChargeSheetField(
                value=f"Synthetic supporting evidence {index}: " + "documented detail " * 18,
                status=FieldStatus.REVIEW_REQUIRED,
                source_references=(source,),
                review_required=True,
            )
            for index in range(93)
        )
        finding = ChargeSheetLegalFinding(
            offence=ChargeSheetField(value="Synthetic offence", status=FieldStatus.REVIEW_REQUIRED, confidence=.8, source_references=(source,), review_required=True),
            proposed_section=ChargeSheetField(value="S-oversized", status=FieldStatus.REVIEW_REQUIRED, confidence=.8, source_references=(source,), review_required=True),
            description=ChargeSheetField(value="Synthetic legal description", status=FieldStatus.REVIEW_REQUIRED, confidence=.8, source_references=(source,), review_required=True),
            status="insufficient_evidence", evidence_strength="high", review_required=True,
            supporting_evidence=evidence,
        )
        data = data.model_copy(update={"legal_findings": (finding,)})
        with TemporaryDirectory() as directory:
            output = IF5Renderer().render(data, Path(directory) / "oversized_legal.pdf")
            payload = output.read_bytes()
            self.assertGreater(len(re.findall(rb"/Type /Page\b", payload)), 2)
            self.assertGreater(output.stat().st_size, 1000)

    def test_renderer_paginates_combined_long_content_and_structured_rows(self):
        data = ChargeSheetPopulator().populate(context(), findings())
        source = SourceReference(document_id=uuid4())
        long_field = lambda prefix: ChargeSheetField(value=f"{prefix}: " + "preserved detail " * 100, status=FieldStatus.REVIEW_REQUIRED, source_references=(source,), review_required=True)
        rows = tuple(IF5Row(serial=index, description=long_field(f"Synthetic annexure {index}"), exhibit=long_field(f"Synthetic exhibit {index}")) for index in range(1, 25))
        activities = "\n".join(f"Synthetic investigation activity {index}: " + "recorded action " * 30 for index in range(1, 45))
        evidence_analysis = "\n".join(["Documentary Evidence:", *[f"- Synthetic evidence {index}: " + "source detail " * 12 for index in range(1, 70)]])
        data = data.model_copy(update={
            "case_summary": long_field("Synthetic case summary"),
            "detailed_facts": long_field("Synthetic detailed facts"),
            "investigation_conducted": long_field("Synthetic investigation heading").model_copy(update={"value": activities}),
            "evidence_analysis": long_field("Synthetic evidence heading").model_copy(update={"value": evidence_analysis}),
            "annexures": rows,
            "timeline": rows,
        })
        with TemporaryDirectory() as directory:
            output = IF5Renderer().render(data, Path(directory) / "oversized_combination.pdf")
            payload = output.read_bytes()
            self.assertGreater(len(re.findall(rb"/Type /Page\b", payload)), 5)
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
