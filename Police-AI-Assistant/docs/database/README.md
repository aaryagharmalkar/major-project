# Supabase Database Schema Design

This document defines the proposed PostgreSQL/Supabase schema for the Police AI Assistant platform.

Scope includes:
- user authentication and profile management
- case management
- uploaded documents
- OCR results
- evidence
- timeline events
- witnesses
- victims
- accused persons
- generated charge sheets
- AI chat history
- audit logs

This is architectural documentation only. No SQL migrations are included.

## Design Principles

- Use Supabase-authenticated users as the root identity model.
- Keep tenant-like access boundaries explicit through ownership and role fields.
- Prefer immutable audit records for legal traceability.
- Use UUID primary keys for distributed-safe identity.
- Separate operational metadata from business content.
- Prepare for future Row Level Security (RLS) enforcement.
