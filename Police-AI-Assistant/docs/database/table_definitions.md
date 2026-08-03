# Table Definitions

## 1. profiles
Purpose: Stores application-level profile information for authenticated users.

### Recommended columns
- id: UUID, primary key
- auth_user_id: UUID, unique, references Supabase auth.users
- display_name: text, nullable
- role: text, default 'investigator'
- avatar_url: text, nullable
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- auth_user_id -> auth.users.id

### Index recommendations
- unique index on auth_user_id
- index on role

### Relationships
- One profile belongs to one auth user.
- One profile may own many cases.

---

## 2. cases
Purpose: Represents an investigation case workspace.

### Recommended columns
- id: UUID, primary key
- owner_user_id: UUID, nullable, references profiles.id
- case_number: text, unique, nullable
- title: text, not null
- status: text, not null
- severity: text, nullable
- summary: text, nullable
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- owner_user_id -> profiles.id

### Index recommendations
- unique index on case_number
- index on owner_user_id
- index on status
- index on created_at

### Relationships
- One case belongs to one owner user.
- One case has many documents, evidence items, timeline events, participants, and chat messages.

---

## 3. documents
Purpose: Tracks uploaded evidence and case documents.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- uploaded_by_user_id: UUID, nullable, references profiles.id
- document_type: text, not null
- storage_path: text, not null
- original_filename: text, not null
- mime_type: text, nullable
- checksum: text, nullable
- file_size_bytes: bigint, nullable
- uploaded_at: timestamptz, default now()
- processed_at: timestamptz, nullable

### Primary key
- id

### Foreign keys
- case_id -> cases.id
- uploaded_by_user_id -> profiles.id

### Index recommendations
- index on case_id
- index on uploaded_by_user_id
- index on document_type
- index on uploaded_at

### Relationships
- One document belongs to one case.
- One document may have zero or one OCR result.

---

## 4. ocr_results
Purpose: Stores OCR extraction results for uploaded documents.

### Recommended columns
- id: UUID, primary key
- document_id: UUID, not null, references documents.id
- case_id: UUID, not null, references cases.id
- extracted_data: jsonb, nullable
- raw_text: text, nullable
- model_name: text, nullable
- confidence_score: numeric, nullable
- created_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- document_id -> documents.id
- case_id -> cases.id

### Index recommendations
- index on document_id
- index on case_id
- GIN index on extracted_data if JSONB search is needed

### Relationships
- One OCR result belongs to one document.
- OCR result belongs to the same case as the document.

---

## 5. evidence_items
Purpose: Captures physical or digital evidence associated with a case.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- title: text, not null
- category: text, nullable
- description: text, nullable
- status: text, default 'logged'
- collected_at: timestamptz, nullable
- chain_of_custody: text, nullable
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id

### Index recommendations
- index on case_id
- index on status
- index on category

### Relationships
- One evidence item belongs to one case.
- May be linked to documents or timeline events later.

---

## 6. timeline_events
Purpose: Stores chronological events relevant to the case.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- occurred_at: timestamptz, not null
- event_type: text, not null
- description: text, not null
- source: text, nullable
- created_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id

### Index recommendations
- index on case_id
- index on occurred_at
- composite index on case_id + occurred_at

### Relationships
- One timeline event belongs to one case.

---

## 7. witnesses
Purpose: Stores witness information for the case.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- full_name: text, not null
- contact_info: text, nullable
- statement_summary: text, nullable
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id

### Index recommendations
- index on case_id
- index on full_name

### Relationships
- One witness belongs to one case.

---

## 8. victims
Purpose: Stores victim information for the case.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- full_name: text, not null
- contact_info: text, nullable
- injury_summary: text, nullable
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id

### Index recommendations
- index on case_id
- index on full_name

### Relationships
- One victim belongs to one case.

---

## 9. accused_people
Purpose: Stores accused persons associated with the case.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- full_name: text, not null
- alias: text, nullable
- status: text, nullable
- legal_status: text, nullable
- created_at: timestamptz, default now()
- updated_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id

### Index recommendations
- index on case_id
- index on full_name
- index on status

### Relationships
- One accused person belongs to one case.

---

## 10. charge_sheets
Purpose: Stores generated charge sheet versions.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, not null, references cases.id
- generated_by_user_id: UUID, nullable, references profiles.id
- version: text, not null
- content: jsonb, not null
- status: text, default 'draft'
- generated_at: timestamptz, default now()
- created_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id
- generated_by_user_id -> profiles.id

### Index recommendations
- index on case_id
- index on generated_by_user_id
- index on generated_at

### Relationships
- One charge sheet belongs to one case.
- One charge sheet may be generated by one user profile.

---

## 11. chat_messages
Purpose: Stores AI conversation history for cases.

### Recommended columns
- id: UUID, primary key
- case_id: UUID, nullable, references cases.id
- sender_user_id: UUID, nullable, references profiles.id
- role: text, not null
- message_content: text, not null
- metadata: jsonb, nullable
- created_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- case_id -> cases.id
- sender_user_id -> profiles.id

### Index recommendations
- index on case_id
- index on sender_user_id
- index on created_at

### Relationships
- One message belongs to one case or may be global/system scoped.
- One message is authored by one user profile if applicable.

---

## 12. audit_logs
Purpose: Stores immutable operational and compliance events.

### Recommended columns
- id: UUID, primary key
- actor_user_id: UUID, nullable, references profiles.id
- case_id: UUID, nullable, references cases.id
- action: text, not null
- entity_type: text, not null
- entity_id: UUID, nullable
- details: jsonb, nullable
- created_at: timestamptz, default now()

### Primary key
- id

### Foreign keys
- actor_user_id -> profiles.id
- case_id -> cases.id

### Index recommendations
- index on actor_user_id
- index on case_id
- index on entity_type
- index on created_at

### Relationships
- Audit logs record actions performed by users or system components.
- They should be append-only and not updated in place.
