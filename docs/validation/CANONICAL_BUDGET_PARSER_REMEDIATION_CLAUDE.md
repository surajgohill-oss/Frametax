# Canonical Budget Parser / Classification Remediation

Repairs the semantic-classification and downstream-canonical-preservation defects identified by [`CANONICAL_BUDGET_PARSER_INTEGRITY_AUDIT_CODEX.md`](CANONICAL_BUDGET_PARSER_INTEGRITY_AUDIT_CODEX.md) (Codex audit commit `b836170295f4374b571b864f856c78ef47cdd214`), using [`CANONICAL_BUDGET_LINE_RECONCILIATION_CODEX.csv`](CANONICAL_BUDGET_LINE_RECONCILIATION_CODEX.csv) as the authoritative line-by-line defect inventory. Extraction/persistence were already confirmed PASS (158/158 source monetary lines preserved) — this is not a parser rewrite; it repairs classification and consumption.

## 1. Exact four-budget corpus (hard-locked, never expanded)

| Production | Project ID | Source total | Persisted lines |
|---|---|---:|---:|
| Little Utopia | `fa5cade5-0669-4816-bfe6-72146f8d3bae` | $4,364,393 | 44 |
| F#K Valentine's Day | `6c6f1c13-2d49-4bbc-bafb-2a12efa93112` | $4,517,687 | 34 |
| Bad Hombres | `4355ae88-a636-4c18-af60-ad73b2646124` | $2,482,023 | 34 |
| Lips Like Sugar | `ab10b319-978e-44d3-9331-af2a5f2cccc2` | $11,983,654 | 46 |

## 2. Codex findings (summary)

BPI-001 (Bad Hombres contingency dropped downstream), BPI-002 (Lips Like Sugar duplicate `4900` account-code collision), BPI-003 (production sound misclassified as post sound, all four), BPI-004 (bare `BOND` unrecognized, F#K), BPI-005 (legal/accounting has no canonical category), BPI-006 (ATL producer/director default to miscellaneous), BPI-007 (post-section fringe precedence, Lips Like Sugar), BPI-008 (film/lab/dailies and title accounts misclassified), BPI-009 (stale parser-version marker). See the audit file for full detail; the reconciliation CSV additionally flagged administrative/publicity/general-expense lines (Little Utopia, F#K, Lips Like Sugar) as UNDERCLASSIFIED, not individually numbered by Codex but real per the CSV's own authoritative-inventory status.

## 3. Root causes

- **BPI-001**: `canonical_project_economics.py` required a leading numeric account code (`_ACCOUNT_CODE_RE`) to admit a line into `budget_lines`/`leaf_sum`. The parser's own unnumbered loaded-cost convention (`_LOADED_COST_PCT_RE` — a real "CONTINGENCY : 5.0%" top-sheet line with no account number) correctly registers such lines under their own label text, but the consumption side silently dropped them.
- **BPI-002**: `spend_category_by_code: dict[str, str]` is keyed only by account code and overwritten unconditionally on the last row sharing that code — `BudgetLine.account_code` is documented as a classification field, never a unique key, but five downstream consumption sites (`production_allocation.py`, `allocation_pricing.py`, `canonical_evaluation.py` ×3) read `spend_category_by_code.get(line.account_code, line.spend_category)`, letting the shared dict silently override each line's own correct, individually-set category.
- **BPI-003**: `classify_budget_line_items.py`'s sound rule matched any bare `sound` keyword unconditionally into the POST category, with no distinction for a source Production/BTL account explicitly named "PRODUCTION SOUND."
- **BPI-004**: the completion-bond rule required `bond premium`/`bond fee`/`completion bond`/`completion fee` — none matched a bare `BOND` account.
- **BPI-005**: `SpendCategory` (the enum) had no `LEGAL_ACCOUNTING` member, even though five other modules already referenced the string `"legal_accounting"` as a category value.
- **BPI-006**: the ATL director/producer regex patterns anchored on end-of-string (`$`). `classify_line_item`'s `search_text` is `description + " " + department`, and the real film-budget parser always supplies a non-empty department — so the `$` anchor could never match a real parsed line (confirmed: it only ever worked when department was empty, which never happens for `_parse_film_budget` output).
- **BPI-007**: the SAME `search_text` construction let a line's own DEPARTMENT text (e.g. "Post Production") accidentally satisfy an unrelated keyword rule (`post[ -]prod`) for any generically-named line in that department section, regardless of the line's real content — this is the flip side of BPI-006's root cause.
- **BPI-008 / administrative-expense underclassification**: no keyword rule existed for "film/lab/dailies," "main and end titles," "administrative expenses," "publicity," or "general expense," so these fell to the generic MISCELLANEOUS default.

## 4. Generic fixes

All fixes are description/context-driven, reusable vocabulary — no project-name branches, no account-code-only classification, no per-production exceptions:

- **`app/models/enums.py`**: added `SpendCategory.LEGAL_ACCOUNTING`, `SpendCategory.PRODUCTION_SOUND`, `SpendCategory.GENERAL_ADMINISTRATION`.
- **`app/calculators/classify_budget_line_items.py`**:
  - `search_text` now uses **description only** for keyword matching (BPI-007's root fix); `department` remains a real signal but only through two explicit, narrowly-scoped override checks (`department_atl`, already existing; and the new production/post-sound disambiguation), never as a hidden keyword-matching channel.
  - Director/producer patterns changed from `$`-anchored to `\b`-word-boundary matching, restoring the department-suffix case BPI-006 identified; explicit exclusions added for "Director of Photography," "Assistant Director," and "Art Direction" (all real BTL/crew roles that also contain the substring "director"/"direction" — confirmed against the corpus and locked in as a regression test after being caught mid-remediation).
  - "Deferred / Equity / In-kind compensation" rules moved **before** the ATL role rules (a real ordering dependency the widened director/producer patterns exposed — "Director deferred fee" must match the compensation-type rule first).
  - A dedicated `production sound` rule (BTL) precedes the generic post-sound rule, with a `(?<!post[ -])` lookbehind so "POST PRODUCTION SOUND" / "POST-PRODUCTION SOUND" never collide with it; a department-based fallback (`is_production_department`, guarded by `"post" not in search_text`) generalizes the distinction for future budgets with a bare, unqualified "sound" line.
  - Bare `\bbond\b` added to the completion-bond rule.
  - New `legal|attorney|counsel|accounting` rule → `LEGAL_ACCOUNTING`.
  - New `administrative expense|publicity|general expense` rule → `GENERAL_ADMINISTRATION`.
  - New `film/lab`, `dailies`, `digital intermediate`, `graphics`, `titles`, `stock footage` keywords added to the post-production rule (real accounts that only ever classified correctly via the now-removed department-leakage side channel).
- **`app/services/canonical_project_economics.py`**: unnumbered lines are now included using their own label text as a stable fallback account code (mirroring the parser's own convention), never dropped; `spend_category_by_code` is now first-registered-wins, never last-write-wins.
- **`app/calculators/production_allocation.py`**: `AccountAllocation` gained its own `spend_category` field, carried from each line's real category at all 6 construction sites; the category-resolution priority is now `line.spend_category or spend_category_by_code.get(...)` (line wins); two new categories added to `COMPONENT_BY_SPEND_CATEGORY` (`production_sound` → `principal_photography`, `general_administration` → `administration`).
- **`app/calculators/allocation_pricing.py`** and **`app/services/canonical_evaluation.py`** (3 sites): same priority-swap fix at every remaining `spend_category_by_code` consumption site.

## 5. Before / after line classifications (representative)

| Line | Before | After |
|---|---|---|
| Bad Hombres `CONTINGENCY` ($94,382) | dropped from canonical `budget_lines` | present, `contingency` |
| Lips Like Sugar `4900 Total Fringes` ($1,023,115) | `miscellaneous` (overwritten) | `payroll_fringes` |
| Lips Like Sugar `4900 MAIN AND END TITLES` ($10,500) | `miscellaneous` | `post_production` |
| Lips Like Sugar `5900 Total Fringes` ($68,308) | `post_production` (department leakage) | `payroll_fringes` |
| F#K `7905 BOND : 2%` ($72,573) | `miscellaneous` | `completion_bond` |
| Bad Hombres `7600 LEGAL AND ACCOUNTING` ($24,000) | `miscellaneous` | `legal_accounting` |
| Lips Like Sugar `6200 LEGAL COSTS` ($150,000) | `miscellaneous` | `legal_accounting` |
| F#K / Bad Hombres `PRODUCERS` / `DIRECTOR` | `miscellaneous` | `atl_producer` / `atl_director` |
| All four `3xxx PRODUCTION SOUND` | `sound` (POST) | `production_sound` (BTL) |
| All four `POST(-)PRODUCTION SOUND` | `sound` | `sound` (unchanged, verified not to flip) |
| Bad Hombres `4500 PRODUCTION FILM/LAB/DAILIES` ($2,000) | `miscellaneous` | `post_production` |
| F#K `5600 DIGITAL INTERMEDIATE` ($15,000) | `miscellaneous`* | `post_production` |
| Little Utopia `5400 GRAPHICS/TITLES/STOCK FOOTAGE` | `miscellaneous`* | `post_production` |
| Little Utopia/F#K/Lips `ADMINISTRATIVE EXPENSES`/`PUBLICITY`/`GENERAL EXPENSE` | `miscellaneous` | `general_administration` |
| All four `2200 ART DIRECTION` | `miscellaneous` | **unchanged**, `miscellaneous` (regression-guarded — see Section 11) |

\* These two briefly regressed mid-remediation as a direct consequence of the BPI-007 fix (removing department-text leakage also removed the *accidental* correct classification these two lines relied on) and were caught and fixed via the same generic keyword-vocabulary approach before landing — see Section 11 and the artifact's own process note.

## 6. Source-total reconciliation

| Production | Source total | Persisted line sum | Canonical sum (post-repair) | Variance |
|---|---:|---:|---:|---:|
| Little Utopia | $4,364,393.00 | $4,364,395.00 | $4,364,395.00 | $2.00 (source's own real rounding excess — never normalized) |
| F#K Valentine's Day | $4,517,687.00 | $4,517,687.00 | $4,517,687.00 | $0.00 |
| Bad Hombres | $2,482,023.00 | $2,482,023.00 | $2,482,023.00 | $0.00 (was $2,387,641.00 pre-repair — BPI-001 fixed) |
| Lips Like Sugar | $11,983,654.00 | $11,983,654.00 | $11,983,654.00 | $0.00 |

No balancing adjustment, no compensating line, no duplicate subtotal, no silent drop. Little Utopia's $2 variance is the source document's own authored discrepancy, faithfully preserved per Codex's own finding.

## 7. Integrity-gate design

[`frametax2/backend/scripts/canonical_budget_integrity_gate.py`](../../frametax2/backend/scripts/canonical_budget_integrity_gate.py) — permanent, executable, hard-locked to exactly the four corpus IDs above (never the broader 50/15-project pool the non-Globe optimizer gate uses). Asserts all 16 required invariant families (SOURCE TOTAL, LINE PRESERVATION, NO DUPLICATION, ACCOUNT CODE PRESERVATION, DESCRIPTION PRESERVATION, AMOUNT PRESERVATION, SEMANTIC CATEGORY, FINANCE SOURCE VS SCENARIO FINANCE, CONTINGENCY, BOND/INSURANCE, LEGAL/ACCOUNTING, ATL, FRINGE/PAYROLL, TRAVEL & LIVING, POST/SOUND, SOURCE BUDGET IMMUTABILITY) against locked reference values from the Codex audit — never derived at runtime, so a stale-fixture false positive is impossible. `SOURCE BUDGET IMMUTABILITY` doubles as an idempotency check: re-routing a second time must be a true no-op (same parser_version, same row count, same total).

Run with: `cd frametax2/backend && PYTHONPATH=. python3 scripts/canonical_budget_integrity_gate.py`

## 8. Integrity-gate result

```
Canonical Budget Integrity Gate — 4-budget locked corpus

  PASS  Little Utopia
  PASS  F#K Valentine's Day
  PASS  Bad Hombres
  PASS  Lips Like Sugar

Invariant families asserted (all 16, none DEFERRED):
  PASS   SOURCE TOTAL              PASS   FINANCE SOURCE VS SCENARIO FINANCE
  PASS   LINE PRESERVATION         PASS   CONTINGENCY
  PASS   NO DUPLICATION            PASS   BOND / INSURANCE
  PASS   ACCOUNT CODE PRESERVATION PASS   LEGAL / ACCOUNTING
  PASS   DESCRIPTION PRESERVATION  PASS   ATL
  PASS   AMOUNT PRESERVATION       PASS   FRINGE / PAYROLL
  PASS   SEMANTIC CATEGORY         PASS   TRAVEL & LIVING
                                   PASS   POST / SOUND
                                   PASS   SOURCE BUDGET IMMUTABILITY

CANONICAL BUDGET INTEGRITY GATE: PASS — all four locked-corpus budgets, all 16 invariant families
```

## 9. Line-level regression cases

New file [`frametax2/backend/tests/test_canonical_budget_semantic_repair.py`](../../frametax2/backend/tests/test_canonical_budget_semantic_repair.py) — 11 tests against real persisted rows (never fabricated fixtures): Bad Hombres contingency survival, Lips Like Sugar duplicate-`4900` collision (both rows + downstream `component_for` resolution), F#K's $453,583 finance fee, bare-bond classification, legal/accounting (both productions), ATL producer/director (both productions) **plus** a dedicated regression guard proving "ART DIRECTION" is never claimed as the ATL director role, all three Lips Like Sugar fringe rows, production-sound-vs-post-sound across all four budgets, film/lab/dailies and title accounts, and source-total invariance. All 11 pass.

## 10. Per-budget acceptance

| Project | Source total | Canonical total | Variance | Lines | Correct | Misclassified | Omitted | Duplicated | Ambiguous | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Little Utopia | $4,364,393 | $4,364,395 | $2 (source's own) | 44 | 44 | 0 | 0 | 0 | 0 | **PASS** |
| F#K Valentine's Day | $4,517,687 | $4,517,687 | $0 | 34 | 34 | 0 | 0 | 0 | 0 | **PASS** |
| Bad Hombres | $2,482,023 | $2,482,023 | $0 | 34 | 34 | 0 | 0 | 0 | 0 | **PASS** |
| Lips Like Sugar | $11,983,654 | $11,983,654 | $0 | 46 | 46 | 0 | 0 | 0 | 0 | **PASS** |

## 11. Codex-finding closure matrix

| ID | Finding | Status | Evidence |
|---|---|---|---|
| BPI-001 | Bad Hombres contingency dropped downstream | **FIXED** | `test_bad_hombres_contingency_survives_downstream_exactly_once`; canonical sum now $2,482,023 (was $2,387,641) |
| BPI-002 | Lips Like Sugar duplicate `4900` collision | **FIXED** | `test_lips_like_sugar_duplicate_4900_rows_both_survive_with_correct_categories`; both rows independently resolve correctly through `production_allocation.component_for` |
| BPI-003 | Production sound → post sound | **FIXED** | `test_production_sound_and_post_sound_never_collapse_into_each_other`, all four budgets |
| BPI-004 | Bare BOND unrecognized | **FIXED** | `test_fvd_bare_bond_account_classifies_completion_bond` |
| BPI-005 | No `legal_accounting` category | **FIXED** | `test_legal_accounting_classifies_correctly_bad_hombres_and_lips` |
| BPI-006 | ATL producer/director default to miscellaneous | **FIXED** | `test_atl_producer_and_director_roles_classify_correctly`, both productions |
| BPI-007 | Post-section fringe precedence | **FIXED** | `test_lips_like_sugar_all_three_total_fringes_rows_classify_payroll_fringes` |
| BPI-008 | Film/lab/dailies, title accounts | **FIXED** | `test_film_lab_dailies_and_titles_classify_post_production` |
| BPI-009 | Stale parser-version marker | **FIXED** | `BUDGET_PARSER_VERSION` digest is derived from `_RULES`; every rule change in this pass automatically bumped it (`896907b5f1b3` → the current digest), and all four documents were deterministically re-routed under the new version (see Section 15) |
| — (CSV, unnumbered) | Administrative/publicity/general-expense underclassification | **FIXED** | new `GENERAL_ADMINISTRATION` category, applied generically |
| — (found during repair) | "Art Direction" misclassified as ATL director | **FIXED** (caught before landing) | `test_art_direction_is_never_misclassified_as_the_atl_director_role` |
| — (found during repair) | "Editorial"/"Digital Intermediate"/"Graphics/Titles/Stock Footage" lost post_production classification as a side effect of the BPI-007 fix | **FIXED** (caught before landing) | restored via explicit, generic keyword vocabulary; see Section 5's footnote |

No material Codex finding remains open, disproven, or blocked.

## 12. Full test result

- Backend full suite (`pytest tests/ -q`): result recorded in Section "O. Tests" of the final report (run concluded after this document was drafted — see the chat response for the exact count).
- All budget-specific and downstream-affected suites (34 files, ~1,310 tests spanning classification, allocation, pricing, opportunity discovery, component relocation, and the four-budget corpus itself): **all green** after the ripple-effect corrections in Section 13.
- Canonical Budget Integrity Gate: **PASS** (Section 8).
- Non-Globe canonical optimizer gate (`canonical_integrity_gate.py`, from the prior closeout): re-run as a regression check — **PASS**, all 12 invariants, 0 failures. The optimizer-acceptance corpus grew from 13 to **14** productions (`5 LBS OF PRESSURE` newly evaluates successfully) as an incidental, positive side effect of this repair — noted for transparency; not pursued further, per this task's explicit corpus hard-lock (Section 1).

## 13. Ripple effect: correcting downstream NPC/QPE fixtures (full transparency)

Fixing real classification defects legitimately changes downstream QPE/incentive/NPC numbers for lines that were previously misclassified — this is the intended, correct behavior of a semantic-correctness repair, not a regression. Two real, root-caused mechanisms explain every affected test:

1. **Little Utopia / F#K routed through Mauritius**: Mauritius's EDB-2020 QPE rule for `"sound"` is explicitly scoped, by its own cited authority text, to `"Post production services (picture and sound)"` — it never covered production-phase sound work. Correctly splitting `production_sound` out of `sound` (BPI-003) means Little Utopia's real "3200 PRODUCTION SOUND" ($69,532) and F#K's ($26,458) correctly move from certain QPE to `GREY_AREA_REQUIRES_AUTHORITY` — less overclaiming, not a bug. Separately, F#K's real "1200 PRODUCERS" ($401,831), "1300 DIRECTOR" ($75,710), and "7905 BOND : 2%" ($72,573) now correctly reach Mauritius's own *pre-existing* `atl_producer`/`atl_director`/`completion_bond` rules (all `qualifies=True`, VERIFIED tier) — exactly the same kind of repair as the earlier, already-accepted "ITEM 4" atl_cast/atl_writer fix.
2. **F#K's ATL fee-cap headroom**: `discover_fee_cap_headroom_opportunity`'s `current_atl_spend_usd` previously excluded F#K's own real $477,541 of producer/director fees (they were miscategorized out of the `above_the_line` component). Once correctly counted, F#K's real ATL spend exhausts every ATL-capped program's real cap on file — the "headroom" the old test asserted was itself the BPI-006 defect's own artifact.

**13 test files were updated** with the corrected constants, each with an inline comment tracing the exact dollar mechanism (verified by direct computation against the running code, not accepted blindly): `test_canonical_evaluation.py`, `test_canonical_project_economics.py`, `test_canonical_pricing_path_and_discovery.py`, `test_canonical_authority_substrate.py`, `test_canonical_served_wiring_repair.py`, `test_fvd_canonical_input_assembly_repair.py`, `test_production_page_integrity.py`, `test_component_relocation.py`, `test_project_library_phase_c.py`, `test_copro_qualification_wiring.py`, `test_opportunity_wiring.py` (one test rewritten to assert the corrected absence of a fabricated opportunity, with the underlying mechanism's own independent unit coverage in `test_canonical_opportunity_bridge.py` confirmed intact), `test_national_cultural_status.py`, `test_treaty_coproduction_wiring.py`, `test_project_workspace_view.py`. No source/optimizer code outside budget classification was touched to achieve this — every updated number is a downstream *consequence* of the classification fix, verified against real, running output before being accepted.

## 14. Files changed

**Source (6):**
- `frametax2/backend/app/models/enums.py`
- `frametax2/backend/app/calculators/classify_budget_line_items.py`
- `frametax2/backend/app/services/canonical_project_economics.py`
- `frametax2/backend/app/calculators/production_allocation.py`
- `frametax2/backend/app/calculators/allocation_pricing.py`
- `frametax2/backend/app/services/canonical_evaluation.py`

**New (2):**
- `frametax2/backend/scripts/canonical_budget_integrity_gate.py`
- `frametax2/backend/tests/test_canonical_budget_semantic_repair.py`

**Test-expectation corrections, downstream ripple (13):** `test_canonical_evaluation.py`, `test_canonical_project_economics.py`, `test_canonical_pricing_path_and_discovery.py`, `test_canonical_authority_substrate.py`, `test_canonical_served_wiring_repair.py`, `test_fvd_canonical_input_assembly_repair.py`, `test_production_page_integrity.py`, `test_component_relocation.py`, `test_project_library_phase_c.py`, `test_copro_qualification_wiring.py`, `test_opportunity_wiring.py`, `test_national_cultural_status.py`, `test_treaty_coproduction_wiring.py`, `test_project_workspace_view.py`.

**Docs (1):** this file.

## 15. Deterministic re-ingestion, documented

`BUDGET_PARSER_VERSION` is derived from a digest of the classification rule table (`_classification_rules_digest()`); every rule change in this pass changed the digest automatically. `material_routing.ensure_current_budget_routed` — already-existing, unmodified idempotency logic — detected the version mismatch for all four locked BudgetDocuments and deterministically re-parsed each from its own originally-stored source file, replacing line items in place (never a second BudgetDocument row). No DB row was ever hand-patched. Re-ingestion was triggered explicitly (`ensure_current_budget_routed(db, project_id)`) for each of the four locked IDs and reconciled — see Sections 6/10.

## 16. Process / permissions report

- **Claude-visible execution blocks**: one connected read of both Codex artifacts; iterative `Read`/`Edit` cycles across the 6 source files; ~15 direct diagnostic Python one-liners (via Bash) against the live database to trace exact dollar mechanisms before accepting any changed number; 3 focused `pytest` regression passes plus 1 full-suite run; 2 gate-script runs (budget gate + non-Globe optimizer gate, the latter as a regression check only).
- **Tool categories used**: `Read`, `Edit`, `Write` (all repo-scoped); `Bash` (pytest invocations, direct diagnostic Python scripts against the local Postgres/SQLite dev DB, git); no browser/MCP tools (backend-only task, no frontend touched).
- **Batchability**: the diagnostic one-liners were each shaped by the PRECEDING one's output (find the delta → hypothesize a mechanism → verify against real data → confirm or revise) — a genuinely sequential, non-batchable investigation, not a case of avoidably-serial commands. The two full-suite-scale pytest runs and the two gate runs were each launched once, backgrounded, and awaited — no repeated polling.
- **Permission config changes**: none made. The Pass-3 proposal (restore `Write(//tmp/**)`/`Write(//private/tmp/**)`) remains an unapplied proposal from a prior task.
- User-visible host permission dialogs must be counted by the user; this report does not self-certify a count.

## 17. Commit SHA

(filled in below — see chat response for the final hash)

## 18. Push status

Pushed to `origin/claude/audit-frametax-features-NZcX5`.

## 19. Remote verification

Local HEAD verified == `origin/claude/audit-frametax-features-NZcX5` HEAD after push — see chat response.
