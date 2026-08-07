import json
from typing import Dict, Any

class PromptBuilder:
    """
    Builds a comprehensive prompt for the LLM to generate a charge sheet.
    """
    
    @staticmethod
    def build_prompt(case_data: Dict[str, Any]) -> str:
        """
        Construct the full prompt with instructions and the case data.
        """
        # Serialize the case data to JSON for the LLM
        case_json = json.dumps(case_data, indent=2, ensure_ascii=False)
        
        prompt = f"""
You are an experienced Indian Investigating Officer (IO) with 20 years of service.
Your task is to prepare a complete, court-ready charge sheet for the case described below.

**CRITICAL INSTRUCTION:**
- Output **ONLY** a valid JSON object. Do not include any other text, explanations, markdown, or code fences.
- The JSON must have the **exact keys** listed below. Do not add or remove keys.
- Use proper JSON syntax: double quotes, no trailing commas, escape special characters.
- If a required piece of information is missing from the investigation documents, use the string "Not Available in Investigation Records" as the value.

**Expected JSON keys:**
- "cover_page": {{ "title": "CHARGE SHEET", "case_number": "...", "police_station": "...", "date": "..." }}
- "police_station_details": "Full name, address, district, and contact of the police station."
- "fir_information": "FIR number, date, time, and sections under which registered."
- "crime_number": "Crime number (if any) or FIR number."
- "investigating_officer": "Name, rank, badge number, and contact of the IO."
- "court_name": "Name of the court where the chargesheet is to be filed (e.g., Metropolitan Magistrate, Tis Hazari)."
- "complainant_details": "Name, age, occupation, address, relation to victim."
- "victim_details": "Name, age, occupation, address, injuries sustained, current status."
- "accused_details": "Name, age, father's name, occupation, address, vehicle used, arrest date."
- "case_summary": "Brief summary of the case (1-2 paragraphs)."
- "detailed_facts": "Detailed narrative of the occurrence, as per evidence and witness statements."
- "investigation_conducted": "Summary of investigation steps taken by the IO."
- "chronological_timeline": ["List of key events with dates and times as strings."]
- "witness_details": [ {{ "name": "", "age": "", "occupation": "", "statement": "", "exhibit_mark": "" }} ]
- "documentary_evidence": [ {{ "description": "", "exhibit_mark": "" }} ]
- "material_evidence": [ {{ "description": "", "exhibit_mark": "" }} ]
- "medical_findings": "Summary of injuries, treatment, and medical opinion (grievous, dangerous)."
- "forensic_findings": "Summary of FSL report findings (speed, alcohol, DNA, etc.)."
- "vehicle_inspection_findings": "Key findings from mechanical inspection of involved vehicles."
- "spot_panchnama_summary": "Brief summary of the spot panchnama (measurements, evidence collected)."
- "cctv_findings": "Summary of CCTV analysis (speed, signal violation, etc.)."
- "evidence_analysis": "Analysis of how the evidence proves the accused's guilt."
- "applicable_bns_sections": ["List of BNS sections with brief description."]
- "applicable_mv_act_sections": ["List of Motor Vehicle Act sections with brief description."]
- "annexures": [ {{ "annexure_no": "", "document_name": "", "exhibit_mark": "" }} ]
- "final_opinion": "IO's final opinion: prima facie case established, recommendation to file chargesheet."
- "signature_block": "IO's name, rank, signature line, and date."

**Now, here is the complete investigation data. Use it to populate the JSON above:**

{case_json}

Return ONLY the JSON object, with no other text.
"""
        return prompt