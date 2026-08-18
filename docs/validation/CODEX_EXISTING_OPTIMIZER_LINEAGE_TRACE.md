# CineGlobe Existing Optimizer / Stacker / Co-Production Lineage Trace

Date: 2026-08-17  
Branch: `claude/audit-frametax-features-NZcX5`  
Reviewed HEAD: `54a3140`  
Final gate: **CODEX_EXISTING_OPTIMIZER_LINEAGE_LOCALIZED**

## Executive finding

CineGlobe does not need a new optimizer designed from scratch. It has three surviving implementation lineages:

1. The current canonical project path, `canonical_evaluation.py`, which correctly discovers canonical program identities, derives canonical QPE, prices one program in one jurisdiction, persists results, and serves both Little Utopia (LU) and F*ck Valentine's Day (FVD) through the same project-state adapter.
2. The account-conserving allocation/pricing lineage, `production_allocation.py` plus `allocation_pricing.py`, which can split existing budget accounts/components among jurisdictions and sum independently priced jurisdiction segments. LU's older, non-project-scoped control endpoint still exercises component, split, conditional-fund, treaty-presence, in-kind, and richer recommendation surfaces from this lineage.
3. Two older combination lineages: the real program-combination/stack-adjustment chain (`generate_structure_scenarios.py` -> `run_full_analysis.py`) and the inventory optimizer under `app/optimization`. They prove combinatorics, compatibility, grant/fund, treaty, and ranking concepts existed, but neither is the current canonical served project optimizer. The former prices through superseded engine `0.1.0`; the latter uses a separate global inventory, hard-coded structure data, heuristic grant values, and estimated rates.

The first shared disconnect is exact: `canonical_evaluation.evaluate_project()` flattens discovery into independent `(jurisdiction_code, program_slug, classification)` candidates, and `_price_candidate()` constructs only a one-participant `single_country` or `full_relocation` `StructureSpec` with exactly one `incentive_programs` entry. It never invokes the surviving composer, stack enumerator, conditional-program attachment, treaty generator, or component candidate generator. Multiple programs are therefore **discovered and priced as separate alternatives**, not combined.

No code, data, frontend, or tests were changed or run for this trace. No external research was performed.

## Scope and runtime boundary

The project UI calls `GET /api/v1/cineglobe/projects/{project_id}/state` through `useCineGlobe(projectId)`. Since the current canonical-path repair, that route no longer title-special-cases LU: LU and FVD both read persisted `ProductionStructure` / `StructureCalculationResult` rows from `canonical_evaluation.py` through `canonical_production_view.py`.

The separate `GET /api/v1/cineglobe/structures` endpoint still calls LU's in-memory `get_state()` and `build_allocated_structures()`. It is useful forensic evidence and still a callable served control surface, but it is not the project-scoped canonical UI path. In the matrix below, “LU live” means the project-scoped path; “LU control” means this older endpoint.

## End-to-end current paths

### LU and FVD — current project-scoped path (`SAME_CANONICAL_PATH`)

`Project/BudgetDocument/BudgetLineItem/ProjectFact`  
-> `build_project_economic_inputs()`  
-> `derive_production_requirements()`  
-> two `discover_executable_jurisdictions()` passes (economics and feasibility kept separate)  
-> one flat candidate for each `(jurisdiction_code, program_slug)`  
-> `_price_candidate()`  
-> one-participant `StructureSpec`  
-> `derive_account_allocation()` (all eligible lines routed to that one candidate jurisdiction)  
-> `price_allocated_structure()`  
-> persisted `ProductionStructure` / `StructureCalculationResult`  
-> `canonical_production_view.build_production_and_structures()`  
-> `structures.allocated_structures`  
-> Overview / Workspace / Scenarios / Globe / Reports.

The adapter computes no economics. It deliberately serves generic empty values for conditional programs, compatibility, treaty, ownership, stacking notes, detailed allocation assignments, written recommendation, stack combinations, and treaty coverage. It preserves real program segments, QPE, incentive, NPC, feasibility, warnings, and priceability from persisted traces.

### LU — older forensic control path (`LEGACY_ONLY` for project routing)

`little_utopia_state.get_state()`  
-> opportunity discovery / graph / composer / recommendations  
-> `build_allocated_structures()`  
-> generated full-relocation, auto component-post, elected split, and registry-backed treaty specifications  
-> `derive_account_allocation()`  
-> one canonical partial register per jurisdiction segment in `price_allocated_structure()`  
-> travel / FX / local-cost / in-kind replacement normalization  
-> conditional fund attachment and compatibility  
-> `rank_allocated_structures()`  
-> `GET /cineglobe/structures`.

This state is rebuilt in memory and is not the canonical project persistence route. Mauritius currently has no registered treaty partner, so LU exercises the treaty candidate machinery as a proven-zero category rather than returning a priced treaty co-production.

## Capability matrix

| Capability | Historical | Current implementation | Canonical data | Consumed by current served project optimizer | LU consumes | FVD/generic consumes | Classification | Canonical modules / functions | First disconnect | Required reconnection | New code genuinely required |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Single-jurisdiction base | YES | YES | YES | YES | YES (live) | YES | `SAME_CANONICAL_PATH` | `canonical_evaluation.evaluate_project`, `_price_candidate`; `derive_account_allocation`; `price_allocated_structure` | None | None | NO |
| Multiple programs in one jurisdiction | YES | YES, but the executable stack path is old engine `0.1.0` | YES/PARTIAL; discovery now preserves program identity and multiple doctrine records | NO; each program becomes a separate structure | NO (live); metadata only in control | NO | `EXISTS_BUT_NOT_CONNECTED` | `generate_structure_scenarios.generate_structure_scenarios`; `allocation_pricing.enumerate_segment_program_stacks`; `apply_stacking_adjustments` | Flat candidate list and one-entry `StructureSpec.incentive_programs` | Group programs by segment, enumerate only evidenced combinations, and price them with the canonical segment kernel | YES — canonical stack-pricing adapter; no new combinatorics engine |
| Federal + provincial/state combination | YES | PARTIAL | PARTIAL; current program identities exist, but interaction rules contain old/variant slugs and gaps | NO | NO | NO | `ENGINE_EXISTS_DATA_NOT_CONSUMED` | `app/optimization/stacking_rules.py`; `LegalStackingRule` migrations; graph edges; `generate_structure_scenarios` | No combination candidate; live DB calculator also passes `stacking_rules=[]` | Canonicalize program identities, load existing exact rules, surface missing interactions as gated, then invoke canonical stack pricing | YES — identity/rule adapter and missing exact interaction publication; no new pair evaluator |
| Component / split allocation | YES | YES | YES for line items, categories, territorial rules; project routing elections only PARTIAL | PARTIAL: allocation function is called, but only for 100% one-jurisdiction structures | NO (live); YES (control) | NO | `PARTIALLY_CONNECTED` | `production_allocation.StructureSpec`, `derive_account_allocation`; `allocation_pricing.price_allocated_structure` | Canonical generator never creates `component_routes`, `account_routes`, or `account_splits` | Generate supported specs from canonical project inputs and persist the already-produced allocation trace | YES — candidate/input/persistence wiring only |
| Program compatibility / stackability | YES | YES/PARTIAL | PARTIAL; DB rules, static rules, graph edges, and aliases are not one canonical source | NO | NO (live); relationship/conditional checks YES (control) | NO | `EXISTS_BUT_NOT_CONNECTED` | `evaluate_legal_stacking`; `apply_stacking_adjustments`; `app.optimization.stacking_rules.evaluate_structure_stacking`; `structure_compatibility.evaluate_structure_compatibility` | No generic candidate reaches any compatibility engine; manual calculation route supplies empty rules | Resolve all rule records to canonical program IDs and pass exact rules to candidate evaluation | YES — one canonical rule-loading adapter |
| Grants / funds | YES | YES, split between current conditional nodes and legacy heuristic scoring | YES/PARTIAL | NO | NO (live); YES as unpriced conditional opportunities (control) | NO | `EXISTS_BUT_NOT_CONNECTED`; heuristic dollar estimator is `LEGACY_ONLY` | `conditional_programs`; `fund_economics_model`; `opportunity_discovery.discover_conditional_opportunities`; composer; compatibility | Generic adapter hard-codes `conditional_programs=[]`; canonical evaluator never attaches nodes | Attach conditional nodes/compatibility to canonical structures; price only authority-backed deterministic awards | YES — attachment/persistence adapter. Do **not** reconnect `score_structures._estimate_grant_value` |
| Official treaty co-production | YES | PARTIAL | PARTIAL; bilateral/multilateral registry and membership data exist, but not a proven complete treaty universe | NO | NO (live); machinery YES/proven-zero for MU (control) | NO | `PARTIALLY_CONNECTED` / `EXISTS_BUT_NOT_CONNECTED` | `treaty_engine`; composer `_treaty_compositions`; LU treaty auto-enumeration; `allocation_pricing._treaty_requirements` | Generic candidate generator emits no multi-party spec and persists `treaty_slug=None` | Generate only registry-supported treaty specs, collect participation/cultural facts, then use canonical segment pricing | YES — generic generator/input adapter and fuller eligibility binding; no new treaty registry design |
| Cultural / co-production qualification and uplift | YES/PARTIAL | PARTIAL | PARTIAL | PARTIAL for ordinary program rate floors/conditional ceilings; NO for generic treaty cultural qualification | NO (live); recommendation/test machinery YES (control) | PARTIAL base-rate conditions only | `PARTIALLY_CONNECTED` | `program_rate_rules`; `resolve_program_rate`; `evaluate_qualification_tests`; production recommendation cultural mapping; treaty flags | Generic project path has no cultural-test result/role-to-test input and treaty candidates do not exist | Bind existing project people/facts to applicable program/treaty tests; unresolved tests gate ceiling/national status, not base economic visibility | YES — generic fact/test adapter |
| Hybrid / anchor | YES | YES | YES/PARTIAL | NO | NO (live); YES for anchor-component control candidates | NO | `EXISTS_BUT_NOT_CONNECTED` | `StructureSpec` types; LU `ALLOC-COMPONENT-POST-*`; `production_structure_composer`; `price_allocated_structure` | Generic candidate generator only creates single/full relocation | Emit existing `component_relocation` / supported `hybrid` specs from canonical components and facts | YES — candidate generator wiring |
| In-kind / support | YES | YES | LU YES; generic project input NO | NO; canonical evaluator passes `inkind_replacement_delta_usd=0.0` | NO (live); YES (control) | NO | `LEGACY_ONLY` for LU input, engine reusable | `inkind_contribution`; LU `build_inkind_model`; `price_allocated_structure` normalization input | No generic persisted in-kind contribution/replacement-cost input | Add a canonical project input and thread it to existing normalization; never add FMV to cash QPE by default | YES — generic input/persistence adapter |
| Reinvestment | YES/PARTIAL | YES as trace/opportunity/recommendation and evidence state | PARTIAL | NO | NO (live); opportunity/recommendation trace YES (control) | NO | `INTENTIONALLY_DEFERRED` | `qualification_model.get_reinvestment_profile`; `discover_reinvestment_opportunities`; recommendation engine; graph | Generic evaluation does not build opportunity collection | Keep deferred; preserve data and evidence tasks only | NO for this phase; economic reconnection intentionally not recommended |
| Scenario generation | YES | YES across three lineages | YES/PARTIAL | PARTIAL; base + independent relocations only | YES (live, same narrow set); richer control YES | YES, narrow set | `PARTIALLY_CONNECTED` | canonical candidate loop; composer; LU builder; `generate_structure_scenarios`; `app.optimization.structure_generator` | Canonical loop does not call richer generators | Reuse canonical discovery as universe and existing allocation/treaty/conditional primitives; exclude hard-coded estimate generator from economics | YES — orchestration adapter |
| Ranking / recommendation | YES | YES | YES/PARTIAL | PARTIAL; canonical adapter ranks only directly comparable candidates and serves `recommendation=None` | YES narrow ranking (live); rich recommendation/control ranking YES | YES narrow ranking; NO written recommendation | `PARTIALLY_CONNECTED` | `rank_allocated_structures`; `build_structure_recommendation`; global ranker; `canonical_production_view` | Rich pricing/recommendation objects are not persisted; generic adapter reconstructs empty fields | Persist rich canonical pricing metadata and run the existing ranker after normalization/comparability | YES — persistence/adapter wiring |
| Feasibility separate from economics | YES | YES | YES/PARTIAL | YES | YES | YES | `EXISTS_AND_CONNECTED` | two-pass discovery in `canonical_evaluation`; `feasibility_status/reasons`; comparability fields | None for separation; capability data breadth remains partial | Keep as-is and use feasibility only for rank/category/warnings | NO |
| Intended scenario categorization | PARTIAL | PARTIAL | YES — rank, priceability, comparability, treaty, feasibility, blockers all exist | PARTIAL; current UI has structural badges and Recommended/Alternative/Unlockable/Additional tiers, not the requested five categories | PARTIAL | PARTIAL | `PARTIALLY_CONNECTED` | `productionOptions.classifyStructure`; `globeData.structureTier`; ranking entries | No single canonical category field maps the existing signals | Deterministic mapping: rank 1 -> Recommended; other comparable -> Alternative; treaty -> Co-pro; priced + low fit/review -> Priced/Low Fit; unpriced -> Not Available | YES — thin category adapter only |

## Real stacker finding

### Yes, a real stacker exists

`generate_structure_scenarios()` enumerates single-, two-, and three-program combinations. For each combination it filters relevant `LegalStackingRule` records, calls `run_full_analysis()`, applies legal evaluation plus spend-reduction/value-cap/mutual-exclusion adjustments, and ranks results. `allocation_pricing.enumerate_segment_program_stacks()` delegates to it.

It is not safe to connect unchanged to canonical served economics: its pricing dependency is `run_full_analysis` engine `0.1.0`, which `canonical_evaluation.py` expressly superseded after it diverged from the accepted canonical QPE/NPC path. The reusable parts are the combination enumeration, legal rule evaluation, and adjustment semantics. A small canonical adapter must price each candidate through current segment qualification/rate rules rather than restoring the superseded economics path.

A second stack evaluator exists in `app/optimization/stacking_rules.py`. It holds a large static pair table and structural fallbacks over `GlobalProgramEntry`. It is used by `app.optimization.optimizer`, not by the project-state optimizer. That optimizer also applies generalized qualifying-spend percentages and confidence/friction heuristics, so it is evidence of surviving capability, not a canonical economics source.

The manual `POST /projects/{id}/structures/{sid}/calculate` route is also not a live stack connection: it loads multiple claimed programs but passes `stacking_rules=[]` and `qualification_tests_with_rules=[]`, both marked TODO.

## North America

### Canada

Canonical discovery can now examine multiple Canada program identities independently, including federal PSTC/CPTC records, provincial service credits, Ontario domestic/service/animation records, and the broader recovered provincial set. This proves **A: multiple programs discovered** and **B: multiple programs evaluated as separate alternatives**. It does not prove **C: combined structure**; the canonical loop never creates one.

Existing exact interaction logic is uneven but real:

- The static stack table directly contains `ca_bc_pstc + ca_federal_cptc` (mutual-exclusion treatment) and `on_ofttc + ca_federal_cptc` (government-assistance/spend-reduction treatment).
- Existing migrations also contain CPTC interactions for Ontario OPSTC, OCASE, BC, Quebec, NOHFC, CMF, Telefilm, and other provincial/fund programs.
- The current canonical slugs `ca_federal_pstc` and `ca_qc_pstc` are not exact keys in the static pair table. Ontario also spans `ca_on_opstc` versus legacy `on_opstc` spellings. Therefore the current foreign-service federal/provincial set is **not** ready for blanket combination merely because both programs are visible.
- `ca_federal_cptc`, `ca_bc_pstc`, and `on_ofttc` are the newly reachable identities with direct pair-rule coverage already present. `ca_on_opstc` has migration coverage but needs canonical rule loading/alias reconciliation. All other current pairs must remain gated until an exact rule is bound; the stacker's default-allowed fallback is not sufficient proof of legal/economic compatibility.

### United States

There is no federal film incentive combination in the modeled US set. State programs are currently separate jurisdiction candidates. New York production and post-production programs can both be discovered, and the canonical rate doctrine records their distinct scopes, but the served path does not combine them. The static stacker has a generic same-jurisdiction-primary mutual-exclusion fallback, not an exact current New York production/post pair. Recovered labor, payroll, regional, or uplift treatments are mostly rate/category conditions inside a state program, not automatically separate stackable program claims.

Therefore the North American blocker is two-stage: candidate composition is absent first; exact canonical rule identity/coverage is incomplete second. Program visibility alone must not be reported as stacking.

## Component, hybrid, and combined economics

`StructureSpec` already supports `component_relocation`, `split_production`, `treaty_coproduction`, `majority_minority`, `multi_party`, `service_production`, and `hybrid`, with participant programs, component routes, account routes, explicit per-account splits, ownership shares, and a treaty slug.

`derive_account_allocation()` allocates every existing budget line exactly once, validates conservation, respects fixed/stated locations, and supports explicit splits. `price_allocated_structure()` builds a separate qualification register for each jurisdiction's allocated segment, resolves that program's rate on that segment's QPE, sums incentives, and applies travel/FX/in-kind/local-cost/financing/implementation adjustments once at structure level.

That is the requested budget-line/component allocation -> jurisdiction QPE -> multiple incentives -> combined NPC capability. It is connected generically only in degenerate form: the canonical evaluator gives it a one-jurisdiction spec, so all accounts flow to one segment. LU's control builder proves the richer component and split routes work with real line items.

## Treaty and co-production lineage

`treaty_engine.py` contains bilateral and multilateral registries, membership lists, contribution thresholds, cultural-test flags, majority/minority unlock slugs, fund unlocks, and eligibility result types. The composer attaches only registered instruments and emits treaty-absence constraints. LU's control builder auto-enumerates registered treaty partners and uses `price_allocated_structure()` to block unsupported official status.

The executable co-production chain is still partial:

- Generic canonical generation creates no co-production candidate.
- `allocation_pricing._treaty_requirements()` checks registry coverage and ownership/spend consistency, but it does not execute the full `evaluate_bilateral_eligibility()` / multilateral threshold/cultural result path.
- The older `app.optimization.structure_generator` has hard-coded treaty maps, rates, allocation percentages, and a 15% treaty bonus. It must remain legacy evidence, not be restored as canonical economics.
- The composer historically priced only the register-backed jurisdiction and reported the remainder as unknown; it is not itself a complete multi-register calculator.

Thus treaty data, generation concepts, and segment pricing exist, but a canonical project input/eligibility adapter is genuinely missing.

## Grants and funds lineage

The current, defensible conditional-funding implementation is `conditional_programs.py`: it attaches national/subnational programs by participant and only attaches supranational funds when a modeled membership registry proves access. It carries documented caps without estimating awards, marks stacking unknown absent evidence, and never includes a discretionary award in NPC. `structure_compatibility.py` evaluates whether an attached node is pursuable/gated/scope-mismatched. LU's control path exposes these and uses pursuable count only as an NPC tie-break.

`fund_economics_model.py` supplies substantial classification, repayment, recoupment, equity, matching, territorial, maximum-award, competition, stackability, and government-assistance metadata. It does not provide production-specific award probability or entitlement.

The older `app.optimization.score_structures._estimate_grant_value()` estimates competitive grants as `min(25% of annual cap, 8% of budget)` and other grants as `min(40% of annual cap, 12% of budget)`, then includes those estimates in scored benefit. That is a legacy heuristic and conflicts with the later canonical conditional-opportunity doctrine. It must not be reconnected.

No surviving canonical engine computes a researched probability distribution/range for selective awards. The correct existing behavior is conditional opportunity with zero guaranteed NPC until award/amount/stacking are evidenced.

## Feasibility, ranking, and categories

The current canonical path correctly separates economic priceability from production feasibility. It performs a real-requirements discovery pass for `feasibility_status/reasons` and an empty-requirements pass for economic candidacy. A weak physical match can remain priced; only authority/rate/threshold failure removes priceability.

`rank_allocated_structures()` ranks fully priced, normalized structures by lowest defensible NPC, uses pursuable conditional opportunities only as a tie-break, and lists blocked structures unranked. The generic adapter goes further: because generic relocation travel/in-kind/local-cost normalization is missing, only the base is directly comparable and other priced structures are displayed under review without a numeric rank. This is an intentional comparability gate, not lost economics.

The signals needed for the requested categories already exist:

- `RECOMMENDED`: numeric rank 1.
- `ALTERNATIVE`: fully priced and directly comparable, not rank 1.
- `CO-PRO OPPORTUNITIES`: explicit `treaty_slug`, with eligibility/blocker status preserved.
- `PRICED / LOW FIT`: fully priced but feasibility weak or not directly comparable; retain its own NPC.
- `NOT AVAILABLE`: genuinely unpriced/capability-only/rule-rejected, with exact blockers.

The current UI instead combines structural badges (Current/Base, Full Relocation, Hybrid/Component, Official Treaty) with Recommended/Alternative/Unlockable/Additional tiers and a comparable/review split. A thin canonical category field is absent; the underlying signals are not.

## Persistence and serving disconnect

`ProductionStructure` already has JSON fields for jurisdiction allocations, claimed program IDs, spend percentages, talent arrangements, official co-production and treaty; `StructureCalculationResult` already has program results, test scores, stacking violations, warnings, optimization opportunities, and a full calculation trace.

The current canonical evaluator writes `claimed_program_ids=[]`, a single 100% jurisdiction allocation, and only the single-program trace. `canonical_production_view` then deliberately supplies empty rich fields. The persistence schema is broad enough for most reconnection metadata, but the current writer/adapter must be extended; the older LU structures are in memory and cannot simply become project IDs without persistence.

## Special questions — direct answers

1. **Is there already a real stacker?** YES. Combination enumeration, legal evaluation, economic adjustments, and ranking exist. Its current pricing orchestrator is superseded, so a canonical pricing adapter is required.
2. **Is there already federal + provincial/state combination logic?** YES/PARTIAL. Canada pair rules and fund/assistance interactions exist; exact current-slug coverage is incomplete and none is called by the served project optimizer. No US federal film program exists to combine.
3. **Is there already component allocation?** YES. It is account-conserving, segment-specific, and multi-register capable. Generic candidate generation does not feed it routes/splits.
4. **Is there already official treaty co-production generation?** YES/PARTIAL. Registry-backed composition and LU auto-enumeration exist; complete generic fact/eligibility execution and persistence do not.
5. **Is there already grant/fund integration?** YES/PARTIAL. Conditional attachment, compatibility, fund economics, and legacy scoring exist. Only conditional zero-guaranteed-value treatment is suitable for canonical reconnection.
6. **Is there already hybrid/anchor generation?** YES. LU auto-generates anchor-component post/VFX/music structures; `StructureSpec` and pricing support them. Generic generation does not.
7. **What is LU exposing that generic projects are not?** On the older control endpoint: automatic component routes, elected splits, treaty-category/proven-zero reporting, detailed account allocations, travel/FX/local-cost/in-kind normalization, conditional funds and compatibility, structure recommendations, conditional tie-breaking, opportunity composition, and cultural/person recommendations. The current project-scoped LU path exposes none of those special routes; it intentionally uses the same canonical path as FVD.
8. **Which recovered North American programs already match existing stack rules?** Direct static coverage exists for `ca_federal_cptc` with `ca_bc_pstc` and `on_ofttc`; migrations additionally cover `ca_on_opstc`, OCASE, Quebec, CMF, NOHFC, Telefilm and other provincial/fund interactions. Current `ca_federal_pstc`, `ca_qc_pstc`, and current US same-state pairs need exact current-identity rule binding; they cannot be declared compatible from default behavior.
9. **What is the first shared disconnect?** `canonical_evaluation.evaluate_project()` after discovery: it flattens program identities into independent candidates and `_price_candidate()` builds only one-program, one-participant specs. No richer candidate reaches any stacker/composer.
10. **What is the minimum ordered reconnection sequence?** Below.

## Minimum ordered reconnection sequence

1. Keep `canonical_evaluation` as the single served orchestrator and current QPE/NPC kernel. Add a candidate-input adapter that preserves discovery's full `(jurisdiction, canonical_program_id)` universe and groups programs without removing the existing single-program candidates.
2. Resolve existing `LegalStackingRule`, graph, migration/static rule identities onto canonical program IDs. Exact known rules may combine; unknown/mismatched pairs remain gated. Do not use default allowance as authority.
3. Generate supported component/split/anchor/treaty specs from existing project budget lines and persisted facts using the existing `StructureSpec` vocabulary. Do not fabricate account percentages, ownership, cultural results, or treaty status.
4. Reuse `generate_structure_scenarios` combinatorics and stacking-adjustment semantics through a new adapter that prices each program/segment with current canonical qualification/rate/allocation logic. Do not restore `run_full_analysis` `0.1.0` or the hard-coded `app.optimization.structure_generator` economics.
5. Attach `conditional_programs` and `structure_compatibility` to each canonical structure. Keep discretionary/editorial awards at zero guaranteed NPC; exclude the legacy grant estimator.
6. Execute applicable existing treaty contribution/cultural checks and carry unresolved facts as gates; then price each jurisdiction's own allocated spend with `price_allocated_structure()`.
7. Persist participants, claimed canonical program IDs, account allocation, segment traces, treaty/ownership, stack adjustments, compatibility, recommendations, and comparability in existing structure/result JSON fields; teach `canonical_production_view` to pass them through instead of emitting empty values.
8. Rank with existing defensible-NPC/comparability/feasibility rules and publish one deterministic scenario category from existing signals. Add generic relocation/in-kind inputs only when real project data exists. Keep reinvestment deferred.

## New build proven necessary

Only these integration pieces are absent:

- A canonical rich-candidate orchestration adapter after discovery.
- A canonical multi-program stack-pricing bridge; the existing enumerator currently calls superseded economics.
- One canonical rule/slug loading adapter across existing DB/static/graph interaction data.
- Generic project fact adapters for explicit component splits/routes, treaty shares/cultural results, relocation normalization, and in-kind replacement cost.
- Persistence/pass-through of rich allocation, stack, treaty, conditional-fund, recommendation, and category fields.
- A thin canonical scenario-category mapper.

No new allocation engine, stack combinator, treaty registry design, conditional-fund model, ranking engine, or optimizer-from-scratch is justified by the repository evidence.

## Final gate

**CODEX_EXISTING_OPTIMIZER_LINEAGE_LOCALIZED**
