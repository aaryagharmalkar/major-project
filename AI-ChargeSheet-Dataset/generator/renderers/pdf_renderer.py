"""Minimal PDF renderer for Markdown documents.

This renderer intentionally uses only the Python standard library so the
document generation layer remains portable. It converts Markdown text into a
simple text-based PDF and keeps the design open for future template support.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from generator.renderers.base_renderer import BaseRenderer


@dataclass(frozen=True, slots=True)
class PDFRenderSettings:
    """Settings that control the layout of the generated PDF."""

    page_width: float = 595.28
    page_height: float = 841.89
    margin: float = 40.0
    font_size: float = 11.0
    line_height: float = 14.0
    lines_per_page: int = 48


class PDFRenderer(BaseRenderer[str, Path]):
    """Render Markdown text into a PDF file."""

    _FONT_OBJECT_NUMBER: Final[int] = 1

    def __init__(
        self,
        output_path: str | Path,
        *,
        settings: PDFRenderSettings | None = None,
        templates_directory: str | Path | None = None,
        template_name: str | None = None,
    ) -> None:
        """Initialize the PDF renderer.

        Args:
            output_path: File path where the PDF will be written.
            settings: Optional layout settings for the PDF output.
            templates_directory: Reserved for future template support.
            template_name: Reserved for future template support.
        """

        self._output_path = Path(output_path).expanduser().resolve()
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings = settings or PDFRenderSettings()
        self._templates_directory = Path(templates_directory).expanduser().resolve() if templates_directory else None
        self._template_name = template_name

    def render(self, value: str) -> Path:
        """Render Markdown text into a PDF file and return the output path."""

        lines = self._markdown_to_lines(value)
        pdf_bytes = self._build_pdf(lines)
        self._output_path.write_bytes(pdf_bytes)
        return self._output_path

    def _markdown_to_lines(self, markdown_text: str) -> list[str]:
        """Convert Markdown text into plain text lines for PDF rendering."""

        lines: list[str] = []
        for raw_line in markdown_text.splitlines():
            line = raw_line.rstrip()
            if not line:
                lines.append("")
                continue

            stripped = line.lstrip()
            if stripped.startswith("#"):
                heading_text = stripped.lstrip("#").strip()
                lines.append(heading_text.upper())
                continue

            if stripped.startswith("- "):
                lines.append(f"- {self._strip_inline_markdown(stripped[2:])}")
                continue

            lines.append(self._strip_inline_markdown(line))

        return lines or [""]

    @staticmethod
    def _strip_inline_markdown(text: str) -> str:
        """Remove lightweight inline Markdown formatting."""

        cleaned = text.replace("**", "").replace("__", "").replace("`", "")
        return cleaned.strip()

    def _build_pdf(self, lines: list[str]) -> bytes:
        """Build a minimal multi-page PDF from plain text lines."""

        settings = self._settings
        lines_per_page = max(1, settings.lines_per_page)
        pages = [lines[index : index + lines_per_page] for index in range(0, len(lines), lines_per_page)] or [[""]]

        content_streams = [self._build_content_stream(page_lines) for page_lines in pages]
        object_count = 2 + len(content_streams) * 2 + 1
        font_obj_num = self._FONT_OBJECT_NUMBER
        content_obj_nums = [2 + index for index in range(len(content_streams))]
        page_obj_nums = [2 + len(content_streams) + index for index in range(len(content_streams))]
        pages_obj_num = 2 + len(content_streams) * 2
        catalog_obj_num = object_count

        objects: dict[int, bytes] = {}
        objects[font_obj_num] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

        for index, content_stream in enumerate(content_streams):
            content_obj_num = content_obj_nums[index]
            page_obj_num = page_obj_nums[index]
            content_bytes = content_stream.encode("latin-1", errors="replace")
            objects[content_obj_num] = (
                f"<< /Length {len(content_bytes)} >>\nstream\n".encode("ascii")
                + content_bytes
                + b"\nendstream"
            )
            objects[page_obj_num] = (
                f"<< /Type /Page /Parent {pages_obj_num} 0 R /MediaBox [0 0 {self._settings.page_width} {self._settings.page_height}] "
                f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> /Contents {content_obj_num} 0 R >>"
            ).encode("ascii")

        kids = " ".join(f"{page_obj_num} 0 R" for page_obj_num in page_obj_nums)
        objects[pages_obj_num] = f"<< /Type /Pages /Kids [ {kids} ] /Count {len(page_obj_nums)} >>".encode("ascii")
        objects[catalog_obj_num] = f"<< /Type /Catalog /Pages {pages_obj_num} 0 R >>".encode("ascii")

        return self._serialize_pdf(objects, catalog_obj_num)

    def _build_content_stream(self, lines: list[str]) -> str:
        """Build the PDF drawing commands for a single page."""

        settings = self._settings
        x = settings.margin
        y = settings.page_height - settings.margin - settings.font_size
        commands = ["BT", f"/F1 {settings.font_size} Tf", f"{x:.2f} {y:.2f} Td"]

        for line in lines:
            commands.append(f"({self._escape_pdf_text(line)}) Tj")
            commands.append(f"0 -{settings.line_height:.2f} Td")

        commands.append("ET")
        return "\n".join(commands)

    @staticmethod
    def _escape_pdf_text(text: str) -> str:
        """Escape text for inclusion inside a PDF string literal."""

        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    @staticmethod
    def _serialize_pdf(objects: dict[int, bytes], catalog_obj_num: int) -> bytes:
        """Serialize PDF objects into a valid PDF byte stream."""

        ordered_numbers = sorted(objects)
        parts: list[bytes] = [b"%PDF-1.4\n"]
        offsets: dict[int, int] = {}
        cursor = len(parts[0])

        for obj_num in ordered_numbers:
            offsets[obj_num] = cursor
            body = objects[obj_num]
            obj_bytes = f"{obj_num} 0 obj\n".encode("ascii") + body + b"\nendobj\n"
            parts.append(obj_bytes)
            cursor += len(obj_bytes)

        xref_start = cursor
        max_obj = max(ordered_numbers)
        xref_lines = [f"xref\n0 {max_obj + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
        for obj_num in range(1, max_obj + 1):
            offset = offsets.get(obj_num, 0)
            xref_lines.append(f"{offset:010d} 00000 n \n".encode("ascii"))
        parts.extend(xref_lines)
        trailer = (
            f"trailer\n<< /Size {max_obj + 1} /Root {catalog_obj_num} 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode(
                "ascii"
            )
        )
        parts.append(trailer)
        return b"".join(parts)
