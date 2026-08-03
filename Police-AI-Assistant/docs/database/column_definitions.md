# Column Definitions

## Conventions
- Use UUID columns for primary identity.
- Use timestamptz for all timestamps to preserve timezone correctness.
- Use text for flexible operational values and jsonb for semi-structured content.
- Prefer nullable foreign keys for optional associations.

## Common conventions
- id: UUID, primary key
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()
- status: text, used for workflow states such as draft, active, archived, completed
- metadata: jsonb, used for non-core context without a dedicated table

## Notes by domain
- profiles.role should be restricted to a controlled set such as investigator, analyst, admin, auditor.
- cases.status should be restricted to a controlled lifecycle set such as draft, active, in_review, closed.
- documents.document_type should reflect categories such as FIR, evidence_photo, witness_statement, medical_report.
- ocr_results.extracted_data should be stored as structured JSON for downstream indexing and analysis.
- charge_sheets.content should be a structured representation of the generated document, not just raw text.
