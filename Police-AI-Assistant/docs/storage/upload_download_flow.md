# Upload and Download Flow

## Upload flow

1. Client requests access to upload a file for a case.
2. The application validates the case context and user authorization.
3. The file is uploaded to the appropriate bucket under the case-specific path.
4. Metadata is recorded, including:
   - case_id
   - document_type
   - original_filename
   - mime_type
   - checksum
   - uploaded_by
   - uploaded_at
5. Derived processing may be triggered, such as OCR or report generation.
6. Resulting artifacts are written to related buckets.

## Download flow

1. Client requests a file using the object path or storage reference.
2. The application validates access to the related case.
3. Supabase Storage returns the object if authorization is allowed.
4. The client receives the file or a signed URL if private access is required.

## Versioning strategy

- Keep the latest approved version as the canonical object.
- Store prior versions in the versions bucket or through Supabase versioning support.
- Use versioned paths for generated documents and exports.
- Preserve immutable snapshots for audit and compliance needs.

## Security considerations

- Use private buckets for sensitive evidence and case documents.
- Avoid exposing raw object paths directly in public-facing interfaces.
- Use signed URLs for time-limited access where appropriate.
- Apply least-privilege access rules and separate read/write permissions.
- Store sensitive metadata outside the file path where possible.
- Keep audit logging for uploads, downloads, deletions, and policy changes.
