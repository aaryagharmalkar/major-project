"""Render case diary schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.diary_schema import CaseDiaryDocument


class DiaryRenderer(BaseRenderer[CaseDiaryDocument, str]):
    """Render a case diary schema into Markdown."""

    def render(self, value: CaseDiaryDocument) -> str:
        lines = [f"# {value.document_type}", ""]
        for entry in value.entries:
            lines.append(f"## Entry {entry.entry_number}")
            lines.append(f"- Time: {entry.timestamp.isoformat()}")
            lines.append(f"- Author: {entry.author_name}")
            lines.append(f"- Content: {entry.content}")
            lines.append("")
        if not value.entries:
            lines.append("- No diary entries recorded.")
        return "\n".join(lines).rstrip() + "\n"
