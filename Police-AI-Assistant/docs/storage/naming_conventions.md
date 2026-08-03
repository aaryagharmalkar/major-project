# Naming Conventions

## General rules
- Use lowercase for bucket names.
- Use kebab-case or snake_case consistently.
- Prefer stable, human-readable names over random IDs.
- Preserve the original filename in metadata while storing a normalized object name.

## File naming pattern

### Uploaded documents
```text
{case_id}_{document_type}_{timestamp}_{original_filename}
```

Example:
```text
CASE-001_fir_20260803T153000_FIR.pdf
```

### OCR outputs
```text
{case_id}_{document_id}_ocr.json
```

Example:
```text
CASE-001_Doc-001_ocr.json
```

### Charge sheets
```text
{case_id}_chargesheet_{version}.pdf
```

Example:
```text
CASE-001_chargesheet_v1.pdf
```

### Reports
```text
{case_id}_{report_type}_{timestamp}.pdf
```

Example:
```text
CASE-001_summary_20260803T153000.pdf
```

### Avatars
```text
{user_id}_{profile_photo}.{ext}
```

Example:
```text
user-001_profile_photo.png
```

## Version naming
- Use semantic versioning-like values such as v1, v2, v3.
- For immutable artifacts, include a timestamp in the path, not only the filename.

## Metadata alignment
File names should remain readable, while object metadata should store:
- case_id
- document_id
- uploaded_by
- content_type
- checksum
- created_at
- version
