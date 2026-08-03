# Chunking Strategy

## Goals
- Preserve semantic coherence.
- Keep chunks retrieval-friendly and small enough for vector search.
- Support both document-level and fact-level retrieval.

## Recommended approach
Use semantic chunking with a fallback size-based strategy.

### Chunk size targets
- Preferred chunk size: 250 to 400 tokens.
- Maximum chunk size: 600 tokens.
- Minimum chunk size: 80 tokens.

### Chunking rules
- Split by section first when a document has distinct blocks such as narrative, evidence, medical, witness, timeline, and charge sheet sections.
- If a section is very long, split at paragraph boundaries.
- Preserve sentence boundaries where possible.
- Avoid splitting between a heading and its following content.

## Chunk metadata
Each chunk should carry:
- case_id
- document_id
- document_type
- section
- chunk_id
- content
- source_path
- version
- created_at

## Chunk overlap
- Use a small overlap of 20 to 50 tokens between adjacent chunks.
- Overlap improves retrieval continuity for multi-chunk facts.

## Document-type-specific considerations
- Medical reports: preserve injury, diagnosis, and treatment sections.
- Witness statements: preserve statement context and chronology.
- Timeline events: maintain event ordering and date references.
- Charge sheets: preserve statutory references and allegations.
