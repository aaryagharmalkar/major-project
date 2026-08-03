"""Render FSL report schema objects to Markdown."""

from __future__ import annotations

from generator.renderers.base_renderer import BaseRenderer
from generator.schemas.documents.fsl_schema import FSLReportDocument


class FSLRenderer(BaseRenderer[FSLReportDocument, str]):
    """Render an FSL report schema into Markdown."""

    def render(self, value: FSLReportDocument) -> str:
        lines = [
            f"# {value.document_type}",
            "",
            f"**Report ID:** {value.report_id}",
            f"**Laboratory:** {value.laboratory_name}",
            f"**Date:** {value.report_date.isoformat()}",
            "",
            "## Summary",
            value.examination_summary or "No summary recorded.",
            "",
            "## Findings",
            value.findings or "No findings recorded.",
            "",
            "## Conclusion",
            value.conclusion or "No conclusion recorded.",
        ]
        return "\n".join(lines) + "\n"
