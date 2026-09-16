# CLAUDE_SPEND_THRESHOLD_AND_ANCHOR_CLOSEOUT

**Canonical branch:** `claude/optimizer-policy-finalization`
**Minimum required ancestor:** `8ca5ab65eb6d65c35142d0e466f82884337c8cab`
**Resolved starting SHA:** `8ca5ab65eb6d65c35142d0e466f82884337c8cab` (branch was already exactly at the minimum ancestor)

## Production code changed: YES — a real, second-order defect found and fixed

Task 1's own investigation revealed that the prior workstream's producer-controlled-fact fix (`_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS`, `canonical-1.62.0`) was **incomplete**: it patched the three real pricing functions (`_price_candidate`, `_price_component_relocation_candidate`, `_price_combined_coproduction_component_candidate`) but not the two `discover_executable_jurisdictions()` call sites in `evaluate_project()`, which decide whether a `(jurisdiction, program)` pair is even **accepted as a candidate** before pricing ever runs. Those two call sites still passed the raw, un-unioned `inputs.evidenced_program_facts`.

**Concrete proof this mattered**: `za_nfvf_rebate`'s only `resolve_program_rate` gate is `za_nfvf_accepted_production_confirmed` (a producer-controlled administrative fact, already correctly in the auto-assumption set). Isolated verification: `resolve_program_rate("za_nfvf_rebate", ..., evidenced_facts=frozenset())` → `None`; the identical call with the auto-assumption set unioned in → resolves a real 25%/30% floor/ceiling. Since discovery used the un-unioned set, `za_nfvf_rebate` was rejected at discovery for all four productions and never reached the (already-correct) pricing pass.

**Fix**: unioned `_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS` into both `discover_executable_jurisdictions()` calls (`feasibility_discovery` and `discovery`) in `canonical_evaluation.py`. `ENGINE_VERSION` bumped `1.62.0 → 1.63.0`. One focused prevention test added (`test_discovery_stage_also_assumes_producer_controlled_facts_not_just_pricing`) and passing, plus 4 existing prevention tests re-verified passing, plus 108 further directly-affected tests across 6 test files re-run with zero regressions.

**Real, verified outcome after the fix**: `za_nfvf_rebate` now correctly generates and prices a real, disclosed conditional structure for all four acceptance productions (Little Utopia $0 floor on a minimal $9,068 component; F#K Valentine's Day $925,309.50; Bad Hombres $596,910.25; Lips Like Sugar $1,527,781.17) — all using the real, current routed component spend, never a fabricated amount. **No other program's disposition changed.** All four anchors are byte-identical before and after this fix.

## Task 1 — the eight programs, precisely classified (never conflating categories)

Full detail: `CLAUDE_EIGHT_PROGRAM_THRESHOLD_MATRIX.csv` (42 rows across the 8 programs × 4 productions, with real multi-structure detail for `us_or_opif`/`za_nfvf_rebate`). Summary disposition per program (same across all four productions unless noted):

| Program | Disposition | Category |
|---|---|---|
| `us_or_opif` | Real spend test, genuinely tested against the real routed component | 3/4 productions show at least one `RULE_REJECTED_SPEND_THRESHOLD` structure (real shortfall, e.g. Little Utopia $9,068 vs $1,000,000) **and** one `PRICED` structure per production (a different, larger real routed component clears the threshold) — never conflated with the separate, disclosed `us_or_opif_award_confirmed` discretionary-approval fact, which stays `USER_FACT_REQUIRED` even on the priced structures |
| `za_nfvf_rebate` | **Fixed this workstream** — now `PRICED` for all 4, using real routed spend | Was previously blocked purely by an unassumed producer-controlled fact, never a genuine spend/cultural/discretionary reason |
| `cz_film_incentive_animation` | `GENUINE_SCOPE_MISMATCH` for all 4 | None of the four productions is an animation production — a real, non-curable creative-scope fact, never a spend-threshold rejection |
| `nl_film_production_incentive` | `CULTURAL_TEST_NOT_EVIDENCED` for all 4 | The points/independence test is a real, substantive, deliberately-unassumed content/ownership test — never a spend-threshold rejection |
| `au_location_offset`, `ca_bc_dave`, `ma_ccm_rebate`, `th_film_incentive` | `DISCOVERY_STAGE_AMOUNT_NOT_PROBED` for all 4 | **Disclosed, real, distinct architecture gap** — `discover_executable_jurisdictions()` has no generic per-jurisdiction amount-fact probe for these programs' AUD/BC-labour/MAD-plus-shooting-days/THB conditions (unlike `us_or_opif`'s own special-cased QPE probe). Their producer-controlled boolean facts ARE now correctly auto-assumed; the remaining gate is a genuinely unprobed amount fact — the spend was **never measured**, not measured-and-found-insufficient. Building a generic amount-probe mechanism for every program is a distinct, larger architecture change and is explicitly out of scope for this narrow workstream (not built this pass) |

**Whether relocation could cure each spend shortfall**: for `us_or_opif`'s genuinely-rejected structures, **yes, runtime-proven** — the same production's own larger real components already independently clear the threshold and price. For the 4 `DISCOVERY_STAGE_AMOUNT_NOT_PROBED` programs, **unknown/not runtime-provable this pass** — the four productions' real gross budgets ($2.5M–$12M) are comfortably above the MAD/THB/BC-labour thresholds in principle, but confirming this would require the missing amount-probe mechanism, which is a real architecture gap disclosed here rather than built. For the 2 substantive-gate programs (`cz_film_incentive_animation`, `nl_film_production_incentive`), relocation of spend **cannot** cure either — one is a creative-format fact, the other a content/independence test.

## Task 2 — complete four-production anchor contract

Full detail: `CLAUDE_FOUR_PRODUCTION_ANCHOR_CONTRACT.csv`. Every figure was read from a **fresh, live `compute_anchor_budget_contract()` call this session** (not copied from a prior artifact), against the `canonical-1.63.0` engine version:

| Production | Anchor | Gross Budget | Supplied Incentive | Calculated Incentive | Anchor NPC | Qualification State |
|---|---|---|---|---|---|---|
| Little Utopia | MU / `mu_edb_incentive` | $4,364,393.00 | `NOT_SUPPLIED` | $573,059.70 | $3,791,333.30 | `AUTHORITY_UNRESOLVED` |
| F#K Valentine's Day | GR / `gr_cash_rebate` | $4,517,687.00 | `NOT_SUPPLIED` | $1,445,659.84 | $3,072,027.16 | `USER_FACT_REQUIRED` |
| Bad Hombres | US-NM / `us_nm_film_credit` | $2,482,023.00 | `NOT_SUPPLIED` | $596,910.25 | $1,885,112.75 | `NOT_APPLICABLE` |
| Lips Like Sugar | US-CA / `ca_film_30` | $11,983,654.00 | `NOT_SUPPLIED` | $3,459,278.90 | $8,524,375.10 | `NOT_APPLICABLE` |

**Verified, not copied**: all four calculated-incentive figures match the previously-reported values exactly, confirmed via a fresh runtime call this session (state fingerprints and `structure_id`s recorded in the CSV for full traceability). None of the four productions currently has a supplied/reference-budget incentive on file — correctly reported as `NOT_SUPPLIED`, never silently converted to `$0` (the prior workstream's own runtime control, `test_supplied_incentive_budget_line_changes_the_fingerprint_and_forces_fresh_anchor_recompute`, already proves the mechanism activates correctly when a real supplied-incentive fact IS present — re-verified passing, not re-run as a new evaluation since it is a self-contained, reversible test).

## Task 3 — anchor semantics, proven

- **Anchor calculates its own credit**: `calculated_anchor_incentive_usd` for every production is a real, non-null, independently-computed number (`compute_anchor_budget_contract()` is a thin reader of a value persisted inside `evaluate_project()`'s own baseline-candidate pricing pass — never re-derived by the served view).
- **Anchor is the reference for net benefit**: unchanged, pre-existing mechanism (`net_benefit_vs_anchor_usd = anchor_npc_usd − candidate_npc_usd`, computed generically over every served structure) — untouched this workstream.
- **Anchor does not restrict candidate generation**: directly proven by this workstream's own fix — `za_nfvf_rebate` began generating and pricing real candidates for all four productions **without any change to any anchor value**. All four anchors (`calculated_anchor_incentive_usd`, `anchor_npc_usd`) are byte-identical before and after both this session's fixes.
- **Anchor spend is not reused as the threshold for a relocated component's real pricing**: confirmed — `us_or_opif`'s real per-component pricing correctly tests the real routed amount (e.g. $9,068) against the real $1,000,000 statutory threshold, never the anchor's $4,364,393 gross budget. (The one place anchor-scale budget IS used is the coarse `discover_executable_jurisdictions()` discovery-stage probe — a pre-filter, not the final pricing threshold — which is the pre-existing, documented, and unchanged design already in place for that stage.)
- **Sub-$100,000 candidates still calculated, not recommended**: unchanged, pre-existing mechanism (`ECONOMICALLY_NON_MATERIAL_NOT_RECOMMENDED` classification) — untouched this workstream, still active in the fresh evaluation.
- **Supplied incentive used only for reconciliation, never trusted over the engine's own calculation**: unchanged, pre-existing mechanism — `pricing.selected_incentive_usd` (the engine's own calculation) is what optimization uses; the supplied figure is reported alongside for comparison only, never substituted in.

No further code change was needed for Task 3 — behavior was already correct; nothing was edited merely to manufacture a change.

## Four-production fresh evaluation

Current-engine cache invalidated for exactly the four acceptance productions; one fresh evaluation run for each after the code change. All four returned `EVALUATION_COMPLETE` at `canonical-1.63.0` with new state fingerprints (required, since production code changed). Anchor incentives/NPCs unchanged for all four. `za_nfvf_rebate` newly prices; total served-structure counts increased by 2–3 per production (the new `za_nfvf_rebate` candidates); no other program's disposition changed.

## CSV validation

Both delivered CSVs parse cleanly under Python's `csv` module: fixed header width, constant field count, expected row count, unique keys, no malformed quoting, no aggregate substitute rows.

| File | Rows | Columns | Malformed |
|---|---|---|---|
| `CLAUDE_EIGHT_PROGRAM_THRESHOLD_MATRIX.csv` | 42 | 16 | 0 |
| `CLAUDE_FOUR_PRODUCTION_ANCHOR_CONTRACT.csv` | 4 | 12 | 0 |

## Out of scope, correctly not touched

No 659-record census, 126-program reconciliation, external program research, general stacking-completeness work, or general optimizer architecture reopened. No reinvestment/in-kind or Globe work. AU–UK, NY, Canadian, and hybrid/co-production behavior confirmed unaffected (108 directly-relevant tests re-run, zero regressions) — no code touched in those areas.

## Status

`READY_FOR_INDEPENDENT_STACKING_AND_CALCULATION_AUDIT` — every one of the eight program dispositions is precisely classified (never conflating spend/cultural/scope/discretionary categories), and the complete four-production anchor contract is runtime-supported by a fresh `compute_anchor_budget_contract()` call this session.
