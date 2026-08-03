# Embedding Strategy

## Embedding provider abstraction

The system should use an embedding provider abstraction so the retrieval layer is not tightly coupled to any single model.

### Proposed abstraction
- `EmbeddingProvider`
- `embed_texts(texts)`
- `embed_query(text)`
- `get_model_name()`

### Supported provider categories
- local deterministic provider for development and testing
- cloud embedding provider for production
- optional reranker integration in the future

## Provider selection guidance
- Use a production-grade embedding model for semantic retrieval over case documents.
- Keep the same provider and dimension across indexing and querying for consistency.
- Store the provider name and model version in payload metadata.

## Embedding metadata
Each indexed point should include:
- embedding_model
- embedding_version
- embedding_provider
- embedding_dimension

## Retrieval considerations
- Use the same embedding strategy for both chunk indexing and query encoding.
- For charge sheet drafting and evidence retrieval, embed the user query with the same model used for indexing.

## Future extension
- Introduce a reranker later for better precision on legal and evidentiary queries.
