# Storage Buckets and Folder Hierarchy

## Recommended buckets

### 1. uploads
Purpose: Stores original user-uploaded documents.

Example structure:
```text
uploads/{case_id}/raw/{document_type}/{original_filename}
```

Examples:
```text
uploads/CASE-001/raw/fir/FIR_001.pdf
uploads/CASE-001/raw/medical/Medical_Report_01.pdf
```

### 2. ocr
Purpose: Stores OCR extraction outputs and derived text artifacts.

Example structure:
```text
ocr/{case_id}/{document_id}/result.json
```

Examples:
```text
ocr/CASE-001/Doc-001/result.json
ocr/CASE-001/Doc-002/result.json
```

### 3. exports
Purpose: Stores generated reports and downloadable documents.

Example structure:
```text
exports/{case_id}/chargesheets/{version}/chargesheet.pdf
exports/{case_id}/reports/{report_type}/{filename}
```

Examples:
```text
exports/CASE-001/chargesheets/v1/chargesheet.pdf
exports/CASE-001/reports/summary/summary_report.pdf
```

### 4. avatars
Purpose: Stores user profile images.

Example structure:
```text
avatars/{user_id}/{filename}
```

Examples:
```text
avatars/user-001/profile.png
avatars/user-002/profile.jpg
```

### 5. versions
Purpose: Stores historical versions of documents and generated artifacts.

Example structure:
```text
versions/{case_id}/{entity_type}/{entity_id}/{version}/{filename}
```

Examples:
```text
versions/CASE-001/documents/Doc-001/v2/FIR.pdf
versions/CASE-001/chargesheets/CS-001/v1/chargesheet.pdf
```

## Case-centric hierarchy

All business content should be organized under:
```text
{bucket}/{case_id}/...
```

This keeps content scoped to an investigation and simplifies future access policies.
