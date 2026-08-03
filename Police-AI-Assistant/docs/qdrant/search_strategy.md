# Search Strategy

## Hybrid search readiness

The architecture should be prepared for hybrid retrieval using dense vector search plus keyword or BM25-style filtering.

### Recommended search flow
1. Apply case-level and document-type filters.
2. Run dense vector similarity search.
3. Optionally apply keyword-based matching over the same chunk set.
4. Re-rank results using metadata and recency.

## Filters

### Core filters
- `case_id`
- `document_type`
- `entity_type`
- `section`
- `case_status`
- `version`

### Example retrieval scenarios
- Evidence retrieval: filter by `case_id` and `entity_type = evidence`
- Timeline retrieval: filter by `case_id` and `entity_type = timeline`
- Witness retrieval: filter by `case_id` and `entity_type = witness`
- Medical report retrieval: filter by `case_id` and `document_type = medical_report`
- Charge sheet drafting: filter by `case_id` and `document_type = chargesheet` or relevant narrative chunks

## Search parameters
- Limit results by relevance and recency.
- Use a modest top-k value for interactive retrieval.
- Provide a fallback path for broad queries when vector search returns sparse results.

## Result ranking
- Prioritize high similarity scores.
- Prefer more recent or primary versions.
- Consider boosting chunks from authoritative documents like medical reports or charge sheets.
