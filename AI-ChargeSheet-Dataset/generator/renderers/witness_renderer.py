"""Render witness statement schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.witness_schema import WitnessStatementDocument


class WitnessRenderer(BaseRenderer[WitnessStatementDocument, str]):
    """Render a witness statement schema into Markdown."""

    def render(self, value: WitnessStatementDocument) -> str:
        statement = value.statement
        witness = value.witness
        lines = [
            f"# {statement.statement_title}",
            "",
            f"**Witness:** {witness.full_name}",
            f"**Relationship:** {witness.relationship_to_case or 'Not recorded'}",
            f"**Recorded by:** {value.recorded_by.name}",
            "",
            "## Statement",
            statement.statement_text,
            "",
            "## Observed Events",
        ]
        if statement.observed_events:
            lines.extend(f"- {event}" for event in statement.observed_events)
        else:
            lines.append("- No specific events recorded.")
        return "\n".join(lines) + "\n"
