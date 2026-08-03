# Supabase Storage Architecture

This document describes the proposed Supabase Storage architecture for the Police AI Assistant.

The design is intentionally case-centric and supports:
- uploaded PDFs
- OCR JSON
- generated charge sheets
- exported reports
- user avatars
- future document versions

This is design documentation only. No implementation code or storage migrations are included.

## Design Goals

- Keep all content organized by case identity.
- Separate user-facing assets from processed artifacts.
- Preserve auditability and traceability for legal workflows.
- Prepare for future versioning and access-control policies.
- Support secure, role-aware storage access through Supabase policies.
