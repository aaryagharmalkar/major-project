"""Formal ReportLab/Platypus renderer for the evidence-backed charge sheet."""

from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from ..chargesheet.form_if5_schema import ChargeSheetData, ChargeSheetField, IF5Row


class IF5Renderer:
    """Render existing ChargeSheetData only; this class never changes its meaning."""

    _MAX_TABLE_ROW_TEXT_LENGTH = 1200

    def render(self, data: ChargeSheetData, output: Path, *, final: bool = False) -> Path:
        if data.disposition == "final_blocked":
            raise ValueError("FINAL_BLOCKED cases cannot render a charge sheet")
        output.parent.mkdir(parents=True, exist_ok=True)
        styles = self._styles()
        story = [Spacer(1, 16 * mm), Paragraph("CHARGE SHEET", styles["DocumentTitle"])]
        status = f"FINALIZED / APPROVED VERSION {data.version}" if final else f"DRAFT / REVIEW COPY - VERSION {data.version}"
        story += [Paragraph(status, styles["Status"]), Spacer(1, 5 * mm), self._case_information(data, styles), Spacer(1, 5 * mm), HRFlowable(width="100%", thickness=.7, color=colors.HexColor("#64748B")), Spacer(1, 4 * mm)]
        self._text_section(story, "Case Summary", data.case_summary, styles)
        self._text_section(story, "Detailed Facts", data.detailed_facts, styles)
        self._text_section(story, "Investigation Conducted", data.investigation_conducted, styles)
        for name, rows in (("Complainant Details", data.complainants), ("Victim Details", data.victims), ("Accused Details", data.accused), ("Witness Details", data.witnesses), ("Chronological Timeline", data.timeline), ("Documentary Evidence", data.documentary_evidence), ("Material Evidence", data.material_evidence)):
            self._table_section(story, name, rows, styles)
        for name, fields in (("Medical Findings", data.medical_findings), ("Forensic Findings", data.forensic_findings), ("Vehicle Findings", data.vehicle_findings)):
            self._findings_section(story, name, fields, styles)
        self._text_section(story, "Evidence Analysis", data.evidence_analysis, styles)
        self._findings_section(story, "Applicable Sections", data.legal_sections, styles)
        self._legal_findings_section(story, data.legal_findings, styles)
        self._review_items_section(story, "Conflicts Requiring Review", data.conflicts, styles)
        self._review_items_section(story, "Missing Information", data.missing_information, styles)
        story.append(PageBreak())
        self._table_section(story, "Annexure Index", data.annexures, styles)
        story += [Spacer(1, 6 * mm), HRFlowable(width="100%", thickness=.5, color=colors.HexColor("#94A3B8")), Spacer(1, 4 * mm), Paragraph(self._paragraph_text(f"Final Opinion of Investigating Officer: {data.final_opinion.rendered}"), styles["Body"]), Spacer(1, 5 * mm), Paragraph(self._paragraph_text(f"Signature: {data.signature.rendered}"), styles["Body"])]
        document = BaseDocTemplate(str(output), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=22 * mm, bottomMargin=17 * mm, title="Charge Sheet Final" if final else "Charge Sheet Draft")
        frame = Frame(document.leftMargin, document.bottomMargin, document.width, document.height, id="body")
        # Draw chrome after each page's flowables.  Continued tables otherwise
        # paint over the chrome that was drawn at page start.
        document.addPageTemplates(PageTemplate(id="charge-sheet", frames=[frame], onPageEnd=self._page_chrome))
        document.build(story)
        return output

    @staticmethod
    def _styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="DocumentTitle", parent=styles["Title"], alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=17, leading=21, spaceAfter=3 * mm, textColor=colors.HexColor("#0F172A")))
        styles.add(ParagraphStyle(name="Status", parent=styles["Normal"], alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.HexColor("#475569")))
        styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=3 * mm, spaceAfter=2 * mm, textColor=colors.HexColor("#172554")))
        styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=9.3, leading=13, spaceAfter=1.5 * mm))
        styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=7.8, leading=9.6))
        styles.add(ParagraphStyle(name="TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=10, textColor=colors.white))
        styles.add(ParagraphStyle(name="RecordHeading", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.HexColor("#172554"), spaceBefore=2 * mm, spaceAfter=1 * mm))
        styles.add(ParagraphStyle(name="FieldLabel", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.4, leading=10.5, textColor=colors.HexColor("#334155"), spaceBefore=1 * mm, spaceAfter=.5 * mm))
        return styles

    def _page_chrome(self, canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#94A3B8")); canvas.setLineWidth(.45)
        canvas.line(document.leftMargin, A4[1] - 13 * mm, A4[0] - document.rightMargin, A4[1] - 13 * mm)
        canvas.setFont("Helvetica", 7.5); canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(document.leftMargin, A4[1] - 10 * mm, "BYOMKESH AI - CHARGE SHEET")
        canvas.drawRightString(A4[0] - document.rightMargin, 9 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    def _case_information(self, data: ChargeSheetData, styles):
        cells = (("Case Number", data.case_number), ("Police Station", data.police_station), ("Court", data.court))
        rows = [[Paragraph(self._paragraph_text(name), styles["Small"]), Paragraph(self._paragraph_text(field.rendered), styles["Body"])] for name, field in cells]
        table = Table(rows, colWidths=[38 * mm, 142 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E2E8F0")), ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#94A3B8")), ("INNERGRID", (0, 0), (-1, -1), .25, colors.HexColor("#CBD5E1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return table

    def _heading(self, story: list, heading: str, styles) -> None:
        story.extend([Paragraph(heading, styles["Section"]), HRFlowable(width="100%", thickness=.35, color=colors.HexColor("#CBD5E1")), Spacer(1, 1.5 * mm)])

    def _text_section(self, story: list, heading: str, field: ChargeSheetField, styles) -> None:
        self._heading(story, heading, styles)
        lines = field.rendered.splitlines()
        if heading == "Investigation Conducted":
            for statement in (line.strip() for line in lines if line.strip()):
                story.append(Paragraph(self._paragraph_text(statement), styles["Body"], bulletText="•"))
            story.append(Spacer(1, 3 * mm))
            return
        for line in lines:
            clean = line.strip()
            if clean.startswith("- "):
                story.append(Paragraph(self._paragraph_text(clean[2:]), styles["Body"], bulletText="•"))
            elif clean.endswith(":"):
                story.append(Paragraph(self._paragraph_text(clean), styles["FieldLabel"]))
            elif clean:
                story.append(Paragraph(self._paragraph_text(clean), styles["Body"]))
        story.append(Spacer(1, 3 * mm))

    def _findings_section(self, story: list, heading: str, fields: tuple[ChargeSheetField, ...], styles) -> None:
        self._heading(story, heading, styles)
        values = fields or (ChargeSheetField(status="unavailable", review_required=True),)
        for field in values:
            story.append(Paragraph(self._paragraph_text(field.rendered), styles["Body"], bulletText="•"))
        story.append(Spacer(1, 3 * mm))

    def _table_section(self, story: list, heading: str, rows: tuple[IF5Row, ...], styles) -> None:
        self._heading(story, heading, styles)
        rendered_rows = rows or (IF5Row(serial=1, description=ChargeSheetField(status="unavailable", review_required=True), exhibit=ChargeSheetField(status="not_applicable", review_required=True)),)
        if any(self._requires_structured_row(row) for row in rendered_rows):
            self._structured_rows(story, rendered_rows, styles)
            return
        table_data = [[Paragraph("S.No.", styles["TableHeader"]), Paragraph("Description", styles["TableHeader"]), Paragraph("Exhibit", styles["TableHeader"])]]
        table_data += [[Paragraph(str(row.serial), styles["Small"]), Paragraph(self._paragraph_text(row.description.rendered), styles["Small"]), Paragraph(self._paragraph_text(row.exhibit.rendered), styles["Small"])] for row in rendered_rows]
        table = Table(table_data, colWidths=[15 * mm, 124 * mm, 41 * mm], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#94A3B8")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])]))
        story.extend([table, Spacer(1, 3 * mm)])

    def _requires_structured_row(self, row: IF5Row) -> bool:
        """Avoid ReportLab table rows that cannot split when one cell is very long."""
        return max(len(row.description.rendered), len(row.exhibit.rendered)) > self._MAX_TABLE_ROW_TEXT_LENGTH

    def _structured_rows(self, story: list, rows: tuple[IF5Row, ...], styles) -> None:
        """Render unbounded row content as independently splittable flowables."""
        for row in rows:
            story.append(HRFlowable(width="100%", thickness=.35, color=colors.HexColor("#94A3B8"), spaceBefore=1 * mm, spaceAfter=1 * mm))
            story.append(Paragraph(f"S.No. {row.serial}", styles["RecordHeading"]))
            self._labelled_value(story, "Description", row.description.rendered, styles)
            self._labelled_value(story, "Exhibit", row.exhibit.rendered, styles)
        story.append(Spacer(1, 3 * mm))

    def _labelled_value(self, story: list, label: str, value: str, styles) -> None:
        story.append(Paragraph(label, styles["FieldLabel"]))
        story.append(Paragraph(self._paragraph_text(value), styles["Body"]))

    @staticmethod
    def _paragraph_text(value: str) -> str:
        return escape(value).replace("\n", "<br/>")

    def _legal_findings_section(self, story: list, findings, styles) -> None:
        if not findings:
            return
        self._heading(story, "Legal Findings", styles)
        for index, finding in enumerate(findings, 1):
            story.append(HRFlowable(width="100%", thickness=.5, color=colors.HexColor("#94A3B8"), spaceBefore=1 * mm, spaceAfter=1 * mm))
            story.append(Paragraph(f"Legal Finding {index}", styles["RecordHeading"]))
            self._labelled_value(story, "Offence / Section", f"{finding.offence.rendered}\n{finding.proposed_section.rendered}", styles)
            self._labelled_value(story, "Status", finding.status, styles)
            self._labelled_value(story, "Offence Description", finding.description.rendered, styles)
            self._labelled_value(story, "Evidence Strength", finding.evidence_strength, styles)
            if finding.offence.confidence is not None:
                self._labelled_value(story, "Confidence", f"{finding.offence.confidence:.2f}", styles)
            self._labelled_value(story, "Review Required", "Yes" if finding.review_required else "No", styles)
            self._evidence_items(story, "Supporting Evidence", finding.supporting_evidence, styles)
            if finding.contradicting_evidence:
                self._evidence_items(story, "Contradicting Evidence", finding.contradicting_evidence, styles)
        story.append(Spacer(1, 3 * mm))

    def _evidence_items(self, story: list, heading: str, fields: tuple[ChargeSheetField, ...], styles) -> None:
        story.append(Paragraph(heading, styles["FieldLabel"]))
        if not fields:
            story.append(Paragraph("Not Available in Investigation Records", styles["Body"]))
            return
        for field in fields:
            story.append(Paragraph(self._paragraph_text(field.rendered), styles["Body"], bulletText="•"))

    def _review_items_section(self, story: list, heading: str, items, styles) -> None:
        if not items:
            return
        self._heading(story, heading, styles)
        for item in items:
            story.append(Paragraph(self._paragraph_text(item.description), styles["Body"], bulletText="•"))
        story.append(Spacer(1, 3 * mm))
