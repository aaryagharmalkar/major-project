"""A4 renderer for the supplied charge-sheet sample structure."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..chargesheet.form_if5_schema import ChargeSheetData, ChargeSheetField, IF5Row


class IF5Renderer:
    def render(self, data: ChargeSheetData, output: Path, *, final: bool = False) -> Path:
        if data.disposition == "final_blocked":
            raise ValueError("FINAL_BLOCKED cases cannot render a charge sheet")
        output.parent.mkdir(parents=True, exist_ok=True)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8.5, leading=10.5))
        story = [Spacer(1, 55 * mm), Paragraph("CHARGE SHEET", styles["Title"])]
        status = f"FINALIZED / APPROVED VERSION {data.version}" if final else f"DRAFT / REVIEW COPY — VERSION {data.version}"
        story += [Spacer(1, 3 * mm), Paragraph(status, styles["Heading2"])]
        story += [Spacer(1, 5 * mm), Paragraph(f"Case Number: {data.case_number.rendered}", styles["Normal"]), Paragraph(f"Police Station: {data.police_station.rendered}", styles["Normal"]), Paragraph(f"To be filed before: {data.court.rendered}", styles["Normal"]), PageBreak()]
        self._scalar_section(story, "Case Summary", data.case_summary, styles)
        self._scalar_section(story, "Detailed Facts", data.detailed_facts, styles)
        self._scalar_section(story, "Investigation Conducted", data.investigation_conducted, styles)
        for name, rows in (("Complainant Details", data.complainants), ("Victim Details", data.victims), ("Accused Details", data.accused), ("Witness Details", data.witnesses), ("Chronological Timeline", data.timeline), ("Documentary Evidence", data.documentary_evidence), ("Material Evidence", data.material_evidence)):
            self._table_section(story, name, rows, styles)
        for name, fields in (("Medical Findings", data.medical_findings), ("Forensic Findings", data.forensic_findings), ("Vehicle Findings", data.vehicle_findings)):
            self._findings_section(story, name, fields, styles)
        self._scalar_section(story, "Evidence Analysis", data.evidence_analysis, styles)
        self._findings_section(story, "Applicable Sections", data.legal_sections, styles)
        self._table_section(story, "Annexures", data.annexures, styles)
        story += [Spacer(1, 7 * mm), Paragraph(f"Final Opinion of Investigating Officer: {data.final_opinion.rendered}", styles["Normal"]), Spacer(1, 5 * mm), Paragraph(f"Signature: {data.signature.rendered}", styles["Normal"])]
        title = "Charge Sheet Final" if final else "Charge Sheet Draft"
        SimpleDocTemplate(str(output), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm, title=title).build(story)
        return output

    def _scalar_section(self, story: list, heading: str, field: ChargeSheetField, styles) -> None:
        story.append(KeepTogether([Paragraph(heading, styles["Heading2"]), Paragraph(field.rendered, styles["Normal"]), Spacer(1, 4 * mm)]))

    def _findings_section(self, story: list, heading: str, fields: tuple[ChargeSheetField, ...], styles) -> None:
        values = fields or (ChargeSheetField(status="unavailable", review_required=True),)
        story.extend([Paragraph(heading, styles["Heading2"]), *[Paragraph(f"- {field.rendered}", styles["Normal"]) for field in values], Spacer(1, 4 * mm)])

    def _table_section(self, story: list, heading: str, rows: tuple[IF5Row, ...], styles) -> None:
        rendered_rows = rows or (IF5Row(serial=1, description=ChargeSheetField(status="unavailable", review_required=True), exhibit=ChargeSheetField(status="not_applicable", review_required=True)),)
        table_data = [["S.No.", "Description", "Exhibit"]] + [[str(row.serial), Paragraph(row.description.rendered, styles["Small"]), Paragraph(row.exhibit.rendered, styles["Small"])] for row in rendered_rows]
        table = Table(table_data, colWidths=[16 * mm, 118 * mm, 38 * mm], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.35, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7E7E7")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        story.extend([Paragraph(heading, styles["Heading2"]), table, Spacer(1, 4 * mm)])
