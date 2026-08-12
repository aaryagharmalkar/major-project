from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from src.domain.common import SourceReference
from src.domain.parsed_documents import ParseMetadata, SeizureItem, SeizureMemo, VehicleInspection
from src.knowledge_graph.graph_builder import GraphBuilder
from src.knowledge_graph.graph_models import GraphEdge, GraphNode, GraphNodeType, GraphProvenance, GraphRelationshipType, InvestigationKnowledgeGraph, PersonRole
from src.normalization.canonical_builder import CanonicalBuilder
from src.normalization.canonical_models import ConflictStatus
from src.normalization.canonical_stage import CanonicalInvestigationStage
from src.workflow.context import ContextItem, WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import WorkflowState


def meta():
    return ParseMetadata(parser_name="fixture_parser", parse_duration_ms=1, retry_count=0, confidence=0.75)


def provenance(document_id=None):
    document_id = document_id or uuid4()
    return GraphProvenance(document_id=document_id, confidence=0.8, parser_name="fixture_parser", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), source_reference=SourceReference(document_id=document_id))


class CanonicalInvestigationTests(unittest.TestCase):
    def _graph(self):
        document = SeizureMemo(document_id=uuid4(), ocr_text_sha256="a" * 64, parse_metadata=meta(), seizure_location="Market Road", prepared_by="Officer Kumar", seized_items=(SeizureItem(description="Mobile phone", exhibit_mark="E-1"),))
        vehicle = VehicleInspection(document_id=uuid4(), ocr_text_sha256="b" * 64, parse_metadata=meta(), vehicle_registration="WB 12 AB 1234", inspected_by="Officer Kumar")
        return GraphBuilder(uuid4()).build((document, vehicle))

    def test_graph_to_canonical_projection(self):
        canonical = CanonicalBuilder().build(self._graph())
        self.assertEqual(len(canonical.documents), 2)
        self.assertEqual(len(canonical.recovered_property), 1)

    def test_person_projection(self):
        canonical = CanonicalBuilder().build(self._graph())
        self.assertEqual(canonical.police_officers[0].name.value, "Officer Kumar")
        self.assertIn(PersonRole.POLICE_OFFICER, canonical.police_officers[0].roles)

    def test_vehicle_projection(self):
        canonical = CanonicalBuilder().build(self._graph())
        self.assertEqual(canonical.vehicles[0].registration_number.value, "WB 12 AB 1234")

    def test_evidence_projection(self):
        canonical = CanonicalBuilder().build(self._graph())
        item = canonical.recovered_property[0]
        self.assertEqual(item.description.value, "Mobile phone")
        self.assertTrue(item.collection_details)

    def test_timeline_ordering(self):
        case_id = uuid4()
        early = GraphNode(node_type=GraphNodeType.TIMELINE_EVENT, label="early", attributes={"occurred_at": datetime(2026, 1, 1, tzinfo=timezone.utc), "description": "Early"}, provenance=(provenance(),))
        late = GraphNode(node_type=GraphNodeType.TIMELINE_EVENT, label="late", attributes={"occurred_at": datetime(2026, 1, 2, tzinfo=timezone.utc), "description": "Late"}, provenance=(provenance(),))
        canonical = CanonicalBuilder().build(InvestigationKnowledgeGraph(case_id=case_id, nodes=(late, early)))
        self.assertEqual([item.description.value for item in canonical.timeline], ["Early", "Late"])

    def test_provenance_is_preserved(self):
        canonical = CanonicalBuilder().build(self._graph())
        fact = canonical.vehicles[0].registration_number
        self.assertEqual(fact.references[0].parser_name, "fixture_parser")
        self.assertEqual(fact.source_document_ids[0], fact.references[0].document_id)

    def test_explicit_conflict_is_unresolved(self):
        case_id = uuid4()
        first, second = GraphNode(node_type=GraphNodeType.LOCATION, label="Location A", provenance=(provenance(),)), GraphNode(node_type=GraphNodeType.LOCATION, label="Location B", provenance=(provenance(),))
        edge = GraphEdge(source_node_id=first.id, target_node_id=second.id, relationship_type=GraphRelationshipType.CONTRADICTS, provenance=(provenance(),))
        canonical = CanonicalBuilder().build(InvestigationKnowledgeGraph(case_id=case_id, nodes=(first, second), edges=(edge,)))
        self.assertEqual(canonical.conflicts[0].status, ConflictStatus.UNRESOLVED)
        self.assertEqual(len(canonical.conflicts[0].competing_values), 2)

    def test_duplicate_entities_remain_single_canonical_record(self):
        one = VehicleInspection(document_id=uuid4(), ocr_text_sha256="c" * 64, parse_metadata=meta(), vehicle_registration="WB 12 AB 1234")
        two = VehicleInspection(document_id=uuid4(), ocr_text_sha256="d" * 64, parse_metadata=meta(), vehicle_registration="WB12AB1234")
        canonical = CanonicalBuilder().build(GraphBuilder(uuid4()).build((one, two)))
        self.assertEqual(len(canonical.vehicles), 1)

    def test_empty_graph_is_preserved_with_missing_information(self):
        canonical = CanonicalBuilder().build(InvestigationKnowledgeGraph(case_id=uuid4()))
        self.assertEqual(len(canonical.missing_information), 1)
        self.assertFalse(canonical.documents)

    def test_stage_writes_artifacts_and_updates_context(self):
        with TemporaryDirectory() as temp_dir:
            graph = self._graph()
            context = WorkflowContext(case_id=graph.case_id, investigation_knowledge_graph=graph, execution_state=WorkflowState(case_id=graph.case_id))
            result = WorkflowEngine(StageRegistry([CanonicalInvestigationStage(Path(temp_dir))])).run(context)
            self.assertTrue(result.report.successful)
            self.assertIsNotNone(result.context.canonical_investigation)
            self.assertEqual(len(result.context.generated_artifacts), 4)
            paths = [Path(temp_dir) / item.storage_key for item in result.context.generated_artifacts]
            self.assertTrue(all(path.is_file() for path in paths))
            self.assertIn("case_metadata", json.loads(next(path for path in paths if path.name == "canonical_investigation.json").read_text(encoding="utf-8")))
            self.assertIn("unresolved_conflicts", result.context.stage_metrics[-1].value)


if __name__ == "__main__":
    unittest.main()
