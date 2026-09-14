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

Fix (fifth pass): the SAME generic line-reconciliation mechanism built for South Africa was
reused. `price_segment()`'s reconciliation block derives (or validates an exact-match caller
scalar against) the real qualifying line subtotal for payroll/other, and — specifically for the
payroll basis — applies `oregon_per_payee_capped_total()` (OAR 951-002-0010's real
USD1,000,000 per-payee exclusion) to each contributing traced line's own amount *before*
summing, so `oregon_per_payee_capped_total` is now a genuine, invoked production dependency, not
merely test-called. A caller-asserted basis with no exact relationship to the real,
per-payee-capped canonical lines is rejected before any candidate is priced or persisted —
closing the negative-NPC reproducer at the source. The existing combined-USD1,000,000 threshold,
multiplicative 1.10 uplift, and dated USD10,600,000 fund cap are unchanged.

**Sixth-pass correction (this pass) — the real DB pipeline surfaced two further defects the
fifth pass's kernel-only tests could not see:**

1. **Wrong reconciliation dimension.** The fifth pass matched Oregon's payroll/other bases
   against `AccountAllocation.component` values `"payroll"`/`"production"`/`"other"` — but the
   real production composer (`production_allocation.component_for`) *never emits those values*;
   it only ever produces `post`/`vfx`/`music`/`above_the_line`/`travel_and_living`/`overhead`/
   `administration`/`principal_photography`. The mechanism was correct in isolation but
   unreachable through any real, composer-built allocation. Fixed with a new
   `RateCondition.component_basis_spend_categories` field (and
   `component_basis_spend_categories_exclude` for the complement side) that matches on the real,
   composer-reachable `spend_category` dimension instead — labor categories
   (`atl_writer`/`atl_director`/`atl_producer`/`atl_cast`/`btl_crew_labor`/`btl_resident_labor`/
   `btl_nonresident_labor`) for payroll, their complement for other.
2. **Two pre-pricing discovery probes had no access to derived facts.** Both
   `production_discovery.py`'s `resolves_for_production` capability check and
   `canonical_evaluation.py::_price_candidate`'s own preflight call `resolve_program_rate` on a
   candidate *before* any `AccountAllocation`/qualification register exists for it — so a
   composite program's exact, canonical-line-derived facts (only computable inside
   `price_segment`, after allocation) were never available at either point, and a real, eligible
   Oregon production was misclassified `STATUTORY_CONDITIONS_UNMET` before ever reaching real
   pricing. Both now pass the segment's own real qualifying-spend total (`qpe_usd`, already
   computed at that point) as a `us_or_opif`-scoped, PROBE-ONLY value for both composite facts —
   sufficient only to let a real, eligible candidate continue to `price_segment`, whose own
   strict, exact-match, per-payee-capped canonical-line reconciliation (never this probe) remains
   the sole authority for the real priced number.

`tests/test_oregon_full_db_pipeline.py` (new) proves the complete, real, database-backed
pipeline — real `BudgetLineItem` rows (the same structured representation the PDF-ingestion path
itself produces) → discovery → composite formula → per-payee cap → uplift → fund cap →
persistence → retrieval → identical reuse — reproducing the independently expected
**USD814,000** exactly, proving `EVALUATION_COMPLETE` → `EVALUATION_REUSED` with a stable
`structure_id` and exactly one persisted result row both times (no duplicate), rejecting Codex's
exact USD50,000,000/USD50,000,000-vs-USD4,517,687 hostile reproducer before any candidate is
priced (never a negative NPC), and proving the real per-payee cap through the pipeline (a real
USD2,000,000 single payee line prices at USD200,000 — 20% of the capped USD1,000,000, never
USD400,000). Zero skips.

## Focused test results

| Suite | Result |
|---|---|
| `test_final_wiring_nl_company_period_conservation.py` (rewritten: public-writer concurrency, event-transition, idempotency, currency, amount validation, missing-period, isolation) | 23 passed |
| `test_final_wiring_oregon_conditional_formula.py` (rewritten: multi-payee lines, per-payee cap, asserted-mismatch rejection, deterministic no-skip provisional proof) | 11 passed |
| `test_oregon_full_db_pipeline.py` (new, this pass — genuine DB-backed pipeline: positive USD814,000 + persistence + reuse, hostile USD50m/USD50m reject, per-payee cap, missing-data fail-closed) | 4 passed, 0 skipped |
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

- Rather than literally cloning FVD's own 34 real budget-document rows (Codex's own audit
  methodology, which used a scratch script never checked into this repository), this pass built
  an equivalent-in-kind isolated Oregon project from real, structured `BudgetLineItem` rows
  (the same structured representation the real PDF-ingestion path produces, read by
  `canonical_project_economics.py` identically either way). The full pipeline is genuinely
  exercised end to end; the source-row provenance differs only in not being FVD's literal 34
  rows.
- Two harmless, isolated migration-test databases from an earlier pass in this workstream
  (`frametax2_migtest_1789412124`, `frametax2_migtest_fresh_1789412169`) remain undropped —
  `dropdb` was denied twice by the Bash tool's own destructive-action permission layer in that
  earlier session; not forced.

## Frozen areas — confirmed unchanged

Selection (P0-SEL-ALT-001), UI/globe, Script Analyzer, Location suitability, MFNI, Reinvestment,
Stacking research, treaties/co-production logic, and every other canonical program: no files
under any of these areas appear in this pass's diff. No frontend files touched. The full backend
suite was not run (out of scope per the controlling prompt).
