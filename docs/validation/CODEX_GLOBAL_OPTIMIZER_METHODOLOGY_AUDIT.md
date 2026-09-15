# CineGlobe Global Multi-Jurisdiction Optimizer Audit — Codex

Audit date: 2026-09-15

Audited engine: `canonical-1.54.0`

Mode: independent read-only methodology/runtime audit
Verdict: **NOT ACCEPTED**

## Scope and exclusions

This audit starts from the current canonical repository and runtime. It does not reopen single-jurisdiction research, the frozen 301-program population, Netherlands, South Africa, Oregon, Malaysia, MFNI, reinvestment, UI/Globe, or location feasibility. It evaluates the requested 285-program optimizer population and uses the four frozen real projects as controls, not as the complete methodology oracle.

Five concurrent cleanup identities/groups were excluded from the verdict exactly as directed: `bg_film_encouragement_act_rebate`, `ca_bc_dave`, the Ohio canonical/proposed pair, `us_nv_film_credit`, and the Czech animation canonical/tier identity. None of the findings below depends on those rows.

## Executive result

The existing ordinary single-program, component-routing, and named in-jurisdiction stack paths retain their accepted arithmetic. All four project anchors and NPCs reproduced exactly. The optimizer nevertheless fails the expanded multi-jurisdiction acceptance gate because it can omit real treaty candidates, reuse one co-production fact tuple across unrelated treaties, publish economics for an unknown same-jurisdiction stack, and cannot generate an executable structure combining co-production, component allocation, and authorized local stacks.

These are methodology and runtime-topology failures. They are not new jurisdiction-research gaps and cannot be closed by preserving four existing winners.

## Gate result

| Gate | Result | Basis |
|---|---|---|
| Official co-production | FAIL | Bilateral cap 5; multilateral cap 10; global rather than treaty/participant-scoped facts; conditional-only partner filter |
| Hybrid anchor/component | FAIL | Base allocation path works, but only `home_best` and one `target_best_by_code` are used; authorized stacks cannot compose on either side |
| Stacked programs | FAIL | Named ordinary stacks fail closed and Ontario arithmetic passes; conditional co-production path bypasses that rule by summing when the stack bridge returns `None` |
| Combined structures | FAIL | No executable co-pro + component + stack topology exists |
| Candidate completeness | FAIL | Pre-evaluation caps and priced-leg prerequisite discard candidates |
| Numerical crosscheck | FAIL | Four baselines and Ontario pass; unknown conditional stack and shared-QPE trace fail |
| Classification contract | FAIL | Existing type/status/relationship signals do not yield exactly one required backend classification |
| Engineering audit | FAIL | Five P0 and three P1 findings remain |

## Candidate generation

### P0-CAND-001 — bilateral and multilateral generation caps

The canonical treaty registry contains 26 bilateral treaties. Independent degree counting finds Canada with 13 partners, Great Britain with 8, and Australia with 6. `evaluate_project()` sets `MAX_TREATY_PARTNERS = 5` and slices the home-partner list before eligibility evaluation (`canonical_evaluation.py:3911-3912`). Therefore a structurally valid sixth or later registered partner cannot be represented.

Eurimages and the European Convention/Ibermedia loops likewise slice candidate participants to ten and pass only the displayed slice into the eligibility evaluator (`canonical_evaluation.py:4118-4127`, `4203-4208`). A presentation bound has become an evaluation bound.

### P0-CAND-003 — conditional partner discovery depends on priced economics

Treaty `candidate_codes` is constructed from `priced_by_code` plus country prefixes (`canonical_evaluation.py:3895-3906`). A registered treaty partner whose relevant ordinary program is awaiting attainable facts has no priced leg and disappears before treaty eligibility is asked. The task contract requires that such a path remain visible as conditional. Candidate identity discovery and economic priceability are improperly coupled.

The ordinary stack search has its own four-program bound. Static enumeration found no current publishable same-location clique larger than four, so no present canonical candidate loss was proven from that constant alone. It is a bounded design risk, not counted as a P0/P1 finding in this verdict.

## Official co-production qualification

### P0-QUAL-001 — facts are not treaty or participant scoped

`_coproduction_facts()` reads only `coproduction_majority_pct`, `coproduction_minority_pct`, and `coproduction_cultural_test_passed` (`canonical_evaluation.py:1695-1738`). The same tuple is passed to every bilateral pair and each multilateral framework. It contains no treaty slug, ordered parties, participant percentage map, or participant-specific creative contribution/quota facts.

Consequently facts entered for one treaty can resolve unrelated treaties, and a multilateral structure cannot prove participant-level percentage and creative requirements. Missing facts are often disclosed, but facts that do exist have insufficient identity.

## Hybrid/component allocation

The existing base component path preserves the anchor, routes one movable component through canonical allocation/pricing, persists rule rejections, and no longer truncates targets. The focused component batch passed 32 tests.

However, `home_best` chooses one anchor program and `target_best_by_code` chooses one target program (`canonical_evaluation.py:3514-3517`, `3543-3558`). This prevents an otherwise valid component structure from applying a separately authorized anchor or target stack. The engine generates a best-program route, not the complete program-combination set for the allocated bases.

## Stacking

The ordinary canonical bridge behaves correctly on the tested named relationships. The independent Ontario oracle is:

`$200,000 OFTTC + ($1,000,000 CPTC base - $200,000 OFTTC) × 25% = $400,000`, with a `$50,000` reduction. Runtime matches exactly, and unknown ordinary pairs return `None`.

### P0-STACK-001 — unknown conditional stackability still produces economics

In `_build_conditional_bilateral_scenario()`, a same-jurisdiction group is passed to `price_program_group_stack()`. If the result is `None`, lines 1421-1436 add the raw incentives anyway, mark `stacking_verified=False`, and later publish `conditional_incentive_usd` and `conditional_npc_usd` from that sum (lines 1463-1471).

Disclosure is not authorization. Unknown stackability must produce visible rule-data-incomplete status with null combined economics, not an economically comparable total.

## Combined structures

### P0-COMB-001 — required topology is absent

All four live project results expose only `single_country`, `full_relocation`, `multi_program`, `component_relocation`, and `treaty_coproduction`. There is no executable structure type or allocation/pricing pass for co-production plus component allocation, hybrid plus authorized local stack, or the full combined co-pro/hybrid/stack case.

Treaty rows may contain `conditional_programs` metadata, and the served view may emit multiple `relationship_types`. That is descriptive composition, not an executable combined candidate with one allocation ledger, participant-specific QPE, stack order, incentive, and NPC.

## Classification contract

`canonical_production_view._empty_structure_entry()` derives `relationship_types` from program count, component allocations, treaty slug, and conditional programs (`canonical_production_view.py:232-262`). It also serves `structure_type`, `candidate_status`, and qualification information. Those fields are useful but do not guarantee exactly one of the required nine classifications. In particular, conditional, authority-locked, rule-incomplete, and combined cases require consumer inference and can overlap.

Required repair: add one backend-owned exclusive classification value derived from the existing canonical topology/status signals. No UI work is required by this audit.

## Numerical independence and conservation

Four independent `gross - incentive = NPC` control calculations and the independent Ontario stack calculation agree exactly with runtime. No baseline economic regression was found.

Two numerical/trace gates fail:

1. The unknown conditional stack publishes a raw sum without an authorized combination rule.
2. A multi-program trace reports `total_qualifying_spend_usd` as the sum of every program's QPE (`canonical_evaluation.py:3453-3473`). Where authorized programs share one base, that number is a claim-base sum rather than unique allocated project spend. The trace needs separate unique-allocation and per-program-claim-base fields to prove conservation without implying double allocation.

## Four real-project controls

| Project | Candidates | Priced / rejected | Treaty / component / stack | Anchor | Incentive | NPC | Result |
|---|---:|---:|---:|---|---:|---:|---|
| The Little Utopia | 243 | 125 / 118 | 9 / 108 / 1 | `mu_edb_incentive` | $573,059.70 | $3,791,333.30 | PASS; no verified winner; Manitoba remains conditional only |
| F#K Valentine's Day | 295 | 160 / 135 | 10 / 159 / 1 | `gr_cash_rebate` | $1,445,659.84 | $3,072,027.16 | PASS; no verified winner; Greece/Romania remains conditional |
| Bad Hombres | 240 | 123 / 117 | 8 / 106 / 1 | `us_nm_film_credit` | $596,910.25 | $1,885,112.75 | PASS; verified winner unchanged |
| Lips Like Sugar | 297 | 176 / 121 | 9 / 162 / 1 | `ca_film_30` | $3,459,278.90 | $8,524,375.10 | PASS; verified winner unchanged |

The live evaluation returned `EVALUATION_REUSED` for each project under `canonical-1.54.0`; the served view was rebuilt from the current generation. The accepted economic baselines are unchanged. Candidate counts are reported as current runtime facts and are not compared to older snapshots because the five concurrent cleanup groups were explicitly excluded.

## Engineering findings

Open findings are six P0 and three P1:

- P0: bilateral treaty cap; multilateral participant cap; priced-leg treaty filter; unscoped co-production facts; unauthorized conditional raw sum; missing combined executable topology.
- P1: exclusive classification contract gap; shared-QPE trace ambiguity; duplicated treaty-row construction across four loops.

The canonical integrity gate contains the previously requested freshness, rejection-accounting, participant, onboarding, and independent treaty recomputation protections. The historical `P1-GATE-001` is therefore closed in current source and is not repeated as an open finding here.

## Test evidence

Focused execution, all under the 180-second process alarm:

- Canonical stack bridge + stacking engine: 60 passed.
- Treaty/co-production group: 155 tests collected; execution completed with zero failures.
- Component/hybrid group: 32 tests collected; execution completed with zero failures.
- Full-inventory/optimizer group: 123 tests collected; execution completed with zero failures.
- Retained independent methodology probes: 6 passed.
- Four-project real canonical pipeline: 4 projects completed; zero timeout.

No full backend suite, browser, external research, UI test, MFNI test, or reinvestment test was run.

## Smallest repair sequence

1. Separate complete treaty identity enumeration from display pagination; remove pre-evaluation partner/participant slices and the priced-leg prerequisite for conditional identity discovery.
2. Scope co-production facts to treaty plus ordered participants and model per-participant allocation/creative facts.
3. Make an unknown stack relationship economically null in the conditional path.
4. Generate one conserved allocation topology capable of composing treaty, component, and named stack layers; enumerate authorized programs on each allocated side instead of choosing only one best program.
5. Serve one exclusive structure classification and distinguish unique allocated spend from reusable per-program claim bases.

After those bounded repairs, run the retained negative oracles plus the existing focused groups and four controls. Another worldwide program audit or jurisdiction-research pass is neither necessary nor authorized.
