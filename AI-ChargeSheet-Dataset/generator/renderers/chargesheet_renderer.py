"""Render charge sheet schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.chargesheet_schema import ChargeSheetDocument


class ChargeSheetRenderer(BaseRenderer[ChargeSheetDocument, str]):
    """Render a charge sheet schema into Markdown."""

    def render(self, value: ChargeSheetDocument) -> str:
        lines = [f"# {value.document_type}", ""]
        lines.append(f"**Investigating Officer:** {value.investigating_officer.name}")
        lines.append(f"**Victim:** {value.victim.full_name}")
        lines.append(f"**Status:** {value.final_status}")
        lines.append("")
        lines.append("## Findings")
        if value.findings:
            for item in value.findings:
                lines.append(f"### {item.heading}")
                lines.append(item.text)
                lines.append("")
        else:
            lines.append("- No findings recorded.")
        return "\n".join(lines).rstrip() + "\n"
