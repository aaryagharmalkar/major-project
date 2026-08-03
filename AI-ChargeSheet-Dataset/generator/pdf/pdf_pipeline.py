"""Pipeline for converting markdown investigation documents into PDF outputs."""

from __future__ import annotations

from pathlib import Path

from generator.pdf.docx_to_pdf import DocxToPdfRenderer
from generator.pdf.markdown_to_docx import MarkdownToDocxRenderer
from generator.pdf.template_manager import TemplateManager


class PDFPipeline:
    """Render markdown content into a PDF, using template placeholders and a lightweight DOCX fallback."""

    def __init__(self, output_directory: str | Path | None = None) -> None:
        self._output_directory = Path(output_directory or Path(__file__).resolve().parent).expanduser().resolve()
        self._output_directory.mkdir(parents=True, exist_ok=True)
        self._template_manager = TemplateManager()
        self._markdown_to_docx = MarkdownToDocxRenderer(self._template_manager)
        self._docx_to_pdf = DocxToPdfRenderer()

    def render_markdown(self, document_type: str, content: str, *, title: str | None = None, output_name: str | None = None) -> Path:
        """Render markdown content into a PDF file and return the output path."""

        docx_path = self._markdown_to_docx.render_with_template(document_type, content, title=title)
        pdf_path = self._docx_to_pdf.render(docx_path)
        destination = self._output_directory / (output_name or pdf_path.name)
        destination.write_bytes(pdf_path.read_bytes())
        return destination
