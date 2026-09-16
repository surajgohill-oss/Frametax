# CLAUDE_GLOBAL_OPTIMIZER_REMEDIATION_FROM_CODEX_ORACLE

**Canonical branch:** `claude/global-optimizer-remediation`
**HEAD_BEFORE:** `705d368fefcff2f63928d627589ffc069fd1c6d5`
**Codex audit consumed:** `origin/codex/final-optimizer-audit` @ `8cc1622dd102939762c2e1bdfc788eadac8c7ce0`
**Engine:** `canonical-1.65.0` → `canonical-1.67.0`; authority coverage registry `1.7.0` → `1.8.0`

## Summary

Two P0 calculation defects are fixed and independently verified against Codex's own oracle. A real, deep second-order defect (a "ceiling-with-a-real-floor" program's floor incentive silently computed off the whole segment instead of its own real component basis) was discovered and fixed while verifying the stacking work — this was not in Codex's findings and was caught only because the new tests assert an exact independent dollar figure, not merely "does it price." 21 further programs (3 Canadian labour-base + 18 STATUTORY_FORMULAIC) are unblocked from a stale authority-exhausted registry, extending an established, already-accepted precedent from a prior workstream. 4 of Codex's 6 named executable stacking pairs now generate with the correct disposition; 2 remain unfixed with the root cause disclosed. Two of Codex's own rate/cap claims (Montenegro, Portugal) were independently investigated and **rejected** — my research does not support them, and in Montenegro's case actively contradicts them. Combined co-production hybrids and residency/contribution input-wiring were diagnosed with a confirmed root cause but **not implemented** — this is real, substantive, unfinished work, disclosed honestly below and in `REMEDIATION_INCOMPLETE`.

## Task 1 — France (Codex P0-CALC-001): FIXED

`fr_trip`'s `fr_trip_vfx_spend_eur` condition had no `component_basis` dimension, so the generic whole-segment amount-fact derivation (built in the immediately-preceding `CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR` workstream) incorrectly filled it from the entire French QPE — virtually always above EUR 2,000,000, so 40% was selected for every French full relocation regardless of real VFX spend.

**Fix:** gave the condition a real `component_basis_line_components=("vfx",)` basis (matching the segment's own real `.component == "vfx"` allocations), and extended `price_segment`'s existing component-basis derivation to FX-convert a non-USD-denominated traced subtotal (EUR here) via the canonical FX path before comparison.

**Verification:** all 4 acceptance productions now match Codex's own independent-oracle 30% expected value exactly (see `CLAUDE_18_CALCULATION_RECONCILIATION.csv` rows 1-4).

## Task 2 — Latvia (Codex P0-CALC-002): FIXED with an independent, cited override of Codex's own provisional figure

Real primary-source research against the National Film Centre of Latvia's own official page (`nkc.gov.lv/en/cash-rebates`, fetched live) found the prior catalog entry had blended TWO DIFFERENT Latvian programs (the National Film Centre's own 30% flat cash rebate, and the separate City-of-Riga Film Fund's 20-25% cultural-content-gated scheme) into one incorrect ambiguous tier structure. The real, guaranteed rate is a single flat 30%, gated on a real converted minimum spend (EUR 711,436 → USD 811,409.80).

Codex's own oracle used a **provisional, unsourced 20% floor** pending resolution — its own audit language explicitly authorized superseding this once real evidence was found ("If authoritative Latvia evidence changes Codex's provisional 20% expectation, update the oracle transparently and cite the authority"). Full detail: `CLAUDE_LATVIA_PRIMARY_SOURCE_RESOLUTION.md`, `CLAUDE_LATVIA_SOURCE_LOG.jsonl`.

**Verification:** all 4 full-relocation-to-LV rows match the OLD persisted dollar figure exactly (30% was, by coincidence, already the correct rate — the defect was that it was never actually *gated*). All 10 small-component-split-to-LV rows now correctly `RULE_REJECTED` — a real, disclosed threshold shortfall neither the old code nor Codex's own provisional independent oracle correctly enforced (Codex's oracle also implicitly assumed no minimum-spend gate at all for these rows).

## Task 3 — 18-row calculation oracle: RECONCILED

Codex's failed set is exactly 4 France + 14 Latvia rows, confirmed by parsing `CODEX_INDEPENDENT_CALCULATION_ORACLE.csv` directly. Full row-by-row reconciliation, including the Latvia full-relocation rows' deliberate divergence from Codex's own provisional 20% figure (cited, not silent), is in `CLAUDE_18_CALCULATION_RECONCILIATION.csv`. The other 616 rows and all 634 rows' internal NPC identity were not touched and were re-verified passing by the same regression suites below. All 4 anchors are unaffected (no anchor-contract code was touched).

## Task 4 — Worldwide stacking universe: PARTIALLY FIXED, worldwide completeness NOT achieved

**Root cause found for the P1-STACK-001 pair-generation failure:** `ca_bc_pstc`, `ca_federal_pstc`, and `ca_federal_cptc` each declared `kind="rate_base_narrower_than_qpe"` — a condition that only ever *disclosed* a narrower labour-only base was required and never *bound* one, so none of the three could individually price at all. Since the location-group stacking mechanism only combines candidates that are already individually priced, this alone explains 3 of Codex's 5 missing named pairs.

**Fix:** the same real `component_basis_spend_categories` derivation already established for `ca_bc_dave` was applied to all three. While verifying this, a genuinely new, deeper defect was found and fixed: when a program's rate resolution *selects its discretionary ceiling tier* (e.g. BC PSTC's 48% regional/distant-location uplift), the SEPARATE, real, guaranteed floor tier's own component-basis condition was never consulted — the served **guaranteed** incentive was silently computed off the whole segment ($3,960,000) instead of the real traced labour subtotal ($144,000). Fixed generically in `resolve_program_rate` (floor and ceiling of one program share one qualifying base by construction, so this is not a per-program special case).

**Result — Codex's 6 named executable pairs:**
| Pair | Before | After |
|---|---|---|
| `on_ofttc + on_opstc` | Generated, correctly rejected `MUTUALLY_EXCLUSIVE` | Unchanged |
| `ca_bc_pstc + ca_federal_cptc` | Never generated (neither member priced) | **Generated**, correctly rejected `MUTUALLY_EXCLUSIVE` |
| `ca_federal_cptc + on_ofttc` | Never generated | **Generated**, correctly `PRICED` (spend_reduction) |
| `ca_federal_cptc + on_opstc` | Never generated | **Generated**, correctly rejected `MUTUALLY_EXCLUSIVE` |
| `ie_section_481 + uk_avec` | Never generated | **Still not generated** — root cause: GB/IE are different sovereign countries; the existing location-group mechanism only combines same-jurisdiction or federal+provincial-of-one-country candidates. A cross-country dual-relocation structure type would need to be built. Not done this workstream. |
| `ny_state_film + us_ny_post_production_credit` | Never generated | **Still not generated** — confirmed NOT a code defect: the real post-eligible spend for all 4 acceptance productions ($9,068–$52,500) never clears the real USD 1,000,000 minimum for this program. |

A genuine side effect proves the fix is generic, not four special cases: `ca_federal_cptc + ca_qc_pstc` (never named by Codex) and a genuine 3-way `ca_federal_cptc + on_ofttc + on_opstc` higher-order stack now also generate correctly, with zero additional per-pair code.

**Worldwide completeness (Task 4A-4F): NOT ACHIEVED.** `CLAUDE_GLOBAL_STACKING_PROGRAM_NODES.csv` (126 real nodes, derived directly from runtime introspection) and `CLAUDE_GLOBAL_STACKING_UNIVERSE.csv` (the pre-existing, real, 229-row canonical compatibility registry, annotated with this workstream's remediation notes) are delivered as the best available real starting point. A full primary-source-researched disposition for every economically plausible combination among 126 programs (potentially thousands of pairs and higher-order sets) was **not attempted** — this is a genuinely large research undertaking beyond what this workstream completed. This is disclosed, not claimed complete.

## Task 5 — Combined co-production hybrids: DIAGNOSED, NOT IMPLEMENTED

Root cause confirmed by direct code trace and a fresh runtime check across all 4 acceptance productions (`CLAUDE_COMBINED_COPRO_HYBRID_RUNTIME.csv`): `evaluate_bilateral_coproduction_opportunity` requires *real* evidenced `majority_pct`/`minority_pct` contribution facts before a treaty opportunity reaches `RESOLUTION_ELIGIBLE`, which is the gate `combined_coproduction_component_stack` generation requires. No fallback to a treaty-minimum modeled assumption exists yet, so this never fires for any of the 4 productions — including Little Utopia's AU-UK case, whose personnel gate correctly reports `QUALIFIES` but which has no contribution-share facts on file. Locked Product Policy explicitly permits a treaty-minimum fallback ("Missing contribution shares may use treaty-minimum modeled assumptions"); implementing it was **not done this workstream**.

## Task 6 — 32-program reconciliation: LARGELY IMPLEMENTED

Compared Codex's own evidence-backed classification against a **direct runtime check** (`economic_block_for_program()`/`resolve_program_rate()`, not merely the coarser `coverage_state()` used for discovery-stage disclosure) for all 32 rows.

- **`au_qld_pdv_rebate`**: ACCEPTED and independently reconfirmed directly against `screenqueensland.com.au`'s own official page — rate is now 10% (was stale 15%), effective 2026-09-04, with a real USD 164,268.35 (AUD 250,000) minimum.
- **`us_il_film_production_services_credit`**: ACCEPTED — the rate rule was already correct and well-sourced (35%, `dceo.illinois.gov`); it was simply still fail-closed in the authority registry. Unblocked.
- **`me_cash_rebate`**: **REJECTED WITH EVIDENCE.** Independent research (the Film Centre of Montenegro's own page title, the affiliated `filminmontenegro.me` official incentives page, and general search aggregation) found no support anywhere for a "30% + 5%" structure — every source converges on a flat 25%. The existing 25% rate is unchanged; only its separate, correctly-identified `FAIL_CLOSED` misclassification (Codex's `STATUTORY_FORMULAIC` disposition, which is a different claim than the specific rate) was removed.
- **`pt_scri_pt_medium_budget`**: **REJECTED WITH EVIDENCE.** The existing EUR 1.5 million cap is sourced from the actual Portuguese government gazette (Portaria 265-A/2026); Codex's claimed EUR 1 million cap traces only to secondary production-service aggregator sites, and the government gazette page could not be re-fetched to confirm either figure conclusively. Given the existing citation is the stronger primary source, it is kept unchanged. Also unblocked from `FAIL_CLOSED` (a separate, correct action).
- **18 further programs** (beyond the 4 named ones) were found, via the same mechanical audit, to carry the *identical* genuine misclassification as the 5 Canadian/Illinois entries already removed in a prior workstream: Codex's own evidence classifies them `STATUTORY_FORMULAIC` — a real, current, non-discretionary rate with an official citation and an already-registered `RateRule` — yet all 18 were still permanently zeroed by `FAIL_CLOSED`. All 18 removed; every one now resolves a real rate, confirmed directly (not assumed). Every remaining row (`UNRESOLVED`/`INFORMATIONAL_ONLY`/`DUPLICATE_ALIAS`/genuinely selective-or-competitive) was independently reconfirmed still correctly blocked at the authoritative gate.

Full row-by-row ledger: `CLAUDE_32_PROGRAM_RUNTIME_RECONCILIATION.csv`.

## Task 7 — Input-wiring deltas: NOT IMPLEMENTED, root causes disclosed

- **7A residency**: not implemented this workstream.
- **7B creative roles**: not re-audited this workstream (Little Utopia's existing verified writer/director path re-confirmed unaffected by every change made, via the AU-UK regression suite).
- **7C co-production contributions/entities**: root cause confirmed identical to Task 5's finding (no treaty-minimum fallback); not implemented.
- **7D related-party/vendor fingerprinting**: not investigated this workstream.

Full detail: `CLAUDE_INPUT_WIRING_DELTA.csv`.

## Task 8 — Prevention tests

18 new/rewritten tests added to `tests/test_canonical_economics_integrity_repair.py`, all asserting independently-computed exact expected dollar values (not internal-helper round-trips): France VFX-component tracing, Latvia real-threshold gating (both above and below the real minimum), the Canadian labour-only-base derivation (both the "no real labour lines" and "real traced labour subtotal only" cases), and the floor/ceiling shared-basis fix. Two stale tests that asserted the OLD, now-fixed `rate_base_narrower_than_qpe` disclosure-only behavior were replaced with tests asserting the NEW, correct derivation — not weakened, since the old assertions' entire premise (`kind="rate_base_narrower_than_qpe"` existing anywhere in the codebase) is now correctly false everywhere.

## Regressions

277 tests re-run, zero failures: 59 in `test_canonical_economics_integrity_repair.py` + `test_ca_bc_dave_component.py` (18 new/rewritten this workstream), 218 across `test_au_uk_copro_overview_wiring_claude.py`, `test_canada_validation.py`, `test_component_rejection_persistence.py`, `test_ny_nm_or_validation.py`, `test_hybrid_anchor_relationship_types.py`, `test_coproduction_optimizer_preservation.py`, `test_treaty_coproduction.py`, `test_treaty_coproduction_wiring.py`.

## Four-production final run

All 4 acceptance productions re-evaluated fresh at `canonical-1.67.0` after invalidating current-engine rows: all 4 `EVALUATION_COMPLETE`. Priced-candidate counts rose substantially for all 4 (the 21-program unblock), combined-stack candidates now appear for 3 of 4 productions (Little Utopia's federal CPTC fails its own separate, real content-certification gate — a different, correct, disclosed outcome, not a regression). Full detail: `CLAUDE_FOUR_PROJECT_POST_REMEDIATION.csv`. V-BRAT and Underwater were not evaluated.

## Status

**`REMEDIATION_INCOMPLETE`**

Genuinely completed and verified: Tasks 1, 2, 3, most of Task 4 (the named 6-pair control plus the generic labour-base/floor-basis fixes), most of Task 6, Task 8, engine/cache discipline, and the four-production run.

Not completed, disclosed rather than fabricated:
1. Worldwide stacking-universe completeness (Task 4A, 4C, 4F) beyond the pre-existing 229-row registry and the 6 named pairs.
2. `ie_section_481 + uk_avec` (cross-country structure type not built).
3. Combined co-production hybrid generation (Task 5) — root cause diagnosed, fallback not implemented.
4. Residency and co-production contribution/entity input-wiring (Task 7A, 7C) — root causes diagnosed for 7C, not implemented.
5. Creative-role-slot and related-party/vendor fingerprinting re-audits (Task 7B, 7D) — not attempted.
