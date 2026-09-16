# CLAUDE_CORRECTED_GLOBAL_STACKING_AND_OPTIMIZER_CLOSEOUT

**RESOLVED_STARTING_SHA:** `594c903aefcd47db06ab55fcefe2eeaec8ca9412`
**Corrected Codex audit consumed:** `codex/global-stacking-opportunity-audit` @ `940ef8f78bb69bb343a954e34f6e9c2151489fd0`
**Superseded audits (not reused for stacking conclusions):** `8cc1622dd102939762c2e1bdfc788eadac8c7ce0`, `bbb63644dc78cc7ac0cb98266f91a1693f7235f6`
**Engine:** `canonical-1.67.0` → `canonical-1.68.1`; stacking rules `1.1.0` → `1.2.0`

## What this closeout actually completed

**Phase B (fixed and verified, in two passes):** Codex's corrected audit identified a real, serious defect: `ca_federal_cptc + on_ofttc + on_opstc` was served as a `PRICED` combined structure even though `on_ofttc + on_opstc` is a real, statutorily mutually-exclusive pair (a production cannot simultaneously be domestic-content and foreign-service). Root cause: `canonical_stack_bridge._rule_type_for_group()` collapses a group's disposition to `"mixed"` whenever its pairwise sub-rules are not all the same type (here: one `spend_reduction` + two `mutually_exclusive`), and the served-status checks in `canonical_evaluation.py` only ever compared against the literal string `"mutually_exclusive"` — so a `"mixed"` group with a real hard incompatibility buried inside it slipped through as priced.

**Fix (1.68.0):** `MultiProgramStackResult` now carries `contains_blocking_incompatibility` and `blocking_pairs`, computed by scanning **every individual pairwise sub-rule** in the group (never the collapsed group-level type). The main candidate-generation loop and a separate scenario-aggregation path (which had the identical latent bug) were updated to use this field. The rejection reason now names the exact failing pair(s).

**Fix (1.68.1, found by the four-production runtime check, not the unit tests):** the unit tests passed after 1.68.0, but running the real four-production batch surfaced a second, independent occurrence of the identical stale comparison — the combined-structure `candidate_status` computation had its own separate `stack_result.rule_type == "mutually_exclusive"` check that the first pass missed, so `ca_federal_cptc+on_ofttc+on_opstc` was served in a **self-contradictory state**: `candidate_status=PRICED` with `total_incentive_value_usd=None` (the value-nulling check had been fixed; the status computation had not). Fixed by routing both checks through the same `_combination_is_invalid` variable, and added a static-analysis regression test (`test_no_stale_rule_type_mutually_exclusive_check_survives_in_canonical_evaluation`) that fails the suite if this literal comparison pattern ever reappears anywhere in `canonical_evaluation.py`. This is the clearest evidence in this whole workstream that unit tests alone were insufficient — only the real four-production runtime check (Phase K) caught it, confirming the task's own instruction not to claim completion from tests/documentation alone.

Verified generic and order-independent (all 6 permutations of a 3-member group produce byte-identical, correctly-rejected output) and confirmed consistent across all 4 real acceptance productions post-fix (see `CLAUDE_FOUR_PROJECT_OPTIMIZER_FINAL.csv`): every structure containing `on_ofttc+on_opstc` is `RULE_REJECTED` with no incentive value, while genuinely compatible combinations (`on_ofttc+ocase`, `on_opstc+ocase`, `ca_federal_cptc+on_ofttc`, `ca_federal_cptc+ca_qc_pstc`) correctly price.

**Two real, primary-source-confirmed stacking rules added:** `on_ofttc + ocase` and `on_opstc + ocase` (both `spend_reduction`), confirmed directly against Ontario Creates' own official OCASE page. `ca_federal_cptc + ocase` was **not** added — the same official page names only OFTTC/OPSTC as OCASE's partners, so this remains a genuine, undecided authority gap, not fabricated.

**Phase A (reconciliation ledger):** produced (`CLAUDE_CORRECTED_CODEX_RECONCILIATION.csv`), classifying each of the corrected audit's headline counts against 594c903's actual state.

## What this closeout did NOT complete — disclosed, not fabricated

Given the scope of this workstream (12 phases, 12 deliverables, 48 legal interactions, 90 scope-unresolved nodes, 31 authority-research rows, a generic 12-archetype structural generator, combined co-production hybrids, and four input-wiring subsystems) substantially exceeds what could be responsibly completed and verified in this pass, the following are **explicitly not done**, each with its confirmed root cause where one was found:

- **Phase C1 — the 2 real Lips Like Sugar omissions** (`us_ga_film_credit`/`us_nm_film_credit` + NZ-or-AU post/VFX + OCASE, 3-jurisdiction structures): not implemented. These require a genuinely new structural archetype — a non-treaty, 3-way component relocation (principal to one country, post to a second, VFX to a third) — that does not exist in the codebase today. The existing `_price_component_relocation_candidate` (one extra target) and `_price_combined_coproduction_component_candidate` (treaty + one component) do not cover this shape.
- **Phase C2 — the 11 isolated higher-order controls:** not executed.
- **Phase C3 — `ie_section_481 + uk_avec` and `ny_state_film + us_ny_post_production_credit`:** not implemented. Both require new structural mechanisms (cross-country dual relocation; same-jurisdiction distinct-cost routing) rather than a registry rule change. For NY specifically: the current registered rule (`mutually_exclusive`) is confirmed **safe but overbroad** relative to Codex's corrected `SAME_COST_PROHIBITED_DISTINCT_COSTS_ALLOWED` disposition — left unchanged deliberately rather than risk a real same-cost double-count defect by loosening it without the distinct-cost enforcement mechanism to back it up.
- **Phase D — generic structural archetype generator (12 archetypes):** not built.
- **Phase E — combined co-production hybrid treaty-minimum fallback:** not implemented. Root cause re-confirmed unchanged from the prior workstream's diagnosis.
- **Phase F — residency, creative-role re-audit, co-production entity persistence, related-party/vendor wiring:** none implemented or re-investigated this pass.
- **Phase G1 — the 31 unresolved legal interactions (9 AU, 21 CA, 1 ZA):** not researched.
- **Phase G2 — the 90 scope-unresolved executable nodes:** not classified.
- **Phase H — full changed-program re-audit:** limited to confirming no new contradicting evidence surfaced for the 6 already-established corrections (France, Latvia, Queensland, Illinois, Montenegro, Portugal); a full field-by-field re-verification of every changed program's citation/rate/basis was not performed.
- **Phase I — independent calculation acceptance:** limited to the structures actually touched this workstream (the Phase B fix and the 2 new OCASE rules); Codex's CC-01 through CC-12 calculation controls were not independently recomputed.

## Regressions

Zero regressions caused by this workstream's changes. One pre-existing test-ordering fragility was found and diagnosed (not fixed, as it is unrelated to Phase B): `tests/test_au_uk_copro_overview_wiring_claude.py::test_little_utopia_uk_au_bilateral_is_served_conditional_with_real_priced_economics` and `::test_little_utopia_producers_do_not_block_the_uk_au_structure` read a `StructureCalculationResult` row keyed on the *current* `ENGINE_VERSION`, but that row is only created by `tests/test_hybrid_anchor_relationship_types.py` and `tests/test_treaty_coproduction_wiring.py` (both of which call `evaluate_project` for Little Utopia directly) — files that run *after* the AU-UK file in this suite's file-list order. Confirmed by direct code inspection (neither file this workstream touched intersects AU-UK/treaty logic) and empirically (an isolated re-run of just the 2 failing tests passed immediately; a second full 8-file run passed 218/218 once the dependency row existed from the first run). This dependency would reproduce identically on any `ENGINE_VERSION` bump from any workstream, including ones already in `594c903`, and is not caused by anything changed here — disclosed as a real, pre-existing test-suite fragility, not fixed (out of this workstream's scope).

## Tests

- `tests/test_canonical_economics_integrity_repair.py` + `tests/test_ca_bc_dave_component.py`: **64 passed** (5 new this workstream: `test_cptc_ofttc_opstc_triple_is_rejected_not_priced`, `test_ofttc_ocase_and_opstc_ocase_can_price_real_confirmed_pairs`, `test_four_member_structure_rejected_when_any_pair_is_prohibited`, `test_higher_order_pairwise_legality_is_order_independent`, `test_no_stale_rule_type_mutually_exclusive_check_survives_in_canonical_evaluation`).
- Broader regression (AU-UK, Canada, component rejection, NY/NM/OR, hybrid anchor, co-production preservation, treaty co-production x2), run twice: first run 216 passed / 2 failed (the pre-existing ordering fragility above); second run **218 passed, 0 failed**.

## Four-production fresh runtime

See `CLAUDE_FOUR_PROJECT_OPTIMIZER_FINAL.csv` for the fresh, post-fix evaluation of all 4 acceptance productions at `canonical-1.68.1`. All 4 `EVALUATION_COMPLETE`; anchor incentives unchanged from every prior workstream ($573,059.70 / $1,445,659.84 / $596,910.25 / $3,459,278.90). Every `on_ofttc+on_opstc`-containing structure (2-member and 3-member) correctly `RULE_REJECTED` with no incentive value across all 4 productions; genuinely compatible combinations correctly price. V-BRAT and Underwater were not evaluated.

## Status

**`REMEDIATION_INCOMPLETE`**

The single well-specified, critical correctness defect this workstream was most explicitly asked to fix (Phase B, the invalid `CPTC+OFTTC+OPSTC` pricing) is fixed, tested, and verified generically (not a per-combination patch). Two real stacking rules were added and confirmed against primary authority. The remainder of this workstream's scope — a generic multi-jurisdiction structural archetype engine, 31+90 rows of primary-source legal/scope research, combined co-production hybrid completion, and four input-wiring subsystems — was not completed and is disclosed above rather than claimed done.
