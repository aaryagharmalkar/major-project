# Index Lifecycle

## Re-indexing

Re-indexing should be explicit and version-aware.

### Trigger conditions
- New document uploaded
- OCR content updated
- Embedding model changed
- Document version changed
- Case content reprocessed

### Recommended process
1. Create a new version marker for the affected content.
2. Build new chunks and embeddings.
3. Upsert the new points into Qdrant.
4. Mark previous points as stale or delete them after validation.

## Case deletion

Cases may need to be removed for privacy or retention reasons.

### Recommended approach
- Delete all points associated with the case_id from Qdrant.
- Remove any associated storage references and metadata.
- Record the removal in an audit trail.

## Collection maintenance

### Periodic maintenance
- Review collection size and point distribution.
- Rebuild or compact the collection if fragmentation increases.
- Validate payload schema compatibility after upgrades.

### Operational guidance
- Keep a backup or export of metadata for recovery.
- Avoid modifying vector values in place without a versioned re-index.
- Maintain a clear mapping between source documents and indexed chunks.
