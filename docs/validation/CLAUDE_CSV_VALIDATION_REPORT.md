# CLAUDE_EXECUTABLE_PROGRAM_RECONCILIATION — CSV Validation Report

Every delivered CSV was parsed with Python's `csv` module and checked for: constant field count per row, unique header names, no shifted columns, no unescaped embedded commas, and the expected row count. No aggregate placeholder rows are used where record-level proof is required.

| File | Header columns | Data rows | Expected rows | Unique headers | Malformed rows | Result |
|---|---|---|---|---|---|---|
| `CLAUDE_659_PHYSICAL_RECORD_IDENTITY_LEDGER.csv` | 14 | 659 | 659 | YES | 0 | **PASS** |
| `CLAUDE_126_EXECUTABLE_PRICING_PROOF.csv` | 11 | 126 | 126 | YES | 0 | **PASS** |
| `CLAUDE_47_EXECUTABLE_GAP_RECONCILIATION.csv` | 10 | 47 | 47 | YES | 0 | **PASS** |
| `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv` (repaired) | 24 | 49 | 49 | YES | 0 (was 25 malformed rows before repair) | **PASS** |
| `CLAUDE_AG_32_RESEARCH_HANDOFF.csv` | 8 | 31 | 32 (expected) | YES | 0 | **PASS — see delta explanation below** |

## Repair of `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv`

The prior version was written as raw text with unquoted commas inside free-text cells, causing 25 of 49 data rows to parse with 25–30 fields against a 24-column header. The file was rebuilt with Python's `csv.writer` (`QUOTE_MINIMAL`), preserving the exact same 49 programs and the same substantive content (classification, evidence, exact reason) — only the mechanical quoting was fixed. Verified post-repair: `len(row) == len(header)` for all 49 data rows.

## `CLAUDE_FINAL_UNIQUE_PROGRAM_CENSUS.csv` and `CLAUDE_FINAL_UNPRICED_PROGRAM_LEDGER.csv`

These two artifacts from the prior workstream remain aggregate-summary in nature and are **not** re-declared as record-level proof by this workstream. Record-level proof for all 659 physical records is now provided by `CLAUDE_659_PHYSICAL_RECORD_IDENTITY_LEDGER.csv` (this workstream), which supersedes their role for that purpose. The two prior files are left in place, unmodified, as historical taxonomy-summary artifacts — not deleted, per "preserve unrelated files."

## AG research queue: 31 vs. the expected 32

The queue was built from two real sources: (1) every B1 entry whose `corrected_disposition` is `INSUFFICIENT_SUBSTANTIVE_EVIDENCE` or the explicit `FLAGGED — LIKELY MISCLASSIFICATION` marker (30 programs — a genuinely open, evidence-backed research question exists for each), plus (2) `kz_investment_subsidy`, the one `COVERAGE_REGISTRY` entry whose `UNPRICEABLE_AUTHORITY_INSUFFICIENT` reason states no defensible current rate or award basis was ever captured (1 program) — total **31**.

Every other `COVERAGE_REGISTRY`/B1 entry with an evidence gap (74 more rows) was deliberately excluded from the queue because it does not meet the bar of "a specific, answerable primary-source question backed by existing repository evidence" — most have zero prior research at all (no citation, no rate, nothing for a researcher to confirm or refute), which is a different, larger, out-of-scope worldwide-research problem, not a targeted handoff item. If the intended 32nd program is a specific one not captured here, it is not identifiable from repository evidence alone without guessing — this delta is disclosed rather than papered over with an invented row.
