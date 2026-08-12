from datetime import date, datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from src.domain.documents import DocumentType
from src.domain.parsed_documents import (
    MedicalReport, ParseMetadata, SeizureItem, SeizureMemo, VehicleInspection,
)
from src.knowledge_graph.graph_builder import GraphBuilder
from src.knowledge_graph.graph_models import GraphNodeType, GraphRelationshipType
from src.knowledge_graph.graph_stage import GraphStage
from src.workflow.context import ContextItem, WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.state import WorkflowState


def metadata() -> ParseMetadata:
    return ParseMetadata(parser_name="mock_parser", parse_duration_ms=1, retry_count=0, confidence=0.8)


def report(document_id, patient_name="Rahul Sharma") -> MedicalReport:
    return MedicalReport(
        document_id=document_id,
        ocr_text_sha256="a" * 64,
        parse_metadata=metadata(),
        report_date=date(2026, 1, 2),
        patient_name=patient_name,
        doctor_name="Dr. Meera Shah",
        hospital_name="City Hospital",
        observations=("Abrasion on left arm",),
    )


class KnowledgeGraphTests(unittest.TestCase):
    def test_duplicate_people_and_vehicles_are_merged(self) -> None:
        case_id, first_id, second_id = uuid4(), uuid4(), uuid4()
        first = report(first_id, "Rahul Sharma")
        second = report(second_id, "Rahul S.")
        vehicle_one = VehicleInspection(document_id=uuid4(), ocr_text_sha256="b" * 64, parse_metadata=metadata(), vehicle_registration="WB 12 AB 1234")
        vehicle_two = VehicleInspection(document_id=uuid4(), ocr_text_sha256="c" * 64, parse_metadata=metadata(), vehicle_registration="WB12AB1234")

        builder = GraphBuilder(case_id)
        graph = builder.build((first, second, vehicle_one, vehicle_two))

        people = [node for node in graph.nodes if node.node_type == GraphNodeType.PERSON and node.label == "Rahul Sharma"]
        vehicles = [node for node in graph.nodes if node.node_type == GraphNodeType.VEHICLE]
        self.assertEqual(len(people), 1)
        self.assertEqual(len(vehicles), 1)
        self.assertGreaterEqual(builder.duplicates_merged, 2)

    def test_relationships_are_created_from_explicit_seizure_fields(self) -> None:
        document = SeizureMemo(
            document_id=uuid4(), ocr_text_sha256="d" * 64, parse_metadata=metadata(),
            seizure_location="Market Road", prepared_by="Officer Kumar",
            seized_items=(SeizureItem(description="Mobile phone", exhibit_mark="E-1"),),
        )
        graph = GraphBuilder(uuid4()).build((document,))
        edge_types = {edge.relationship_type for edge in graph.edges}

        self.assertIn(GraphRelationshipType.RECOVERED_FROM, edge_types)
        self.assertIn(GraphRelationshipType.COLLECTED_BY, edge_types)
        self.assertIn(GraphRelationshipType.MENTIONS, edge_types)

    def test_nodes_and_edges_keep_complete_provenance(self) -> None:
        document_id = uuid4()
        graph = GraphBuilder(uuid4()).build((report(document_id),))

        provenance = graph.nodes[0].provenance[0]
        self.assertEqual(provenance.document_id, document_id)
        self.assertEqual(provenance.source_reference.document_id, document_id)
        self.assertEqual(provenance.parser_name, "mock_parser")
        self.assertEqual(provenance.confidence, 0.8)
        self.assertIsNotNone(provenance.timestamp)
        self.assertTrue(all(edge.provenance for edge in graph.edges))

    def test_graph_stage_writes_artifacts_and_updates_workflow_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            case_id, document_id = uuid4(), uuid4()
            context = WorkflowContext(
                case_id=case_id,
                parsed_documents=(ContextItem(key=str(document_id), value=report(document_id)),),
                execution_state=WorkflowState(case_id=case_id),
            )
            result = WorkflowEngine(StageRegistry([GraphStage(Path(temp_dir))])).run(context)

            self.assertTrue(result.report.successful)
            self.assertIsNotNone(result.context.investigation_knowledge_graph)
            self.assertEqual(len(result.context.generated_artifacts), 3)
            metric = result.context.stage_metrics[-1].value
            self.assertIn("entities", metric)
            self.assertEqual(metric["conflicts"], 0)
            paths = [Path(temp_dir) / artifact.storage_key for artifact in result.context.generated_artifacts]
            self.assertTrue(all(path.is_file() for path in paths))
            graph_path = next(path for path in paths if path.name == "investigation_graph.json")
            self.assertIn("nodes", json.loads(graph_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
