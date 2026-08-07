import json
import re
import json5
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomSectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomSubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=4,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomSignature',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            spaceBefore=20,
            fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))
    
    def generate_pdf(self, response_text: str, output_path: Path) -> None:
        # Save raw response for debugging
        debug_path = output_path.parent / "llm_response_raw.txt"
        debug_path.write_text(response_text, encoding='utf-8')
        print(f"Raw LLM response saved to {debug_path}")
        
        # Try to extract JSON
        json_str = response_text.strip()
        # Remove markdown code fences
        code_fence_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.findall(code_fence_pattern, json_str, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
            # If no code fence, try to find a JSON object directly
            json_pattern = r"(\{.*\})"
            match = re.search(json_pattern, json_str, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
        
        # Attempt parsing with json5 first (handles trailing commas, comments)
        try:
            import json_repair
            repaired_json = json_repair.repair_json(json_str)
            data = json5.loads(repaired_json)
            print("Successfully repaired and parsed JSON.")
        except Exception as e:
            # Fallback to standard json if repair fails
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e2:
                print(f"Warning: LLM response is not valid JSON. Error: {e2}")
                data = {"raw_text": response_text}
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=2.54*cm,
            rightMargin=2.54*cm,
            topMargin=2.54*cm,
            bottomMargin=2.54*cm,
        )
        story = []
        
        def add_page_header(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.grey)
            fir_no = self._get_fir_number(data)
            canvas.drawCentredString(4.13*inch, 10.8*inch, f"CHARGE SHEET – RAJINDER NAGAR POLICE STATION – FIR NO. {fir_no}")
            canvas.drawCentredString(4.13*inch, 0.8*inch, f"Page {doc.page}")
            canvas.restoreState()
        
        doc.onPage = add_page_header
        
        if "raw_text" in data:
            story.append(Paragraph("The LLM response could not be parsed as JSON. Below is the raw response:", self.styles['CustomBodyText']))
            story.append(Spacer(1, 0.2*inch))
            text = data["raw_text"].replace("\n", "<br/>")
            story.append(Paragraph(text, self.styles['CustomBodyText']))
            doc.build(story)
            print(f"PDF generated with raw text: {output_path}")
            return
        
        # Build structured content
        self._build_cover_page(story, data)
        story.append(PageBreak())
        self._build_section(story, "police_station_details", "Police Station Details", data)
        self._build_section(story, "fir_information", "FIR Information", data)
        self._build_section(story, "crime_number", "Crime Number", data)
        self._build_section(story, "investigating_officer", "Investigating Officer", data)
        self._build_section(story, "court_name", "Court", data)
        self._build_section(story, "complainant_details", "Complainant Details", data)
        self._build_section(story, "victim_details", "Victim Details", data)
        self._build_section(story, "accused_details", "Accused Details", data)
        story.append(PageBreak())
        self._build_section(story, "case_summary", "Case Summary", data)
        self._build_section(story, "detailed_facts", "Detailed Facts of the Case", data)
        self._build_section(story, "investigation_conducted", "Investigation Conducted", data)
        self._build_timeline(story, data.get("chronological_timeline", []))
        story.append(PageBreak())
        self._build_witness_table(story, data.get("witness_details", []))
        self._build_evidence_list(story, "Documentary Evidence", data.get("documentary_evidence", []))
        self._build_evidence_list(story, "Material Evidence", data.get("material_evidence", []))
        story.append(PageBreak())
        self._build_section(story, "medical_findings", "Medical Findings", data)
        self._build_section(story, "forensic_findings", "Forensic Findings", data)
        self._build_section(story, "vehicle_inspection_findings", "Vehicle Inspection Findings", data)
        self._build_section(story, "spot_panchnama_summary", "Spot Panchnama Summary", data)
        self._build_section(story, "cctv_findings", "CCTV Findings", data)
        self._build_section(story, "evidence_analysis", "Evidence Analysis", data)
        story.append(PageBreak())
        self._build_section(story, "applicable_bns_sections", "Applicable BNS Sections", data)
        self._build_section(story, "applicable_mv_act_sections", "Applicable Motor Vehicle Act Sections", data)
        self._build_annexures(story, data.get("annexures", []))
        self._build_section(story, "final_opinion", "Final Opinion of Investigating Officer", data)
        self._build_signature(story, data.get("signature_block", ""))
        
        doc.build(story)
        print(f"PDF generated: {output_path}")
    
    # ... (rest of the methods remain the same as before)
    
    def _get_fir_number(self, data: Dict[str, Any]) -> str:
        cover = data.get("cover_page", {})
        if "case_number" in cover:
            return cover["case_number"]
        fir = data.get("fir_information", "")
        if "FIR" in fir:
            match = re.search(r'FIR[\/\s]*No\.?\s*[\d]+', fir)
            if match:
                return match.group(0)
        return "Not Available"
    
    def _build_cover_page(self, story, data):
        cover = data.get("cover_page", {})
        title = cover.get("title", "CHARGE SHEET")
        case_no = cover.get("case_number", "Not Available")
        ps = cover.get("police_station", "Not Available")
        date = cover.get("date", datetime.now().strftime("%d-%m-%Y"))
        
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"<b>Case Number:</b> {case_no}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Police Station:</b> {ps}", self.styles['CustomBodyText']))
        story.append(Paragraph(f"<b>Date:</b> {date}", self.styles['CustomBodyText']))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("UNDER THE BHARATIYA NYAYA SANHITA, 2023 & MOTOR VEHICLES ACT, 1988", self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("(To be filed before the Metropolitan Magistrate, Tis Hazari Courts, Delhi)", self.styles['CustomBodyText']))
    
    def _build_section(self, story, key, heading, data):
        content = data.get(key, "Not Available")
        if not content or content == "":
            content = "Not Available"
        story.append(Paragraph(heading, self.styles['CustomSectionHeading']))
        if isinstance(content, dict):
            text = "\n".join([f"• {k}: {v}" for k, v in content.items()])
        elif isinstance(content, list):
            text = "\n".join([f"• {item}" for item in content])
        else:
            text = str(content)
        text = text.replace("\n", "<br/>")
        story.append(Paragraph(text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.2*inch))
    
    def _build_timeline(self, story, timeline):
        if not timeline:
            return
        story.append(Paragraph("Chronological Timeline", self.styles['CustomSectionHeading']))
        data = [["Time/Date", "Event"]]
        for item in timeline:
            if isinstance(item, dict):
                time = item.get("time", item.get("date", ""))
                event = item.get("event", item.get("description", ""))
                data.append([time, event])
            elif isinstance(item, str):
                data.append(["", item])
            else:
                data.append(["", str(item)])
        table = Table(data, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    def _build_witness_table(self, story, witnesses):
        if not witnesses:
            return
        story.append(Paragraph("Witness Details", self.styles['CustomSectionHeading']))
        data = [["S.No.", "Name", "Age", "Occupation", "Statement Summary", "Exhibit"]]
        for idx, w in enumerate(witnesses, 1):
            if isinstance(w, dict):
                name = w.get("name", "")
                age = str(w.get("age", ""))
                occ = w.get("occupation", "")
                summary = w.get("statement", w.get("summary", ""))
                exhibit = w.get("exhibit_mark", "")
                data.append([str(idx), name, age, occ, summary, exhibit])
            else:
                data.append([str(idx), str(w), "", "", "", ""])
        table = Table(data, colWidths=[0.5*inch, 1.2*inch, 0.7*inch, 1.2*inch, 2.5*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    def _build_evidence_list(self, story, heading, evidence_list):
        if not evidence_list:
            return
        story.append(Paragraph(heading, self.styles['CustomSectionHeading']))
        data = [["S.No.", "Evidence Description", "Exhibit Mark"]]
        for idx, ev in enumerate(evidence_list, 1):
            if isinstance(ev, dict):
                desc = ev.get("description", ev.get("document_name", str(ev)))
                exhibit = ev.get("exhibit_mark", "")
                data.append([str(idx), desc, exhibit])
            else:
                data.append([str(idx), str(ev), ""])
        table = Table(data, colWidths=[0.5*inch, 4.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    def _build_annexures(self, story, annexures):
        if not annexures:
            return
        story.append(Paragraph("Annexures", self.styles['CustomSectionHeading']))
        data = [["Annexure No.", "Document Name", "Exhibit Mark"]]
        for item in annexures:
            if isinstance(item, dict):
                an = item.get("annexure_no", "")
                doc = item.get("document_name", "")
                exhibit = item.get("exhibit_mark", "")
                data.append([an, doc, exhibit])
            else:
                data.append(["", str(item), ""])
        table = Table(data, colWidths=[1.2*inch, 4*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    def _build_signature(self, story, signature_block):
        if not signature_block:
            signature_block = "Inspector Suresh Chandra\nInvestigating Officer\nRajinder Nagar Police Station\nDate: " + datetime.now().strftime("%d-%m-%Y")
        story.append(Paragraph("Signature Block", self.styles['CustomSectionHeading']))
        text = signature_block.replace("\n", "<br/>")
        story.append(Paragraph(text, self.styles['CustomBodyText']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("___________________________", self.styles['CustomBodyText']))
        story.append(Paragraph("Signature of Investigating Officer", self.styles['CustomBodyText']))