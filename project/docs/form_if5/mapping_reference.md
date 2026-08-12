# Mapping reference

| Inventory field | Phase 10 source | Rule |
|---|---|---|
| case/FIR/station/court | CaseContext metadata | copy only a supported fact |
| persons | CaseContext victims/accused/witnesses | rows retain provenance |
| timeline/findings/property/documents | CaseContext | deterministic table/list projection |
| legal sections | LegalFindings | only SUPPORTED findings populate normally |
| opinion/signature/narrative claims | no supported source by default | mark unavailable |

FINAL_BLOCKED produces a validation/review JSON artifact only. REVIEW_REQUIRED produces a PDF marked as a review copy.
