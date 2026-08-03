"""Render medical report schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.medical_schema import MedicalReportDocument


class MedicalRenderer(BaseRenderer[MedicalReportDocument, str]):
    """Render a medical report schema into Markdown."""

    def render(self, value: MedicalReportDocument) -> str:
        examination = value.examination
        lines = [
            f"# {value.document_type}",
            "",
            f"**Patient:** {value.patient.full_name}",
            f"**Examining Doctor:** {examination.doctor_name}",
            f"**Facility:** {examination.hospital_name}",
            f"**Date:** {examination.examination_datetime.isoformat()}",
            "",
            "## Findings",
            examination.medical_opinion or "No opinion recorded.",
            "",
            "## Injuries",
        ]
        if value.injuries:
            for injury in value.injuries:
                lines.append(f"- {injury.body_part}: {injury.injury_type} ({injury.severity})")
        else:
            lines.append("- No injuries recorded.")
        return "\n".join(lines) + "\n"
