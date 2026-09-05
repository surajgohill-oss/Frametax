# CineGlobe Optimizer Wiring / Capability Audit — Codex

Audit date: 2026-09-04

Repository state audited: `claude/audit-frametax-features-NZcX5` at `5ec16632cdaae4f1ad85c8b1ce582607b54931fb`

Method: read-only repository/runtime forensics plus six narrow non-mutating unit-test modules (`65 passed`)

Production code, database records, program data, and UI changed: **none**

## 1. EXECUTIVE VERDICT

**NO_GO_FOR_OPTIMIZER_BEHAVIORAL_ACCEPTANCE**

The canonical optimizer is real and executable for single-jurisdiction, full-relocation, component-relocation, program-stack, treaty-opportunity, and discretionary/selective pathways. Component relocation demonstrably changes allocation and economics. However, behavioral acceptance is blocked by three current P0 defects:

1. When the evaluator has no comparable Recommended candidate, it clears `Project.leading_structure_id`; the served canonical view instead selects the lowest-NPC fully priced candidate, including non-comparable `PRICED_LOW_FIT` structures. Little Utopia (LU) and F#K Valentine's Day (FVD) therefore expose Saudi Arabia full-relocation structures as canonical selections even though the evaluator selected none.
2. Component-relocation participant persistence includes non-claiming stated-location segments. All 134 current LU component candidates expose `US` as a participant in addition to the actual anchor and target jurisdictions.
3. Treaty conditional pricing prices the entire project independently in each participant jurisdiction, while its nominal minimum shares can total less than 100%. LU's GB/IE conditional scenario prices $8,126,528 of QPE against a $4,364,393 gross budget.

Other named families—non-treaty splits, majority/minority and multi-party co-production, service-production as a distinct family, grant/fund economics, hybrid economics, reinvestment economics, and in-kind economics—do not have a complete canonical executable chain. They must not be advertised as operational optimizer structures.

## 2. CANONICAL PIPELINE MAP

The current canonical path is:

`POST /api/v1/evaluation/projects/{project_id}/begin` (`backend/app/api/v1/evaluation.py::begin_project_evaluation`)
→ `backend/app/services/canonical_evaluation.py::evaluate_project`
→ `production_discovery.discover_executable_jurisdictions`
→ family generation in `evaluate_project`
→ `production_allocation.StructureSpec` / `derive_account_allocation`
→ `allocation_pricing.price_allocated_structure` / `price_segment`
→ optional `canonical_stack_bridge.price_program_group_stack`
→ result classification and `_summarize_evaluation`
→ `ProductionStructure` + `StructureCalculationResult` persistence using engine version and input fingerprint
→ `canonical_production_view.build_production_and_structures`
→ API production payload
→ frontend `frontend/src/lib/globeData.js::activeStructure` and `bestPricedCandidate.js`.

The complete per-family stage/status inventory is in `OPTIMIZER_STRUCTURE_CAPABILITY_MATRIX_CODEX.csv`.

## 3. STRUCTURE CAPABILITY MATRIX

| Family | Operational conclusion | Overall status |
|---|---|---|
| Single jurisdiction | Full canonical chain exists | READY_WITH_LIMITATIONS |
| Full relocation | Full chain exists, but non-comparable candidates can be canonically selected | NOT_READY |
| Component relocation | Real split allocation/pricing exists; participant persistence is defective | NOT_READY |
| Stacked incentive | Canonical bridge and rule enforcement exist; no current positive real-project candidate | NOT_READY |
| Treaty co-production | Opportunity/eligibility path exists; conditional economics are materially invalid | NOT_READY |
| Non-treaty split/combination | No canonical generator | NOT_IMPLEMENTED |
| Majority/minority co-production | Data concepts only; no canonical structure path | NOT_IMPLEMENTED |
| Multi-party co-production | Data concepts only; no canonical structure path | NOT_IMPLEMENTED |
| Service production | Programs use ordinary single/full paths; no distinct family | NOT_IMPLEMENTED |
| Grants/funds | Discovery metadata only; no priced structure economics | NOT_IMPLEMENTED |
| Discretionary/selective | Generic project-policy-controlled program path exists | READY_WITH_LIMITATIONS |
| Hybrid | Relationship metadata only; no combined allocation/economics | NOT_IMPLEMENTED |
| Anchor | Real role inside component relocation, not a standalone family | READY_WITH_LIMITATIONS |
| Reinvestment | Opportunity metadata only | NOT_IMPLEMENTED |
| In-kind | Pricing parameter/model exists but is disconnected from canonical evaluation | NOT_IMPLEMENTED |

## 4. SINGLE JURISDICTION TRACE

`ENTRY evaluate_project` → `GENERATOR home-jurisdiction candidate loop` → `ELIGIBILITY production_discovery + _price_candidate gates` → `ALLOCATION StructureSpec/derive_account_allocation` → `PRICING price_allocated_structure/price_segment` → `STACK/CAP program pricing rules` → `RANK _summarize_evaluation` → `TRACE StructureCalculationResult.trace` → `PERSIST ProductionStructure/StructureCalculationResult` → `SELECT canonical_production_view`.

Bad Hombres is a valid real-project example: New Mexico baseline structure `c123cf6e-d7b4-4fb0-8fca-8c0061c0b230`, incentive `$596,910.25`, NPC `$1,885,112.75`, and Recommended classification. The family is executable, but the cross-family canonical-selection defect prevents an unqualified acceptance verdict.

## 5. FULL RELOCATION TRACE

`ENTRY discover_executable_jurisdictions` → `GENERATOR evaluate_project full-relocation loop` → `ELIGIBILITY discovered program/project facts` → `ALLOCATION StructureSpec(full_relocation)` → `PRICING _price_candidate` → `STACK/CAP program rules` → `RANK deliberately non-comparable review classification` → `TRACE persisted calculation trace` → `PERSIST canonical rows` → `SELECT canonical_production_view fallback`.

The generation/pricing chain is real. The defect is selection: FVD Saudi structure `ea7abc5c-cd3c-46d7-b838-93775b54da97` is `PRICED_LOW_FIT`, `is_directly_comparable=false`, yet becomes `canonical_selected_structure_id` when no comparable rank-1 result exists. That contradicts `_summarize_evaluation`, which sets `top_result=None` and clears `leading_structure_id`.

## 6. COMPONENT RELOCATION TRACE

`ENTRY evaluate_project component target loop` → `GENERATOR _price_component_relocation_candidate` → `ELIGIBILITY target program + project facts` → `ALLOCATION component-aware StructureSpec/derive_account_allocation` → `PRICING price_allocated_structure by segment` → `STACK/CAP per-program rules` → `RANK _summarize_evaluation` → `TRACE segments/components` → `PERSIST canonical rows` → `SELECT canonical_production_view`.

This is not a relabeled single-country result. FVD evidence:

- Greece baseline: QPE `$3,614,149.60`, incentive `$1,445,659.84`, NPC `$3,072,027.16` (`08a198da...`).
- Romania full relocation: QPE `$3,701,238.00`, incentive `$1,110,371.40`, NPC `$3,418,005.60` (`c7165f30...`).
- Greece anchor + Romania post component: Greece QPE `$3,554,792.00`, Romania post QPE `$146,446.00`, total incentive `$1,465,850.60`, NPC `$3,062,526.40` (`adcbeb4f-42f9-44fa-8118-854dcb86896c`).

The economic allocation is real, but participant persistence is wrong. `canonical_production_view._empty_structure_entry` appends every segment jurisdiction. LU's non-claiming stated-location `US` segment therefore appears as a participant. Example `8172eb82-c2cc-4816-a331-beffddab5199` exposes `['MU','CA-MB','US']`; the economic participants are `['MU','CA-MB']`. The defect affects all 134 current LU component candidates.

## 7. STACKING TRACE

`ENTRY program groups discovered for jurisdiction` → `GENERATOR evaluate_project combinations` → `ELIGIBILITY constituent program gates` → `ALLOCATION shared StructureSpec` → `PRICING canonical_stack_bridge.price_program_group_stack` → `STACK/CAP explicit compatibility, exclusivity, ordering and aggregate-cap rules` → `RANK only eligible/comparable priced outputs` → `TRACE distinct constituents and rule decisions` → `PERSIST multi_program structure/result` → `SELECT canonical view`.

Unknown or conditional stackability fails closed; the bridge does not silently sum unknown pairs. N-way generation is bounded at four programs. Current LU, FVD, Bad Hombres, and Lips Like Sugar each have one current `multi_program` row, all representing the same Ontario OPSTC/OFTTC mutually exclusive `RULE_REJECTED` diagnostic. LU example: `75fb0b1c-2e80-48a2-99fc-ceab609bb40c`.

The mechanics have narrow unit coverage, but no current real project supplies a positive, accepted multi-program stack. Positive behavioral acceptance would therefore require fabricated data, prohibited by this audit. The family is not ready for the requested real-project acceptance phase.

## 8. TREATY / CO-PRO TRACE

`ENTRY proactive_opportunity_discovery/canonical_treaty_bridge` → `GENERATOR treaty opportunity rows in evaluate_project` → `ELIGIBILITY treaty/cultural/project-fact gates` → `ALLOCATION no canonical shared co-production allocation` → `PRICING _build_conditional_bilateral_scenario calls _price_candidate once per country` → `STACK/CAP summed country results` → `RANK opportunity is not a normal comparable candidate` → `TRACE treaty evidence/conditional scenario` → `PERSIST treaty_coproduction row` → `SELECT surfaced as opportunity`.

Participant identities survive opportunity persistence, but the conditional economics do not allocate one budget among them. `solve_bilateral_minimum_contribution` returns the treaty minimum percentages without requiring them to total 100, and each jurisdiction then receives the whole budget.

LU GB/IE proof: gross budget `$4,364,393`; assumed shares 20% + 20%; GB QPE `$4,063,264`, IE QPE `$4,063,264`; combined QPE `$8,126,528` (186.2% of gross); combined incentive `$2,185,829.43`; conditional NPC `$2,178,563.57`. The nested scenario nevertheless reports `fully_priced=true`. This is a material formula defect.

## 9. NON-TREATY COMBINATION TRACE

`ENTRY none in canonical evaluation` → `GENERATOR absent` → `ELIGIBILITY absent` → `ALLOCATION kernel/type concepts only` → `PRICING absent` → `STACK/CAP absent` → `RANK absent` → `TRACE absent` → `PERSIST absent` → `SELECT absent`.

`split_production`, `majority_minority`, `multi_party`, and a distinct `service_production` can be found in types, kernels, legacy/stateless helpers, or terminology, but `canonical_evaluation.evaluate_project` never builds or persists these families. Ordinary service incentives may still be priced through single/full relocation; that is not proof of a separate service-production structure.

## 10. GRANTS / FUNDS TRACE

`ENTRY conditional_programs registry/discovery` → `GENERATOR conditional_unpriced node attached to a parent structure` → `ELIGIBILITY unresolved/project-specific` → `ALLOCATION absent` → `PRICING absent` → `STACK/CAP unknown and fail-closed` → `RANK excluded from deterministic economics` → `TRACE conditional metadata` → `PERSIST inside parent trace` → `SELECT no standalone economic selection`.

The implementation truthfully discloses grant/fund opportunities but does not create project-specific award economics. No fund type observed has the full canonical path required for optimizer support.

## 11. DISCRETIONARY / SELECTIVE TRACE

`ENTRY production discovery` → `GENERATOR ordinary single/full candidate` → `ELIGIBILITY _is_discretionary_program + _discretionary_policy_resolve using ProjectFact/program_requirements.allocation_type` → `ALLOCATION generic StructureSpec` → `PRICING ordinary program pricing` → `STACK/CAP normal program rules` → `RANK deterministic result with administrative-risk disclosure` → `TRACE policy/gate warnings` → `PERSIST canonical result` → `SELECT canonical view`.

The generic project-policy control changes candidate inclusion and fails closed when required facts are absent; the home baseline is deliberately protected. The current system does not probability-weight or risk-adjust economics. FVD/LU Saudi alternatives demonstrate the path. Because the P0 fallback can elevate such a non-comparable discretionary alternative to canonical selection, the family is only ready with limitations after that defect is fixed.

## 12. HYBRID TRACE

`ENTRY relationship metadata` → `GENERATOR no hybrid StructureSpec` → `ELIGIBILITY inherited metadata only` → `ALLOCATION absent` → `PRICING absent` → `STACK/CAP absent` → `RANK absent` → `TRACE relationship_types may contain coproduction + conditional_fund` → `PERSIST metadata only` → `SELECT no hybrid instance`.

The term “hybrid” describes coexisting relationship flags, not an executable structure that combines distinct production components or economic pathways. It is not implemented operationally.

## 13. ANCHOR TRACE

`ENTRY project home/stated production assumptions` → `GENERATOR component relocation builder` → `ELIGIBILITY anchor program gates` → `ALLOCATION retained components assigned to anchor` → `PRICING segment pricing` → `STACK/CAP normal rules` → `RANK component candidate economics` → `TRACE anchor role` → `PERSIST component_relocation` → `SELECT canonical view`.

Anchor is real and assumption-driven, but it is a role inside component relocation, not a standalone structure family or hard-coded preference. LU and FVD are the best real examples. Its readiness inherits component relocation's participant and selection blockers.

## 14. REINVESTMENT TRACE

`ENTRY canonical_opportunity_bridge reinvestment discovery` → `GENERATOR opportunity node only` → `ELIGIBILITY known/potential fact status` → `ALLOCATION absent` → `PRICING zero/unpriced` → `STACK/CAP absent` → `RANK excluded` → `TRACE opportunity metadata` → `PERSIST inside parent candidate trace` → `SELECT no reinvestment structure`.

LU's baseline `459b4f56-ac7c-45d8-8ef2-a84e5f74b58d` contains reinvestment opportunities, proving discovery. There is no conversion from confirmed terms to `StructureSpec`, allocation, priced economics, or selection.

## 15. IN-KIND TRACE

`ENTRY no canonical contribution discovery` → `GENERATOR absent` → `ELIGIBILITY absent` → `ALLOCATION no in-kind assignment` → `PRICING parameter exists in allocation_pricing but canonical evaluation always passes 0` → `STACK/CAP not applicable` → `RANK no adjusted candidate` → `TRACE no canonical contribution trace` → `PERSIST absent as economics` → `SELECT absent`.

Standalone/demo calculators and an `inkind_replacement_delta_usd` parameter exist. Current canonical evaluation explicitly supplies `0.0`; the repository comments identify generic support as absent. This is disconnected capability, not an executable optimizer family.

## 16. CANONICAL SELECTION / PERSISTENCE TRACE

Persistence uses `ProductionStructure` plus `StructureCalculationResult`, current `ENGINE_VERSION`, and `input_fingerprint`. Current runtime rows exist for 14 projects. The four accepted real projects contain:

| Project | Current rows | Single | Full | Component | Multi-program | Treaty | Persisted leading |
|---|---:|---:|---:|---:|---:|---:|---|
| Little Utopia | 283 | 1 | 123 | 134 | 1 | 24 | null |
| F#K Valentine's Day | 356 | 1 | 123 | 206 | 1 | 25 | null |
| Bad Hombres | 283 | 1 | 123 | 135 | 1 | 23 | valid |
| Lips Like Sugar | 381 | 1 | 123 | 232 | 1 | 24 | valid |

Only five canonical structure types are currently persisted: `single_country`, `full_relocation`, `component_relocation`, `multi_program`, and `treaty_coproduction`.

Selection is not unified in the no-comparable case:

- `canonical_evaluation._summarize_evaluation` returns no top result and clears `Project.leading_structure_id` when no candidate is Recommended/comparable.
- `canonical_production_view.build_production_and_structures` falls back to the minimum NPC among all fully priced structures.
- `frontend/src/lib/globeData.js::activeStructure` and `bestPricedCandidate.js` consume `allocated.canonical_selected_structure_id`; the frontend renders this backend identity rather than recomputing NPC.

Current proof:

- LU: `leading_structure_id=null`, `ranked_count=0`, but canonical selection is Saudi full relocation `c57272cc-c0ac-4aa6-a3ea-4791372b98a9`, `PRICED_LOW_FIT`, non-comparable, NPC `$2,661,175.40`.
- FVD: `leading_structure_id=null`, `ranked_count=0`, but canonical selection is Saudi full relocation `ea7abc5c-cd3c-46d7-b838-93775b54da97`, `PRICED_LOW_FIT`, non-comparable, NPC `$2,628,204.20`.
- Bad Hombres and Lips Like Sugar have matching valid leading/rank-1 selections.

## 17. BYPASS / PARALLEL PATH FINDINGS

The mounted `/api/v1/optimization` endpoints expose stateless legacy calculators and structure generators. They do not persist canonical evaluation rows and no current frontend caller was identified. The legacy `POST /projects/{id}/structures/{sid}/calculate` endpoint returns HTTP 410. These paths are isolated from current selection, but their mounted presence is materially confusing and should be explicitly documented as non-canonical.

Manual project patching can set leading-related fields, but normal frontend selection uses the priced canonical payload. No evidence showed it as the source of the current LU/FVD mismatch.

Directly importing `canonical_production_view` before `canonical_evaluation` triggers an import-order circularity involving `DoctrineRateTier` and `executable_jurisdiction_registry`; importing the evaluator first succeeds. This is acceptance-harness fragility, not evidence of a second production economics path.

## 18. REAL-PROJECT TESTABILITY MATRIX

| Family | Best real project | Existing candidate | Observable acceptance target |
|---|---|---|---|
| Single jurisdiction | Bad Hombres | `c123cf6e-d7b4-4fb0-8fca-8c0061c0b230` | New Mexico baseline QPE/incentive/NPC persists and is rankable |
| Full relocation | FVD | `ea7abc5c-cd3c-46d7-b838-93775b54da97` | Non-comparable Saudi candidate must never become canonical selection |
| Component relocation | FVD | `adcbeb4f-42f9-44fa-8118-854dcb86896c` | Romania post allocation changes QPE/incentive/NPC |
| Component participants | LU | `8172eb82-c2cc-4816-a331-beffddab5199` | Participants equal claiming anchor/target only |
| Stacked incentive | LU | `75fb0b1c-2e80-48a2-99fc-ceab609bb40c` | OPSTC/OFTTC exclusion remains rejected; no positive real fixture exists |
| Treaty/co-production | LU | GB/IE treaty opportunity | Allocated country shares conserve one budget before pricing |
| Grants/funds | FVD or LU | Conditional nodes present | Discovery disclosure only; no deterministic economics/ranking |
| Discretionary/selective | FVD | Saudi full relocation | Project policy changes inclusion; low-fit result is not selected |
| Anchor | FVD | Component candidate above | Retained Greece spend and routed Romania post remain distinct |
| Reinvestment | LU | Baseline opportunity metadata | Discovery remains unpriced and excluded from rank |
| In-kind | LU | none | No behavioral acceptance possible on current canonical path |

Non-treaty split, majority/minority, multi-party, service-production as a distinct family, hybrid, and in-kind have no current real candidate and must not receive fabricated behavioral acceptance fixtures.

## 19. P0 DEFECTS

### P0-1 — Canonical selection semantics diverge

**Files/functions:** `backend/app/services/canonical_evaluation.py::_summarize_evaluation`; `backend/app/services/canonical_production_view.py::build_production_and_structures`; `frontend/src/lib/globeData.js::activeStructure`; `frontend/src/lib/bestPricedCandidate.js`.

The evaluator selects none, while the served view selects lowest NPC regardless of comparability. LU and FVD therefore expose non-comparable Saudi full-relocation candidates as project truth. `backend/tests/test_canonical_selection_consistency.py` encodes the fallback instead of asserting evaluator/served-selection equivalence.

### P0-2 — Component participant contamination

**File/function:** `backend/app/services/canonical_production_view.py::_empty_structure_entry`.

Every segment jurisdiction is persisted/exposed as a participant, including non-claiming stated-location segments. All 134 LU component candidates gain false `US` participation. `backend/tests/test_canonical_scenario_participants.py` only requires at least two participants and misses exact identity.

### P0-3 — Treaty conditional pricing double-counts the project

**Files/functions:** `backend/app/services/canonical_evaluation.py::_build_conditional_bilateral_scenario`; `canonical_treaty_bridge.solve_bilateral_minimum_contribution`; `_price_candidate`.

Minimum shares need not conserve 100%, and each participant prices the full project. LU GB/IE produces QPE equal to 186.2% of gross while reporting `fully_priced=true`. `backend/tests/test_copro_conditional_pricing_bridge.py` checks positive arithmetic but not allocation/share conservation.

## 20. P1 DEFECTS

1. Positive stack economics have no current real-project acceptance candidate; only a correctly rejected mutually exclusive Ontario pair is present.
2. Grants/funds are discovery-only and cannot resolve project eligibility, award amount, allocation, stacking, or economic ranking.
3. “Hybrid” is relationship metadata and can overstate operational support if presented as a structure.
4. Confirmed reinvestment facts have no conversion path into canonical allocation/pricing.
5. In-kind models and pricing parameters are disconnected from canonical project evaluation.
6. Discretionary/selective administrative risk is disclosed but does not probability-adjust ranking; this limitation must remain explicit.

## 21. P2 FINDINGS

1. Mounted stateless `/api/v1/optimization` endpoints create a confusing parallel capability surface despite having no identified canonical consumer.
2. `canonical_production_view` has import-order circularity that can break isolated acceptance probes.
3. Current tests do not assert exact component participant sets, treaty allocation conservation, or equivalence between evaluator top-result semantics and served canonical selection.

## 22. EXACT CLAUDE BEHAVIORAL ACCEPTANCE PLAN

Do not begin this plan until P0-1 through P0-3 are repaired and independently regression-tested. Claude must exercise the canonical evaluation endpoint/service and then retrieve the canonical production payload; it must not call legacy stateless optimization endpoints.

### Single jurisdiction — Bad Hombres

**GIVEN** the current canonical Bad Hombres budget/facts and New Mexico baseline program.

**WHEN** canonical evaluation runs and the production payload is retrieved.

**THEN** discovery includes the program; one canonical single-country structure is generated; eligibility gates are recorded; source accounts allocate once; QPE, incentive `$596,910.25`, and NPC `$1,885,112.75` reconcile; caps and warnings appear in the same trace; result/fingerprint persist; rank and canonical selected ID equal the valid leading structure.

### Full relocation — FVD

**GIVEN** current FVD data and its Saudi full-relocation candidate.

**WHEN** canonical evaluation and view building complete with no comparable Recommended result.

**THEN** discovery/generation/pricing may retain Saudi as a review candidate, but it remains non-comparable, cannot become rank 1, cannot populate canonical selected/leading identity, and its trace/persistence clearly explains low fit.

### Component relocation and anchor — FVD and LU

**GIVEN** FVD's Greece anchor/Romania-post case and LU's Mauritius/Manitoba case.

**WHEN** canonical evaluation generates component candidates.

**THEN** component allocation differs from both baseline and full relocation; jurisdiction QPE/incentives sum exactly to the candidate totals; NPC reconciles; stack/cap rules apply by constituent; claiming participants persist exactly once; LU excludes non-claiming `US`; explanation, result, and canonical identity reference the same structure.

### Stacking — LU negative case

**GIVEN** LU's OPSTC/OFTTC pair.

**WHEN** canonical stack generation evaluates it.

**THEN** programs remain distinct; the mutual-exclusion rule rejects the pair; no incentive sum, rank, or selection is produced; the rejection trace and persisted diagnostic name the rule. A positive stack cannot be accepted until a current real project naturally generates one; do not fabricate a fixture.

### Treaty/co-production — LU GB/IE

**GIVEN** the existing GB/IE opportunity and verified contribution assumptions.

**WHEN** a conditional or executable co-production scenario is built after repair.

**THEN** participants survive generation; treaty/cultural/legal gates are explicit; allocated shares cover exactly one canonical project budget; no source account is duplicated; each country prices only its allocated eligible spend; combined QPE cannot exceed the properly allocated eligible base; combined incentive and NPC reconcile; uncertainty prevents Recommended rank; trace and persistence retain both participants.

### Discretionary/selective — FVD

**GIVEN** the same project/program with the generic project-policy fact absent, false, and affirmatively enabled in controlled reversible probes.

**WHEN** canonical evaluation runs for each state.

**THEN** candidate inclusion changes according to policy; no absent/false alternative is priced; an enabled result carries discretion/preapproval warnings; administrative uncertainty is not disguised; a non-comparable result never becomes canonical selection. Restore the original fact after the probe.

### Grants/funds and reinvestment — disclosure boundary

**GIVEN** existing LU/FVD conditional opportunities.

**WHEN** canonical evaluation runs.

**THEN** discovery and explanation may persist the opportunity, but it has zero deterministic economics, does not stack, does not alter NPC, does not rank, and cannot become canonical selection. This accepts truthful disclosure only, not an optimizer structure.

Families classified `NOT_IMPLEMENTED` receive no behavioral acceptance test until a separate authorized implementation phase supplies a canonical generator, eligibility, allocation, pricing, explanation, persistence, selection path, and real-project coverage.

## 23. GO / NO-GO RECOMMENDATION

**NO_GO_FOR_OPTIMIZER_BEHAVIORAL_ACCEPTANCE**

Blocking conditions are precisely P0-1 canonical-selection divergence, P0-2 component participant contamination, and P0-3 treaty conditional budget double-counting. After those are repaired, rerun the targeted canonical tests and the real-project plan above. Preserve the boundary that metadata-only/unimplemented families are not optimizer capabilities, and require a real positive stack before accepting positive stack behavior.
