# CineGlobe Final Optimizer Health / Safety Acceptance Audit

## Decision

`ONE_CONSOLIDATED_CORRECTION_PASS_REQUIRED`

The restored economic/provenance policy is directionally correct: incomplete structured provenance no longer kills an otherwise deterministic economic rule, while genuinely unresolved economic, selective, conditional, superseded, and non-economic programs remain blocked. That policy did not, by itself, grant Recommended status to the sampled original-58 programs.

The served optimizer is nevertheless not healthy. Two P0 defects prevent acceptance:

1. the project API serves persisted rows as current solely because they carry `canonical-1.34.0`, even though those rows predate later qualification, knowledge, and provenance changes; and
2. combined structures can lose or weaken member qualification state before the Recommended gate.

A mounted `0.1.0` calculation/persistence route and live unparameterized Little-Utopia state also leave more than one production-capable lineage. The targeted suite remains green because the most relevant guards do not exercise these behaviors.

## Baseline

| Check | Evidence |
|---|---|
| Repository | `surajgohill-oss/Frametax` (`origin=https://github.com/surajgohill-oss/Frametax.git`) |
| Branch | `claude/audit-frametax-features-NZcX5` |
| Audited HEAD | `6b4497334f3808c746a723a5719d10be5cb182ba` |
| Remote baseline | Same SHA, verified before the audit |
| Latest Claude closeout | `docs/validation/CLAUDE_FINAL_CANONICAL_BACKEND_CLOSEOUT.md` |
| Capability ledger | `docs/architecture/CAPABILITY_LEDGER.md` |
| Working tree at start | Only ten pre-existing, unrelated untracked files; none was read as authority, modified, or staged |
| Canonical evaluator | `backend/app/services/canonical_evaluation.py`, `ENGINE_VERSION = "canonical-1.34.0"` |

No external authority research was performed. Runtime and repository evidence only were used.

## 1. Optimizer lineage health

**Verdict: `ENGINE_WIRING_DEFECT`.**

The project-scoped frontend path is correctly shaped:

`useCineGlobe(projectId)` → `GET /api/v1/cineglobe/projects/{project_id}/state` → `canonical_production_view.build_production_and_structures()` → current-version `StructureCalculationResult` rows.

There is no title branch in `get_project_state`; LU and FVD use the same project-scoped adapter. Runtime modules inspected by `test_no_runtime_web_dependency.py` do not read the web, and the canonical runtime modules do not open validation artifacts.

However, two other mounted lineages remain production-capable:

- `POST /api/v1/projects/{project_id}/structures/{structure_id}/calculate` calls `run_full_analysis`, returns `engine_version="0.1.0"`, and persists the result in the same `structure_calculation_results` table (`backend/app/api/v1/structures.py::calculate_structure_impl`). It cannot become `leading_structure_id`, but it is still a served calculation API and persisted result lineage.
- The unparameterized `/api/v1/cineglobe/*` routes call `app.demo.little_utopia_state.get_state()` and are consumed by live company screens. Their prefix is `/cineglobe`, not an explicit demo namespace.

The project-scoped view filters the `0.1.0` rows out, so no current LU/FVD project response was observed selecting one. That containment is narrower than the required condition that no stale `0.1.0` path is serving and that no LU-specific production shortcut exists.

## 2. Original 58 control

### Economics restored

The current policy separates provenance and economics correctly at the registry boundary:

- 123 registered programs;
- 88 `AUTHORITY_VERIFIED_PRICEABLE`;
- 35 `AUTHORITY_UNRESOLVED_NON_PRICEABLE` as a retained provenance label;
- economic axis: 108 deterministic, 12 conditional/nondeterministic, 2 materially unresolved, 1 superseded;
- `AUTHORITY_UNRESOLVED_NON_PRICEABLE` is not in `BLOCKING_STATES`.

Read-only served samples from the original 58 confirm deterministic economics remain visible while provenance and qualification remain separate:

| Program | Provenance | Economic state | Served status | Qualification | Scenario |
|---|---|---|---|---|---|
| `au_nsw_pdv_rebate` | unresolved | deterministic | PRICED | RULE_DATA_INCOMPLETE | PRICED_LOW_FIT |
| `ca_mb_film_video_credit` | unresolved | deterministic | PRICED | RULE_DATA_INCOMPLETE | PRICED_LOW_FIT |
| `sg_made_with_singapore_rebate` | unresolved | deterministic | PRICED | NOT_APPLICABLE | PRICED_LOW_FIT |
| `us_az_motion_picture_production` | unresolved | deterministic | PRICED | RULE_DATA_INCOMPLETE | PRICED_LOW_FIT |

The sampled rows did not enter Recommended. Genuinely economic blockers remain governed by `BLOCKING_STATES`, and targeted direct-pricing tests passed.

### Limitation

These served project rows were generated before the final restoration commit. They demonstrate the present response shape, but they do not constitute a fresh served-runtime proof of the quarantine reversal. The stale-cache defect prevents claiming that the final correction itself was executed end to end.

**Original-58 verdict:** policy and single-program separation are correct; final served restoration proof is stale. No evidence of an `if previously accepted, always price and rank` bypass was found.

## 3. Economic / provenance separation

**Verdict: `STATE_MODEL_DEFECT`.**

Single-program state is separated correctly:

- deterministic economics may calculate with incomplete provenance;
- unresolved qualification remains priced/disclosed but is excluded from Recommended;
- economic blockers fail before rate pricing;
- conditional/selective programs do not enter deterministic NPC;
- provenance is separately reported.

The separation fails on combined structures because qualification state can be dropped or weakened. Once that happens, the Recommended gate no longer has the independent qualification dimension it expects.

The compatibility report also retains a misleading legacy field, `priceable_partial_authority: 0`, hard-coded to zero while 35 provenance-incomplete programs can price. The separate `authority_unresolved_non_priceable: 35` and economic-state counts preserve the underlying information, but the legacy field must not be used as proof that no priceable partial-provenance rows exist.

## 4. Qualification gating

**Verdict: `STATE_MODEL_DEFECT` for combined structures; healthy for sampled singles.**

For singles, the Recommended admission set is limited to `QUALIFIES` and `NOT_APPLICABLE`; `HARD_FAIL`, `CURABLE_GAP`, `USER_FACT_REQUIRED`, `SCRIPT_FACT_REQUIRED`, `AUTHORITY_UNRESOLVED`, and `RULE_DATA_INCOMPLETE` cannot enter the comparable pool.

For stacks, `canonical_evaluation.py` records single states under `(single_jurisdiction_code, program_slug)` but later looks up every stack member under `(stack_result.jurisdiction_code, program_slug)`. A federal `CA` member inside a `CA-ON` stack therefore misses its state. In addition, `_QUAL_STATE_SEVERITY` omits `RULE_DATA_INCOMPLETE`; its fallback severity equals the admitted `NOT_APPLICABLE`/`QUALIFIES` tier. A member ordering such as `[NOT_APPLICABLE, RULE_DATA_INCOMPLETE]` therefore incorrectly resolves to `NOT_APPLICABLE`.

Current persisted LU/FVD stack rows expose `role_qualification: null` for every combined structure. They predate the attempted propagation fix, another direct symptom of stale served state.

## 5. Stacking health

**Verdict: `STATE_MODEL_DEFECT`.**

Static stack mechanics are otherwise strong: the canonical bridge fails closed on unknown/conditional interactions, supports pairwise and N-way combinations, applies reductions in the declared direction, resolves aliases, and rejects mutual exclusions. The targeted stack suite passed.

Worst-state qualification propagation is not correct:

- federal-member states can be lost by jurisdiction-key mismatch;
- `RULE_DATA_INCOMPLETE` lacks an explicit severity;
- null state is admitted by the production-view helper for backward compatibility;
- no non-vacuous served test proves that every combined member contributes to the resulting worst state.

This is safety-critical because a fresh home-jurisdiction stack could be directly comparable and reach Recommended with a missing or weakened qualification state.

## 6. New York health

**Verdict: canonical data is correctly structured; served result is stale.**

Static canonical knowledge distinguishes the film credit, post-production credit, Upstate/scoring enhancements, and Production Plus as an uplift ceiling rather than a fake standalone program. Discovery is generic and the two NY programs are separate. The post credit is mutually exclusive with the production credit.

The actual FVD project response still exposes the film-credit ceiling as 50%, not the current canonical 60% Production Plus ceiling. This is an explained stale-cache failure, not a New York rule-modeling failure.

## 7. Ontario health

**Verdict: program discovery is present; combined served safety is defective.**

The actual FVD response contains separate CPTC, OPSTC, OFTTC, and OCASE singles. It also contains CPTC/OPSTC/OFTTC combinations and applies no reported stacking violations.

It does not contain the later OCASE combinations described by the closeout, and every served Canada/Ontario stack has null qualification. Static current code can generate the broader combination set, but the project API is serving an older snapshot and the fresh stack-state algorithm remains defective.

## 8. Contingency health

**Verdict: healthy mechanism; current served proof is stale.**

LU has a persisted, approved project fact:

`contingency_expected_utilization_pct = 100`, source `recovered_demo_state`.

The generic calculation applies contingency × expected utilization before jurisdiction-specific projected QPE. No Mauritius program-slug branch was found in that calculation. FVD has no such project election. Fingerprint tests show sensitivity to changes in the utilization value. Projected expected use and actual incurred/deployed treatment remain separate.

The generic project response's `contingency` presentation block is empty, but the LU baseline trace includes the 100% expected-deployed contingency amount and its persisted fact is present. The larger cache-generation defect still means the final snapshot has not been freshly regenerated.

## 9. Structuring intelligence health

**Verdict: `ENGINE_WIRING_DEFECT` due to stale served candidate state.**

The canonical opportunity bridge and specialized engines remain connected for treaty alternatives, national-treatment opportunities, non-party exceptions, contribution/qualification gaps, conditional funds, ATL headroom, reinvestment/deferred, and timing disclosures. Treaty opportunities remain unresolved opportunities rather than deterministic economics. No second recommender was found inside the project-scoped canonical evaluator.

Component/PDV recovery does not reach the actual project response: neither `ca_bc_dave` nor `au_pdv_offset` appears in LU or FVD, although both are current canonical programs and targeted tests resolve them through the canonical registry. This is the candidate/cache divergence, not missing static knowledge.

## 10. Ranking / Recommended safety

**Verdict: unsafe for combined structures.**

Actual LU and FVD each show zero Recommended rows, so no unsafe current winner was observed. Singles with unresolved qualification are correctly classified as alternatives/low-fit rather than Recommended, and conditional or unresolved co-production rows do not inflate NPC.

The absence of an observed winner is not sufficient acceptance. The combined-qualification defect can produce an admitted `NOT_APPLICABLE` state or null from unresolved members. Because the production-view admission helper accepts null and `NOT_APPLICABLE`, the safety invariant is not guaranteed for a comparable home-jurisdiction stack.

## 11. Candidate universe health

**Verdict: `ENGINE_WIRING_DEFECT`.**

Static discovery is generic across all registered doctrine records, and the targeted multi-program invariant passed. Aliases and superseded programs retain canonical handling.

The served candidate universe is not current:

- LU: 132 structures, while the final closeout reported 201 after canonical recoveries;
- FVD: 144 structures;
- both omit `ca_bc_dave` and `au_pdv_offset`;
- FVD's NY ceiling remains 50%;
- served Canada stacks retain no combined qualification state.

Candidate counts are diagnostics, not immutable targets. Here the content-level omissions and pre-change timestamps establish staleness independently of the count.

## 12. Canonical knowledge consolidation

**Verdict: canonical program knowledge is consolidated, but the served lineage is not singular.**

The main evaluator follows program → canonical rule → structured provenance and does not open validation artifacts. Current canonical discovery can reach registered programs generically.

The system still exposes legacy comparison/optimization paths and an LU-only live state path. More importantly, current canonical knowledge changes do not necessarily invalidate persisted project state. Therefore the canonical store can be correct while production users see an older truth.

## 13. Cache / stale results

**Verdict: `ENGINE_WIRING_DEFECT` (P0).**

Read-only database evidence:

| Project | Current-labeled rows | Row creation time (America/Los_Angeles) | Fingerprints | Served candidates |
|---|---:|---|---:|---:|
| The Little Utopia | 132 | 2026-08-20 12:11:59 | 1 | 132 |
| F#K Valentine's Day | 144 | 2026-08-20 12:11:31 | 1 | 144 |

`canonical-1.34.0` was introduced by commit `e67d4ce` at 2026-08-20 13:11:10, after those rows. Combined qualification propagation arrived in `b245f1b` at 15:49:39. BC DAVE/AU PDV arrived in `9d0266b` on 2026-08-21, and the final provenance policy arrived in `6b44973` on 2026-08-22. No engine-version bump followed those result-affecting changes.

`_compute_fingerprint()` includes project budget/territorial/contingency/personnel/script/co-production inputs and four registry constants. It omits material authority/economic-state, stacking, treaty, opportunity-pattern, spend-rule, executable-registry, and consolidation versions. The four included version constants also rely on manual bumps. `canonical_production_view` selects the first row matching the engine string and then all rows sharing that fingerprint; it does not compare the stored fingerprint to a fingerprint freshly computed from current canonical knowledge.

Consequently, stale rows masquerade as current.

## 14. LU / FVD actual served runtime

### The Little Utopia

- NPC: `$3,057,794.90`
- incentive: `$1,306,598.10`
- qualification: `AUTHORITY_UNRESOLVED`
- Recommended: `0`
- candidates/ranking rows: `132 / 132`
- contingency election: persisted `100%`, approved, source `recovered_demo_state`
- economics depend on provenance-only override: no direct override found; current registry policy permits deterministic economics independently of provenance
- runtime state: stale current-labeled snapshot; missing BC DAVE and AU PDV; combined Ontario qualification null

### F#K Valentine's Day

- NPC: `$3,072,027.16`
- incentive: `$1,445,659.84`
- qualification: `USER_FACT_REQUIRED`
- Recommended: `0`
- candidates/ranking rows: `144 / 144`
- contingency election: none
- economics depend on provenance-only override: no direct override found
- runtime state: stale current-labeled snapshot; missing BC DAVE/AU PDV, NY Production Plus, later Ontario stacks; all six combined structures have null qualification

## 15. Existing 35-item acceptance matrix

**Result: not 35/35.**

The repository does not retain an enumerated standalone copy of the original 35-item matrix. The authoritative retained evidence is the capability-ledger cross-reference, which explicitly says the matrix had not been walked item by item. To obey the instruction not to invent a replacement matrix, this audit does not fabricate labels for missing item numbers.

The retained numbering is sufficient to identify these failures:

- qualification group `#1-8`: single-state behavior has proof, but the required combined-structure propagation does not; actual stacks are null and fresh-code worst-state resolution is defective;
- `#16` component/PDV opportunity: current canonical records pass static tests, but actual LU/FVD served output omits both recovered programs;
- `#23-24` fingerprint sensitivity/current-generation GET: fail; stale pre-change rows are served as current;
- durability/genericity group `#25-35`: cannot be accepted item by item because current canonical knowledge does not reliably invalidate and reach served project state, and the original exact item labels are not retained.

All other retained group-level proofs were either unaffected or passed the targeted suite, but no exact verified numerator is asserted without the missing source checklist.

## 16. Test quality

Targeted result: **145 passed** across authority disposition, CBA-002 vocabulary, stacking, knowledge consolidation, multi-program discovery, fingerprinting, legacy isolation, no-runtime-web, structuring opportunities, contingency, and role qualification.

That green result is not an acceptance proof:

1. `test_point_table_role_is_point_bearing_not_mandatory` contains `any("fr_composer" in lever or True ...)`; any non-empty lever list passes regardless of composer behavior.
2. `test_registry_versions_are_present_in_the_payload` asserts only that constants and a hash are truthy. It neither proves fingerprint sensitivity to a version change nor covers the registries changed after the cached rows were written.
3. `test_cineglobe_unparameterized_endpoints_are_explicitly_demo_scoped` asserts that two function-name strings exist in one module. It does not prove a separate route namespace, consumer isolation, or absence of LU-only served state.
4. No test proves worst-state qualification propagation across every member of a pairwise/N-way stack. Existing stack tests exercise economics/interactions, not the qualification join used by Recommended.
5. Canonical-knowledge recovery tests call the registry/rate resolver directly. They do not prove that a current project GET invalidates old persisted rows and contains the recovered candidates.
6. No non-mutating acceptance test compares persisted row generation time/knowledge version with the current evaluator generation.

## Consolidated correction handoff

### OH-001 — P0 — stale canonical snapshots masquerade as current

Make the persisted evaluation generation identity change whenever any calculation-, qualification-, stacking-, structuring-, or provenance-policy input can change served output. Cover the complete canonical dependency set with one centrally owned generation/version manifest. In GET, do not accept an arbitrary row merely because its engine string matches; require a current generation/fingerprint match or return an explicit stale/not-evaluated state. Regenerate LU/FVD only after the invalidation contract is fixed.

Required proof: rows created before a knowledge/version change are rejected; a fresh evaluation exposes all current canonical candidates and current qualification traces; LU/FVD project GETs contain BC DAVE, AU PDV, the NY 60% conditional ceiling, and the current Ontario combination set; no pre-change fingerprint is served as current.

### OH-002 — P0 — combined qualification state can be lost/weakened

Key member qualification by canonical program identity, not the stack jurisdiction, and give every qualification state an explicit total severity/order. Null must mean only that no member has a qualification dimension; it must never erase an existing member state. Recommended admission must fail closed if a combined structure has any missing member-state trace.

Required proof: pairwise and N-way, order-invariant runtime tests cover every state; CPTC `USER_FACT_REQUIRED` + OPSTC `NOT_APPLICABLE` resolves `USER_FACT_REQUIRED`; OPSTC `NOT_APPLICABLE` + OFTTC `RULE_DATA_INCOMPLETE` resolves `RULE_DATA_INCOMPLETE`; a comparable home-jurisdiction stack with either state cannot enter Recommended.

### OH-003 — P1 — multiple production-capable engine lineages remain mounted

Retire the `0.1.0` structure calculation endpoint or route it through the canonical evaluator and canonical generation contract. Move LU-only routes under an explicit demo boundary/storage contract and remove production-screen dependence on them, or migrate those consumers to project-scoped canonical state. Keep stateless advisory tools explicitly advisory and unable to represent canonical economics.

Required proof: route inventory and HTTP integration tests show every production calculation endpoint uses the canonical engine; no route can persist a `0.1.0` result; no production/company screen receives LU economics without a project identity; legacy/demo calls cannot affect canonical project GET output.

### OH-004 — P1 — acceptance tests can pass without exercising the safety contract

Replace the vacuous/string-presence assertions and add served-runtime cache and combined-qualification tests. Each collection-based assertion must prove a non-zero inspected count. Tests must cross canonical data → persisted evaluation → project API rather than stop at registry metadata.

Required proof: each new guard fails against baseline `6b44973`, passes only after OH-001/OH-002/OH-003, and includes explicit negative controls for stale rows, omitted recovered candidates, state-loss in stacks, and unparameterized LU state.

## Final gate

`ONE_CONSOLIDATED_CORRECTION_PASS_REQUIRED`

This is one bounded backend correctness pass. It is not a new authority-research phase and does not require another worldwide audit.
