"""Render arrest memo schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.arrest_schema import ArrestMemoDocument


class ArrestRenderer(BaseRenderer[ArrestMemoDocument, str]):
    """Render an arrest memo schema into Markdown."""

    def render(self, value: ArrestMemoDocument) -> str:
        lines = [
            f"# {value.document_type}",
            "",
            f"**Memo Number:** {value.memo_number}",
            f"**Arrested Person:** {value.arrested_person.full_name}",
            f"**Date/Time:** {value.arrest_datetime.isoformat()}",
            f"**Location:** {value.arrest_location}",
            f"**Grounds:** {value.grounds_of_arrest}",
            "",
            "## Remarks",
            value.remarks or "No additional remarks.",
        ]
        return "\n".join(lines) + "\n"
