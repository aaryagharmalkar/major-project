# Access Rules and File Lifecycle

## Access rules

### uploads
- Read access should be restricted to users who can access the associated case.
- Write access should be limited to authorized investigators or system services.
- Original uploads should generally be immutable after processing.

### ocr
- Read access should be available to authorized case participants.
- Write access should be limited to the OCR processing pipeline and trusted internal services.
- OCR artifacts should be treated as derived data, not as the canonical upload.

### exports
- Read access should be restricted to authorized case participants and authorized admins.
- Write access should be limited to document generation services.
- Exported files should be treated as generated artifacts tied to a case and version.

### avatars
- Read access should be public or authenticated-user-readable depending on product requirements.
- Write access should be limited to the owning user and authorized admin services.

### versions
- Read access should follow the access rules of the parent artifact.
- Write access should be restricted to trusted services and administrators.

## File lifecycle

### Upload stage
1. User uploads a file.
2. Metadata is recorded in the application database.
3. The file is stored in the appropriate bucket and path.
4. The system validates format and size.

### Processing stage
1. OCR or document processing services consume the uploaded file.
2. Derived artifacts are written to the ocr or exports bucket.
3. Processing status is updated in application metadata.

### Retention stage
- Keep source uploads for the case lifecycle.
- Preserve generated reports and charge sheets as long as the case remains active or archived.
- Use retention policies for obsolete versions and temporary exports.

### Deletion stage
- Deletion should be governed by explicit policy and audit logging.
- Prefer archival or version retention over destructive deletion where legal compliance requires it.
