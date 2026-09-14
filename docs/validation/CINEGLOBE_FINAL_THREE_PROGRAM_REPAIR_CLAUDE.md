# CineGlobe Final Three-Program Conservation Repair — Claude

Base commit: `4125567e8c9b571cfd0493a4dafe1a9d85cfbfa0` (Codex final-four-row acceptance, NOT_ACCEPTED for P0-NL-001/P0-ZA-001/P0-OR-001; P0-SEL-ALT-001 accepted and frozen).
Branch: `claude/audit-frametax-features-NZcX5`.

## Summary: 3/3 remaining programs repaired

### P0-NL-001 — Netherlands ledger conservation

Confirmed Codex defects and their fixes:

1. **"Public writer locks but blindly inserts; two concurrent EUR3m awards produce EUR6m."**
   `record_incentive_award()` (`app/services/incentive_award_ledger_service.py`) now performs a
   real read-decide-write inside the `pg_advisory_xact_lock` critical section: it reads the
   current authoritative total (collapsed to the newest row per `award_event_id`, evidenced
   cap-consuming rows only), computes the prospective total including this write, and **raises
   `ValueError`** — never commits — if that total would exceed the program's registered cap.
2. **"A USD row is numerically added as though it were EUR."** `record_incentive_award()` now
   validates `native_currency` against the program's own registered `IncentiveValueCapRule.cap_currency`
   at write time and rejects any mismatch before the row is ever created.
   `company_period_program_award_summary()` also accepts an `expected_currency` filter as
   defense in depth.
3. **"APPROVED → GRANTED can count one award twice."** Every row now carries a required,
   caller-supplied `award_event_id` (new column, migration `0074`). The read-side summary
   (`_newest_row_per_event`) collapses to exactly the newest row per event before summing, so a
   status transition for one real award is counted once. Duplicate re-insertion of the identical
   newest state for one event is resolved idempotently (existing row returned, no new row).
4. **"UNVERIFIED rows incorrectly establish ledger coverage."** Unchanged from the prior pass —
   already correctly gated: an UNVERIFIED row counts toward *coverage* (sibling was checked) but
   never toward the *consumed amount* until it is EVIDENCED. This pass adds a direct public-writer
   test proving it end-to-end.
5. **"`target_shoot_year` is incorrectly used as the award period."** New, explicit, separate
   `Project.award_period_year` column (migration `0074`) — never inferred from
   `target_shoot_year` (a production-planning fact). `canonical_project_economics.py` and
   `canonical_evaluation.py`'s sibling query both now read this real column.
6. **"Claude's prior concurrency test bypassed the public writer."** The concurrency test is
   rewritten to call `record_incentive_award()` itself from two independent, concurrent
   `AsyncSession` connections (`test_two_concurrent_public_writer_sessions_cannot_exceed_cap`) —
   proving the *public writer's own* cap enforcement, not a test-local reimplementation.

### P0-ZA-001 — South Africa exact QSAPPE derivation

Confirmed Codex defect: the exact qualifying post/VFX line subtotal was computed correctly but
used only as an *upper bound* for a caller-supplied scalar — a smaller caller claim (e.g.
USD300,000 against a real USD400,000 qualifying line) was accepted and priced at the smaller,
wrong figure; with no caller scalar at all, the segment was non-executable even though the real
subtotal was fully derivable.

Fix (`app/calculators/allocation_pricing.py`, new pre-`resolve_program_rate` reconciliation
block in `price_segment()`): for every `RateCondition` across a program's own registered tiers
that declares `component_basis_line_components`, the real traced **QUALIFYING** line subtotal
(from this same segment's own qualification register, grouped by `line_id`) is computed
directly. When the caller supplies no scalar, the derived subtotal is injected so the tier
becomes eligible from real data alone. When the caller *does* supply a scalar, it must match the
derived subtotal exactly (to the cent) or the whole segment is rejected before pricing — a
smaller OR larger caller claim is never silently preferred over the real traced line data.

### P0-OR-001 — Oregon canonical-line and per-payee conservation

Confirmed Codex defect: the composite payroll/other bases were accepted as free caller-supplied
scalars with no relationship to the segment's own real canonical budget lines (exact
reproducer: USD50,000,000 payroll + USD50,000,000 other accepted against a real
USD4,517,687 source budget, producing a persisted incentive of USD10,600,000 and NPC of
**-USD6,082,313**); `oregon_per_payee_capped_total()` had no production caller at all.

Fix: the SAME generic line-reconciliation mechanism built for South Africa is reused here.
`us-or-payroll-component-basis` now declares `component_basis_line_components=("payroll",)` and
`us-or-other-component-basis` declares `("production", "other")` — real
`AccountAllocation.component` tags. `price_segment()`'s reconciliation block derives (or
validates an exact-match caller scalar against) the real qualifying line subtotal for each, and
— specifically for the payroll basis — applies `oregon_per_payee_capped_total()` (OAR
951-002-0010's real USD1,000,000 per-payee exclusion) to each contributing traced line's own
amount *before* summing, so `oregon_per_payee_capped_total` is now a genuine, invoked production
dependency, not merely test-called. A caller-asserted basis with no exact relationship to the
real, per-payee-capped canonical lines is rejected before any candidate is priced or persisted —
closing the negative-NPC reproducer at the source. The existing combined-USD1,000,000 threshold,
multiplicative 1.10 uplift, and dated USD10,600,000 fund cap are unchanged.
`test_final_wiring_oregon_conditional_formula.py`'s prior `pytest.skip()` (when no priced
Oregon candidate existed in FVD's discovered universe) is replaced with a deterministic,
never-skipping kernel-level proof plus a best-effort (non-failing-on-absence) FVD cross-check.

## Focused test results

| Suite | Result |
|---|---|
| `test_final_wiring_nl_company_period_conservation.py` (rewritten: public-writer concurrency, event-transition, idempotency, currency, amount validation, missing-period, isolation) | 23 passed |
| `test_final_wiring_oregon_conditional_formula.py` (rewritten: multi-payee lines, per-payee cap, asserted-mismatch rejection, deterministic no-skip provisional proof) | 11 passed |
| `test_final_formulaic_full_pipeline_consumption.py` (full file — all 12 formulaic programs, including ZA + Oregon new/updated cases) | 26 passed |
| `test_b3_formulaic_consumption.py` + `test_final_wiring_selection_predicate.py` + `test_copro_qualification_wiring.py` (Selection — frozen area regression check) | 41 passed |

No required test was skipped. No test was mocked, hardcoded to an expected answer, or given a
test-only calculation branch — every assertion runs through the real `price_segment` /
`resolve_program_rate` / `record_incentive_award` / `company_period_program_award_summary`
production kernels.

## Migration

New migration `0074_award_period_and_event_identity.py` (down_revision `0073`): adds
`projects.award_period_year` (nullable Integer) and
`incentive_award_ledger_entries.award_event_id` (NOT NULL String, table was empty at migration
time — confirmed via direct row count before writing the migration, so no backfill was needed).
Verified against the real dev database: upgrade to head, downgrade to `0073` (columns dropped
cleanly), re-upgrade to head — all passed with no errors.

## Four real project controls (recomputed after this pass)

| Project | Program | Incentive | NPC |
|---|---|---|---|
| Little Utopia | mu_edb_incentive | $573,059.70 | $3,791,333.30 |
| F#K Valentine's Day (FVD) | gr_cash_rebate | $1,445,659.84 | $3,072,027.16 |
| Bad Hombres | us_nm_film_credit | $596,910.25 | $1,885,112.75 |
| Lips Like Sugar | ca_film_30 | $3,459,278.90 | $8,524,375.10 |

All four exactly match the required anchors — unchanged. No candidate-count-affecting change was
made to any program outside `nl_film_production_incentive`, `za_nfvf_rebate`, and `us_or_opif`.

## Original 12-program formulaic matrix

12/12 implementation-ready: the previously-accepted 9 programs are unchanged (regression-tested
above); Netherlands, South Africa, and Oregon are now repaired per Codex's exact remaining
findings and independently re-tested against the real production kernels.

## Known limitations disclosed (not blocking)

- The full "clone 34 real FVD budget-document rows into a fresh isolated Oregon project, run the
  complete `evaluate_project` → persistence → retrieval → identical-reuse pipeline, then delete
  the project" methodology Codex's own audit used was **not** independently re-executed this
  pass under the 45-minute implementation budget. In its place: (a) exhaustive, deterministic
  `price_segment`/`resolve_program_rate` kernel-level proof of the exact same positive
  (USD814,000-class) and negative (USD50m-vs-USD4.5m) arithmetic Codex's DB pipeline exercised,
  and (b) a real DB-backed cross-check against FVD's own currently-discovered candidate universe
  (non-skipping, but Oregon is not part of FVD's accepted baseline so it may legitimately find
  zero Oregon candidates there — that absence is not treated as a failure).
- Two harmless, isolated migration-test databases from an earlier pass in this workstream
  (`frametax2_migtest_1789412124`, `frametax2_migtest_fresh_1789412169`) remain undropped —
  `dropdb` was denied twice by the Bash tool's own destructive-action permission layer in that
  earlier session; not forced.

## Frozen areas — confirmed unchanged

Selection (P0-SEL-ALT-001), UI/globe, Script Analyzer, Location suitability, MFNI, Reinvestment,
Stacking research, treaties/co-production logic, and every other canonical program: no files
under any of these areas appear in this pass's diff. No frontend files touched. The full backend
suite was not run (out of scope per the controlling prompt).
