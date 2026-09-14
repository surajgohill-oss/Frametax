# CineGlobe Final Four-Row Acceptance — Codex

**Target:** `fe55ceaf72e08c4e21823137c76d0cdeec3f90f6`

**Required ancestor:** `9afc24d0f0185079c8bc6f70bd3cd78f2e0a76e7`
**Verdict:** **NOT_ACCEPTED**

This was a delta-only engineering and runtime acceptance. No external research, production-code edits, full-suite run, or permanent project mutation was performed.

## Results

| Control | Result | Independent evidence |
|---|---|---|
| P0-SEL-ALT-001 | **ACCEPTED** | LU remains anchored to `mu_edb_incentive`; Manitoba is the distinct conditional with the rule-data gap plus all four CA-MB relocation dimensions. FVD remains anchored to `gr_cash_rebate`; Greece+Romania is distinct and retains Greek `gr_aggregate`, Romanian cultural disposition, both administrative disclosures, and all four RO relocation dimensions. Synthetic exact-equality/mutation-sensitive blocker tests pass. Bad Hombres and Lips remain selected and unchanged. |
| P0-NL-001 | **NOT_ACCEPTED** | Two concurrent calls through the actual public `record_incentive_award()` service each recorded EUR3,000,000; the summary returned EUR6,000,000. The service locks but never reads remaining capacity or enforces the cap. A USD1,000,000 row was then numerically added to the native total as if EUR, producing 7,000,000. Append-only status transitions also lack award identity and can double-count one real award. An UNVERIFIED row counts as complete ledger coverage. The project-side period remains `target_shoot_year`, not an explicit award period. |
| P0-ZA-001 | **NOT_ACCEPTED** | With one exact qualifying Post line of USD400,000, an exact claim prices USD100,000, but a USD300,000 caller claim also prices USD75,000. With no caller scalar, the row is non-executable. The implementation calculates an upper bound, not the exact line-derived QSAPPE required by the acceptance gate. |
| P0-OR-001 | **NOT_ACCEPTED** | A real isolated DB project cloned from FVD's 34 canonical budget rows successfully discovers, prices, persists and reuses `us_or_opif`; a valid USD1.2m payroll/USD2m other split with 10% uplift produces the independently expected USD814,000. However, the same full pipeline accepts USD50m payroll + USD50m other facts against a USD4,517,687 source budget, persists the USD10.6m cap and produces NPC **-USD6,082,313**. `oregon_per_payee_capped_total()` has no production caller. Therefore canonical line reconciliation and per-payee consumption are not implemented. |

## Exact code findings

### Netherlands

- `app/services/incentive_award_ledger_service.py:92-130` acquires the advisory lock and blindly inserts/commits. It performs no read-decide-write cap check.
- `app/services/incentive_award_ledger_service.py:76-89` sums all evidenced APPROVED/GRANTED rows without award-event identity, supersession, currency validation, or cap validation.
- `app/models/incentive_award_ledger.py:122-126` has only a non-unique lookup index; no unique award identity or integrity constraint exists.
- `app/services/canonical_project_economics.py:686-691` still binds `award_period_year` to `Project.target_shoot_year`.
- Claude's concurrency test at `tests/test_final_wiring_nl_company_period_conservation.py:682-705` implements its own safe read-decide-write sequence instead of calling the public writer under test, masking the defect.

The `0072 → 0073 → 0072 → head` migration cycle passed on a task-owned database, which was then dropped. Schema reversibility does not cure the ledger semantics.

### South Africa

- `app/calculators/allocation_pricing.py:956-965` correctly derives an exact qualifying line subtotal.
- `app/calculators/allocation_pricing.py:971-987` rejects only values outside `[0, subtotal]`; it does not require equality or use the derived subtotal as the basis. An arbitrary smaller scalar therefore prices.

### Oregon

- `app/data/program_rate_rules.py:2063-2086` trusts two generic amount facts and never reconciles their sum or membership to the segment's canonical lines.
- `app/data/program_rate_rules.py:2022-2042` defines the per-payee helper, but repository search finds no production call; only tests call it.
- Claude's purported DB-backed provisional test explicitly skips at `tests/test_final_wiring_oregon_conditional_formula.py:135-137` when no priced Oregon candidate exists. The focused run therefore reported one skip rather than proving that gate.
- Legacy `or_opif` references are alias-bound to `us_or_opif`; one canonical Oregon candidate was observed and no separate Greenlight candidate was generated. This avoids current double counting, but Greenlight is only narrative data and not a consumed interaction.

## Four-project controls

All accepted economics and candidate counts are unchanged from the pre-delta Codex artifact:

| Project | Candidates / priced / unpriceable | Anchor | Incentive | NPC |
|---|---:|---|---:|---:|
| Little Utopia | 241 / 124 / 117 | `mu_edb_incentive` | $573,059.70 | $3,791,333.30 |
| F#K Valentine's Day | 292 / 159 / 133 | `gr_cash_rebate` | $1,445,659.84 | $3,072,027.16 |
| Bad Hombres | 238 / 122 / 116 | `us_nm_film_credit` | $596,910.25 | $1,885,112.75 |
| Lips Like Sugar | 294 / 175 / 119 | `ca_film_30` | $3,459,278.90 | $8,524,375.10 |

Candidate-count delta: **zero for all four projects**.

## Test boundary

- Claude owning tests: **55 passed, 1 skipped, 18 deselected** in 117.71 seconds.
- Independent negative probes: Netherlands actual-service concurrency/currency failure; ZA smaller-scalar mismatch; Oregon kernel conservation failure; Oregon genuine DB full-pipeline conservation failure.
- Oregon positive DB path: canonical clone → discovery → pricing → candidate persistence → retrieval → identical reuse; USD814,000 exact.
- Migration: upgrade, downgrade and reapply passed.
- Timed-out commands: **0**.

## Gate

- Selection predicate: **accepted**.
- Formulaic program matrix: **9/12 accepted**, unchanged; Netherlands, South Africa and Oregon remain open.
- Full-pipeline consumption: **not accepted**.
- Remaining four-row items: **3**.
- Safe to leave the global incentive wiring phase: **NO**.

The smallest bounded repair is recorded in `CINEGLOBE_FINAL_FOUR_ROW_REMAINING_CODEX.csv`.
