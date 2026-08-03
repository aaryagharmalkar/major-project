You are generating exactly one fictional but realistic Indian criminal investigation case.

Use the supplied schema and reference data as the only sources of truth.

SCHEMA:
{{SCHEMA}}

REFERENCE_DATA:
{{REFERENCE_DATA}}

PRIMARY CONSTRAINTS:
- Generate exactly one complete investigation.
- The output must match the MasterCase schema exactly.
- Return only valid JSON.
- Do not wrap the JSON in markdown, code fences, or commentary.
- Do not include explanations, notes, or comments.
- Do not invent any field that is not present in the schema.
- Do not omit required fields.
- Keep every ID unique within the case.
- Keep every fact internally consistent across all nested objects.
- Never change a name, date, place, or identifier once established.
- Never create contradictions between FIR, witness statements, medical report, IO notes, seizure memo, FSL report, and charge sheet.
- Never use placeholder values or obviously fake names.
- Use realistic Indian names, places, police designations, hospitals, and legal references from the supplied reference data.
- Do not fabricate police station names or legal sections if they are not present in the reference data.

CASE SEED:
- Crime category: {{CRIME_CATEGORY}}
- State: {{STATE}}
- District: {{DISTRICT}}
- City or locality: {{LOCATION}}
- Investigation style: {{INVESTIGATION_STYLE}}
- Case outcome: {{CASE_OUTCOME}}

CONSISTENCY RULES:
- If a person is the victim in the FIR, the same person must remain the victim in every document and nested record.
- If a person is the accused in one place, do not rename or replace that person elsewhere.
- If a witness is identified by one relationship, keep that relationship consistent across the case.
- If an evidence item is recovered, it must appear in the timeline, seizure details, and any FSL-related record if forensic testing is required.
- If a medical report is included, its subject_person_id must refer to the same victim or examined person used throughout the case.
- If an arrest occurs, it must follow a logical timeline after the incident and investigation steps that justify it.
- If no arrest is appropriate, represent that clearly in the case structure by leaving arrest-related collections empty or null as allowed by the schema.
- Dates and times must follow a plausible chronological sequence.
- The incident date should not be after the FIR date.
- Investigation events must be ordered logically from incident to reporting, evidence collection, medical examination, forensic processing, and final decision.
- The final investigation status must be consistent with the evidence, timeline, and legal sections selected.

NARRATIVE QUALITY:
- Write rich, realistic narrative content for descriptions, summaries, remarks, and entries.
- Avoid one-line summaries when the schema allows descriptive text.
- Make the case feel like a genuine Indian investigation file while remaining completely fictional and privacy-safe.
- Vary motives, evidence types, witness relationships, and investigation outcomes across generated cases.
- Keep the investigation legally plausible and operationally realistic.

DOCUMENT-LEVEL REQUIREMENTS:
- FIR registration must be explicit and consistent with the case information.
- The incident description must clearly connect the victim, accused, location, and nature of offence.
- The victim, accused, witnesses, and investigating officer must remain consistent across all nested records.
- The timeline must contain a coherent sequence of events with matching timestamps and descriptions.
- Evidence collected must align with the offence category and the narrative.
- Arrest details, if present, must contain lawful and plausible grounds and officer details.
- Seizure details must describe what was seized, from where, by whom, and with witness support when applicable.
- Spot panchanama must describe scene observations that match the incident location.
- Medical examination details must match the victim’s injuries and the incident narrative.
- FSL findings must match only the evidence that logically requires forensic examination.
- Case diary entries must reflect the investigation history and avoid contradicting earlier facts.
- Applicable BNS sections must be realistic, consistent, and supported by the facts in the case.

OUTPUT REQUIREMENTS:
- Output a single JSON object only.
- The JSON must validate against the MasterCase schema exactly.
- Preserve schema field names exactly as provided.
- Use the supplied reference data to populate names, locations, hospitals, police roles, and related entities.
- Ensure all nested objects are complete and coherent.
- Return the final JSON and nothing else.

When generating the case, prefer diversity in:
- crime category
- location
- motive
- evidence profile
- witness relationships
- investigative outcome

If any schema field allows null or an empty collection, use that only when it is logically appropriate.

Now generate one complete MasterCase JSON object that satisfies all of the above.
