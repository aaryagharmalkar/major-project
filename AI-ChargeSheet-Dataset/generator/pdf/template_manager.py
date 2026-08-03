"""Manage DOCX templates for markdown-to-PDF rendering."""

from __future__ import annotations

from pathlib import Path


class TemplateManager:
    """Load and populate document templates without modifying source facts."""

    TEMPLATE_NAMES = {
        "FIR": "fir_template.docx",
        "Complaint": "complaint_template.docx",
        "Witness Statement": "witness_template.docx",
        "Medical Report": "medical_template.docx",
        "Seizure Memo": "seizure_template.docx",
        "Spot Panchanama": "spot_panchanama_template.docx",
        "Arrest Memo": "arrest_template.docx",
        "FSL Report": "fsl_template.docx",
        "Case Diary": "diary_template.docx",
        "Charge Sheet": "chargesheet_template.docx",
    }

    def __init__(self, templates_directory: str | Path | None = None) -> None:
        self._templates_directory = Path(templates_directory or Path(__file__).resolve().parent / "templates")
        self._templates_directory.mkdir(parents=True, exist_ok=True)

    def load_template(self, document_type: str) -> str | None:
        """Return the contents of a template file if present, otherwise a built-in fallback."""

        template_name = self.TEMPLATE_NAMES.get(document_type)
        if template_name is None:
            return None

        template_path = self._templates_directory / template_name
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        return self._fallback_template(document_type)

    def _fallback_template(self, document_type: str) -> str:
        return (
            f"<docx-template document-type=\"{document_type}\">\n"
            "{{title}}\n"
            "{{content}}\n"
            "</docx-template>"
        )
