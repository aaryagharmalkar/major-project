# Collection Design

## Recommended collection strategy

Create a single primary collection for all case-derived retrieval content, with a strong case-centric payload schema.

### Collection name
- `police_case_content`

### Why a single primary collection
- Simplifies cross-document search across a case.
- Enables case-scoped filtering and consistent metadata.
- Supports future hybrid retrieval and multi-tenant expansion.

## Collection-level characteristics

### Vector configuration
- Dense vector field for semantic retrieval.
- Optional sparse vector support later for keyword-style search.

### Recommended dimensions
- Use a configurable embedding dimension that matches the embedding provider.
- Keep the dimension stable across all indexed documents.

### Storage considerations
- Store only indexed chunk content plus metadata required for retrieval.
- Keep the payload lean to optimize memory and query performance.

## Document model
Each indexed point should represent one chunk, not an entire document.

### Core fields
- `id`: unique point identifier
- `vector`: dense embedding
- `payload.case_id`
- `payload.document_id`
- `payload.document_type`
- `payload.chunk_id`
- `payload.section`
- `payload.content`
- `payload.source_path`
- `payload.created_at`

## Collection maintenance
- Rebuild the collection when embedding model changes.
- Use a versioned metadata field for compatibility.
- Keep collection-level naming consistent across environments.
