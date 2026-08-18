# CineGlobe Existing Optimizer Engine Correctness Audit

Date: 2026-08-18

Branch: `claude/audit-frametax-features-NZcX5`

Audited baseline: `86f1547f0f3e5cd454a49d0b79334114fbcb6e60` plus the accepted worldwide base-program closeout

Mode: read-only forensic code audit; no external research; no program-data re-audit

Final gate: **CODEX_EXISTING_OPTIMIZER_ENGINE_CORRECTNESS_CLASSIFIED**

## Executive decision

Claude's current reconnection must **ALTER COURSE** before runtime acceptance.

The account-conserving allocation and canonical segment-pricing path is reusable. The conditional-fund model, normalized-NPC ranker, and unknown-as-gated compatibility model are also sound within their stated contracts. The old scenario stacker, the Phase E inventory optimizer, and the hard-coded structure generator are not safe economic engines.

Commit `86f1547` adds an important fail-closed boundary for an entirely unknown pair, but the generated pair is still persisted as `PRICED` when the named rule is mutually exclusive, conditional, or an unexecuted spend reduction. A warning is not a valid substitute for a defensible adjusted value. The observed unpublished N-way expansion must not be accepted merely because every pair has a named row: pair coverage does not make sequential pairwise arithmetic order-independent or prove a lawful N-way result.

The minimum safe course is to retain canonical per-program pricing, retain single-program candidates, and gate every combined result unless an exact canonical interaction rule both resolves and executes. Mutually exclusive pairs remain separate alternatives. Conditional and non-executable reductions remain unpriced combinations. N-way runtime publication remains gated until adjustment direction, bases, caps, and ordering are explicit.

## Settled correctness boundary

A rich structure may enter numeric recommendation ranking only when all of the following are true:

1. Every claimed program has one canonical identity and independently resolved canonical QPE/rate economics.
2. Every pair in a multi-program claim has explicit current rule coverage; absence is `UNKNOWN`, never `ALLOWED`.
3. Every applicable adjustment actually executes against a named source, target, base, and structured parameter. A disclosure-only adjustment is not priced.
4. Mutual exclusion and prohibition remove the combined claim; they do not create a two-program structure with one value zeroed.
5. Account allocation is conserving and based on a real structure election or fact. Entity domicile alone does not establish where services were performed or goods used.
6. Treaty/co-production status passes the applicable instrument's complete ownership/contribution, cultural/national-status, partner, and program-unlock gates.
7. Selective funding has zero guaranteed NPC value until an award and compatible amount are evidenced.
8. NPC is on a common, normalized cost basis. Feasibility and comparability remain separate from economic priceability.

## Material correctness findings

| ID | Classification | File / function | Exact behavior | Risk | Smallest correction | Reconnection course |
|---|---|---|---|---|---|---|
| S-01 | `SAFE` | `backend/app/calculators/canonical_stack_bridge.py::load_named_pair_rule` at `86f1547` | An entirely unmapped exact slug pair returns `None`; the legacy default-allowed fallback is not called. | Correctly prevents unknown visibility from becoming permission in this bridge. | Retain this fail-closed boundary and apply it to every canonical combination path. | Proceed with this boundary unchanged. |
| S-02 | `UNSAFE_DEFAULT` | `backend/app/calculators/generate_structure_scenarios.py::generate_structure_scenarios`, `_run_combo` | Enumerates every 1..N combination. It filters the rules supplied for a combination but never requires complete pair coverage. Absence of a rule is treated as no restriction. | Unknown compatibility is silently equivalent to allowed; N-way combinations may have uncovered pairs. | Before pricing, require an explicit resolved rule for every pair; otherwise emit a gated/unpriced candidate or do not generate the combination. | Alter; do not reconnect this entry point unchanged. |
| S-03 | `BUG` | `backend/app/calculators/generate_structure_scenarios.py::_run_combo`, `_rank`; `backend/app/calculators/apply_stacking_adjustments.py::apply_stacking_adjustments` | `prohibited` has no numeric adjustment. The scenario retains the full combined incentive, is merely flagged, and remains eligible for composite ranking. | An illegal claim can appear economically superior and be recommended. | Exclude prohibited combinations from priced/ranked output; preserve them only as rejected candidates with reasons. | Alter before any runtime use. |
| S-04 | `BUG` | `backend/app/calculators/apply_stacking_adjustments.py::_apply_mutually_exclusive`; `evaluate_legal_stacking.py::evaluate_legal_stacking`; `canonical_stack_bridge.py::price_program_pair_stack`; `canonical_evaluation.py::evaluate_project` | Mutual exclusion zeroes the lower value rather than rejecting the combined claim. The legal evaluator does not classify `mutually_exclusive` as a violation. Commit `86f1547` then persists both claimed slugs as a `PRICED` combined structure; `legal_review_required` can remain false. | A non-stack is represented as a lawful stack and duplicates an existing single-program alternative under a false two-program identity. | Do not generate a combined structure for mutual exclusion. Return a rejected/gated combination and retain the already-existing single-program candidates. Treat mutual exclusion as a blocking legal decision. | Alter immediately. |
| S-05 | `BUG` | `backend/app/calculators/apply_stacking_adjustments.py::_apply_spend_reduction`; `canonical_stack_bridge.py::price_program_pair_stack`; `canonical_evaluation.py::evaluate_project` | Reduction direction is inferred only when one side has type `grant`, `regional_fund`, or `discretionary_fund`. It omits current types such as `direct_grant`, `development_fund`, and `co_production_fund`, and cannot represent tax-credit-as-government-assistance reductions. Commit `86f1547` discloses the failure but persists the unreduced sum as `PRICED`. | Overstates incentive and understates NPC while presenting a non-executed statutory interaction as priced. | Make source program, target program, affected base, and reduction amount/rate explicit in the rule contract. Until then, a non-executed reduction must be unpriced and excluded from recommendation. | Alter immediately. |
| S-06 | `BUG` | `backend/app/calculators/apply_stacking_adjustments.py::_apply_value_cap`; `backend/app/models/incentive.py::LegalStackingRule` | The calculator parses a numeric cap from free-text `condition_text`; the rule model has no structured cap amount, currency, percentage/base, or allocation method. No surviving static `value_cap` binding was found. Parse failure leaves raw values in place with only a review flag. | Cap math is effectively unbindable and can fail open. | Add a structured, evidenced cap parameter/basis before enabling this rule type; parse failure must block pricing. | Alter; value-cap combinations remain gated. |
| S-07 | `BUG` | `backend/app/calculators/apply_stacking_adjustments.py::apply_stacking_adjustments`, `_apply_spend_reduction`, `_apply_value_cap`, `_apply_mutually_exclusive` | Rules mutate `program_values` sequentially in caller order, while spend reduction continues to read raw award/QPE inputs. There is no dependency graph or precedence for mixed reductions, caps, and exclusions. | N-way results can vary by rule order, reduce an already excluded program, or reduce the same base repeatedly. Pairwise coverage alone does not solve this. | Keep N-way unpriced until a deterministic adjustment plan names dependencies and cumulative bases. For safe pairs, execute one fully specified interaction only. | Alter; do not publish the current N-way draft. |
| S-08 | `UNSAFE_DEFAULT` | `backend/app/calculators/evaluate_legal_stacking.py::evaluate_legal_stacking` | It evaluates only supplied rows. Missing pair coverage produces no decision and `legal_review_required=False`; confidence tier is carried but never affects eligibility. | Any caller that does not independently prove rule completeness treats unknown as clean. | Return explicit `UNKNOWN` decisions for uncovered claimed pairs, or require a completeness manifest from the caller. Non-verified rules cannot authorize a priced stack. | Alter API contract before general reuse. |
| S-09 | `BUG` | `backend/app/calculators/generate_structure_scenarios.py::_rank` | The docstring promises lexicographic NPC/value/flags ordering, but code ranks ordinal positions using weights 0.50/0.30/0.20. Illegal/review scenarios remain in the same ranking. | Ranking can select a higher-NPC scenario and can reward legally unusable combinations. | Remove illegal/unresolved candidates first; rank comparable priced structures by normalized NPC, with only deterministic non-dollar tie-breaks. | Alter; use the canonical ranker instead. |
| S-10 | `STALE_ASSUMPTION` | `backend/app/calculators/generate_structure_scenarios.py::_run_combo`; `backend/app/calculators/allocation_pricing.py::enumerate_segment_program_stacks` | Delegates economics to `run_full_analysis` engine `0.1.0`, the superseded QPE/NPC path. | Reintroduces arithmetic already rejected by the canonical pipeline. | Reuse only combinatorics after the fail-closed corrections; price through canonical segment qualification/rate/allocation. | Alter. |
| S-11 | `IDENTITY_GAP` | `generate_structure_scenarios.py::_run_combo`; `evaluate_legal_stacking.py`; `apply_stacking_adjustments.py` | Scenario labels use slugs, but rule filtering uses `program.id`; rule callers may supply DB UUIDs or slugs. The calculators compare opaque strings without canonicalization. | Valid rules can silently miss; unrelated aliases can create duplicate identities. | Canonicalize every claimed program and rule endpoint once, then preserve canonical ID plus source DB UUID as provenance. | Alter through an identity adapter. |
| S-12 | `IDENTITY_GAP` | `backend/app/optimization/stacking_rules.py::infer_slug`, `evaluate_pair`; `_NAME_SLUG_RULES` | Compatibility depends on display-name fragments and legacy slugs. First fragment match wins. Current aliases such as `ca_on_opstc`/`on_opstc` and `ca_qc_pstc`/`qc_film_production` span registries. | Name changes and overlapping fragments can select the wrong or no rule. | Do not infer runtime identity from display names. Resolve `canonical_program_id` through `canonical_program_identity` and use names only for display. | Alter. |
| S-13 | `MISSING_EXISTING_RULE_BINDING` | `backend/app/calculators/canonical_stack_bridge.py::load_named_pair_rule`; `backend/app/api/v1/structures.py::calculate_structure_impl` | The bridge reads a static private table, labels every matched row `VERIFIED`, sets `statutory_reference=None`, and does not load `LegalStackingRule` DB rows/source documents. The manual calculate route still passes `stacking_rules=[]`. | Static/migration presence is mistaken for current verified authority, while DB rules are disconnected. | One loader must resolve canonical IDs to exact existing rule rows, source/confidence, direction, and parameters. Unknown or source-less authorization stays gated. | Alter. |
| S-14 | `UNSAFE_DEFAULT` | `backend/app/optimization/stacking_rules.py::evaluate_pair`, `_is_government_assistance_in_jurisdiction` | Unknown pairs return `None` meaning allowed. Same-jurisdiction primary programs are presumed mutually exclusive, and any CA/AU grant-type program can be presumed government assistance by country/type. | Industry/generalized assumptions replace program-specific authority in both directions. | Restrict to exact canonical evidenced rules; return `UNKNOWN` otherwise. | Do not reconnect this fallback. |
| S-15 | `SAFE` | `backend/app/calculators/production_allocation.py::derive_account_allocation`; `backend/app/calculators/allocation_pricing.py::price_allocated_structure` | Uses actual budget lines, requires explicit splits to sum to 100%, prevents duplicate whole-account allocation, verifies conservation, derives an independent register per jurisdiction segment, and applies structure-level adjustments once. | Correctly prevents whole-budget reuse and ordinary split double counting. | Retain conservation and partial-register contracts unchanged. | Proceed with these contracts. |
| S-16 | `UNSAFE_DEFAULT` | `backend/app/calculators/production_allocation.py::component_for`, `derive_account_allocation` default branch | Unmapped categories become principal photography. Movable work, ATL, overhead, and administration default to the primary jurisdiction; rationale says overhead/administration follow entity domicile. `RECOMMENDED` assignments do not block full pricing. | Can invent service location/vendor/residency and qualify spend from SPV domicile alone, contrary to the settled territoriality boundary. | Location-bound shoot lines may follow an explicitly proposed shoot. All other lines require a real route/fact or remain conditional/non-incentive until evidenced; unknown categories cannot default to principal photography. | Alter before generic component/split reconnection. |
| S-17 | `PROVEN_ABSENT` | `backend/app/calculators/production_allocation.py::StructureSpec` | `incentive_programs` is `dict[jurisdiction, one slug]`. It cannot represent multiple claims in one segment, anchor program vs stacked programs, or per-claim interaction provenance. | Rich stacks must bypass the conserving allocator, flatten semantics, or lose rule trace. | Extend the spec with typed per-segment program claims and explicit anchor/stack roles; preserve the existing single-program form as a compatibility adapter. | New bounded data-contract capability required. |
| S-18 | `SAFE` | `backend/app/calculators/conditional_programs.py`; `backend/app/calculators/structure_compatibility.py` | Selective/editorial programs are conditional nodes, carry caps only as metadata, keep stacking unknown without evidence, and always have `enters_npc=False`. | Correctly avoids guaranteed-value contamination. | Reconnect as metadata/gates only; persist the existing verdict and gate trace. | Proceed with adapter wiring. |
| S-19 | `BUG` | `backend/app/optimization/score_structures.py::_estimate_grant_value`, `score_structure`; `run_full_analysis` fixed/competitive grant path | Estimates grant awards from annual program caps and budget percentages, then includes them in producer benefit. The old full-analysis fixtures also treat competitive fixed face amounts as economic value. | Selective face value becomes deterministic NPC reduction. | Exclude these estimators. Only an evidenced awarded amount may enter economics; otherwise attach the conditional node at zero. | Do not reconnect. |
| S-20 | `STALE_ASSUMPTION` | `backend/app/optimization/enumerate_structures.py::enumerate_structures`; `backend/app/optimization/score_structures.py::score_structure`; `backend/app/optimization/structure_generator.py::_estimate_soft_money`, `generate_structures` | Uses global inventory types, a generic 65% QPE share, highest-rate program selection, approximate 50/50 splits, hard-coded jurisdiction rates, 40/60 allocation, 15% treaty bonus, and estimated grant values. | Produces plausible-looking but non-canonical economics and treaty uplift. | Preserve only non-economic vocabulary if useful; no value, rank, split, or eligibility result may reach canonical runtime. | Do not reconnect. |
| S-21 | `BUG` | `backend/app/calculators/treaty_engine.py::evaluate_bilateral_eligibility` | Missing required cultural-test input is only a warning, so `is_eligible` may be true. Contribution percentages need not sum to 100. Unlock lists are returned in the same order regardless of which signatory is actually majority. | Can grant official status and the wrong national-program unlocks to an unresolved or reversed structure. | Missing required tests and invalid totals must be unresolved/blocking. Map unlocks by signatory identity, not the misleading majority/minority field names. | Alter before reuse. |
| S-22 | `BUG` | `treaty_engine.py::evaluate_eurimages_eligibility`, `evaluate_ibermedia_eligibility`, `evaluate_european_convention_eligibility` | Cultural character is warned but never evaluated. Eurimages percentage-total mismatch is only a warning; Ibermedia/Convention do not validate totals. Duplicate country inputs are not rejected and can inflate participant count. | A malformed or culturally unresolved composition can be marked eligible and unlock a fund. | Validate unique participants and 100% contributions; require an explicit cultural/national-status result where the instrument requires it. Unknown remains unresolved. | Alter. |
| S-23 | `BUG` | `backend/app/calculators/allocation_pricing.py::_treaty_requirements` | Checks registry presence and a generic majority-share/spend heuristic, but never calls the full treaty eligibility evaluators. It ignores the claimed `treaty_slug`, uses the last matched pair as the result, requires pairwise bilateral/convention coverage for multi-party structures, and treats every `hybrid` as treaty-dependent. | A registry hit can substitute for certification; the wrong instrument can be assigned; non-treaty hybrids can be blocked; valid multilateral structures can be rejected. | Dispatch by explicit structure semantics and exact claimed instrument; bind project facts into the corrected bilateral/multilateral evaluator; carry unresolved status as blockers. | Alter immediately before co-pro reconnection. |
| S-24 | `ADAPTER_REQUIRED` | `backend/app/calculators/production_structure_composer.py::_treaty_compositions`, `_build_candidate` | Attaches only registered instruments and honestly prices only the one register-backed segment. It is composition/opportunity evidence, not complete treaty eligibility or multi-register economics. | Unsafe only if its attached treaty is promoted to `eligible` or its partial economics to a complete NPC. | Use it for candidate discovery; pass the candidate through corrected eligibility, account allocation, and multi-register pricing before recommendation. | Proceed only through adapters. |
| S-25 | `BUG` | `production_allocation.py::StructureSpec`; `allocation_pricing.py::_treaty_requirements`, `build_structure_recommendation` | `primary_jurisdiction` provides an anchor jurisdiction, but there is no anchor-program/stacked-program/co-pro-role model. `hybrid` is a catch-all and is automatically treated as treaty-like. | Anchor-component, stacked, and treaty hybrids flatten into the same ambiguous shape. | Keep `component_relocation` for non-treaty anchor/component candidates. Add explicit claim roles and an explicit treaty-status field; do not infer treaty from `hybrid`. | Alter. |
| S-26 | `SAFE` | `backend/app/calculators/inkind_contribution.py::analyse_inkind_contribution`; `allocation_pricing.py::price_allocated_structure` | The LU model recommends `UNKNOWN`, gives in-kind zero QPE pending a ruling, and the allocation pricer accepts only an explicit replacement-cost normalization outside QPE. | Prevents free FMV from inflating QPE and prevents double counting as both budget and support. | Retain zero-QPE/explicit-replacement treatment. Add generic project input only when evidenced. | Proceed with adapter wiring. |
| S-27 | `STALE_ASSUMPTION` | `inkind_contribution.py::INTERNATIONAL_PRECEDENTS`, `make_post_inkind_contribution` | Contains frozen jurisdictional summaries and LU-specific FMV/relationship assumptions inside executable code. | Could be mistaken for current authority or generalized to another project. | Treat as LU forensic notes only; canonical decisions must use current registered authority and real project contribution facts. | Do not generalize unchanged. |
| S-28 | `SAFE` | `backend/app/calculators/allocation_pricing.py::rank_allocated_structures`; `backend/app/services/canonical_production_view.py` comparability gate | Ranks fully priced normalized structures by lowest NPC; conditional opportunities are only a tie-break. The generic served adapter keeps non-normalized relocations out of numeric ranking. | Correct ranking discipline if its inputs satisfy the contract. | Preserve NPC primary key and explicit comparability gate. | Proceed with contract enforcement. |
| S-29 | `ADAPTER_REQUIRED` | `rank_allocated_structures`; `build_structure_recommendation` | The ranker trusts `is_fully_priced`; it does not independently enforce feasibility, direct comparability, legal-review state, or complete stacking/treaty resolution. | Rich structures can enter ranking if an upstream caller incorrectly labels them complete. | Add one admission predicate requiring complete economics, normalization, exact legal interactions, treaty status, and direct comparability; feasibility affects category/risk, not QPE. | Alter orchestration, not ranking math. |
| S-30 | `BUG` | `backend/app/services/canonical_production_view.py::_scenario_category`; commit `86f1547` combined rows | Signals are sufficient, but the mapper does not inspect `legal_review_required`, `stacking_violations`, or `disclosed_limitations`. A home-jurisdiction combination could become recommended once marked comparable even if its adjustment did not execute. | Category can overstate actionable status. | Gate category admission on the same resolved-legal/economic predicate as ranking. A non-executable combination is `NOT_AVAILABLE`; a fully priced but weak/non-comparable result is `PRICED_LOW_FIT`. | Alter before widening comparability. |

## Area conclusions

### Stacking

**Safe:** canonical single-program values; fail-closed return for an entirely unmapped exact pair in the `86f1547` bridge; deterministic trace objects; `allowed` as a no-op only after exact rule authorization.

**Defects:** prohibited combinations retain value; mutual exclusions become false combined structures; conditional and failed reductions can remain `PRICED`; credit-to-credit reductions have no direction; cap rules have no structured numeric contract; mixed/N-way adjustments are order-dependent; legacy ranking is not lexicographic and does not exclude illegal claims.

**Unsafe defaults:** missing rule means allowed in both `generate_structure_scenarios` and Phase E `evaluate_pair`; country/type generalizations stand in for exact authority.

### Identity

**Gaps:** DB UUID, canonical slug, legacy slug, display name, and jurisdiction code are compared in different paths. Static name-fragment inference and exact legacy table keys are not a canonical rule binding. The required adapter must resolve both endpoints to canonical program IDs, preserve source DB UUID/source document/confidence, and reject ambiguous or superseded identities.

### Component / split

**Status:** core allocation and multi-register economics are **SAFE WITH AN INPUT ADAPTER**. They operate on actual lines, conserve the cash budget, require explicit splits, prevent ordinary double allocation, derive QPE independently, and combine incentives once.

**Defects:** default domicile/location routing can invent territorial facts; unmapped spend categories become principal photography; `RECOMMENDED` routes do not block pricing; one-program-per-jurisdiction cannot carry a real stack.

### Grants / funds

**Status:** `conditional_programs` plus `structure_compatibility` is **SAFE TO RECONNECT** as zero-NPC opportunity metadata.

**Defects:** Phase E grant estimation and old fixed competitive-award pricing are unusable. A program cap is not an expected award, and selective face value cannot reduce NPC without a project award.

### Co-production

**Status:** registry-backed candidate discovery is **NEEDS_ADAPTER**. The current eligibility/pricing chain is not safe to reconnect.

**Defects:** cultural tests fail open; percentage totals/unique parties are not enforced; bilateral unlock roles can reverse; `_treaty_requirements` substitutes registry presence and a generic heuristic for complete eligibility, mishandles multilateral coverage, and treats all hybrids as treaties.

### Hybrid / anchor

**Status:** component relocation already represents a non-treaty anchor/component structure. `primary_jurisdiction` is a usable anchor-jurisdiction field.

**Defects:** no anchor-program/stacked-program/co-pro-role representation exists; `hybrid` is semantically ambiguous and triggers treaty logic unconditionally.

### Ranking

**Status:** `rank_allocated_structures` and the generic comparability gate are safe when upstream completeness is true. Phase E scoring, the old scenario composite rank, and hard-coded structure estimates are unusable.

**Defects:** upstream legal/treaty/interaction completeness is not part of the ranker's own admission contract. Conditional award depth is correctly only a tie-break; it must stay that way.

### Scenario categories

The existing signals are sufficient: numeric rank, full priceability, direct comparability, explicit treaty instrument, feasibility, and blockers can deterministically support `RECOMMENDED`, `ALTERNATIVE`, `CO_PRO_OPPORTUNITIES`, `PRICED_LOW_FIT`, and `NOT_AVAILABLE`. No new scoring doctrine is needed. The existing mapper needs one correction: unresolved legal/stacking/treaty economics must gate recommendation/category admission.

## High-priority corrections before runtime acceptance

1. **Stop publishing unresolved pair economics as priced.** Mutual exclusion/prohibition must reject the combination; conditional, unexecuted spend reduction, and unparseable cap must be unpriced. Keep all independently priced single-program alternatives.
2. **Create one canonical, fail-closed interaction binding.** Resolve canonical program IDs to exact source-backed rules with explicit source/target, affected basis, numeric parameter, confidence, and coverage state. Remove name inference and default allowance from the canonical route.
3. **Keep N-way publication gated.** Complete pair coverage is necessary but not sufficient. Do not accept the unpublished N-way reconnection until mixed adjustments are dependency-aware and order-independent, with cumulative bases and global caps handled explicitly.
4. **Bind real territorial routing.** Preserve the allocator but make non-location-bound default routes conditional until service/vendor/residency/use facts or an explicit producer election exist. SPV domicile alone cannot qualify foreign spend.
5. **Repair and bind treaty eligibility.** Enforce unique parties, 100% contribution, cultural/national-status resolution, correct signatory unlocks, and the exact claimed instrument before pricing official co-production status.
6. **Use one ranking admission predicate.** Fully priced, legally resolved, treaty-resolved, normalized, and directly comparable structures may rank; feasibility then informs category/risk without deleting valid economics.

## New optimizer capability required — proven absent only

1. A structured canonical interaction contract carrying direction, affected base, numeric cap/reduction parameters, precedence/dependencies, authority provenance, and explicit unknown coverage.
2. An order-independent N-way adjustment planner for mixed spend reductions, basis reductions, caps, exclusions, and shared/global limits. Existing combination enumeration is not this capability.
3. A typed multi-claim segment model that represents anchor program, stacked programs, claim roles, and per-claim rule provenance while retaining the existing conserving account allocation.

Everything else required for the safe path is correction or adapter work around surviving capabilities; a new optimizer, allocator, treaty registry design, conditional-fund model, ranking formula, or scoring doctrine is not justified.

## Final gate

**CODEX_EXISTING_OPTIMIZER_ENGINE_CORRECTNESS_CLASSIFIED**

Production code changed: **NO**

Frontend changed: **NO**

External research: **NO**
