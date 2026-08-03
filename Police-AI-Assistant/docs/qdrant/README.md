# Qdrant Architecture Design

This document defines the proposed Qdrant architecture for the Police AI Assistant.

The design supports:
- multiple investigation documents
- case-level filtering
- evidence retrieval
- timeline retrieval
- witness retrieval
- medical report retrieval
- charge sheet drafting

This is design documentation only. No implementation code or Qdrant configuration is included.

## Design Principles

- Keep the vector store case-centric.
- Separate chunk content from structured metadata.
- Support both semantic and keyword-style retrieval in the future.
- Keep indexing operations auditable and reversible.
- Design for predictable re-indexing and case deletion workflows.
