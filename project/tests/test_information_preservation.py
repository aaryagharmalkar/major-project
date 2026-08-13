"""Generic boundary tests for typed investigation information preservation."""

from datetime import datetime, timezone
from unittest import TestCase
from uuid import uuid4

from src.chargesheet.chargesheet_populator import ChargeSheetPopulator
from src.context.case_context_builder import CaseContextBuilder
from src.domain.common import SourceReference
from src.domain.documents import DocumentType
from src.domain.parsed_documents import FIR, CaseDiary, CaseDiaryEntry, FSLReport, MedicalReport, ParseMetadata, SeizureItem, SeizureMemo, WitnessStatement
from src.knowledge_graph.graph_builder import GraphBuilder
from src.legal.legal_findings import EvidenceMapping, EvidenceStrength, LegalFinding, LegalFindingStatus, LegalFindings
from src.normalization.canonical_builder import CanonicalBuilder
from src.normalization.canonical_models import CanonicalConflict, ConflictStatus
from src.validation.evidence_validator import EvidenceValidator


def parsed_metadata() -> ParseMetadata:
    return ParseMetadata(parser_name="synthetic_parser", parse_duration_ms=1, retry_count=0, confidence=.85)


class InformationPreservationTests(TestCase):
    def _case(self, *, complainant: str, accused: str, location: str, section: str):
        case_id, fir_id, witness_id, medical_id, seizure_id, diary_id, fsl_id = (uuid4() for _ in range(7))
        documents = (
            FIR(document_id=fir_id, ocr_text_sha256="a" * 64, parse_metadata=parsed_metadata(), fir_number=f"F-{section}", complainant_name=complainant, accused_names=(accused,), victim_names=(complainant,), occurrence_datetime=datetime(2026, 2, 3, 10, tzinfo=timezone.utc), occurrence_location=location, reported_sections=(section,), narrative_text=f"Incident recorded at {location}."),
            WitnessStatement(document_id=witness_id, ocr_text_sha256="b" * 64, parse_metadata=parsed_metadata(), witness_name=complainant, statement_text="Observed the incident."),
            MedicalReport(document_id=medical_id, ocr_text_sha256="c" * 64, parse_metadata=parsed_metadata(), patient_name=complainant, doctor_name="Dr Example", observations=("Documented injury",)),
            SeizureMemo(document_id=seizure_id, ocr_text_sha256="d" * 64, parse_metadata=parsed_metadata(), seizure_location=location, seized_items=(SeizureItem(description="Recorded item", exhibit_mark="EX-1"),), prepared_by="Officer Example"),
            CaseDiary(document_id=diary_id, ocr_text_sha256="e" * 64, parse_metadata=parsed_metadata(), officer_name="Officer Example", entries=(CaseDiaryEntry(entry_number="1", entry_datetime=datetime(2026, 2, 4, tzinfo=timezone.utc), text="Investigation action recorded."),)),
            FSLReport(document_id=fsl_id, ocr_text_sha256="f" * 64, parse_metadata=parsed_metadata(), examined_items=("Recorded item",), findings=("Forensic observation",)),
        )
        graph = GraphBuilder(case_id).build(documents)
        canonical = CanonicalBuilder().build(graph)
        competing = canonical.complainants[0].name.model_copy(update={"value": f"{complainant} variant"})
        canonical = canonical.model_copy(update={"conflicts": (CanonicalConflict(field_path="persons.name", competing_values=(canonical.complainants[0].name, competing), source_references=(SourceReference(document_id=fir_id),), status=ConflictStatus.UNRESOLVED),)})
        context = CaseContextBuilder().build(canonical, EvidenceValidator().validate(canonical))
        mapping = EvidenceMapping(source_document_id=medical_id, field_path=canonical.medical_findings[0].source_path, description=str(canonical.medical_findings[0].value), source_references=(SourceReference(document_id=medical_id),))
        findings = LegalFindings(findings=(LegalFinding(legal_reference_id=uuid4(), offence="Synthetic offence", proposed_section=section, description="Evidence requires review.", supporting_evidence=(mapping,), evidence_strength=EvidenceStrength.MEDIUM, confidence=.7, status=LegalFindingStatus.INSUFFICIENT_EVIDENCE, review_required=True, source_references=mapping.source_references),), review_required=True, validation_disposition=context.validation_disposition, retry_count=0)
        return documents, graph, canonical, context, ChargeSheetPopulator().populate(context, findings), fir_id

    def test_two_unrelated_cases_preserve_facts_roles_provenance_and_review_state(self):
        for values in (("Ira Bose", "Dev Nair", "North Crossing", "S-201"), ("Mina Das", "Kiran Paul", "Harbor Lane", "S-305")):
            with self.subTest(values=values):
                documents, graph, canonical, context, sheet, fir_id = self._case(complainant=values[0], accused=values[1], location=values[2], section=values[3])
                self.assertEqual(documents[0].complainant_name, values[0])
                person = next(node for node in graph.nodes if node.label == values[0] and node.node_type.value == "person")
                self.assertEqual({role.value for role in person.roles}, {"complainant", "victim", "witness"})
                self.assertEqual(canonical.complainants[0].name.value, values[0])
                self.assertEqual({role.value for role in canonical.complainants[0].roles}, {"complainant", "victim", "witness"})
                self.assertTrue(context.documents)
                self.assertTrue(context.investigation_actions)
                self.assertEqual(context.documents[0].attributes["fir_number"].source_document_ids, (fir_id,))
                self.assertIn("03 February 2026, 10:00", sheet.case_summary.value)
                self.assertIn(values[2], sheet.case_summary.value)
                self.assertIn(values[0], sheet.case_summary.value)
                self.assertIn(values[1], sheet.case_summary.value)
                self.assertIn("Incident recorded", sheet.detailed_facts.value)
                self.assertIn("record was examined", sheet.investigation_conducted.value)
                self.assertIn("Documentary Evidence:", sheet.evidence_analysis.value)
                self.assertTrue(sheet.annexures)
                self.assertEqual(sheet.legal_findings[0].status, "insufficient_evidence")
                self.assertTrue(sheet.legal_findings[0].review_required)
                self.assertEqual(sheet.legal_sections[0].value, values[3])
                self.assertTrue(sheet.conflicts)
                self.assertTrue(sheet.conflicts[0].source_references)
                self.assertFalse(sheet.missing_information)
