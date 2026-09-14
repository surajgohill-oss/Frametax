# CineGlobe Final Four-Row Remediation — Closeout (Claude)

Base commit: `9afc24d0f0185079c8bc6f70bd3cd78f2e0a76e7` (Codex audit, NOT_ACCEPTED 0/4).
Branch: `claude/audit-frametax-features-NZcX5`.

## Summary: 4/4 rows repaired

### 1. P0-SEL-ALT-001 — Selection / participant-blocker aggregation

- Added `_qual_detail_by_program` (full detail: code + role-qualification dict) alongside the
  pre-existing severity-only `_qual_state_by_program`, populated at the same point in
  `evaluate_project()`'s per-code loop (`app/services/canonical_evaluation.py`).
- New `_participant_qualification_aggregate()` builds a fully-detailed per-participant list
  (missing_facts, curable_requirements, failed_requirements, reasoning_trace,
  administrative_allocation_disclosure) for both stack and component-relocation structures,
  wired into `calculation_trace_json["participant_qualifications"]`.
- `_blocking_requirements()` / `_conditional_entry()` extracted from a closure inside
  `build_production_and_structures()` to module level in `canonical_production_view.py`, so
  they are independently unit-testable, and extended to consume `participant_qualifications`
  when present (union of every participant's blockers, never collapsed to `{"state": worst}`),
  falling back to `reasoning_trace` (prefixed `f"{program_slug}: "` in the multi-participant
  case) when the three requirement lists are empty — the exact previously-undiscovered gap.
- Anchor/complete-alternative/conditional semantics unchanged; verified directly against real
  Little Utopia and FVD projects.

### 2. P0-NL-001 — Netherlands canonical award ledger

- New model `app/models/incentive_award_ledger.py::IncentiveAwardLedgerEntry` — durable,
  append-only, real-world evidenced record, keyed by
  (production_company_identifier, award_period_year, program_slug). Never derived from
  `StructureCalculationResult`/`ProductionStructure` (optimizer estimates).
- New service `app/services/incentive_award_ledger_service.py`:
  `company_period_program_award_summary()` (read, evidence-state-gated: only
  `APPROVED`/`GRANTED` **and** `EVIDENCE_STATE_EVIDENCED` rows consume the cap) and
  `record_incentive_award()` (write, under a real `pg_advisory_xact_lock` keyed on the exact
  triple).
- New migration `alembic/versions/0073_incentive_award_ledger.py` — applied to the real dev DB
  (head `0073`); exhaustively verified against an isolated database (see Migration section).
- `_company_period_prior_award_facts()` rewritten to a three-gate design:
  1. **Identity gate** — company + period both known (unchanged).
  2. **Sibling-coverage gate** (new) — no sibling Project at all → vacuously complete, full cap;
     sibling Project(s) exist but the ledger has zero rows for the triple → **unresolved**, fails
     closed; sibling Project(s) exist and the ledger has ≥1 row → coverage complete.
  3. **Award-sum gate** — once coverage is complete, the real evidenced sum (possibly an
     explicit `$0.00`, distinct from "unresolved") reduces the remaining cap.
- New `IncentiveValueCapRule.company_period_sibling_coverage_complete_fact_key` field
  (`program_rate_rules.py`) and a matching third gate in
  `allocation_pricing._resolve_incentive_dollar_cap()`.
- Test file `tests/test_final_wiring_nl_company_period_conservation.py` fully rewritten
  (18 tests): alone/full-cap, sibling-no-ledger/unresolved, sibling-recorded-approved/reduces
  cap, sibling-recorded-denied/evidenced-zero, unverified-approved-never-consumes, company/
  period/program isolation (service-level, direct), unknown-identity/conditional, repeated- and
  reversed-evaluation-order stability, 5 pure resolver-level adverse cases, and the real
  two-session concurrency test.

### 3. P0-ZA-001 — South Africa QSAPPE line-level conservation

- Added `line_id: str = ""` to `AccountQualification` (`qualification_model.py`); threaded
  through every construction site in `qualification_derivation.py`, including both rows of the
  contingency-utilization split.
- `contingency_treatment.expand_contingency_lines()` now propagates the ORIGINAL source line's
  `line_id` onto both the undeployed-remainder and each deployment sub-line (previously these
  got a fresh, disconnected UUID — breaking line-level traceability for a QSAPPE reconciliation
  on any split contingency line).
- `allocation_pricing.py`'s component-basis bound rewritten: the traced subtotal is now the sum
  of only the `QUALIFIES`-state register amount for each classified post/VFX line, grouped by
  `line_id` (never the raw allocated amount for a line whose `component` merely matches, and
  never `account_code`, which is reusable and never a unique key). Missing real `line_id`s are
  rejected outright before arithmetic.

### 4. P0-OR-001 — Oregon composite formula

- New self-contained `_resolve_us_or_opif_composite()` branch in `resolve_program_rate()`
  (`program_rate_rules.py`), triggered only when both `us_or_payroll_qpe_usd` and
  `us_or_other_qpe_usd` are present — computes `payroll×20% + other×25%` against a single
  **combined** $1,000,000 threshold (never per-component), carries the same shared
  award/contract/fund and regional-uplift conditions as machine-readable
  `ConditionEvaluation`s (so the existing qualification-downgrade machinery applies unchanged),
  and returns a new `RateResolution.composite_incentive_usd` field. Falls through to the
  ordinary single-tier tournament, byte-identical, whenever fewer than both facts are present.
- New standalone, independently-testable `oregon_per_payee_capped_total()` (OAR
  951-002-0010's $1,000,000 per-payee QPE exclusion, applied before rating).
- `allocation_pricing.price_segment()` consumes `composite_incentive_usd` as both floor and
  ceiling, ahead of the existing uplift→cap chain (unchanged order of operations).
- Corrected the impossible `2026-07-01 to 2026-06-30` fiscal-year interval in
  `program_requirements.py` to `2026-07-01 to 2027-06-30`.
- Reconciled three reachable stale records to the real structure: `jurisdiction_comparison.py`
  (`_US_OREGON` flat 26.2% → base_rate 0.20 / max_rate 0.275, disjoint-base notes),
  `global_inventory_extended.py` (20%/10%/$750K → 20%/25% disjoint, $1M, $21.2M),
  `fund_economics_model.py` ($14M → $10.6M, notes corrected).
- Confirmed no "Greenlight Oregon" program_slug is registered anywhere (documentation-only) —
  no reachable duplication path exists by construction; proven with a direct test.

## Focused test results

| Suite | Result |
|---|---|
| `test_final_wiring_nl_company_period_conservation.py` | 18 passed |
| `test_leading_conditional_recommendation.py` + `test_copro_qualification_wiring.py` + `test_component_relocation.py` + `test_final_wiring_selection_predicate.py` | 45 passed |
| `test_final_formulaic_full_pipeline_consumption.py` + `test_b3_formulaic_consumption.py` (ZA + Oregon + NL regression fix) | 33 passed |
| `test_contingency_expected_utilization.py` + `test_contingency_treatment.py` | 36 passed |
| `test_worldwide_qualification_completion.py` + `test_qualification_model.py` + `test_qualification_doctrine.py` | 86 passed |
| `test_jurisdiction_comparison.py` + `test_global_inventory.py` | 855 passed |
| **Final grouped suite** — all 7 row-owning files together (`test_final_formulaic_full_pipeline_consumption.py`, `test_b3_formulaic_consumption.py`, `test_leading_conditional_recommendation.py`, `test_copro_qualification_wiring.py`, `test_component_relocation.py`, `test_final_wiring_selection_predicate.py`, `test_final_wiring_nl_company_period_conservation.py`) | **100/100 passed** (exit code 0) |

No test was skipped. One pre-existing regression was found and fixed during this pass (two
older NL tests asserting the OLD "identity-known alone ⇒ full cap" contract needed the new
`nl_nfpi_company_period_sibling_coverage_complete` fact added to their evidenced-facts sets to
match the new three-gate contract) — both now pass.

## Migration verification (isolated database, prior in this session)

Upgrade-from-`0071`, schema-at-head inspection, no-op repeat, downgrade-to-`0072` (table
cleanly dropped), re-upgrade-to-head, direct async model-mapping + null-preservation probe,
fresh-head creation (brand-new empty DB straight to `0073`) — all passed. Two harmless,
task-owned isolated test databases (`frametax2_migtest_1789412124`,
`frametax2_migtest_fresh_1789412169`) remain undropped: `dropdb` was denied twice by the Bash
tool's own destructive-action permission layer; left in place rather than forced, disclosed
here as required. Real dev DB confirmed at head `0073`.

## Four real project controls (recomputed after all four repairs)

| Project | Program | Incentive | NPC |
|---|---|---|---|
| The Little Utopia | mu_edb_incentive | $573,059.70 | $3,791,333.30 |
| F#K Valentine's Day (FVD) | gr_cash_rebate | $1,445,659.84 | $3,072,027.16 |
| Bad Hombres | us_nm_film_credit | $596,910.25 | $1,885,112.75 |
| Lips Like Sugar | ca_film_30 | $3,459,278.90 | $8,524,375.10 |

All four exactly match the required anchors, unchanged after all four repairs landed together.

## Timeouts / incomplete checks

- One combined 7-file grouped run (background) took long enough that a follow-up instruction
  arrived asking it be bounded; it had in fact already completed (exit code 0, 100/100) by the
  time it was inspected — no command genuinely timed out or was left incomplete.
- A brand-new-project, DB-backed, end-to-end `evaluate_project()` pass through the full
  canonical pipeline specifically exercising Oregon (no existing real project has Oregon spend)
  was **not** run — Oregon coverage here is direct-kernel (`resolve_program_rate`,
  `price_segment`) and unit-level (`oregon_per_payee_capped_total`), not a DB-round-trip
  integration test. The kernel-level tests are exact and literal; the DB-pipeline path was not
  independently exercised for Oregon specifically.

## Files changed (task-owned only)

```
frametax2/backend/app/calculators/allocation_pricing.py
frametax2/backend/app/calculators/contingency_treatment.py
frametax2/backend/app/calculators/jurisdiction_comparison.py
frametax2/backend/app/calculators/qualification_derivation.py
frametax2/backend/app/calculators/qualification_model.py
frametax2/backend/app/data/fund_economics_model.py
frametax2/backend/app/data/global_inventory_extended.py
frametax2/backend/app/data/program_rate_rules.py
frametax2/backend/app/data/program_requirements.py
frametax2/backend/app/models/__init__.py
frametax2/backend/app/models/incentive_award_ledger.py                (new)
frametax2/backend/app/services/canonical_evaluation.py
frametax2/backend/app/services/canonical_production_view.py
frametax2/backend/app/services/incentive_award_ledger_service.py      (new)
frametax2/backend/alembic/versions/0073_incentive_award_ledger.py     (new)
frametax2/backend/tests/test_b3_formulaic_consumption.py
frametax2/backend/tests/test_copro_qualification_wiring.py
frametax2/backend/tests/test_final_formulaic_full_pipeline_consumption.py
frametax2/backend/tests/test_final_wiring_nl_company_period_conservation.py
frametax2/backend/tests/test_final_wiring_selection_predicate.py
docs/validation/CINEGLOBE_FINAL_FOUR_ROW_REMEDIATION_CLOSEOUT_CLAUDE.md (new)
```

Explicitly **excluded** from this commit (pre-existing, unrelated, out-of-scope probe/debug
files — preserved on disk, untouched, not part of this workstream):
`frametax2/backend/tests/test_canonical_economics_integrity_repair.py` (an unrelated debug test
was appended to this file by an earlier, different session — left in place, not committed),
`frametax2/backend/test_four_projects.py`, `frametax2/backend/tests/test_four_projects_print.py`,
`test_conditional.py`, `test_four_projects.py`, `test_four_projects2.py`, `test_four_projects3.py`
(repo root).

## Frozen areas — confirmed unchanged

UI/globe, Script Analyzer, Location suitability, MFNI, Reinvestment, Global research: no files
under any of these areas appear in the diff (`git diff --name-only` checked against each area).
No frontend (`.tsx`/`.jsx`) files touched.
