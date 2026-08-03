"""Convert markdown text into a simple DOCX-compatible placeholder document."""

from __future__ import annotations

from pathlib import Path

from generator.pdf.base_pdf_renderer import BasePDFRenderer
from generator.pdf.template_manager import TemplateManager


class MarkdownToDocxRenderer(BasePDFRenderer[str, Path]):
    """Render Markdown content into a lightweight template-backed DOCX-like text file."""

    def __init__(self, template_manager: TemplateManager | None = None) -> None:
        self._template_manager = template_manager or TemplateManager()

    def render(self, value: str) -> Path:
        output_path = Path(__file__).resolve().parent / "output.docx"
        output_path.write_text(value, encoding="utf-8")
        return output_path

    def render_with_template(self, document_type: str, content: str, *, title: str | None = None) -> Path:
        """Render markdown content into a template-backed DOCX-like file."""

        template_text = self._template_manager.load_template(document_type)
        if template_text is None:
            template_text = "{{title}}\n{{content}}"

        populated = template_text.replace("{{title}}", title or document_type).replace("{{content}}", content)
        output_path = Path(__file__).resolve().parent / f"{document_type.lower().replace(' ', '_')}.docx"
        output_path.write_text(populated, encoding="utf-8")
        return output_path
