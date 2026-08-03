"""Render complaint schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.complaint_schema import ComplaintDocument


class ComplaintRenderer(BaseRenderer[ComplaintDocument, str]):
    """Render a complaint schema into Markdown using a simple placeholder template."""

    def render(self, value: ComplaintDocument) -> str:
        return (
            f"# Complaint\n\n"
            f"## Complaint Number\n{value.complaint_number}\n\n"
            f"## Complainant\n{value.complainant.full_name}\n\n"
            f"## Incident Details\n- Date: {value.incident_date}\n- Place: {value.location}\n- Offence: {value.offence_description}\n\n"
            f"## Narrative\n{value.narrative}\n\n"
            f"## Accused\n{value.accused_details}\n\n"
            f"## Signature\n{value.signature}\n"
        )
