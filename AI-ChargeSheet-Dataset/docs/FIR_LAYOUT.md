# FIR Layout Reference

This document describes the target FIR layout architecture for the synthetic generation pipeline. It is based on the structure of a real Maharashtra-style FIR document and is intended to guide the template and schema redesign.

## Overall design principles

- The FIR is treated as a structured legal form with a fixed visual order.
- The template is section-driven rather than free-form.
- The generator never invents facts; it only maps validated MasterCase values into the FIR structure.
- The layout is reusable for future fictional FIR generation while staying visually consistent with the reference document.

## Page 1

### Purpose
The opening page establishes the identity of the case, the registration details, and the complainant's account.

### Sections
1. Header / document title
2. Registration details
3. Occurrence details
4. Place of occurrence
5. Complainant details
6. Accused details
7. Property details
8. Narrative / complaint body
9. Officer signature block

### Field ordering
1. FIR number
2. Date and time of registration
3. Police station
4. District and state
5. Crime category / offence type
6. Place of occurrence
7. Date and time of incident
8. Complainant name and details
9. Accused details
10. Property or evidence details
11. Narrative description
12. Signature / endorsement area

### Mandatory fields
- FIR number
- Police station
- District
- State
- Date of registration
- Incident date and time
- Complainant name
- Narrative description

### Optional fields
- Accused list
- Property details
- Additional evidence references
- Officer remarks

## Page 2

### Purpose
The continuation page carries the full narrative and any supporting details not completed on the first page.

### Layout
- Continuation heading
- Narrative continuation block
- Additional details or investigation notes
- Officer attestation area

### Content
- Continued complaint narrative
- Investigation notes
- Additional references to persons or evidence

## Additional pages

### Purpose
Additional pages are used for long narratives, annexures, or continuation content.

### Layout
- Page number or continuation marker
- Same header style as the first page
- Continued narrative or attached details

## Visual conventions

- Formal police letterhead or heading block
- Clearly separated form sections
- Narrative paragraphs under a defined heading
- Signature or endorsement areas near the bottom
- Continuation pages follow the same structure and style
