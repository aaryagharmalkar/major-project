"""Render seizure memo schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.seizure_schema import SeizureMemoDocument


class SeizureRenderer(BaseRenderer[SeizureMemoDocument, str]):
    """Render a seizure memo schema into Markdown."""

    def render(self, value: SeizureMemoDocument) -> str:
        lines = [
            f"# {value.document_type}",
            "",
            f"**Memo Number:** {value.memo_number}",
            f"**Date:** {value.seizure_datetime.isoformat()}",
            f"**Location:** {value.seizure_location}",
            f"**Officer:** {value.seizing_officer.name}",
            "",
            "## Evidence",
        ]
        if value.evidence:
            for item in value.evidence:
                lines.append(f"- {item.evidence_type}: {item.description}")
        else:
            lines.append("- No evidence recorded.")
        return "\n".join(lines) + "\n"
