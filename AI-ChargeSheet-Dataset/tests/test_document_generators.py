from __future__ import annotations

from pathlib import Path

from generator.case_builder import CaseBuilder
from generator.document_generators.complaint_generator import ComplaintDocumentGenerator
from generator.document_generators.fir_generator import FIRDocumentGenerator
from generator.document_generators.witness_generator import WitnessDocumentGenerator
from generator.pdf.template_manager import TemplateManager
from generator.schemas.master_case_schema import MasterCase


def _build_master_case() -> MasterCase:
    return MasterCase(
        case_information={
            "case_id": "CASE_001",
            "crime_category": "Theft",
            "offence_description": "Theft of a motorcycle from the victim's residence.",
            "police_station": "Shivaji Nagar",
            "district": "Pune",
            "state": "Maharashtra",
            "FIR_number": "FIR/001/2024",
            "FIR_date": "2024-01-10",
            "incident_date": "2024-01-09",
            "incident_time": "22:30:00",
            "location": "Lane 4, Shivajinagar",
        },
        victim={
            "person_id": "V001",
            "full_name": "Asha Rao",
            "age": 29,
            "gender": "Female",
            "occupation": "Teacher",
            "address": "Lane 4, Shivajinagar",
            "phone": "9999999999",
        },
        accused=[
            {
                "person_id": "A001",
                "full_name": "Ravi Sharma",
                "age": 35,
                "gender": "Male",
                "occupation": "Mechanic",
                "address": "Kothrud",
                "phone": "8888888888",
                "alias_names": [],
                "charges": ["Theft"],
            }
        ],
        witnesses=[
            {
                "person_id": "W001",
                "full_name": "Meera Rao",
                "age": 24,
                "gender": "Female",
                "occupation": "Student",
                "address": "Shivajinagar",
                "phone": "7777777777",
                "statement_summary": "Saw the accused near the residence shortly before the theft.",
                "relationship_to_case": "Neighbor",
                "is_hostile": False,
            }
        ],
        investigating_officer={
            "name": "Officer Nair",
            "rank": "API",
            "buckle_number": "B-101",
            "police_station": "Shivaji Nagar",
            "phone": "6666666666",
        },
        timeline=[
            {
                "timestamp": "2024-01-09T22:30:00",
                "event_type": "Incident",
                "description": "Theft reported by the victim.",
                "related_people": ["V001", "A001"],
                "related_evidence": [],
            }
        ],
        evidence=[],
        applicable_bns_sections={"sections": []},
    )


def test_case_builder_generates_documents(tmp_path: Path) -> None:
    master_case = _build_master_case()
    builder = CaseBuilder(master_case, tmp_path)
    builder.register_default_generators()

    report = builder.run()

    assert report.success is True
    assert (tmp_path / "CASE_001" / "documents" / "fir.md").exists()
    assert (tmp_path / "CASE_001" / "documents" / "complaint.md").exists()
    assert (tmp_path / "CASE_001" / "documents" / "witness_01.md").exists()
    assert (tmp_path / "CASE_001" / "pdfs" / "fir.pdf").exists()
    assert (tmp_path / "CASE_001" / "pdfs" / "complaint.pdf").exists()
    assert (tmp_path / "CASE_001" / "pdfs" / "witness_01.pdf").exists()


def test_template_manager_loads_default_template() -> None:
    manager = TemplateManager()
    template = manager.load_template("FIR")
    assert template is not None
    assert "{{title}}" in template
