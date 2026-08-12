# Supplied charge-sheet reference: field inventory

Reference inspected: project/output/ChargeSheet.pdf (9 A4 portrait pages). The supplied PDF does not print “FORM IF-5”; this inventory records only its observed labels/layout.

| ID | Page | Section / official label | Type | Rows / continuation | Source |
|---|---:|---|---|---|---|
| F01 | 1 | CHARGE SHEET; Case Number; Police Station; Date | scalar | fixed cover | case metadata |
| F02 | 1 | statute heading; filing court line | scalar | fixed cover | legal findings / court |
| F03 | 2 | Police Station Details; FIR Information; Crime Number; Investigating Officer; Court | scalar | fixed | canonical/context |
| F04 | 2 | Complainant Details; Victim Details | person details | repeated persons | canonical persons |
| F05 | 3 | Accused Details | person/arrest details | repeated persons | canonical persons |
| F06 | 4 | Case Summary; Detailed Facts; Investigation Conducted | text | may continue | supported actions only |
| T01 | 4-5 | Chronological Timeline: Time/Date, Event | table | page-5 continuation | canonical timeline |
| T02 | 6 | Witness Details: S.No., Name, Age, Occupation, Statement Summary, Exhibit | table | continuation allowed | canonical witnesses |
| T03 | 6 | Documentary Evidence: S.No., Evidence Description, Exhibit Mark | table | continuation allowed | canonical documents |
| T04 | 6 | Material Evidence: S.No., Evidence Description, Exhibit Mark | table | continuation allowed | evidence/property |
| F07 | 7 | Medical; Forensic; Vehicle; Spot; CCTV Findings | text | may continue | canonical findings |
| F08 | 8 | Evidence Analysis | text | continuation | unavailable unless supported |
| T05 | 9 | Applicable BNS Sections; Applicable Motor Vehicle Act Sections | list | continuation allowed | Phase 9 legal findings |
| T06 | 9 | Annexures: Annexure No., Document Name, Exhibit Mark | table | continuation allowed | canonical documents |
| F09 | 9 | Final Opinion; Signature Block; Date; Signature | scalar/signature | fixed closing | unavailable unless supported |

All fields retain value, status, confidence, sources, review flag. Unsupported data renders as Not Available in Investigation Records.
