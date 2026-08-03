"""Render spot panchanama schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.spot_panchanama_schema import SpotPanchanamaDocument


class SpotPanchanamaRenderer(BaseRenderer[SpotPanchanamaDocument, str]):
    """Render a spot panchanama schema into Markdown."""

    def render(self, value: SpotPanchanamaDocument) -> str:
        lines = [
            f"# {value.document_type}",
            "",
            f"**Panchanama ID:** {value.panchanama_id}",
            f"**Prepared by:** {value.prepared_by}",
            f"**Prepared at:** {value.prepared_at.isoformat()}",
            f"**Location:** {value.location}",
            "",
            "## Observation Summary",
            value.observation_summary,
        ]
        return "\n".join(lines) + "\n"
