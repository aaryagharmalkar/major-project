# Payload Schema

The payload schema should remain lightweight and query-friendly.

## Recommended payload fields

```json
{
  "case_id": "CASE-001",
  "document_id": "DOC-001",
  "document_type": "medical_report",
  "chunk_id": "CASE-001:DOC-001:medical:1",
  "section": "medical",
  "content": "Text content of the chunk",
  "source_path": "ocr/CASE-001/DOC-001/result.json",
  "source_bucket": "ocr",
  "entity_type": "medical_report",
  "entity_subtype": "injury_summary",
  "created_at": "2026-08-03T00:00:00Z",
  "updated_at": "2026-08-03T00:00:00Z",
  "version": "v1",
  "is_primary": true,
  "case_status": "active",
  "keywords": ["injury", "medical", "witness"],
  "participants": ["victim", "doctor"],
  "confidence": 0.92
}
```

## Field purposes
- `case_id`: Enables case-level filtering.
- `document_id`: Supports document-level retrieval.
- `document_type`: Helps route queries to specific evidence types.
- `section`: Distinguishes narrative, evidence, witness, medical, and timeline sections.
- `content`: The searchable text payload.
- `source_path`: Supports traceability back to source data.
- `entity_type`: Useful for retrieval over evidence, timeline, witness, or medical records.
- `keywords`: Precomputed token hints for hybrid retrieval.
- `participants`: Helpful for role-aware search and summarization.
- `confidence`: Useful if OCR or extraction confidence needs to influence ranking.

## Recommended indexing fields
- Filterable fields: `case_id`, `document_type`, `entity_type`, `section`, `case_status`
- Searchable field: `content`
- Metadata fields: `source_path`, `created_at`, `version`
