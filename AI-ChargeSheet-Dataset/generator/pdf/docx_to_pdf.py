"""Convert DOCX-like files into PDF files using a lightweight fallback."""

from __future__ import annotations

from pathlib import Path

from generator.pdf.base_pdf_renderer import BasePDFRenderer


class DocxToPdfRenderer(BasePDFRenderer[Path, Path]):
    """Convert a DOCX-like file into a simple PDF document."""

    def render(self, value: Path) -> Path:
        output_path = value.with_suffix(".pdf")
        output_path.write_bytes(self._build_simple_pdf(value.read_text(encoding="utf-8")))
        return output_path

    @staticmethod
    def _build_simple_pdf(content: str) -> bytes:
        lines = content.splitlines()
        simple_text = "\n".join(lines) if lines else ""
        return (
            b"%PDF-1.4\n"
            + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            + b"4 0 obj\n<< /Length 0 >>\nstream\nendstream\nendobj\n"
            + b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            + b"xref\n0 6\n"
            + b"0000000000 65535 f \n"
            + b"0000000010 00000 n \n"
            + b"0000000062 00000 n \n"
            + b"0000000119 00000 n \n"
            + b"0000000204 00000 n \n"
            + b"0000000309 00000 n \n"
            + b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
        )
