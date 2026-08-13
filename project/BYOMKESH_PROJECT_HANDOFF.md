# BYOMKESH Engineering Handoff

> **Scope and evidence.** This is a code-derived handoff for the repository state inspected on 14 August 2026. It describes the active typed pipeline in `src/` and separately calls out retained legacy modules. It does not contain secrets and makes no claim that is not supported by the repository. Where a fact cannot be established from code/artifacts, it says so explicitly.

## 1. Purpose: intended system vs implemented system

BYOMKESH is an AI-assisted, provenance-preserving investigation-to-charge-sheet pipeline. The intended users are investigating officers/reviewers and engineers operating their workflow. It takes a directory of case documents (currently PDF/JPEG/PNG are OCR-capable), produces typed intermediate artifacts, evaluates evidence quality, creates review-oriented legal findings, and emits a ReportLab charge-sheet PDF.

The intended flow is:

```text
case documents -> intake -> OCR -> typed parsing -> knowledge graph
-> canonical investigation -> evidence validation -> case context
-> legal findings -> ChargeSheetData -> deterministic presentation -> PDF
```

The LLM role is intentionally narrow: Gemini is used for raw OCR and document-local JSON extraction. The production legal reasoner is deterministic unless an explicitly injected `LegalReasoningClient` is supplied. Deterministic Python code controls IDs, checksums, classification, graph/canonical projection, validation, legal-reference loading, presentation, review lifecycle, artifacts, and rendering.

**What current code actually implements:** the typed pipeline is composed in `src/workflow/production.py`; the CLI is `python -m src.main`. It requires Gemini configuration for both OCR and parsing, and a version-pinned local legal-reference dataset for production. It generates a review PDF only when validation is not `final_blocked`. It does **not** make a final legal determination: legal findings retain status, confidence, evidence strength, evidence mappings, and review flags.

**Not determinable from the current repository:** deployed UI/API, authentication/authorization, database storage, real production deployment, user onboarding, or an institutional approval process.

## 2. Repository map

```text
project/
├── src/                         # active implementation (and retained legacy modules)
│   ├── main.py                  # typed CLI entry point
│   ├── config.py                # environment-backed configuration
│   ├── workflow/                # immutable context, stage registry/engine, composition root
│   ├── intake/                  # safe upload validation, SHA-256, manifest, storage
│   ├── extraction/              # OCR port, Gemini OCR adapter, persisted OCR/resume
│   ├── parsers/                 # Gemini JSON parsing, per-document parsers, artifacts
│   ├── knowledge_graph/         # graph nodes/edges and deterministic graph builder
│   ├── normalization/           # canonical investigation projections and conflicts
│   ├── validation/              # completeness/support/conflict/timeline/provenance validation
│   ├── context/                 # compact legal/presentation context
│   ├── legal/                   # versioned legal refs, evidence mapper, legal findings
│   ├── chargesheet/             # schema, population, validation, artifacts, presentation
│   ├── rendering/if5_renderer.py# active ReportLab renderer
│   └── review/                  # draft/review/approve/finalize lifecycle
├── tests/                       # 18 test modules; no external API calls in fixtures
├── references/legal/bns_sections.json # local versioned BNS reference dataset
├── docs/form_if5/               # supplied-form observations and mapping notes
├── BYOMKESH_E2E_CASE_001/       # local PDF fixture corpus
├── dummy_case/                  # legacy JSON fixture corpus
├── output/                      # generated case artifacts (working-tree artifacts)
├── requirements.txt
└── BYOMKESH_PROJECT_HANDOFF.md  # this document
```

Retained, **non-production-composed** modules are `src/llm.py`, `loader.py`, `prompt_builder.py`, `pdf_generator.py`, `models.py`, `evidence_graph/models.py`, and most of `rendering/if5_layout.py`, `pagination.py`, `styles.py`, `template_mapping.py`. `run_production_workflow()` states that no legacy code participates; `test_end_to_end_pipeline.py` protects against legacy charge-sheet imports in the production CLI.

### Active module navigation index

| Directory / module | Responsibility and principal callers |
|---|---|
| `workflow/context.py`, `state.py`, `engine.py`, `registry.py`, `stage.py` | Immutable cross-stage payload, lifecycle records, generic execution, registration, and base contract. Called by every stage and composed from `workflow/production.py`. |
| `workflow/production.py` | Sole production composition root: builds every client/provider/stage in required order. Called by `main.py`. |
| `intake/checksum.py`, `file_validator.py`, `document_classifier.py` | Streaming hashing, basic safe file validation, deterministic filename/MIME classification. Called by `UploadManager`. |
| `intake/storage_layout.py`, `upload_manifest.py`, `upload_manager.py`, `document_intake_stage.py` | Case directory naming, typed manifest, original copying/duplicate handling, workflow adapter. Output feeds OCR. |
| `extraction/ocr_client.py`, `ocr_result.py`, `ocr_exceptions.py` | Provider abstraction, raw OCR contract, typed failure taxonomy. Used by `OCRStage` and test fakes. |
| `extraction/gemini_ocr.py` | Google GenAI OCR provider; the only production OCR network adapter. Instantiated in production composition. |
| `extraction/ocr_artifacts.py`, `ocr_stage.py` | Persist/load/revalidate OCR artifacts and attach results/metrics, including resume behavior. Output feeds parser stage. |
| `parsers/base_parser.py` | Parser port, Gemini parser adapter, prompt/schema/entity support validation, retry behavior, unknown fallback. Base for all parsers. |
| `parsers/*_parser.py` | One typed parser configuration per document model; selected only through `parser_registry.py`. |
| `parsers/parser_registry.py`, `parser_stage.py`, `parser_artifacts.py` | Registry construction, stage orchestration, JSON persistence. Parsed output feeds graph. |
| `knowledge_graph/graph_models.py`, `entity_resolver.py`, `graph_registry.py`, `graph_builder.py`, `graph_artifacts.py`, `graph_stage.py` | Graph contract, identity key/matching, document-to-graph mapping registry/builder, persistence/stage. Feeds canonicalization. |
| `normalization/canonical_models.py`, `fact_projection.py`, `entity_projection.py`, `evidence_projection.py`, `timeline_projection.py` | Canonical fact/entity/evidence/timeline model and deterministic projections. Called by builder. |
| `normalization/conflict_registry.py`, `canonical_builder.py`, `canonical_artifacts.py`, `canonical_stage.py` | Conflict tracking, assembly, persistence/stage. Feeds validation/context. |
| `validation/*.py` | Validation models, completeness/support/conflict/timeline checks, `EvidenceValidator`, artifacts/stage. Consumes canonical only. |
| `context/case_context.py`, `case_context_builder.py`, `context_artifacts.py`, `context_stage.py` | Downstream compact context model, deterministic selection, persistence/stage. Feeds legal and charge-sheet stages. |
| `legal/legal_rules.py`, `evidence_mapper.py`, `legal_findings.py`, `legal_reasoner.py`, `legal_artifacts.py`, `legal_stage.py` | Version-pinned reference data, finite evidence allow-list, legal contract/reasoner/artifacts/stage. Feeds charge sheet. |
| `chargesheet/form_if5_schema.py`, `chargesheet_populator.py`, `chargesheet_validator.py`, `presentation.py` | Output data contract, deterministic projection, second-line validation, safe recursive human formatting. Consumed by stage/renderer. |
| `chargesheet/chargesheet_artifacts.py`, `chargesheet_stage.py` | Persist data/review state and render draft only where allowed. |
| `review/review_models.py`, `review_service.py` | Approval/audit/version/hash lifecycle and final PDF safety. The workflow creates a draft; external caller code would operate later transitions. |
| `rendering/if5_renderer.py` | Active ReportLab PDF renderer called by charge-sheet stage/review finalization. |

Supporting `__init__.py` files are package markers/exports. `infrastructure/` and `repositories/base.py` are present but no production-composition dependency was identified from the inspected code.

## 3. Execution architecture and stages

`create_production_registry()` fixes stage order to:

| Stage | Class | Input -> output | API? | Failure/determinism |
|---|---|---|---|---|
| Intake | `DocumentIntakeStage` | `IncomingUpload` -> `SourceDocument`, `UploadManifest` | No | deterministic; invalid/duplicate entries are recorded; critical errors stop engine |
| OCR | `OCRStage` | valid OCR-capable document -> `OCRResult` | Gemini unless valid resume artifact | provider errors fail critical stage; deterministic reuse checks |
| Parsing | `ParserStage` | `OCRResult` -> typed `ParsedDocument` | Gemini unless a test client is injected | two schema attempts by default, then critical failure |
| Graph | `GraphStage` / `GraphBuilder` | parsed documents -> `InvestigationKnowledgeGraph` | No | deterministic projection |
| Canonical | `CanonicalInvestigationStage` | graph -> `CanonicalInvestigation` | No | deterministic projection/conflict registry |
| Validation | `EvidenceValidationStage` | canonical -> `ValidationReport` | No | does not mutate investigation |
| Context | `CaseContextStage` | canonical + report -> `CaseContext` | No | deterministic selection |
| Legal | `LegalReasoningStage` | context -> `LegalFindings` | No in normal production composition | may use injected client; constrained/validated |
| Charge sheet | `ChargeSheetStage` | context + findings -> JSON/review/PDF | No | `final_blocked` writes data but no draft PDF |

The generic `WorkflowEngine` registers stage state, skips already completed/non-runnable stages, catches exceptions into `StageExecutionRecord`, stops only on critical failure, and returns the latest immutable `WorkflowContext` plus a report. Stages return replacements via `WorkflowContext.with_updates`; they must not return another case ID.

## 4. Data flow and preservation contracts

```text
SourceDocument(id, sha256, storage_key)
  -> OCRResult(document_id, pages, raw_text, OCRMetadata)
  -> ParsedDocument(document_id, ocr_text_sha256, ParseMetadata)
  -> GraphNode/GraphEdge(GraphProvenance -> SourceReference)
  -> CanonicalFact / typed canonical entities
  -> CaseContext (provenance-carrying compact view)
  -> LegalFinding(EvidenceMapping allow-list)
  -> ChargeSheetData(ChargeSheetField provenance contract)
  -> formatted strings only -> ReportLab PDF
```

At each typed boundary document IDs are retained. Upload SHA-256 identifies original bytes; parsed documents carry a SHA-256 of OCR text; graph provenance carries source document ID, parser name, timestamp and confidence; each `CanonicalFact` requires source document IDs and graph references; populated/review-required charge-sheet fields require `SourceReference` values.

Intentional transformations/discarding: OCR turns binary content into text; parsing extracts only fields defined by document schemas; context is explicitly described in code as a “compact … view—not a source of truth”; renderer receives strings/rows, not source objects. Unknown documents retain raw text through `UnknownDocument`. No code path should turn unavailable data into populated data.

## 5. Key models and schemas

All `DomainModel` subclasses are frozen Pydantic v2 models with `extra="forbid"` and whitespace stripping.

| Area | Main models and meaning |
|---|---|
| Common | `SourceLocation`, `SourceReference(document_id, location, excerpt, confidence)`, `ProvenancedValue`; enums include populated/unavailable/conflict/review status and confidence/review flags. |
| Intake | `SourceDocument`: immutable metadata, UUID, case ID, safe original name, storage key, MIME type, SHA-256, size, detected/declared type, lifecycle states. `UploadManifestEntry` and `UploadManifest` retain acceptance/duplicate/rejection outcome. |
| OCR | `OCRPage(page_number,text,confidence)`, `OCRMetadata(provider,model,mime,time,usage,cost,provider_metadata)`, `OCRResult(document_id,pages,raw_text,confidence,warnings,language,metadata)`. |
| Parsed documents | `ParsedDocument(document_id,document_type,ocr_text_sha256,parse_metadata)` plus FIR, Complaint, MedicalReport, PostmortemReport, FSLReport, WitnessStatement, CaseDiary, ArrestMemo, SeizureMemo, SpotPanchnama, VehicleInspection, SitePlan, CCTVMetadata and `UnknownDocument`. Fields are optional unless document identity/metadata requires otherwise. |
| Graph | `GraphNode(node_type,label,attributes,roles,provenance)`, `GraphEdge(source,target,relationship_type,provenance)`, `GraphProvenance`, `InvestigationKnowledgeGraph`. Node types include person/vehicle/evidence/event/document/findings/property/location. |
| Canonical | `CanonicalFact(value,source_document_ids,references,source_path,confidence,extraction_method,timestamp)`, canonical person/vehicle/location/evidence/document/timeline models, `CanonicalConflict`, `MissingInformation`, and `CanonicalInvestigation`. |
| Validation | `ValidationIssue`, `ValidationRules`, `ValidationReport`; disposition is `draft_allowed`, `review_required`, or `final_blocked`. |
| Legal | `LegalReference`, dataset/provider models; `EvidenceMapping`; `LegalFinding`; `LegalFindings`. Finding statuses are `supported`, `insufficient_evidence`, `conflicted`, `review_required`. |
| Charge sheet | `ChargeSheetField`, `IF5Row`, `ChargeSheetLegalFinding`, `ChargeSheetReviewItem`, `ChargeSheetData`. `content_hash` is stable SHA-256 over JSON data/version. |
| Review | `ChargeSheetReview`, `ReviewEvent`, status/event enums, governed by `ReviewService`. |

Role semantics are deliberately explicit in `knowledge_graph.graph_models.PersonRole`: `COMPLAINANT`, `VICTIM`, `ACCUSED`, `WITNESS`, `POLICE_OFFICER`, `DOCTOR`. A merged graph person can have multiple explicit roles only when identity resolution identifies one person; separate names are not silently merged.

## 6. Intake and artifact storage

`FileValidator` accepts PDF/JPEG/PNG/DOCX/MP4/MOV/WAV, validates existence, size, extension and basic signatures. `DeterministicDocumentClassifier` uses filename keywords and MIME type; it uses no AI. `UploadManager` validates safe filenames, detects SHA-256 duplicates, copies accepted originals to UUID-named files, and writes `processed/upload_manifest.json`.

Generic layout:

```text
output/CASE_<case UUID hex>/
├── originals/<document UUID>.<ext>
└── processed/
    ├── upload_manifest.json
    ├── ocr/<stem>_<id>_{raw.txt,metadata.json,OCRResult.json}
    ├── parsed/<stem>_<id>.json
    ├── graph/{investigation_graph,nodes,edges}.json
    ├── canonical/{canonical_investigation,timeline,evidence,conflicts}.json
    ├── validation/{validation_report,conflicts,missing_information}.json
    ├── context/case_context.json
    ├── legal/{legal_findings,evidence_mapping}.json
    └── chargesheet/{draft/ChargeSheet_vN_data.json,draft/ChargeSheet_vN_review.pdf,review_state.json,final/...}
```

The current working tree contains a populated `CASE_37e9…` artifact set. These are generated artifacts, not source-of-truth fixtures.

## 7. Gemini OCR integration

`GeminiOCRClient` uses the current `google-genai` SDK import style: `from google import genai`, then `genai.Client(api_key=...)`. Supported input MIME types are `application/pdf`, `image/png`, `image/jpeg`. The default model is `gemini-flash-latest` (CLI/config overrideable).

OCR uses temperature 0 and `response_mime_type="application/json"` plus a JSON schema requiring ordered pages, language and warnings. PDFs are uploaded through `client.files.upload`, polled up to 30 seconds while state is `PROCESSING`, sent to `client.models.generate_content`, then deleted in `finally`. Images are passed as `google.genai.types.Part.from_bytes`. It prefers `response.parsed` (dict or Pydantic `model_dump`) and only falls back to `response.text`, including fenced JSON stripping. It requires nonempty `pages`; malformed response JSON raises `OCRResponseError`, other provider failures become `OCRProviderError`.

There is no explicit OCR retry/backoff policy for 429/503 errors. These are caught as provider errors and fail the stage; rerunning/resume is the available workflow behavior. There is no explicit 404/model-availability branch. Temporary remote PDF deletion is attempted after generation; if upload itself fails, no object is available to delete. Tests exercise SDK PDF upload/delete, inline image parts, `response.parsed`, and malformed/fenced JSON.

The repository’s tests and code reflect a migration to `google-genai`; no deprecated `google.generativeai` import is present in the active OCR/parser adapters. Exact historical migration commits are **not determinable from the six available Git commit messages**.

## 8. OCR resume safety

CLI flag: `--resume`. `create_workflow_context` loads the case manifest only in resume mode. Intake reuses a manifest only when the current valid-upload SHA-256 multiset exactly equals persisted accepted-document checksums. Otherwise it performs fresh intake.

For each pending OCR document, `OCRStage` first checks that the stored original checksum equals `SourceDocument.sha256`, then loads all three OCR artifacts. Loading validates JSON schemas, result document ID, computed page count, metadata equality, raw text equality and `raw_text == "\n\n".join(page.text)`. If document IDs were regenerated but a byte-identical prior original exists in the same case’s `originals/`, it searches matching extension/UUID candidates, verifies checksum, validates that candidate’s artifact, and only then rebinds the result to the current ID. Bad/missing/stale artifacts cause a fresh OCR call rather than reuse.

Safety guarantee: resume never reuses an OCR result merely by filename or case; it requires current/candidate bytes and complete validated artifacts. It does not resume parsing, graph or later stage artifacts; after a parser failure, valid OCR can be reused and parsing retried.

## 9. Parsing

`BaseDocumentParser` builds a schema-constrained prompt containing the typed model JSON schema and raw OCR transcription. It says to use only explicitly stated information, null/empty lists for unavailable fields, and not infer facts/legal sections. Gemini parsing requests JSON at temperature 0. Pydantic validates results; `max_attempts=2` retries parse/validation failures.

`supported_entity_fields` causes normalized returned names/identifiers to be checked against normalized OCR text. Unsupported/invented entities are rejected. The registry selects document-specific parsers for FIR, complaint, medical/postmortem/FSL, witness, diary, arrest, seizure, spot, vehicle, site-plan and CCTV metadata; unknown types use `UnknownDocumentParser`, retaining raw text without interpretation. Individual parser files primarily specify `document_type`, output model, supported fields and type-specific instructions.

## 10. Graph, canonicalization, and information preservation

`GraphBuilder` creates one document node for every parsed document and preserves all parser-exposed nonempty fields in its `attributes`. Registered mappers create people, vehicles, locations, timeline events, medical/FSL findings and recovered property, linking them with `MENTIONS`, `ASSERTED_BY`, `SUPPORTED_BY`, `PART_OF`, `RECOVERED_FROM`, `COLLECTED_BY`, `EXAMINED_BY`, etc. Every node/edge has graph provenance.

Identity keys are normalized by `EntityResolver`; person fuzzy matching is used only when exactly one candidate matches. Duplicate nodes merge provenance and union roles. FIR/Complaint map complainant, accused and victim separately; tests cover matching explicit identity role union and different explicit identities remaining distinct.

Canonical projections in `normalization/` convert graph material into typed canonical objects without LLM inference. `project_fact` preserves graph provenance/source path; entity/evidence/timeline projections construct role-specific collections and ordered events. `CanonicalConflict` carries competing `CanonicalFact` values and resolution status; missing information is retained, not fabricated. `CaseContextBuilder` selects all canonical role collections, documents, findings/evidence, locations, timeline, actions, validation issues and references for legal/presentation use.

## 11. Evidence validation and legal reasoning

`EvidenceValidator` is read-only. It runs completeness, expected-document support, unresolved canonical conflict, suspicious chronology, provenance/unsupported fact, low-confidence and unresolved-entity checks. Any canonical fact lacking valid source IDs/references becomes a **critical** unsupported-fact issue. Critical issues yield `final_blocked`; errors/conflicts/timeline/unresolved entities yield `review_required`; otherwise `draft_allowed`.

`LocalLegalReferenceProvider.load()` requires both `LEGAL_REFERENCE_PATH` and `LEGAL_REFERENCE_VERSION`, validates the JSON dataset and pins every record to the dataset version. The supplied file has version `bns-2023-2024-07-01` and one BNS section 115 reference.

`EvidenceMapper` creates the legal evidence allow-list only from current context facts/evidence/timeline. Deterministic `LegalReasoner` marks a reference `supported` only if evidence exists and required-element text is found; it marks `conflicted` for context conflicts and `insufficient_evidence` otherwise. It preserves evidence strength/confidence and sets `review_required` for non-supported statuses. `final_blocked` returns no findings.

An optional injected legal client is constrained: its disposition must equal the context disposition, its sections must exist in the local provider, and every supporting mapping must be in the allow-list. Invalid output is retried twice, then returns empty review-required findings. Thus an LLM cannot introduce a legal section or evidence mapping; neither the populator nor renderer upgrades `insufficient_evidence` to supported/proven.

## 12. Charge-sheet and presentation layer

`ChargeSheetPopulator` deterministically projects `CaseContext` and `LegalFindings` into `ChargeSheetData`. `ChargeSheetField` rejects populated/review-required values without provenance and rejects values for unavailable/not-applicable fields. `ChargeSheetValidator` performs a second provenance/review pass. `ChargeSheetStage` writes data/review state; it avoids draft PDF creation for `final_blocked`.

Section semantics:

| Section | Projection |
|---|---|
| Case Summary | concise occurrence/date/location/roles/vehicle overview from context |
| Detailed Facts | occurrence-event descriptions |
| Investigation Conducted | source-supported document examination/recording activities, excluding narrative attributes |
| Evidence Analysis | groups available documentary/material/medical/forensic/vehicle/witness evidence plus collection/custody details |
| Legal Findings | section/offence/status/strength/confidence/review and supporting/contradicting evidence |
| Annexure Index | document type, document ID and every non-null document attribute |
| Review items | validation/canonical conflicts and missing information |

`chargesheet/presentation.py` is deliberately source-neutral and deterministic. `format_value` recursively renders mappings as labels, sequences as bullets, `None` as “Not Available”, booleans as Yes/No, dates/datetimes and ISO date/datetime strings in readable dates; it removes raw Python `repr` syntax. It is used for nested document attributes, evidence, legal evidence and annexures. `document_action_statement` maps generic document types to factual investigative actions and suppresses narrative fields. No LLM is used for formatting, avoiding a final hallucination/data-loss boundary.

## 13. ReportLab and review lifecycle

`IF5Renderer` uses ReportLab Platypus (`BaseDocTemplate`, `Frame`, `PageTemplate`, `Paragraph`, `Table`, `ListFlowable`, `KeepTogether`). A4 margins are 15 mm left/right, 22 mm top, 17 mm bottom. It defines title/status/section/body/small/table-header styles, case-information table, navy table headers, alternating table rows, wrapped HTML-escaped paragraphs, section rules, evidence lists, legal-finding table, annexure table, and a forced page break before annexures.

Page chrome is drawn with `onPageEnd` so continued tables cannot paint over it: header “BYOMKESH AI - CHARGE SHEET” and `Page N` footer on every page. Table headings are held with their table when feasible; large tables continue with repeated headers. Review PDFs say `DRAFT / REVIEW COPY`; finalized PDFs say `FINALIZED / APPROVED`.

`ReviewService` governs draft -> review_required -> approved/rejected/draft revision -> finalized. Data version plus content hash must match on every transition; final-blocked data cannot be approved/finalized, final PDF cannot overwrite an existing final artifact, and finalized records are immutable.

## 14. Configuration

`.env` is loaded by `python-dotenv` at import of `src.config`.

| Variable | Required by active CLI? | Default | Used for |
|---|---:|---|---|
| `GEMINI_API_KEY` | Yes, unless `--gemini-api-key` | none | OCR and parser client creation |
| `GEMINI_MODEL` | No | `gemini-flash-latest` | OCR/parser model |
| `LEGAL_REFERENCE_PATH` | Yes for production registry | none | local legal JSON dataset |
| `LEGAL_REFERENCE_VERSION` | Yes for production registry | none | strict dataset version pin |
| `MAX_UPLOAD_FILE_SIZE_BYTES` | No | 104857600 | per-file intake cap |
| `MAX_CASE_UPLOAD_SIZE_BYTES` | No | 524288000 | aggregate intake cap |
| `LLM_PROVIDER`, `GROQ_API_KEY`, `GROQ_MODEL` | Not used by typed production path | groq / llama default | retained legacy `llm.py` only |
| `INPUT_DIR`, `OUTPUT_DIR` | Not used by typed CLI args | dummy_case / output | retained config defaults |

Example only: `LEGAL_REFERENCE_PATH=references/legal/bns_sections.json`, `LEGAL_REFERENCE_VERSION=bns-2023-2024-07-01`. Never put secrets in this document or Git.

## 15. Running and debugging commands

PowerShell:

```powershell
cd 'C:\Github\Major Project\project'
..\.venv\Scripts\Activate.ps1
py -3.13 -m pip install -r requirements.txt
$env:GEMINI_API_KEY='replace-with-secret'
$env:LEGAL_REFERENCE_PATH='references/legal/bns_sections.json'
$env:LEGAL_REFERENCE_VERSION='bns-2023-2024-07-01'
py -3.13 -m src.main --case-id '<uuid-or-stable-id>' --input-dir .\BYOMKESH_E2E_CASE_001 --output-dir .\output
py -3.13 -m src.main --case-id '<same-id>' --input-dir .\BYOMKESH_E2E_CASE_001 --output-dir .\output --resume
py -3.13 -m pytest -q
py -3.13 -m compileall -q src tests
git diff --check
```

macOS/Linux use `python3 -m venv .venv`, `source .venv/bin/activate`, and `python3 -m ...`; environment assignments may prefix a command. PowerShell uses backtick for line continuation; POSIX shells use backslash.

## 16. Test suite

The tests cover: domain immutability; intake/path traversal/signatures/limits; OCR adapter/artifacts/failures/resume; parsers and unsupported entities; graph identity/provenance; canonical projections; evidence validation; context/legal constraints/reference datasets; review lifecycle; charge-sheet formatting/status; workflow engine; production hardening; typed E2E/final E2E; and Gemini SDK smoke behavior.

| Test file | Focus |
|---|---|
| `test_domain_models.py` | hash, safe filename, immutability, source confidence |
| `test_document_intake.py`, `test_production_hardening.py` | classifier, signatures, duplicates, isolation, limits, deferred media, production composition |
| `test_ocr_layer.py`, `test_ocr_resume.py`, `test_gemini_sdk_smoke.py` | Gemini adapter, artifact contract, failure retention, resume and current SDK availability |
| `test_document_parsers.py` | registry, schema retries, typed artifacts, entity support, parser-to-graph regression |
| `test_knowledge_graph.py`, `test_canonical_investigation.py` | graph merge/provenance/roles and canonical projection/conflicts |
| `test_evidence_validation.py` | completeness, source support, conflicts, chronology, unsupported/low-confidence facts |
| `test_case_context_and_legal.py`, `test_legal_reference_provider.py` | context filtering, legal allow-list/status, configured reference/version behavior |
| `test_chargesheet.py`, `test_information_preservation.py` | output provenance, recursive formatting, section distinctness, insufficiency preservation, renderer grouping |
| `test_officer_review.py` | review transition/version/content-hash/final artifact safety |
| `test_workflow_engine.py` | stage order, skip, critical/noncritical failure semantics |
| `test_end_to_end_pipeline.py`, `test_final_end_to_end.py` | complete typed fixture path, blocked/failure behavior, final approval, renderer determinism |

The most recent full suite run in this workspace passed: **129 passed, 1 skipped, 10 subtests passed**. It did not make external API calls; fixtures inject clients. `test_gemini_sdk_smoke.py` is the relevant SDK availability/smoke coverage. No source/test file was changed for this handoff.

## 17. Known issues, risks, and improvement boundaries

### Confirmed bugs

None discovered during the preceding final verification after the current renderer fix. The active review PDF was visually inspected after regeneration and had six pages with complete headers/footers, wrapped content, repeated table headers, and no raw Python representations.

### Potential risks (code-supported)

1. Gemini OCR/parser has no explicit 429/503 backoff/retry; provider/model/quota outages fail critical stages.
2. Production requires online Gemini plus a configured local legal dataset/version; environment mistakes fail before work.
3. Resume is OCR-only; later stages recompute and no persisted parse/graph/canonical resume is implemented.
4. Parsing controls explicit supported entity values, but general scalar factual extraction is still model-dependent.
5. Legal deterministic required-element matching is string containment, not a full legal-element engine. This is an engineering limitation, not legal advice.
6. Renderer uses ReportLab tables; unusually huge single rows may remain constrained by Platypus table splitting behavior. Current inspected artifact rendered acceptably.
7. `git diff --check` reports whitespace sequences inside the tracked/generated PDF binary; source/test diff check is clean. This is an artifact hygiene issue, not a Python formatting failure.
8. Retained legacy modules have a broad LLM prompt that asks for court-ready content. They are not production-composed and must not be accidentally reintroduced.

### Future improvements (not implemented)

Explicit API retry/backoff telemetry; parsing resume; richer human identity resolution; comprehensive legal reference corpus; formal production deployment/security configuration; and wider real-provider integration tests. No TODO/FIXME comments were found in active source.

## 18. Recent implementation history visible in current tree

The Git log has only generic messages (`dynamic jsons - part 2`, etc.), so exact problem/root-cause/fix chronology is **not determinable** from history alone. The current dirty working tree and tests demonstrate these completed changes:

| Current behavior | Protection |
|---|---|
| `google-genai` OCR/parse adapters with structured OCR response support | `test_ocr_layer.py`, `test_gemini_sdk_smoke.py` |
| checksum-validated OCR resume and cross-ID rebinding | `test_ocr_resume.py` |
| explicit FIR/Complaint complainant/victim/accused preservation | parser/graph/canonical/information-preservation tests |
| provenance-preserving canonical/context projection | canonical, validation, context/legal tests |
| generic recursive charge-sheet formatting and distinct sections | `test_chargesheet.py`, `test_information_preservation.py` |
| ReportLab page chrome and non-orphaned table heading | `test_renderer_keeps_table_heading_with_the_table` plus final visual PDF inspection |

## 19. Architecture / contracts that must be preserved

1. **Immutable typed boundaries:** do not replace models with untyped dicts; validation and provenance traversal depend on them.
2. **Document ID/checksum pairing:** resume safety and artifact binding depend on both.
3. **Role semantics:** do not collapse complainant, victim, accused, or witness collections for presentation convenience.
4. **Provenance requirements:** populated `CanonicalFact` and `ChargeSheetField` data must remain traceable.
5. **Validation disposition:** legal reasoning must not change it; final-blocked must not render a draft/final PDF.
6. **Legal status fidelity:** never convert `insufficient_evidence`, `conflicted`, or review requirements into conclusive language.
7. **Legal-reference version pinning:** prevents silent legal dataset drift.
8. **Presentation-only scope:** formatter/renderer may change display, never upstream facts/references/confidence/status.
9. **Review content hash/version:** preserves approval integrity and finalization safety.

## 20. Practical troubleshooting

| Symptom | Inspect first | Safe response |
|---|---|---|
| `google-genai package is required` | active venv and `requirements.txt` | install requirements with the intended interpreter |
| missing `GEMINI_API_KEY` | environment/CLI arg | set secret outside source control |
| Gemini 404 | `GEMINI_MODEL`, account access | choose an account-available model through config; do not hardcode it |
| Gemini 429/503 | quota/service state, saved OCR artifacts | retry later or use `--resume` for validated completed OCR |
| malformed OCR/parser JSON | stored raw OCR and error text | inspect artifact/prompt/schema; preserve failed context; do not fabricate data |
| resume did fresh OCR | manifest checksums, original bytes, all three OCR artifacts | restore matching case artifacts or accept fresh OCR |
| legal reference error | path/version/file JSON | set exact path/version matching dataset |
| no PDF | workflow report and validation disposition | fix upstream data/validation; final-blocked intentionally suppresses PDF |
| ReportLab layout error | `ChargeSheetData` and renderer tests | use a synthetic regression test; do not alter investigation logic |
| PowerShell parser error | quoting/line continuation | use single-quoted paths; PowerShell backtick, not POSIX backslash |

## 21. Safe development workflow

1. Identify the relevant typed boundary and existing contract/test.
2. Add a synthetic, generic regression test first.
3. Change only the owning layer; presentation bugs must not alter OCR/parsing/graph/canonical/legal code.
4. Run focused tests, then `py -3.13 -m pytest -q` and `py -3.13 -m compileall -q src tests`.
5. Run `git diff --check`; distinguish source defects from generated binary artifacts.
6. For renderer work, regenerate only from persisted/local typed data and inspect extracted text plus page images.
7. Do not make external calls for tests or presentation verification.

## 22. Current status summary

The active typed pipeline, OCR resume safeguards, role/provenance preservation, validation gating, constrained legal findings, charge-sheet population, review lifecycle, and ReportLab review PDF are implemented and covered by the current suite. The current generated review PDF is a six-page readable artifact with preserved `insufficient_evidence` status. Gemini functionality is code-configured and mock-tested but real-account availability/quota is inherently external. The most important next engineering work is operational hardening (provider retries/observability and configuration/deployment), not casual changes to typed/provenance/legal contracts.
