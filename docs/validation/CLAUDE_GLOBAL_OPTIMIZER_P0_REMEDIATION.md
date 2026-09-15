# CineGlobe Global Optimizer P0 Remediation — Claude

Base commit (required starting HEAD, verified unchanged throughout): `0c97a6a692bcfb5d1344bd1c2f1ffc3db112cae2`.
Codex audit source (read directly via `git show`, never merged): `cdaf1968fe38e64af873ac9c4c6da53d03687446`.
Branch: `claude/audit-frametax-features-NZcX5`. Worktree: `~/cineglobe-frametax-claude-remediation`
(the sibling `~/cineglobe-frametax` was checked out to another agent's `ag/ui-refinement-review`
branch throughout and was never touched).

## Summary

Implements the six P0 optimizer defects and two functional P1 contract defects proven by
Codex's global optimizer methodology audit. P1-ENG-001 (duplicated treaty-construction
refactor) is explicitly deferred per the user's instruction. All work is confined to
`app/services/canonical_evaluation.py`, `app/services/canonical_production_view.py`, and
test files; no canonical program values, no frozen economics, no MFNI/reinvestment/UI/Globe/
location-feasibility work.

## P0 findings

### P0-CAND-001 — five-partner pre-evaluation cap removed

The home-anchored bilateral loop's `MAX_TREATY_PARTNERS = 5` slice (`find_real_bilateral_partners(...)[:5]`)
discarded every registered partner beyond the first five in list order **before** eligibility
was ever checked — Canada alone has 13 registered partners. Removed; every partner
`find_real_bilateral_partners` returns is now evaluated. Any future display/pagination limit
belongs in the served-view layer, never in generation.

### P0-CAND-002 — ten-participant multilateral display cap decoupled from evaluation

Both the Eurimages block and the European Convention/Ibermedia loop sliced the sorted partner
set to `MAX_*_DISPLAY = 10` **before** calling the evaluator itself, so an 11th+ eligible member
was never evaluated or accounted for, in any state. Fixed by keeping the `[:10]` slice
(`shown` / `_fw_shown`) strictly for the served `coproduction_partners` display list, while
the evaluator (`evaluate_eurimages_coproduction_opportunity`, the European Convention/Ibermedia
`_evaluator`) is now called against the full sorted set (`_eurimages_participants` /
`_fw_participants`).

### P0-CAND-003 — candidate identity decoupled from priceability

`reachable_codes` (the shared base set every treaty-type loop draws `candidate_codes` from)
was `set(priced_by_code)` only — a registered partner whose own ordinary program had not yet
priced deterministically (`RULE_DATA_INCOMPLETE`/`capability_only`/etc.) silently vanished as a
treaty *party*, even though `production_discovery` had genuinely examined it. Fixed:
`reachable_codes = {c[0] for c in candidates} | set(priced_by_code)` — the full canonical
discovery universe (`candidates`, built from `discovery.accepted` / `accepted_alternatives` /
`capability_only`) is now unioned in. A registered partner with only attainable missing facts
remains a visible, disclosed conditional candidate instead of disappearing. Verified directly:
Little Utopia's real GB+AU (`uk-au-bilateral`) opportunity — previously hidden as a downstream
side effect of an unrelated B1 authority ruling reclassifying AU's only priced leg fail-closed —
correctly reappears as a disclosed, never-priced, never-ranked conditional opportunity, restoring
the exact behavior `test_lu_australia_uk_bilateral_opportunity_surfaces_independent_of_mauritius`
was originally written to prove. FVD's non-home-anchored bilateral count moved from 8 to 25 real,
independently-discovered candidate pairs (full enumeration; both counts and reasoning recorded in
`test_treaty_coproduction_wiring.py`'s own updated history comments).

### P0-QUAL-001 — co-production facts scoped to treaty + ordered participants

`_coproduction_facts` read exactly three project-global `ProjectFact` keys
(`coproduction_majority_pct`/`minority_pct`/`cultural_test_passed`), fetched once and reused
across every treaty a project discovers — a fact entered for one treaty resolved every other
treaty and every other participant combination. Fixed: fact keys are now scoped to
`(treaty_slug, ordered participant identities)` via `_coproduction_fact_scope`/
`_coproduction_fact_keys`. For bilateral treaties, `treaty_slug` is resolved via a read-only
registry lookup (`te.get_bilateral_treaty`, no side effects) before facts are fetched, since the
slug is not known statically. For the three multilateral frameworks (Eurimages,
`european-convention-coproduction`, `ibermedia-multilateral`), `treaty_slug` is a fixed constant
with no such ordering problem. A new `_multilateral_coproduction_facts` helper supports
**participant-specific percentages** for N-party frameworks (`coproduction_participant_pct::<scope>::<code>`
per participant; `country_pcts` stays `None` — never a partially-filled dict — unless every
participant has an on-file value). The fingerprint's co-production input is no longer one
hardcoded 3-tuple: `_all_coproduction_facts_for_fingerprint` reads every scoped co-production
fact row for the project (prefix match across all three key families) so a change to *any*
treaty's facts still invalidates cached results; both fingerprint computation sites
(`evaluate_project` and `current_generation_fingerprint`) were updated identically so they
never diverge.

### P0-STACK-001 — unknown stackability publishes no combined economics

`_build_conditional_bilateral_scenario`'s same-jurisdiction multi-slug loop fell back to a raw,
unadjusted **sum** of each program's own incentive whenever `price_program_group_stack` found no
named rule — an economically unknown combination was published and ranked identically to a
verified one. Fixed: an unresolved group's incentives are never summed into the scenario total.
`unresolved_stack_groups` tracks each such group (`rejection_reason_class: "RULE_DATA_INCOMPLETE"`,
retained, never dropped); if any exist, the whole scenario publishes
`conditional_incentive_usd=None`, `conditional_npc_usd=None`, `fully_priced=False`,
`status="RULE_DATA_INCOMPLETE"`, and a machine-readable `blocking_reason` naming every unresolved
group's jurisdiction/program_slugs. Individually-priced legs stay visible in `priced_components`.
The already-working resolved path (a named rule genuinely applies) is unchanged and still
publishes real combined economics — proven by both a positive and negative Claude-owned test.

### P0-COMB-001 — combined co-production + component + anchor + authorized-local-stack topology

No prior structure type combined an official co-production leg with a routed component leg
inside one conserved allocation. Implemented directly on the **existing, already-tested**
`StructureSpec` + `derive_account_allocation` + `price_allocated_structure` kernel — using
`structure_type="hybrid"`, a `STRUCTURE_TYPES` entry the architecture's own comments already
reserved for exactly this combination ("treaty co-production, majority/minority, multi-party,
hybrid, anchor-component are all combinations...") but which no caller had ever constructed.
`_price_combined_coproduction_component_candidate` prices three participants (home anchor,
treaty partner, a genuinely third component-routed jurisdiction) through one conserved
allocation — `derive_account_allocation`'s own conservation invariants (no unallocated account,
no duplicate account, totals conserve) are the structural guarantee against double allocation,
not a new hand-rolled check. `_authorized_local_stack_for_side` layers "authorized local stacks
on allocated sides" on top: it checks the anchor side for a second same-jurisdiction candidate
and applies `price_program_group_stack` (the same P0-STACK-001 fail-closed gate) — a resolved
named rule adds only the *incremental* delta over the base program's own already-counted value
(never double-counted); an attempted-but-unresolved stack is retained as its own separate
`RULE_DATA_INCOMPLETE` rejected candidate while the base (unstacked) combined structure still
stands on its own. Every rejected/unresolved candidate is retained with a machine-readable
`rejection_reason_class`, never dropped. Ranking admission is gated by `is_fully_priced`, the
same existing mechanism every other structure type uses — an unresolved combination never
ranks. Scoped deliberately for this bounded pass: activates only for a home-anchored bilateral
partner whose treaty resolves `ELIGIBLE` (real ownership/cultural facts on file), attempting the
single highest-spend movable component routed to the single best remaining distinct target per
eligible partner (a documented search-space bound, not a truncation of an already-priceable
candidate — none of the frozen/fresh productions currently have treaty ownership facts on file,
so this topology is additive and touches no existing candidate for any of them).

**Performance repair applied during verification** (not a P0 finding, but load-bearing for
correctness/efficiency, per direct diagnosis — see "Performance diagnosis" below): the initial
implementation ran the partner/treaty/facts discovery a second, fully redundant time in a
separate loop. Merged into the existing home-anchored loop, reusing the same-iteration `opp`/
`partner_jur` instead of recomputing — eliminates genuine duplicate `find_real_bilateral_partners`
/ `te.get_bilateral_treaty` / `_coproduction_facts` / `evaluate_bilateral_coproduction_opportunity`
calls. Verified via `cProfile` before/after (5.76s → 5.71s for a forced-fresh FVD evaluation) and
via the full regression suite (no behavioral change, only fewer redundant calls).

## Functional P1 closeout

### P1-CLASS-001 — one backend-owned, mutually exclusive classification

`canonical_production_view._structure_classification` derives exactly one of nine values
(`SINGLE_JURISDICTION`, `OFFICIAL_COPRODUCTION`, `HYBRID_ANCHOR_COMPONENT`, `STACKED_PROGRAMS`,
`COMBINED_COPRO_HYBRID_STACK`, `CONDITIONAL_USER_FACT_REQUIRED`, `RULE_DATA_INCOMPLETE`,
`AUTHORITY_LOCKED`, `REJECTED_FOR_PROJECT`) for every emitted structure, from fields this module
already reads off `calculation_trace_json` for every other served field — never a new signal,
never left for a frontend consumer to infer from `structure_type` + `candidate_status` +
`relationship_types` combinations on its own. Served as `"classification"` on every structure
entry; proven present and valid for every structure of a real, freshly-evaluated project
(Little Utopia).

### P1-TRACE-001 — unique allocated spend vs. reusable claim bases separated

The multi-program stack combination branch labeled `sum(per_program_qpe_usd[...])` as
`total_qualifying_spend_usd` — a sum of each stacked program's own (potentially overlapping)
claim base, presented as if it were a single unique QPE figure. Fixed: the sum is now honestly
named `total_claim_bases_usd`; `total_qualifying_spend_usd` keeps its original key (so a reader
expecting "the QPE figure" is never silently handed the wrong number) but its value is now
`max(per_program_qpe_usd.values())` — the most conservative non-invented lower bound on unique
allocated spend available from this stacking path's already-rolled-up `StackCandidate` objects
(a true line-level union is not reconstructable here without inventing one; `max()` never
overstates it the way `sum()` did).

## Deferred — P1-ENG-001

The duplicated treaty-construction-loop refactor (home-anchored vs. non-home-anchored bilateral
loops share near-identical structure-building code) was **not** performed this pass, per the
explicit instruction not to mix a nonfunctional refactor into the P0 repair. Remains open.

## Performance diagnosis (raised mid-session, resolved)

During DB-backed test verification, `tests/test_codex_final_optimizer_health_audit.py` repeatedly
timed out (observed up to ~13 minutes on one run). Diagnosed with `cProfile` against a forced-fresh
`evaluate_project(FVD)` (fingerprint monkeypatched to guarantee no cache reuse): genuine fresh
generation consistently completed in **5.5–6.4 seconds** end to end (624–676 real INSERTs,
proportional to the correctly-widened candidate universe — no Cartesian explosion, no repeated
identical treaty evaluation in generation itself). Root cause was proven to be **outside the
optimizer entirely**: the test file's own pre-existing `_current_rows()` helper ran an unbounded,
unordered `SELECT *` against `structure_calculation_results`/`production_structures` — FVD alone
has accumulated **204,635 historical rows** across this project's long multi-session development
history (every prior `evaluate_project()` run ever persisted, never pruned). Timed in complete
isolation from all optimizer code: **>200 seconds** just to fetch and deserialize that result set.
Repaired by adding `.order_by(created_at.desc()).limit(500)` to the helper (preserves every
test's real intent — both fresh and immediately-superseded-stale rows are always among the most
recent — while bounding runtime independent of historical table size). All 9 tests in the file
now pass/skip in 5.52s total. A separate, minor genuine inefficiency was also found and fixed
during this investigation (the P0-COMB-001 duplicate-pass merge described above). The 204,635-row
historical accumulation itself is a pre-existing data-hygiene characteristic of this long-running
project, unrelated to and out of scope for this P0 remediation pass; not remediated here.

## Frozen economics — confirmed exact, under a genuinely fresh (`EVALUATION_COMPLETE`) evaluation

| Project | Incentive (USD) | NPC (USD) | Match |
|---|---|---|---|
| Little Utopia | 573,059.70 | 3,791,333.30 | Exact |
| F#K Valentine's Day | 1,445,659.84 | 3,072,027.16 | Exact |
| Bad Hombres | 596,910.25 | 1,885,112.75 | Exact |
| Lips Like Sugar | 3,459,278.90 | 8,524,375.10 | Exact |

All four recomputed directly against the fully-remediated engine (`canonical-1.55.0`) after
deleting each project's current-engine-version cached rows to force genuine regeneration
(`EVALUATION_COMPLETE`, not `EVALUATION_REUSED`). Byte-exact against the established figures.

## `ENGINE_VERSION` bump

`ENGINE_VERSION` bumped `canonical-1.54.0` → `canonical-1.55.0` so every previously-persisted
`StructureCalculationResult` row (generated under the pre-remediation candidate/fact/stacking/
topology logic) is treated as stale and regenerated fresh on next evaluation — never silently
served as `EVALUATION_REUSED` under the corrected engine.

## Tests

`tests/test_claude_global_optimizer_p0_remediation.py` (new, Claude-authored from scratch against
the actual post-remediation code — Codex's own test file, if present, is read-only evidence and
was never copied or cherry-picked): 27 tests covering all eight findings — source-inspection
negative oracles for the removed caps (P0-CAND-001/002), a direct proof that `reachable_codes`
unions the full discovery universe (P0-CAND-003), pure scope-derivation plus an end-to-end DB
fact-isolation proof (P0-QUAL-001), positive and negative `_build_conditional_bilateral_scenario`
proofs (P0-STACK-001), allocation-conservation and stack-retention proofs
(P0-COMB-001), parametrized classification-derivation coverage plus a live served-view proof
(P1-CLASS-001), and a direct `total_claim_bases_usd`/`total_qualifying_spend_usd` divergence proof
(P1-TRACE-001). All 27 pass.

Two existing repo tests in `tests/test_treaty_coproduction_wiring.py` encoded the exact
pre-remediation defects (P0-CAND-001/002/003) as their expected behavior and were updated in
place to the corrected, intended behavior, with the reasoning and exact new counts recorded
directly in the test file's own history comments (matching that file's established convention):
`test_lu_australia_uk_bilateral_opportunity_surfaces_independent_of_mauritius` (GB+AU now
correctly reappears) and `test_fvd_eurimages_opportunity_reaches_co_pro_opportunities_category`
(non-home-anchored bilateral count: 8 → 25, fully enumerated and explained).

## Focused test results

| Suite | Result |
|---|---|
| `tests/test_claude_global_optimizer_p0_remediation.py` (new) | 27 passed |
| Treaty/co-production/stacking/component/integrity focused suite (21 files, ~506 tests) | 504 passed, 2 pre-existing failures (see below) |
| `tests/test_codex_final_optimizer_health_audit.py` | 7 passed, 2 skipped (legitimate — program not a candidate for current inputs) |
| Four frozen project controls (direct fresh recomputation) | 4/4 exact, unchanged |

### Pre-existing failures (proven, not caused by this pass)

`test_price_program_pair_stack_mutually_exclusive_zeroes_lower_value` and
`test_conditional_scenario_routes_same_jurisdiction_multi_slug_through_stack_engine` (and two
narrower-base-rejection tests in `test_canonical_economics_integrity_repair.py`) fail because
`ca_bc_pstc`'s rate no longer resolves at all — confirmed via direct `git stash` + re-run against
**pristine, unmodified `0c97a6a`**: all four fail identically before any change in this pass. Root
cause is the prior session's own accepted `ca_bc_pstc` B1 discretionary-ruling addition
(`docs/validation/CINEGLOBE_CANONICAL_STATE_CLEANUP_CLAUDE.md`, already part of `0c97a6a`), not
this workstream, and out of scope for it.

## Fresh production runtime — see `CLAUDE_FOUR_PRODUCTION_FRESH_RUNTIME.csv`

Little Utopia, F#K Valentine's Day, and Underwater were forced to genuinely fresh
(`EVALUATION_COMPLETE`) evaluation by deleting each project's current-`ENGINE_VERSION` cached
rows before evaluating. **V-BRAT does not exist in the application database under any spelling**
(confirmed via both an `ILIKE` search across all 59 project titles and a broader raw-SQL pattern
search) — reported `BLOCKED_NOT_PRESENT_IN_APPLICATION`, no substitute project evaluated in its
place.

## Guardrails honored

No external jurisdiction research. No MFNI/reinvestment/UI/Globe/location-feasibility work. No
canonical program value changed to make a test pass — the two remaining test failures are
pre-existing and were left exactly as found, documented rather than silently patched around. The
frozen 301-program single-jurisdiction population was not reopened. Grants/in-kind remain separate
from QPE (untouched). Every rejected candidate/component carries a machine-readable
`rejection_reason_class`. No mock production records were created or used.

## Remaining defect (precise)

P1-ENG-001 (duplicated treaty-construction-loop refactor) remains open, as explicitly deferred.
Underwater's served view carries no `is_baseline=True` single-jurisdiction structure (its
"current base" jurisdiction has no priced candidate under current facts) — observed during fresh
verification, not a frozen-economics regression (Underwater is not one of the four protected
projects), not investigated further as out of scope for this bounded pass; flagged for a future
session.
