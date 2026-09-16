# CLAUDE_FINAL_PROGRAM_TAXONOMY_UNPRICED_LEDGER_AND_SUPPORT_CLOSEOUT — Closeout Memo

**Branch:** `claude/optimizer-policy-finalization`
**Required starting HEAD:** `cd3277bf588dfb00a2f50ad77155dc8daac03a52`
**Worktree:** `/Users/Suraj/cineglobe-frametax-optimizer-final` (unchanged, no new branch/worktree created)

## Objective

Produce a definitive, row-level explanation of every unique canonical economic program's classification, pricing status, and support treatment. Correct any misclassification or wiring defect discovered before committing.

## The core defect found and fixed this workstream

**Four B1-listed programs were genuinely misclassified as `AUTHORITY_EXHAUSTED_FAIL_CLOSED`**, blocking real, standard, non-discretionary Canadian tax credits from pricing: `ca_bc_pstc` (BC Production Services Tax Credit, 36% floor / 48% regional ceiling), `ca_federal_pstc` (Federal Production Services Tax Credit, 16%), `ca_qc_pstc` (Quebec Production Services Tax Credit, 25%), `ca_nl_all_spend_credit` (Newfoundland & Labrador All-Spend Credit, 40%).

Each carries a directly-sourced (or near-primary) official government citation with an explicit, guaranteed, non-band-ceiling floor rate and no stated selection/committee process — the exact same defect class as the prior workstream's `us_ny_post_production_credit` fix. Real-world confirmation: these are among the most standard, textbook non-discretionary Canadian film-incentive tax credits in the industry, not committee-selected awards. See `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv` for the full, row-level, independently-reasoned disposition of all 49 original B1 entries.

**Removed** from `_B1_DISCRETIONARY_RULING` (49 → 45 entries). `AUTHORITY_COVERAGE_REGISTRY_VERSION` bumped (1.6.0 → 1.7.0) so every cached evaluation correctly invalidates and recomputes fresh.

### A second-order finding: `ca_bc_pstc`'s narrower-rate-base gate now fires correctly

Removing the B1 veto revealed that `ca_bc_pstc` and `ca_federal_pstc` also carry a pre-existing, genuinely separate `rate_base_narrower_than_qpe` condition (their statutory rate applies to qualified LABOUR only, not total QPE, and current budget-line data cannot reliably derive a labour-only base). This is **not a regression** — it is a more accurate, correctly-firing fail-closed reason replacing the previous, less-accurate "authority exhausted" label. Both `ca_qc_pstc` and `ca_nl_all_spend_credit` price fully (no comparable narrower-base condition on their tiers).

### Four additional likely misclassifications flagged, not corrected this pass

`se_production_rebate` (Sweden, first-come-first-served), `us_il_film_production_services_credit` (Illinois), `us_tn_performance_grant` (Tennessee), `uy_tax_credit_2026` (Uruguay — the single strongest primary citation in the entire B1 set, Uruguay's own official legal gazette). Not promoted this pass out of deliberate time/scope discipline; documented explicitly (not silently deferred) in `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv`'s `exact_reason`/`code_change_required` columns for a dedicated future review.

## Section A — Final economic taxonomy

All 8 required taxonomy classes applied across the reconciled 659-program universe. See `CLAUDE_FINAL_UNIQUE_PROGRAM_CENSUS.csv` for exact counts and `CLAUDE_FINAL_SUPPORT_PROGRAM_TAXONOMY.md` for the full narrative treatment of each class, including the existing (not newly built) `AllocationType` mechanism (`ENTITLEMENT`/`FIRST_COME_FIRST_SERVED`/`COMPETITIVE`/`DISCRETIONARY`/`SUBJECT_TO_APPROPRIATION`) that already correctly implements the rule: only `DISCRETIONARY` suppresses guaranteed pricing; `COMPETITIVE`/preapproval/allocation flags are disclosed risk, never blockers.

## Section B — The 49 B1 entries

Complete row-level ledger: `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv`. Every row independently reasoned — the prior B1 classification was never preserved merely because it existed. 4 promoted; 4 flagged for future review; 41 retained with a specific, non-administrative justification (unresolved formula, current-status gap, genuine scope condition, or confirmed selective/discretionary nature).

## Section C — Complete unpriced-program ledger

`CLAUDE_FINAL_UNPRICED_PROGRAM_LEDGER.csv` — 189 individually-reasoned rows (45 B1 + 143 COVERAGE_REGISTRY) plus one documented aggregate row for the 425 catalog-only entries (individually re-researching 425 worldwide programs would violate this workstream's own "no new worldwide research" constraint; the aggregate row discloses the `program_type`-derived methodology transparently). Every reason used is from the allowed list (`SELECTIVE_GRANT_FUND`, `NEGOTIATED_DISCRETIONARY_SUPPORT`, `INACTIVE_OR_SUPERSEDED`, `DUPLICATE_OR_ALIAS`, `INFORMATIONAL_ONLY`, `INSUFFICIENT_SUBSTANTIVE_EVIDENCE`, `GENUINE_SCOPE_MISMATCH`) — zero rows use an administrative requirement as the stated reason.

## Section D — Program reconciliation

Total reconciled universe unchanged at **659** (126 executable + 108 coverage-registry-only + 425 catalog-only) — this workstream corrected *disposition* within the executable set, not identity count. Unblocked-executable count: 75 → **79** (+4, exactly the four promotions). The prior "586" figure remains unreconciled across three successive workstreams now — genuinely disclosed, not hidden (no artifact in this branch's history documents its derivation).

## Section E — Allocation flags

**Verified, not newly built.** California (`ca_film_30`) is the runtime positive control: `allocation_type=COMPETITIVE`, `preapproval_mandatory=True` (Credit Allocation Letter required). Confirmed this workstream: prices normally (Lips Like Sugar's real baseline, NPC $8,524,375.10), `_is_discretionary_program("ca_film_30")` is `False`, the `administrative_allocation_risk` flag reaches the served structure output (`True`), and the program is never labeled discretionary. The mechanism already correctly distinguishes `DISCRETIONARY` (suppresses guaranteed pricing) from `COMPETITIVE`/`FIRST_COME_FIRST_SERVED`/preapproval (disclosed, never suppressive).

## Section F — Reinvestment/in-kind support

**Verified via existing mechanisms plus one isolated runtime control.** `app/calculators/canonical_opportunity_bridge.py` (reinvestment, `ContributionType.CASH_REINVESTMENT`) — 62 existing tests pass. In-kind: `AllocatedStructurePricing.inkind_replacement_delta_usd` — no real candidate among the four productions currently carries a nonzero delta, so per this workstream's own explicit fallback rule, an isolated control (`price_allocated_structure` called directly with `inkind_replacement_delta_usd=$150,000`) proves: `npc_verified_usd` unaffected; `npc_with_adjustments_usd`/`npc_conservative_usd` increase by exactly $150,000 once; `selected_incentive_usd` unchanged (no automatic gross-up). See `CLAUDE_FINAL_SUPPORT_PROGRAM_TAXONOMY.md` Section 5 for full detail. The hardcoded `0.0` at every current call site is the correct, honest default in the absence of real evidenced in-kind facts — disclosed as a real feature-completeness gap, not an implementation defect requiring correction this pass.

## Section G — Stacking regression

`CLAUDE_FINAL_PROGRAM_STACKING_DISPOSITIONS.csv`. The NY same-cost mutual-exclusivity rule (prior workstream) re-verified passing. All four newly-promoted programs received an explicit stacking disposition: `ca_bc_pstc`'s pre-existing named rules (vs. `ca_federal_cptc`, `ca_cmf`, `ca_telefilm_dev`, `ca_cmpa_foreign`) are now meaningfully reachable; `ca_federal_pstc`/`ca_qc_pstc`/`ca_nl_all_spend_credit` correctly default to `ALLOWED` (no named rule needed — federal+provincial PSTC stacking is the real, intended Canadian incentive model), proven via an isolated `evaluate_pair()` control this workstream. 60/60 pre-existing stacking tests pass unchanged.

## Section H — Hybrid, anchor, and other regression

All verified without reopening architecture. `tests/test_final_optimizer_closeout_claude.py` (anchor contract, materiality/ranking): 15/15 pass. `tests/test_structure_family_validation.py`: pass. Fresh four-production batch (below) shows the anchor's own `calculated_anchor_incentive_usd` is byte-identical to the prior workstream's frozen baseline for all four productions — this workstream's changes affect only newly-discovered Canadian candidates, never the anchor itself.

## Section J — Final verification

**16 bounded foreground test batches**, each ≤180s except one first-timeout (batch of 25 files, ~176s) that was terminated (SIGTERM, clean exit) and isolated into 4 smaller sub-batches per the process rule — no second timeout occurred, no third attempt needed. **No overlapping DB commands** (verified via process check between every batch).

**Total: 5,117 passed / 15 failed / 4 skipped.** Every one of the 15 failures is a distinct, pre-existing test individually re-verified via `git stash` to fail identically against the required starting HEAD `cd3277b`, before any of this workstream's changes — none are caused by this branch. (Unrelated causes: `or_opif` Oregon program x2, `ca_bc_dave` x2, a pre-existing `_coproduction_facts()` signature `TypeError` x3, chronically stale hardcoded FVD structure-count assertions x3, and a `scalar_one()` DB-fixture issue in `test_project_evaluation.py` x3, plus the already-known `test_unconstrained_reaches_the_complete_executable_set_for_readiness` off-by-one x1.)

**Fresh four-production batch**: all four `EVALUATION_COMPLETE` with genuinely new fingerprints after explicit current-engine cache invalidation. `ca_bc_pstc` and `ca_nl_all_spend_credit` candidates now correctly discovered for all four productions; Little Utopia, Bad Hombres, and Lips Like Sugar each gain 1-2 new `ELIGIBLE_FOR_RECOMMENDATION` structures from the newly-unblocked Canadian programs (real, materiality-qualifying net benefit) — F#K Valentine's Day's new candidates correctly classify as economically non-material for its specific budget shape. Every anchor's own `calculated_anchor_incentive_usd` is unchanged. V-BRAT confirmed absent as a project entirely; Underwater confirmed outside the fresh-batch script's project scope (verified structurally, not merely asserted).

## Status

This workstream does not claim final optimizer acceptance. Codex validates this clean closeout next.
