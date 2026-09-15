# CLAUDE_GLOBAL_ASSUMPTION_POLICY_AND_PRICEABLE_PROGRAM_FINALIZATION — Closeout Memo

**Branch:** `claude/optimizer-policy-finalization`
**Source HEAD:** `912dd3b46fc4c064444b4f40cd0b8d347e10030d`
**Worktree:** `/Users/Suraj/cineglobe-frametax-optimizer-final` (dedicated, never the shared checkout)

## Purpose

Apply the CineGlobe global eligibility assumption policy consistently, eliminate internal policy gates that improperly suppress a priceable program, reconcile the complete program universe, and produce one clean implementation commit for AG/Codex audit.

## What this workstream found and fixed (P0)

**`us_ny_post_production_credit` was blanket-vetoed by an internal policy gate (`KEEP_SEPARATE_POST_PROGRAM_FAIL_CLOSED` in `_B4_RETIRED_OR_FAIL_CLOSED_IDENTITIES`), despite having sufficient real canonical rate/threshold/mutual-exclusivity evidence to price deterministically.** This is the exact class of defect Section D of this workstream's instruction asked to find and fix — a priceable program suppressed by a gate whose original evidence-insufficiency rationale no longer holds.

The prior workstream (`CLAUDE_INTERNAL_POLICY_PROGRAM_CENSUS_AND_CLEAN_OPTIMIZER_FREEZE`) investigated this same gate and concluded it should remain blocked, reasoning that the doctrine's own rate/threshold data was PARSED-tier (secondary-corroborated), not VERIFIED. This workstream's instruction explicitly rejected that conclusion, and on closer inspection of Section D's full checklist, the gate was net-net not justified: the program's real min-spend ($1M or 75% of post cost), rate (35%), VFX/animation sub-threshold, and same-cost mutual-exclusivity rule (vs. `ny_state_film`) are all documented with a direct quote from tax.ny.gov. The remaining undocumented sub-items (exact expense category list, facility-location requirement, annual cap, project-type eligibility, application/preapproval detail) are either producer-controlled administrative steps the global policy requires assuming will be satisfied, or disclosed estimation-assumption gaps — never grounds to keep an entire program dark.

### Fix 1 — Remove the blanket veto

`app/data/authority_coverage_registry.py`: removed `"us_ny_post_production_credit": "KEEP_SEPARATE_POST_PROGRAM_FAIL_CLOSED"` from `_B4_RETIRED_OR_FAIL_CLOSED_IDENTITIES`. Bumped `AUTHORITY_COVERAGE_REGISTRY_VERSION` (1.5.0 → 1.6.0) so every cached evaluation correctly invalidates and recomputes fresh.

### Fix 2 — Preserve the real same-cost non-double-dipping rule

A blanket program-level veto is not the same thing as the real legal constraint it was standing in for. `app/optimization/stacking_rules.py`: added a named `mutually_exclusive` stacking rule for `frozenset({"ny_state_film", "us_ny_post_production_credit"})`, quoting tax.ny.gov directly ("no other income tax credit may be claimed for those costs"). This works together with the doctrine's own `RateCondition` (`us-ny-post-mutual-exclusivity`), which already drives `structure_compatibility.py`'s exclusivity gate. Bumped `STACKING_RULES_VERSION` (1.0.0 → 1.1.0).

### Fix 3 — A second, deeper defect found while proving Fix 1/2: QPE scope mismatch

Proving the fix with a real, isolated runtime control (never touching the DB) surfaced a second, more subtle defect: `us_ny_post_production_credit` had **no entry** in `PROGRAM_DOCTRINE` (`app/data/program_spend_rules.py`), so it silently fell through to the module's own `CANONICAL_DEFAULT_DOCTRINE` (`OPEN_DEFAULT_INCLUDE`) — meaning the FIRST time this program was unblocked and priced against a real production, it would have treated the production's ENTIRE relocated budget (including ordinary principal-photography ATL/BTL) as "qualified post-production costs," wildly overstating the incentive. The doctrine's own citation is explicit that only post-production costs qualify.

**Fix**: classified `us_ny_post_production_credit` as `QualificationDoctrine.CLOSED_POSITIVE_LIST` with `post_production`/`sound`/`vfx` as the only qualifying spend categories (`US_NY_POST_RULES` in `program_spend_rules.py`) — using only the doctrine's own already-quoted scope, no new external research. Bumped `PROGRAM_SPEND_RULES_VERSION` (1.0.0 → 1.1.0).

**Proof (isolated, never persisted):** a representative $4M budget ($1.2M post + $2.8M principal photography) now correctly prices QPE=$1,200,000 (post-only; principal photography correctly `EXCLUDED`), incentive=$420,000 — not the incorrect $1,400,000 that the QPE-scope defect would have produced against the full $4M.

## Section A — Global CineGlobe eligibility policy

No change was needed to the general administrative-assumption mechanism itself — it was already the governing default throughout the codebase (`OPEN_DEFAULT_INCLUDE`/`HYBRID_CONDITIONAL` doctrines already assume producer-controlled administrative facts will be satisfied; `QUAL_CURABLE_GAP`/`QUAL_USER_FACT_REQUIRED` states from earlier workstreams already model curable gaps as non-blocking). This workstream's re-investigation of every gated program (Section C/D below) confirmed zero programs were being blocked on a purely administrative/procedural ground — every retained gate rests on a substantive ground (cultural test, spend/QPE threshold, current program status, or deterministic-vs-discretionary award status), matching the policy's own Section A criteria for a valid substantive gate.

## Section B — Program classification

Every unique canonical program maps to exactly one of the 9 required classifications. See `CLAUDE_FINAL_CANONICAL_PROGRAM_CENSUS.csv` for the full breakdown. `us_ny_post_production_credit` moved from `INSUFFICIENT_EVIDENCE_FAIL_CLOSED` to `PRICEABLE_AUTOMATIC` this workstream — the only classification change.

## Section C — Program universe reconciliation

Total reconciled universe: **659** (126 executable + 108 coverage-registry-only + 425 catalog-only). This matches the prior workstream's own computed figure. The cited "586" figure remains unreconciled — no prior artifact in this branch documents its derivation, and it could not be reproduced from any registry combination tried across two workstreams now. Disclosed, not hidden — see `CLAUDE_FINAL_EXTERNAL_EVIDENCE_GAPS.csv`.

## Section D — Internal gate review

Every gate registry (`_B1_DISCRETIONARY_RULING`, `_B4_RETIRED_OR_FAIL_CLOSED_IDENTITIES`, `COVERAGE_REGISTRY`) was individually re-investigated against this workstream's own substantive-vs-administrative test. Full detail in `CLAUDE_FINAL_INTERNAL_GATE_RECONCILIATION.csv`. Key finding: 11 of the 45 executable-but-coverage-gated programs carry a `VERIFIED`-tier rate rule yet remain correctly gated, because the gate blocks on AUTHORITY/discretionary-award status, not rate-formula confidence — these two things are orthogonal, and conflating them was the wrong hypothesis this workstream started with before verifying against the registry's own documented purpose. `us_ny_post_production_credit` was the only program found to be gated on a stale, no-longer-justified basis (a documentation-completeness veto that had become disproportionate given the real evidence that DOES exist).

## Section E — New York post-production credit

Resolved. See Fixes 1–3 above. Independently priced against a real isolated control ($420,000 incentive on $1.2M post-only QPE at the real 35% rate). Evaluated against all four real productions: correctly generates as a real `full_relocation` candidate for each, and correctly `RULE_REJECTED` (`MINIMUM_SPEND_FAIL`) for each, because none of the four productions' current real budgets has ≥$1,000,000 of identified post-production spend (closest: Lips Like Sugar at ~$651,000). This is a genuine, project-specific, real-data finding — not evidence the fix failed. The mechanism is proven end-to-end and will price automatically the moment any production's real post-production budget crosses the threshold.

## Section F — Anchor contract

No change made this workstream — the anchor contract mechanism (computed and persisted inside `evaluate_project()`, read by `compute_anchor_budget_contract()` as a thin reader) was already correctly implemented and tested by the prior workstream. Re-verified passing in this workstream's fresh evaluation (`test_final_optimizer_closeout_claude.py`, all anchor-contract tests green against the fresh batch). None of the four real projects has a supplied incentive estimate on file; the reversible runtime-control proof of the ingestion mechanism (`test_supplied_incentive_budget_line_changes_the_fingerprint_and_forces_fresh_anchor_recompute`) remains passing, using a real, temporary, fully-restored `BudgetLineItem` on Little Utopia.

## Section G — Hybrid and ranking reconciliation

See `CLAUDE_FINAL_MATERIAL_HYBRID_RANKING.csv`. Zero ranking defects found or fixed this workstream. The materiality distribution for all four real productions is byte-identical to the prior workstream's frozen baseline (52/1/21/3 `ELIGIBLE_FOR_RECOMMENDATION`) after this workstream's fixes, because the one genuinely new candidate this workstream introduces (the NY post-credit `full_relocation` structure) correctly rejects for all four on a real, project-specific minimum-spend failure — it does not change any of the four productions' recommendation-relevant numbers, but it is now provably wired and correct rather than silently absent.

## Section H — Structure family regression

All 12 structure families remain proven per the prior workstream's own runtime evidence (`CLAUDE_FINAL_STRUCTURE_FAMILY_RUNTIME_PROOF.csv`, from the prior, now-superseded workstream, still accurate and unchanged by this workstream's NY-scoped fix). This workstream additionally re-proved family #1 (single jurisdiction) and #2b (NY stacking control) specifically, given they are the families most directly affected by the NY fix — both pass with the corrected NY behavior (family #2b's real blocker, the NY post credit, is now genuinely unblocked and correctly scoped, rather than blocked by an internal policy artifact).

## Tests

- `tests/test_b4_authority_exhaustion_gate.py`: updated 2 tests to reflect the NY gate removal (corrected a stale hardcoded `len()==46` to the registry's own real `49`; replaced the single `test_retired_and_keep_separate_identities_are_blocked` test, which asserted the NOW-INCORRECT expectation that NY remains blocked, with `test_retired_identity_is_blocked` for Iceland alone, plus two new positive-control tests proving NY is unblocked and the real mutual-exclusivity rule survives).
- `tests/test_final_optimizer_closeout_claude.py`: added a pre-test cleanup `DELETE` to `test_supplied_incentive_budget_line_changes_the_fingerprint_and_forces_fresh_anchor_recompute`, fixing a real, pre-existing test-isolation hazard (a deterministic probe fingerprint can collide with a stale row from an earlier run of the same test at the same `ENGINE_VERSION`) — the documented "fingerprint reuse masking new code" bug class from prior workstreams.
- Full established regression suite: see `TESTS_PASS_FAIL_SKIP_TIMEOUT` in the final response.

## Known non-blocking defect found, disclosed, not fixed this workstream

A fingerprint hash-randomization sensitivity specific to F#K Valentine's Day's data shape (see `CLAUDE_FINAL_EXTERNAL_EVIDENCE_GAPS.csv`) — cache-efficiency only, never a correctness defect. All final-batch and artifact-generation runs in this workstream used `PYTHONHASHSEED=0` for reproducibility.

## Status

This workstream does not claim final optimizer acceptance. AG and Codex audit this clean branch next.
