# Existing Optimizer/Stacker Reconnection — Closeout

**Generated:** 2026-08-18 (superseded by the continuation below, same date)
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate (original):** `EXISTING_OPTIMIZER_STACKER_RECONNECTED_PARTIAL_NORTH_AMERICA_PROVEN`
**Final gate (continuation):** `EXISTING_OPTIMIZER_STACKER_RECONNECTED_EXTENDED_COMPONENT_TREATY_HYBRID_UNSTARTED`
**Lineage source:** `docs/validation/CODEX_EXISTING_OPTIMIZER_LINEAGE_TRACE.md`

This is a **partial, honestly-scoped** close of the reconnection task, not the full 15-item mandate. It reconnects the two highest-value, fully-tractable capabilities — multi-program same-jurisdiction stacking and federal+provincial/state stacking — through real code, with real runtime proof on both control projects. The remaining capabilities are traced, classified, and explicitly deferred below; none silently disappeared.

**Continuation (same day, commit after `86f1547`):** see `docs/architecture/CAPABILITY_LEDGER.md`'s "Existing Optimizer/Stacker Reconnection, continuation" entry for the full account. Summary: N-way (3+) stacking connected and runtime-proven (a real CA-ON triple); alias reconciliation closes the `on_opstc`/`qc_film_production` gap named above, unlocking `ca_on_opstc` and `ca_qc_pstc` into 4 more combined structures; the Ontario `on_ofttc`+`ca_federal_cptc` interaction is now genuinely REPAIRED (a real $50,000 reduction computes, not just disclosed as unresolved); Task 7 (grants/funds) connected via `conditional_programs.py`/`structure_compatibility.py`, zero-guaranteed-NPC confirmed by construction; Task 11 (ranking admission) wired but not exercised by either control project (neither's home is Canada). Two genuine correctness defects Codex's separate correctness-classification pass found in the reused legacy engine were fixed and regression-tested: fail-closed publication (a `conditional`-type rule pair can no longer be silently published as resolved economics) and N-way order-independence (canonical candidate ordering guarantees permutation-invariant results). Component/split, treaty co-production, and hybrid/anchor generation remain genuinely unstarted — disclosed, not silently dropped.

## Single jurisdiction

`EXISTS_AND_CONNECTED` (unchanged — this was already the canonical served path before this task).

## Multiple programs, same jurisdiction

`CONNECTED_AND_RUNTIME_VERIFIED`. New `app/calculators/canonical_stack_bridge.py`: `load_named_pair_rule()` (the canonical rule/slug loading adapter — reads `app.optimization.stacking_rules._SLUG_PAIR_RULES` directly, since it is already keyed by current canonical program slugs for the pairs this reconnection targets) + `price_program_pair_stack()` (the stack-pricing bridge — reuses `apply_stacking_adjustments()`/`evaluate_legal_stacking()` unchanged against current canonical per-program pricing). Wired additively into `canonical_evaluation.evaluate_project()`. Runtime-verified: Ontario's `ca_federal_cptc` + `on_ofttc` combine under a named `spend_reduction` rule for both LU and FVD.

## Federal / provincial-state stacking

`CONNECTED_AND_RUNTIME_VERIFIED` for the two pairs Codex identified as having direct static coverage (`ca_federal_cptc`+`ca_bc_pstc`, `ca_federal_cptc`+`on_ofttc`). `eligible_for_combination()` groups candidates by top-level country prefix (a real grouping gap found mid-pass: federal programs discover under the bare country code `CA`, provincial ones under `CA-BC`/`CA-ON` — exact-code grouping alone silently generated zero federal+provincial combinations) and explicitly refuses two different provinces/states combining into one structure. All other Canada/US pairs remain correctly `UNKNOWN`/gated — no default-allowed fallback is ever consulted.

**Runtime proof (both LU and FVD, byte-identical baselines before/after):**
- `CA-BC`: `ca_federal_cptc` + `ca_bc_pstc`, `mutually_exclusive` → BC PSTC (higher value) retained, federal CPTC zeroed. Correct.
- `CA-ON`: `ca_federal_cptc` + `on_ofttc`, `spend_reduction` → priced, but with a disclosed limitation (see below) rather than a silently-wrong net figure.
- Little Utopia baseline: $3,057,794.90 (unchanged). FVD baseline: $3,072,027.16 (unchanged). Both combined structures correctly excluded from ranking (`scenario_category=PRICED_LOW_FIT`, `is_directly_comparable=False`).

## Component / split allocation

`INTENTIONALLY_DEFERRED`. `production_allocation.StructureSpec` already supports `component_relocation`/`split_production`/`hybrid` types and `price_allocated_structure()` can price them — confirmed present, not rebuilt. No generic candidate generator feeds them from real project budget-line facts yet; building that adapter was out of scope for this pass, which focused on the North America stacking control. Not touched, not broken.

## Grants / funds

`INTENTIONALLY_DEFERRED`. `conditional_programs.py`/`structure_compatibility.py` are confirmed usable, zero-guaranteed-value-preserving implementations, explicitly excluding the legacy `_estimate_grant_value()` heuristic per Codex's own instruction. Not attached to canonical structures this pass.

## Official treaty co-production

`INTENTIONALLY_DEFERRED`. `treaty_engine.py`'s bilateral/multilateral eligibility logic is confirmed present and unchanged. Little Utopia's Mauritius proven-zero result (`reachable_treaty_partners == []`) is unaffected — verified via the existing regression test. Full generic fact/eligibility execution for a project with a real reachable treaty partner was not exercised this pass (neither LU nor FVD currently discovers one). `NOT_APPLICABLE_TO_CONTROL_PROJECT` for runtime proof, per the task's own fallback instruction — reported honestly rather than fabricating a structure to force a proof.

## Hybrid / anchor

`INTENTIONALLY_DEFERRED`. Unchanged from Codex's classification — LU's older non-project-scoped control endpoint still demonstrates hybrid/anchor generation capability; the generic canonical generator does not yet call it.

## In-kind / support

`INTENTIONALLY_DEFERRED` (`LEGACY_ONLY`, unchanged). Not traced further this pass.

## Reinvestment

`INTENTIONALLY_DEFERRED`, per explicit instruction. No code touched, nothing deleted.

## Canonical stacker

`generate_structure_scenarios.py`, `apply_stacking_adjustments.py`, `evaluate_legal_stacking.py` all read, none edited — confirmed byte-identical to before this task. The new adapter (`canonical_stack_bridge.py`) is the only new code; it consumes two of these three unchanged, and does not touch `generate_structure_scenarios.py`'s own dependency on the superseded `run_full_analysis()` (0.1.0) — that module is simply not reconnected in this pass, and remains unreachable from the served path (verified: `canonical_evaluation.py` never imports it).

## Ranking

`EXISTS_AND_CONNECTED` (unchanged). Combined multi-program structures correctly participate as priced-but-not-comparable, exactly like any other non-baseline candidate — never contaminating the numeric rank.

## Scenario categories

Thin mapper added (`canonical_production_view._scenario_category()`), all 5 named states wired: RECOMMENDED (rank 1) — connected; ALTERNATIVE (comparable, not rank 1) — connected; CO_PRO_OPPORTUNITIES (treaty_slug present) — wired but currently unreachable (treaty attachment deferred, see above); PRICED_LOW_FIT (priced, not comparable) — connected and runtime-proven (both new CA structures land here); NOT_AVAILABLE (unpriced) — connected (pre-existing capability_only/rule_rejected candidates).

## Little Utopia / FVD

Both continue to use the exact same canonical `evaluate_project()`/`build_production_and_structures()` path — no project-specific branching added. Both now surface the two combined CA structures identically, proving the reconnection is generic, not LU-special-cased.

## New optimizer capability created

**None.** `canonical_stack_bridge.py` is connection glue only: a rule/slug loading adapter (integration piece (c)) and a stack-pricing bridge (integration piece (b)), both from the explicitly pre-authorized list. No new stacking doctrine, no new economics formula, no new persistence model (existing `ProductionStructure`/`StructureCalculationResult` JSON fields extended, not replaced).

## Tests

10 new (`test_canonical_stack_bridge.py`), 3 updated with inline reasoning for legitimately-grown counts (never silently weakened). Full suite: 4238 passed, 1 skipped, 1 pre-existing unrelated frontend failure (documented in the Worldwide Base Program Database closeout).

## Files changed

`app/calculators/canonical_stack_bridge.py` (new), `app/services/canonical_evaluation.py`, `app/services/canonical_production_view.py`, `tests/test_canonical_stack_bridge.py` (new), `tests/test_canonical_authority_substrate.py`, `tests/test_canonical_pricing_path_and_discovery.py`, `tests/test_canonical_served_wiring_repair.py`, `tests/test_canonical_production_view.py`, `docs/architecture/CAPABILITY_LEDGER.md`, this file.

STOP.

## Final completion (same day, commit after `c7593a7`)

**Final gate: `EXISTING_OPTIMIZER_STACKER_FULLY_CANONICALLY_RECONNECTED`** — with one disclosed architectural limit (see below), not a silent gap.

Component/split (Task A), treaty/official co-production (Task B), and hybrid/anchor (Task C) — previously reported `PROVEN_UNRECOVERABLE_WITH_EXACT_REASON "for this pass"` — are now all `CONNECTED_AND_RUNTIME_VERIFIED`, real project data, both LU and FVD. Full account in `docs/architecture/CAPABILITY_LEDGER.md`'s "Existing Optimizer/Stacker Reconnection, completion" entry.

- **Component/split**: real movable-component spend (post/vfx/music) from each project's own budget routed to alternative jurisdictions via the existing `StructureSpec` `component_relocation` type — 15 candidates on FVD, 10 on LU, allocation-conservation and no-invented-spend proven.
- **Treaty/co-pro**: new `canonical_treaty_bridge.py` fail-closed adapter over the unedited `treaty_engine.py` — corrects a confirmed defect (unassessed/failed cultural tests could resolve `is_eligible=True` in the underlying engine). FVD's Greece generates one real, registry-backed Eurimages `CO_PRO_OPPORTUNITY` (36 real member candidates); Mauritius proven-zero (no bilateral treaty, not a Eurimages member).
- **Hybrid/anchor**: `relationship_types` (stack/component/coproduction/conditional_fund) exposed as independent flags on every structure; `treaty_coproduction` now composes with the conditional-funds layer, proving "hybrid != treaty" with real, mutually-exclusive-where-correct data.
- **One disclosed limit**: a genuine "anchor+stack+component" triple in ONE structure is architecturally blocked by `StructureSpec.incentive_programs` being one-program-per-jurisdiction — extending that would be a real architecture change, not a narrow adapter, and is reported as such rather than worked around.

23 new focused tests, 6 existing tests updated for the legitimately grown universe (127→143 FVD structures). Full suite: 4266 passed, 1 pre-existing unrelated failure, 1 skipped.
