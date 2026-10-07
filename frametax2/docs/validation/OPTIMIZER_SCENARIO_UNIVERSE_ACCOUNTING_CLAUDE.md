# Optimizer scenario-universe accounting (canonical-1.104.0)

Date 2026-10-06. Branch `claude/global-optimizer-remediation`, started at `dac1514`. Database `frametax2_claude_optimizer_acceptance_20260919` (asserted on every read, test and regeneration). No external research.

## Result

The canonical optimizer universe is exhaustive at 1.104.0, and every candidate has exactly one recorded disposition. Three silent-drop coverage defects were found in the candidate generator. All three are repaired in their canonical owner (`backend/app/services/canonical_evaluation.py`, `ENGINE_VERSION = canonical-1.104.0`). Each of the four productions was regenerated exactly once under the 720 s ceiling:

| Project | Regeneration time |
|---|---|
| LU | 96.9 s |
| BH | 13.7 s |
| FVD | 421.1 s |
| LLS | 571.9 s |

Every candidate that existed at 1.103.0 keeps identical economics. Across every economic identity served at both versions there are 0 differences in verified NPC, adjusted NPC, incentive, confirmed floor or maximum. Also identical at both versions: the baseline NPC, the 217-row single-jurisdiction contract, best-per-jurisdiction winners and the leading structures. No rate, QPE, cap, eligibility, stacking, materiality or music-carve-out threshold changed.

## What "complete canonical universe" means in this engine

The engine never materialises one row per candidate (PERSISTENCE CARDINALITY RULE). The terms are therefore defined against its own counters:

- **Generated candidates (G).** Every structure the generator hands to the bulk writer as a priced or dispositioned candidate. This is `evaluation_generation_summaries.total_rows`. It is not a CSV row count, a loop count, the persisted-row count or a UI card count.
- **Fail-closed identity at commit.** `G = persisted detailed rows + Σ evaluation_candidate_aggregates.candidate_count`.
- **Complete canonical universe.** G plus the two classes of hybrid combinations a branch-and-bound proof accounts for without generating them:
  - (a) **Bound-dominated:** combinations whose naive upper bound cannot beat the incumbent (`dominated_combination_count`).
  - (b) **Non-route visits:** visited index-tuples that are not a distinct route (`non_route_combination_counts`, new in 1.104.0).

  For every hybrid search, `total_candidate_combinations = Π |candidate list| = visited + dominated` and `visited = evaluated + non-route`. The hybrid candidates in G equal Σ evaluated over the proof rows exactly.
- **Structural no-candidate conditions are not candidates.** These are: a component with zero spend; the home jurisdiction as its own destination; a subset whose legal target list is empty for the anchor; and a program pair already represented or provably illegal under the anchor's authority scope. They are pre-candidate rules of the canonical owner, listed in its code comments.

## Per-project reconciliation (1.104.0, persisted summaries and aggregates, read-only SQL)

Disposition mapping used in these tables:

- **Retained/served:** retained PRICED rows.
- **Aggregated:** PRICED candidates outside the retention lanes. They are counted per group with exact count, NPC range and best identity, and are reachable at `GET /projects/{id}/evaluation/aggregates`.
- **Dominated:** `DOMINATED_WITH_PROOF` rows, plus the bound-dominated combinations each one proves.
- **Incompatible/illegal:** `RULE_REJECTED` (pairwise incompatible, threshold not met, minimum spend, statutory conditions, no authority) and `QUALIFICATION_HARD_FAIL`.
- **Conditional/needs facts:** `CO_PRO_OPPORTUNITY` and `FEASIBILITY_REVIEW_REQUIRED`.
- **Non-priceable:** `UNPRICEABLE_AUTHORITY_INSUFFICIENT`.
- **Policy-suppressed:** a curation of served priced scenarios, shown in the served table below.

### Generated-candidate equation

| | LU | FVD | BH | LLS |
|---|---:|---:|---:|---:|
| **Generated G** | **223,058** | **1,199,447** | **11,491** | **1,280,568** |
| = persisted detailed rows | 977 | 1,731 | 917 | 1,721 |
| + aggregated (Σ group counts) | 222,081 | 1,197,716 | 10,574 | 1,278,847 |
| aggregate groups | 5,354 | 5,885 | 5,034 | 5,713 |
| PRICED = retained + aggregated | 197,534 = 659 + 196,875 | 248,088 = 1,052 + 247,036 | 11,062 = 602 + 10,460 | 1,278,362 = 1,037 + 1,277,325 |
| DOMINATED_WITH_PROOF | 274 | 634 | 271 | 641 |
| RULE_REJECTED (incompatible/illegal) | 25,206 | 950,680 | 114 | 1,522 |
| QUALIFICATION_HARD_FAIL | 1 | 0 | 0 | 0 |
| CO_PRO_OPPORTUNITY (needs facts) | 25 | 27 | 25 | 25 |
| FEASIBILITY_REVIEW_REQUIRED (conditional) | 8 | 8 | 8 | 8 |
| UNPRICEABLE_AUTHORITY_INSUFFICIENT | 10 | 10 | 11 | 10 |
| Check: PRICED + unpriced = G | ✓ | ✓ | ✓ | ✓ |

### Hybrid search space (`ordinary_component_hybrid` proof rows)

| | LU | FVD | BH | LLS |
|---|---:|---:|---:|---:|
| proof rows (searches) | 274 | 634 | 271 | 641 |
| of which single-unit (new) | 182 | 270 | 180 | 273 |
| total combinations = Π lists | 344,509 | 20,341,348 | 323,471 | 29,710,123 |
| bound-dominated (not generated) | 118,272 | 19,096,500 | 312,446 | 28,388,469 |
| visited | 226,237 | 1,244,848 | 11,025 | 1,321,654 |
| evaluated (= hybrid candidates in G) | 222,424 | 1,198,331 | 10,844 | 1,279,441 |
| non-route: same destination, nested bundle (post_vfx_package + vfx) | 3,813 | 15,259 | 0 | 12,340 |
| non-route: same destination, separate bundles (music + post/VFX) | 0 | 31,258 | 181 | 29,873 |
| non-route: degenerate / duplicate route | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

### Served reconciliation (`GET /api/v1/cineglobe/projects/{id}/state`, engine 1.104.0, reuse only)

| | LU | FVD | BH | LLS |
|---|---:|---:|---:|---:|
| retention generated / retained / aggregated | = summary ✓ | ✓ | ✓ | ✓ |
| optimizer candidates (retained priced hybrid + component rows, distinct identities) | 557 | 948 | 501 | 932 |
| Σ raw_variant_count over scenarios + suppressed (no identity collapse) | 557 | 948 | 501 | 932 |
| curated scenarios (`optimizer_scenarios_total`) | 557 | 418 | 152 | 481 |
| music policy-suppressed (≤ $25,000 or costlier) | 0 | 530 | 349 | 451 |
| music splits surfaced (> $25,000) | 0 | 0 | 0 | 65 |
| recommended + evaluated alternatives = curated | 0 + 557 | 0 + 418 | 0 + 152 | 0 + 481 |
| co-production opportunities needing facts | 25 | 27 | 25 | 25 |
| jurisdiction winners (`best_per_jurisdiction`) | 92 | 91 | 91 | 92 |
| single-jurisdiction contract rows (unique) | 217 | 217 | 217 | 217 |
| leading / strong / reference / conditional / not suitable / unavailable / incomplete | 1/0/73/20/18/1/104 | 1/0/72/20/18/2/104 | 0/0/0/111/0/2/104 | 1/0/25/51/35/1/104 |
| fit confirmed / unconfirmed / low-fit | 379/0/178 | 307/0/111 | 0/152/0 | 170/184/127 |

Retained priced rows that are not optimizer candidates are the single-jurisdiction and stack rows: LU 102, FVD 104, BH 101, LLS 105. These are served in the single-jurisdiction surfaces.

## Structure-family coverage

| Family | Engine owner / disposition | Status |
|---|---|---|
| Single-jurisdiction / full relocation | `full_relocation`, `single_country`. The 217 single-jurisdiction contract covers every jurisdiction (winner, conditional, not suitable, unavailable or data incomplete). | covered |
| Two-party hybrid, home principal + one unit | `component_relocation`, now routed under both the destination's best overall program and the component's own best program (D3) | covered (repaired) |
| Two-party hybrid, relocated principal + one unit (ARCH-01..04) | hybrid branch-and-bound, single-unit subsets (D1) | **was missing; repaired** |
| Three-/four-party hybrid | hybrid branch-and-bound, r ≥ 2 subsets | covered |
| Treaty / co-production, multi-principal | `CO_PRO_OPPORTUNITY` rows. No priced official co-production exists for these four projects because the ownership/cultural facts are not on file. | covered (needs facts) |
| Post/VFX package and permitted VFX split | bundle `post_vfx_package`, with `vfx` exposed only where a destination program distinguishes VFX spend (e.g. OCASE) | covered |
| Music carve-out | every music split is generated and priced. Curation is served-only (strict > $25,000 vs the repriced bundled counterpart); suppressed splits are kept in `optimizer_scenarios_music_suppressed`. | covered |
| Grant/fund and selective overlays | `multi_program`, stacks and `FEASIBILITY_REVIEW_REQUIRED` (selective / non-guaranteed / authority-unresolved) | covered |
| References costlier than the anchor | served as `COSTS_MORE` evaluated alternatives. Never removed. | covered |

## Silent-drop defects found and repaired

1. **D1: relocated principal + a single movable unit was never enumerated.**
   - **Cause:** the hybrid search started every anchor at two routed units (`for _r in range(2, …)`).
   - **When it became a real gap:** since the 1.98.0 Post/VFX bundling, "principal in X, post/VFX package (or music, or VFX) to Y" had no generator for any non-home anchor. That is canonical archetypes ARCH-01..04 with a relocated principal, and the commonest practical two-jurisdiction hybrid.
   - **Fix:** a non-home anchor now starts at one routed unit. The home anchor still starts at two, because its single-unit routes are the `component_relocation` family.
   - **Added before curation:** LU +182, FVD +270, BH +182, LLS +275 two-jurisdiction relocated-principal hybrids.
2. **D2: visited hybrid tuples with no disposition.**
   - **Cause:** tuples routing two units to one destination (and degenerate or duplicate routes) returned `None`. They were counted only implicitly as visited − evaluated.
   - **Fix:** each is now counted by reason in the proof row.
   - **Nested bundles** (post_vfx_package + vfx to one destination) are the single-unit route D1 now generates.
   - **Separate bundles** (music + post/VFX to one destination) are not a distinct-destination hybrid. That combination is priced only as the music carve-out's bundled counterfactual (see Remaining).
3. **D3: home single-component family missed component-specific programs.**
   - **Cause:** the family routed each destination's best overall program only.
   - **Effect:** LLS's Portugal medium-budget tier (`pt_scri_pt_medium_budget`), which prices the music and VFX slices better than `pt_scri_pt_cash_rebate`, was never routed.
   - **Fix:** the per-component ranking now runs before the family, and the component's own best program is also routed. 2 routes added (LLS).

Displaced from the served detail by the bounded-retention lanes (top-100 per key; not lost): 11 rows that were served at 1.103.0 (LU 1, FVD 3, BH 2, LLS 5). Each one traces to a 1.104.0 aggregate group whose count and NPC range include its NPC. Six of them are that group's best identity.

## Materiality

These policies affect curation only:

- the $100,000 / $200,000 additional-jurisdiction recommendation threshold (`recommendation_status`);
- the strict > $25,000 music carve-out;
- fit priority.

Every structure that fails a threshold is still served as an evaluated, neutral or costs-more alternative, or as a music-suppressed entry with its delta and counterpart. Recommended + evaluated alternatives equals curated, and curated + suppressed equals the pre-curation total, for all four projects.

Example trace (BH):

- **Retained:** Ontario principal + post/VFX → Manitoba: PRICED, `EVALUATED_ALTERNATIVE`, `NOT_MUSIC_SPLIT`, one raw variant.
- **Suppressed:** Manitoba principal + music → Belgium: `SUPPRESSED_BELOW_THRESHOLD`, delta −$222,750 against its bundled counterpart, which is $1,407,584.55 with music kept with the Manitoba principal.

## Tests (each family run once, reuse only, acceptance DB asserted)

| Family | File(s) | Result |
|---|---|---|
| New: candidate accounting, search space, single-unit coverage, D3 programs, served reconciliation | `backend/tests/test_optimizer_scenario_universe_accounting.py` | 20/20. 3 nodes failed first on a JSONB key-order assumption in the test itself; they were fixed and only those 3 nodes were rerun. |
| Persisted to served | `test_canonical_production_view.py`, `test_jurisdiction_accounting.py` | 70/70. The 4 curated-total oracles and the ordering test were updated (see below). |
| Identity, structure family, materiality, music | `test_economic_identity.py`, `test_structural_archetype_generator.py`, `test_music_carveout.py`, `test_marginal_materiality_explanation.py` | all pass |
| Candidate-accounting invariant | `test_bounded_candidate_retention.py` | 9/10. See below. |
| Frontend count/reachability contract | 8 workspace/optimizer/single-jurisdiction contract files | 106/106 |

Two corrections in `test_canonical_production_view.py`:

- **Curated-total oracles:** updated to LU 557, FVD 418, BH 152, LLS 481.
- **Ordering test:** the fit-aware order of 2026-10-01 sorts by fit priority first, and tier then NPC hold within each fit group. The test asserted tier order across the whole list, which only held while no practical route was weak-fit.

`test_bounded_retention_equals_full_enumeration_exactly` is pre-existing, not addressed, **INCOMPLETE**:

- **Reproduced:** it fails identically at the unchanged `dac1514`.
- **Cause:** it has been stale since 1.92.0. The bounded writer stamps `structural_classification` onto persisted traces, but the legacy control path never did.
- **Correction attempted:** correcting that comparison lets the test reach code that has not run since then. Its `_aggregator.rows()` call omits the family argument production now passes, and it compares thousands-entry dicts.
- **Outcome:** the corrected run stalled twice. Per the anti-loop rule the node is final as INCOMPLETE, and the test file was reverted.

## Browser (local, implementation evidence only)

Workspace counts read on `http://localhost:5173` against the restarted 1.104.0 backend, with no new generation created:

| Project | Single Jurisdiction | Optimizer |
|---|---|---|
| LU | 6 of 92 winners, all 217 reachable, 1/73/20/18/1/104 | 6 of 557, 25 co-production, fit 379/0/178 |
| FVD | 91 winners, 1/72/20/18/2/104 | 418, 27 co-production, 307/0/111 |
| BH | 91 winners, 111 conditional / 2 / 104 | 152, 25 co-production, 0/152/0 |
| LLS | 92 winners, 1/25/51/35/1/104 | 481, 25 co-production, 170/184/127 |

All match the API. New relocated-principal practical hybrids render (e.g. "Qatar: Post vfx package → Manitoba"). The UI status is `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION`.

## Remaining (not blockers for generation accounting)

1. `optimizer_scenarios_music_suppressed` (FVD 530, BH 349, LLS 451) is served by the API but no UI surface reads it. Policy-suppressed structures are therefore accounted for and reachable through the API, but not reachable on screen.
2. Aggregated PRICED candidates (outside the top-100 lanes) are reachable via `/evaluation/aggregates` only.
3. Routing music and post/VFX to the same destination is not a standalone hybrid candidate. It is counted (`same_destination_separate_bundles`) and priced only as the music carve-out counterfactual. Making it a candidate is a product decision, because the 1.98.0 bundling doctrine keeps music its own bundle.
4. `test_bounded_retention_equals_full_enumeration_exactly`, stale since 1.92.0 (see Tests).
