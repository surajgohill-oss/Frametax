# CINEGLOBE POST-CLAUDE RECONCILIATION AUDIT

**AUDITED COMMIT:**
`bb4b6a25317e398be628c70a0c6899bff2fd8e44`

**CANONICAL REMOTE HEAD:**
`origin/claude/audit-frametax-features-NZcX5` = `bb4b6a25317e398be628c70a0c6899bff2fd8e44`

**CONCURRENCY AFFECTED AUDIT:**
NO. The audit used the immutable committed tree at `bb4b6a2`, independently of unrelated untracked files in the shared worktree. The remote branch resolved to the same commit before the audit branch was created.

## EXECUTIVE RESULT

**CLAUDE bb4b6a2 SAFE BASELINE:**
NO. It is a stable source baseline for the next repair, but not a safe economic-output baseline: material pre-existing classification, incentive-base, authority-gating, requirements-gating, rate, and dollar-cap defects still produce deterministic incentive/NPC values. `bb4b6a2` also introduces one new read-path side-effect defect.

**CLAUDE FINANCE IMPLEMENTATION:**
PARTIAL. Persistence, fingerprinting, candidate-pricing propagation, QPE isolation, explicit evaluation, and refetch are wired. The meaning of the field is not reconciled with financing already inside the imported gross budget, so entering the same cost again adds it twice to NPC. The API also does not enforce non-negative/finite economic bounds independently of the frontend.

**CLAUDE DISPLAY-NAME IMPLEMENTATION:**
PARTIAL. The edited direct-code fields now resolve through `jurisdictionName`, but backend-authored `ProductionStructure.name` values containing raw jurisdiction codes and program slugs remain visible on affected sidebars and Inspector context.

**CLAUDE FUTURE-PROJECT CLAIM:**
PARTIAL. The implementation is generic and contains no title/UUID branch, but the added backend tests mutate the existing Little Utopia project and the frontend tests are static source scans. No clean-slate project propagation test exists.

**PREVIOUS CODEX LIPS CALCULATION DEFECT:**
STILL VERIFIED.

**PREVIOUS CODEX OPTIMIZER CONSUMPTION DEFECT:**
STILL VERIFIED. Conditional-value exclusion is correctly safe, but labour bases, authority/requirements consumption, caps, mutual-exclusion structure emission, conditional attachment, and producer presentation remain defective or incomplete.

**NEW REGRESSIONS FROM bb4b6a2:**
1 defect class, present in two GET/read builders: supposedly read-only fingerprint reconstruction calls a project-input builder that can persist budget routing and home-jurisdiction facts.

## CLAUDE DELTA AUDIT

### `backend/app/api/v1/cineglobe.py`

- **reason:** Add `financing_cost_usd` to the generic project-assumption whitelist.
- **expected:** YES.
- **unexpected:** No server-side range/finite-value economic validation was added; `answers` remains `dict[str, Any]`.
- **risk:** A direct API caller can persist negative or non-finite-like numeric text accepted by the downstream float conversion even though the browser rejects non-finite input. More importantly, the endpoint cannot distinguish incremental/off-budget financing from financing already included in the source budget.

### `backend/app/services/canonical_project_economics.py`

- **reason:** Define `FACT_FINANCING_COST_USD`, add it to `ProjectEconomicInputs`, and resolve it from `ProjectFact` using existing user-override precedence.
- **expected:** YES.
- **unexpected:** None in the storage/read chain itself.
- **risk:** The field is documented as a production financing/bridge cost but has no canonical scope flag establishing whether it is incremental to the source budget. `build_project_economic_inputs` also has pre-existing write-capable behavior when used from the new GET paths.

### `backend/app/services/canonical_evaluation.py`

- **reason:** Add financing to the canonical input fingerprint and pass it into both normal and component-relocation pricing.
- **expected:** YES.
- **unexpected:** The value is passed to every candidate as a full project-wide NPC addition without reconciliation to imported finance lines.
- **risk:** Material NPC double counting if the producer enters a financing amount already included in gross budget. `inputs.financing_cost_usd or 0.0` also treats an invalid negative value as active rather than rejecting it.

### `backend/app/services/canonical_production_view.py`

- **reason:** Replace unordered selection of one current-engine fingerprint with recomputation of the fingerprint from current inputs.
- **expected:** The freshness correction is justified and resolves the multi-fingerprint/revert defect.
- **unexpected:** The GET/read builder calls `build_project_economic_inputs`, which can route/persist a missing budget and can resolve/persist home jurisdiction, including `session.commit()`.
- **risk:** Page loads can mutate project state. If inputs are incomplete, fallback to the newest prior current-engine fingerprint can still serve economics that no longer correspond to currently evaluable state.

### `backend/app/services/project_workspace_view.py`

- **reason:** Apply the same current-input fingerprint selection to the workspace view.
- **expected:** The freshness correction is justified.
- **unexpected:** Same write-capable dependency from a read path.
- **risk:** Same GET-side state mutation and incomplete-input stale fallback as the production view.

### `backend/tests/test_financing_cost_assumption.py`

- **reason:** Cover fact resolution, NPC-only treatment, fingerprint change, and whitelist presence.
- **expected:** YES.
- **unexpected:** Every runtime test uses the existing Little Utopia UUID; the persistence test writes directly to `ProjectFact` instead of exercising the assumptions endpoint; no restore-to-prior-value test, invalid-input test, source-finance coexistence test, GET-no-write test, or clean-slate-project test exists.
- **risk:** The tests prove the narrow chain but over-support a future-project PASS and do not detect the new read-side effect or finance double-count semantics.

### `frontend/src/components/BudgetRail.jsx`

- **reason:** Add persisted Finance Costs editing; explicitly evaluate before refetch after Finance or Contingency changes; remove fake local-only adjustments; humanize routing labels; make existing in-kind amount read-only.
- **expected:** YES.
- **unexpected:** The label and tooltip describe a broad financing/bridge cost without distinguishing incremental/off-budget cost from finance already present in the budget. A successful fact write followed by failed evaluation leaves persisted state changed while the editor remains in an error path with no user-facing reconciliation in this component.
- **risk:** Producer double entry can inflate NPC. The fake economics controls are correctly gone.

### `frontend/src/lib/jurisdictions.js`

- **reason:** Add display/coordinate entries for Alberta, Manitoba, and Montana.
- **expected:** YES for the affected direct lookup surfaces.
- **unexpected:** This remains a geographic map and is not a complete canonical display-name registry.
- **risk:** Any caller that lacks a backend canonical display name can still fall back to raw code, and subnational names elsewhere can reflect hub-oriented map data rather than authoritative registry names.

### `frontend/src/screens/company/CompanyGlobe.jsx`

- **reason:** Render the baseline jurisdiction through `jurisdictionName` in the company sidebar/preview.
- **expected:** YES.
- **unexpected:** None within the bounded diff.
- **risk:** Fallback remains raw code when the geographic map lacks an entry.

### `frontend/src/screens/production/Overview.jsx`

- **reason:** Read `facts.answers.financing_cost_usd` and pass it plus the refetch callback to `BudgetRail`.
- **expected:** YES.
- **unexpected:** NONE.
- **risk:** Only the upstream finance semantics apply. No Globe, hover, scenario-composition, below-Globe-card, or scroll change occurred.

### `frontend/src/screens/production/Settings.jsx`

- **reason:** Humanize the baseline-jurisdiction field.
- **expected:** YES.
- **unexpected:** None.
- **risk:** Raw-code fallback for an unmapped code.

### `frontend/src/shell/Inspector.jsx`

- **reason:** Humanize direct jurisdiction fields in account cross-reference, assignment routing, and jurisdiction title.
- **expected:** YES.
- **unexpected:** `structureLabel` remains rendered verbatim in cross-reference rows and allocation-segment eyebrows.
- **risk:** Producer-visible backend labels still expose strings such as `Full relocation to CA-MB`, `US anchor — post routed to CA-MB`, and combined labels containing `ca_federal_cptc + on_ofttc`.

### `frontend/tests/producer-display-names-and-budget-assumptions.test.mjs`

- **reason:** Static assertions for direct display-name helpers, finance wiring, and removal of local-only adjustment controls.
- **expected:** YES as source-level regression checks.
- **unexpected:** They do not render affected screens, call the API, create a new project, inspect backend-authored labels, or prove refresh behavior.
- **risk:** The tests can pass while producer-visible raw structure/program identifiers and future-project propagation remain unverified.

`git diff --check e4e70a0..bb4b6a2` was clean. No broad test suite was run, as required by the audit scope.

## FINANCE ASSUMPTION TRACE

**source-budget finance classification:**
Still defective. Lips accounts `6500 FINANCING FEES` ($450,000), `6600 BRIDGE` ($250,000), and `6700 BANKING FEE` ($1,000,000) remain BTL / `misc` / QPE-candidate lines. The current classifier patterns still do not match these exact department descriptions.

**producer financing assumption:**
`facts.answers.financing_cost_usd` → `POST /projects/{id}/assumptions` → whitelisted `ProjectFact` with `USER_OVERRIDE` source → `_fact_float` → `ProjectEconomicInputs.financing_cost_usd` → `_compute_fingerprint` → `_price_candidate` and `_price_component_relocation_candidate` → `price_allocated_structure` → persisted `StructureCalculationResult.true_net_cost_usd` and the production-view `npc_with_adjustments_usd` → UI rendering.

**separate concepts:**
YES in storage and calculation routing. The assumption does not rewrite a budget line, gross budget, or QPE register. They are not sufficiently separated in producer meaning or validation.

**double-count risk:**
YES. Gross budget already contains Lips' $1.7M source finance lines. If the producer enters that same $1.7M as `financing_cost_usd`, the formula adds another $1.7M to NPC. There is no deduplication, exclusion, source-reference, or “incremental/off-budget only” contract.

**persistence:**
Generic `ProjectFact`, fact key `financing_cost_usd`, `USER_OVERRIDE` precedence. Lips currently has no persisted value; current input is `None`.

**fingerprint:**
Included directly in the deterministic JSON payload. Sorted budget lines, outside-account sets, role codes, script facts, and co-production facts remain stable. `None` and explicit `0` intentionally produce different fingerprints even though pricing is equal; changing a value changes the fingerprint; restoring the identical prior value reconstructs the identical prior fingerprint and reuses that row set. No unrelated nondeterminism was found in `_compute_fingerprint`.

**pricing:**
Passed to both full/normal candidates and component relocations. In `allocation_pricing.price_allocated_structure`:

`npc_verified = gross_budget - selected_incentive + financing_cost + implementation_cost`

`npc_with_adjustments = npc_verified + travel + FX + in-kind replacement + local-cost deltas`

**QPE effect:**
NONE from the producer assumption. The source budget finance lines separately and incorrectly remain QPE candidates.

**NPC effect:**
Dollar-for-dollar addition to every priced candidate's verified and adjusted NPC.

**read-path side effects:**
SIDE EFFECT FOUND. Both `build_production_and_structures` and `build_project_workspace_view` call `build_project_economic_inputs` on read. That builder can call `ensure_current_budget_routed` when no `BudgetDocument` exists and `_resolve_home_jurisdiction`, which can set `Project.home_jurisdiction_id`, insert/update a `ProjectFact`, commit, and refresh.

**classification:**
PARTIALLY RESOLVED for implementation; PRE-EXISTING CURRENT DEFECT / CLASSIFICATION for source finance; REQUIRES PRODUCT/ECONOMIC DOCTRINE DECISION / CALCULATION for incremental-vs-in-budget semantics; NEW REGRESSION IN `bb4b6a2` / PERSISTENCE for GET-side mutation.

## PRIOR CODEX FINDINGS RECONCILIATION

| ID | PRIOR FINDING | CURRENT STATUS | DOMAIN | EVIDENCE | ROOT CAUSE | bb4b6a2 EFFECT | NEXT ACTION |
|---|---|---|---|---|---|---|---|
| 1 | Six Lips ATL departments totaling $3,174,975 classified below the line | PRE-EXISTING CURRENT DEFECT | CLASSIFICATION | Current normalized totals report ATL $0. Departments 1100/1200/1300/1400/1500/1900 total $3,174,975 but resolve BTL. | Classifier matches line/department text incompletely; travel and fringes are forced BTL and top-sheet labels do not match ATL patterns. | None. | Repair generic top-sheet/department classification, then reparse and recompute. |
| 1B | $1.7M finance/bridge/banking lines classified misc and admitted to QPE | PRE-EXISTING CURRENT DEFECT | CLASSIFICATION | Accounts 6500/6600/6700 remain BTL, `misc`, QPE candidates; open-default QPE includes them. | Current finance regexes do not match the actual source descriptions. | New producer assumption is separate and does not fix source lines. | Classify source finance and explicitly exclude/apportion under program rules. |
| 1C | Residuals Reserve classified as contingency with true contingency | PRE-EXISTING CURRENT DEFECT | CLASSIFICATION | Account 6800 $400,000 and account 7100 $400,000 both map to `contingency`; both are excluded in the open-default register. | “Reserve” semantics collapse residual reserve into contingency. | None. | Add residual-reserve classification and reparse/recompute. |
| 1D | Classification-only corrected control approximately $9,883,654 versus $11,183,654 | VERIFIED CURRENT DEFECT | CALCULATION | Excluding $1.7M finance while retaining residual reserve outside contingency produces $9,883,654 under the engine's generic category semantics. | Defective normalized categories feed open-default inclusion. | None. | Use only as a reconciliation control; do not call it legal QPE. |
| 2A | Stored `budget-1.0.0` parse is stale versus current `budget-1.2.0` | STALE PERSISTED RESULT | PERSISTENCE | Lips BudgetDocument remains parser `budget-1.0.0`; current parser constant is `budget-1.2.0`. | No migration/reparse of the persisted document. | None. | Reparse after classifier repair, preserve provenance, recompute. |
| 2B | Current-engine result selected by unordered `limit(1)` among multiple fingerprints | RESOLVED BY bb4b6a2 | FINGERPRINT/CACHE | Both production and workspace views now reconstruct the current input fingerprint and query exact engine+fingerprint rows. Restore-to-prior-value selects the earlier matching fingerprint deterministically. | Prior view guessed current state from an unordered result row. | Corrected. | Keep, but extract a genuinely read-only fingerprint-input path. |
| 2C | Persisted leading structure can reference a superseded fingerprint | PRE-EXISTING CURRENT DEFECT | PERSISTENCE | Lips current fingerprint is `ff1de830…`; `Project.leading_structure_id` points to SA structure `621e7321…` whose latest result is fingerprint `c04e5df…`. Project summary reads that row; current production structures do not. | `_summarize_evaluation` preserves any leading structure whose latest result merely has current engine version, not current fingerprint. | Current production view no longer uses it to select rows, limiting impact; pointer remains stale. | Reconcile explicit manual-leading semantics with fingerprint freshness; never silently use a superseded row in summaries. |
| 3 | Manitoba credit applies to almost all spend instead of Manitoba labour | PRE-EXISTING CURRENT DEFECT | CALCULATION | Current LIPS QPE $11,183,654 × 45% = $5,032,644.30. Repository inventory describes 45% base on Manitoba labour. | No Manitoba labour spend rule; open-default inclusion treats all eligible-looking lines as QPE. | None. | Implement canonical labour-base derivation and acceptance trace. |
| 4 | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` Manitoba program still priced | PRE-EXISTING CURRENT DEFECT | AUTHORITY | Coverage state is unresolved/non-priceable, but `BLOCKING_STATES` omits it; candidate is `PRICED`, qualification `RULE_DATA_INCOMPLETE`, with deterministic incentive/NPC. | Registry marks the state non-blocking despite `PROJECT_RULES.md` final authority gate. | None. | Make authority disposition a fail-closed priceability gate; invalidate/recompute affected rows. |
| 5 | Ontario labour-base modeling | PRE-EXISTING CURRENT DEFECT | CALCULATION | OFTTC and OCASE use $11,183,654 all-spend. CPTC uses 60% × $11,983,654 gross as a conservative surrogate, not actual labour. | Missing program-specific labour base and actual labour allocation. | None. | Implement program bases; recompute. |
| 5B | CPTC/OFTTC assistance reduction | CORRECT CURRENT BEHAVIOR | STACKING | Modeled OFTTC $3,914,278.90 reduces modeled CPTC base, producing CPTC $818,978.38 and combined $4,733,257.28. | Existing government-assistance adjustment operates on the modeled surrogate bases. | Unchanged. | Retain algorithm; rerun against corrected bases. |
| 6A | Multi-program enumeration and mutual exclusions | PRE-EXISTING CURRENT DEFECT | STACKING | CPTC+OPSTC, OPSTC+OFTTC, and triple combinations are emitted although calculation zeroes mutually exclusive members. | Enumerator emits invalid combinations; calculation later suppresses benefits rather than rejecting structures. | None. | Filter/mark invalid combinations before served structure creation. |
| 6B | Multi-program structures serve `segments=[]` and QPE $0 | PRE-EXISTING CURRENT DEFECT | PRESENTATION | Ontario combined rows carry incentive/NPC but empty segments and `total_qualifying_spend_usd=0`. | Stack result is not projected into canonical segment/QPE schema. | None. | Emit program-result/segment trace consistent with the calculated stack. |
| 7 | Chile base/rate/cap/conditions conflict | PRE-EXISTING CURRENT DEFECT | CALCULATION | Requirements record says 30% base, 40% outside Santiago, $3M cap, competitive/preapproval. Runtime resolves lone 40% ceiling as floor and pays 40%; dollar cap and qualification conditions are not consumed. | `resolve_program_rate` promotes a lone ceiling to floor; requirements/cap are metadata outside pricing gates. | None. | Correct tier semantics, consume cap and eligibility conditions, then recompute. |
| 8 | Dollar caps metadata-only | PRE-EXISTING CURRENT DEFECT | CALCULATION | Canonical pricing consumes percentage `QPE_CAP_RULES` but not doctrine `annual_cap_usd` or requirements `per_project_cap_usd`. Cyprus prices $3,914,278.90 despite a $741,340.57 doctrine cap; at least $3,172,938.33 overstated if that canonical field is the applicable production cap. Fiji also exceeds its stored cap. | Cap metadata is disconnected from `price_segment`/allocation pricing. | None. | Define cap precedence/scope and enforce it with trace. |
| 9 | Program requirement fields do not gate deterministic pricing | PRE-EXISTING CURRENT DEFECT | ELIGIBILITY | Saudi local-entity/preapproval/competitive/minimum-shoot requirements and Chile preapproval/competitive/regional conditions do not block deterministic values. Manitoba lacks complete rule data but prices. | `recommendation_confidence` consumes requirements for confidence, not eligibility; rate gates support only a small subset of conditions. | None. | Create a canonical hard/conditional gate bridge before pricing. |
| 10 | Conditional grants/funds do not enter deterministic NPC/ranking | CORRECT CURRENT BEHAVIOR | CONDITIONAL ECONOMICS | `conditional_programs.py` explicitly forbids invented awards and `enters_npc=False`; Manitoba grant is competitive and value is not earned. | Intentional fail-safe design. | None. | Preserve deterministic exclusion. |
| 10B | Manitoba grant conditional scenario/opportunity consumption | PARTIALLY RESOLVED | CONDITIONAL ECONOMICS | Manitoba grant node and compatibility metadata attach, including a $550,000 cap, but no numeric award is invented. Backend serves conditional metadata; no distinct valued scenario is justified without award facts. | Conditional node is the designed opportunity representation; producer presentation is disconnected. | None. | Present the conditional node and requirements. A separately valued scenario requires explicit product/economic doctrine. |
| 11 | Manitoba receives Saskatchewan and PEI conditional nodes | PRE-EXISTING CURRENT DEFECT | CONDITIONAL ECONOMICS | CA-MB candidate attaches CA-SK, Canadian-national, CA-PE, and CA-MB nodes. Even the exact CA-MB node gets a sub-territory-allocation warning. | Parent-country fallback is applied too broadly; exact subnational match is not privileged. | None. | Scope subnational nodes exactly, then add parent/national nodes only under explicit compatibility rules. |
| 12A | Reinvestment implemented but not consumed | PARTIALLY RESOLVED | CONDITIONAL ECONOMICS | `_opportunities_for_candidate` calls reinvestment discovery only for a successfully priced home candidate; opportunity metadata does not affect QPE/NPC. Lips' US home candidate is not priceable, so its current opportunities list is empty. | Reinvestment exists as non-economic opportunity metadata, not a producer fact or priced adjustment. | Fake local input removed, correctly. | Decide whether a persisted input and economic model are required; otherwise preserve metadata-only behavior. |
| 12B | In-kind pricing receives hardcoded zero | PRE-EXISTING CURRENT DEFECT | CONDITIONAL ECONOMICS | Both generic candidate paths still pass `inkind_replacement_delta_usd=0.0`; no generic producer fact feeds it. | Generic in-kind qualification/replacement doctrine is absent. | Fake edit removed; LU-only real amount is read-only. | Doctrine decision before any persisted input or pricing consumption. |
| 13 | Cultural qualification only partially gates program eligibility | PARTIALLY RESOLVED | ELIGIBILITY | Role/cultural bridge runs; `HARD_FAIL` blocks; unresolved states may be priced for disclosure but cannot enter Recommended. Other program requirements remain outside this gate. | Cultural bridge is narrower than full program-eligibility model. | None. | Preserve disclosure/Recommended split; connect complete canonical program gates. |
| 14 | Conditional opportunities preserved without uncertain economics in Recommended | CORRECT CURRENT BEHAVIOR | CONDITIONAL ECONOMICS | Conditional nodes are annotated and excluded from NPC/rank. | Intentional uncertainty safety. | None. | Keep numeric exclusion. |
| 14B | Conditional opportunities not producer-presented | PRE-EXISTING CURRENT DEFECT | PRESENTATION | Backend returns `conditional_programs` and `conditional_compatibility`; active frontend has no consumer for those payload fields. | Served metadata is disconnected from UI. | None. | Add producer presentation after attachment scoping is corrected. |

## CURRENT LIPS ECONOMICS

**Source budget:**
$11,983,654, file `v7LLS_RevBudget_T1B_27days_022524.pdf`, 46 persisted budget lines. Persisted leaf sum equals the declared gross total.

**Current normalized classification:**

| Normalized grouping | Current amount |
|---|---:|
| ATL | $0 |
| BTL | $10,264,325 |
| POST | $813,329 |
| OTHER | $906,000 |

Material spend-category totals include `misc` $7,493,682, payroll/fringes $1,278,406, contingency $800,000, locations/set $808,296, transportation $547,205, post $439,968, music $206,774, sound $126,587, insurance $106,000, crew labour $76,175, travel $60,561, and VFX $40,000.

**Current generic economic/QPE input:**
$11,183,654 for open-default programs because both $400,000 reserve-labelled lines are excluded as contingency while the $1.7M finance lines remain included. The approximately $9,883,654 classification-only control excludes finance but restores residual reserve as non-contingency. Neither number is asserted as final jurisdictionally qualified QPE.

**Finance lines:**

| Account | Description | Amount | Current classification | Current generic effect |
|---|---|---:|---|---|
| 6500 | FINANCING FEES | $450,000 | BTL / misc | QPE candidate |
| 6600 | BRIDGE | $250,000 | BTL / misc | QPE candidate |
| 6700 | BANKING FEE | $1,000,000 | BTL / misc | QPE candidate |

**Residual reserve:**
Account 6800, $400,000, currently OTHER / contingency and excluded with contingency.

**Contingency:**
Account 7100, $400,000, currently OTHER / contingency. No current persisted expected-utilization fact was present in the audited runtime state.

**Parser version:**
Persisted `budget-1.0.0`; current code `budget-1.2.0`. Current classifier code still misses the displayed top-sheet/finance descriptions, so a version-only reparse before classifier repair would not cure the material errors.

**Persisted evaluation version/fingerprint:**
Current engine `canonical-1.41.0`. Current input fingerprint `ff1de8307900f1e7efcd93241de9ddde7c18ce7aa523df5a80e399536ac55cbe`, with 168 rows. Other retained current-engine fingerprints are `23b086…`, `540e8…`, and `c04e5d…`, each with 168 rows. Older `canonical-1.39.0` and `canonical-1.40.0` row sets remain for provenance. Current production/workspace views select exact `ff1de830…` rows. Persisted `leading_structure_id` still references an SA row at `c04e5d…`.

**Top Six current state:**
These are the six cheapest currently priced structures, not six rank-eligible Recommendations. Rank fields are null and relocation candidates are `PRICED_LOW_FIT` because directly comparable relocation costs are not normalized.

| Order | Structure | Incentive | NPC | Served QPE note | Qualification state |
|---:|---|---:|---:|---|---|
| 1 | Full relocation to SA | $6,710,192.40 | $5,273,461.60 | $11,183,654 segment QPE | NOT_APPLICABLE |
| 2 | Full relocation to CA-MB | $5,032,644.30 | $6,951,009.70 | $11,183,654 segment QPE | RULE_DATA_INCOMPLETE |
| 3 | CA-ON CPTC + OFTTC combined | $4,733,257.28 | $7,250,396.72 | `segments=[]`; top-level QPE $0 | Incomplete program gating |
| 4 | Full relocation to BE | $4,697,134.68 | $7,286,519.32 | Open-default basis | Unresolved/conditional facts vary by trace |
| 5 | Full relocation to CA-NL | $4,473,461.60 | $7,510,192.40 | Open-default basis | Incomplete program gating |
| 6 | Full relocation to CL | $4,473,461.60 | $7,510,192.40 | $11,183,654 at erroneous 40% | NOT_APPLICABLE despite stored requirements |

## MANITOBA

**labour base:**
Defective. Repository inventory says 45% base on Manitoba labour; runtime applies 45% to $11,183,654 open-default spend. The 65% tier is treated as a ceiling requiring confirmation, so selecting the 45% base rather than the ceiling is safe, but the base itself is wrong.

**authority disposition:**
`AUTHORITY_UNRESOLVED_NON_PRICEABLE`.

**deterministic pricing:**
Still allowed: $5,032,644.30 incentive and $6,951,009.70 NPC, candidate status `PRICED`, qualification `RULE_DATA_INCOMPLETE`. This contradicts the final authority gate in `PROJECT_RULES.md` because the state is omitted from `authority_coverage_registry.BLOCKING_STATES` and is described as non-blocking.

**grant attachment:**
The Manitoba candidate receives Saskatchewan, national Canadian, PEI, and Manitoba conditional nodes. Exact-subnational matching is defective.

**grant conditional consumption:**
The specific Manitoba film/music support grant is represented as competitive/discretionary, cap $550,000, stacking unknown, `enters_npc=false`. That numeric exclusion is safe. Metadata is served but not presented in the active frontend.

**classification:**
PRE-EXISTING CURRENT DEFECT / CALCULATION for labour base; PRE-EXISTING CURRENT DEFECT / AUTHORITY for deterministic pricing; PRE-EXISTING CURRENT DEFECT / CONDITIONAL ECONOMICS for attachment; CORRECT CURRENT BEHAVIOR for not inventing a grant award.

## ONTARIO

**labour base:**
Missing for the relevant labour-based calculations.

**CPTC base:**
60% × total worldwide gross budget: 60% × $11,983,654, producing raw CPTC $1,797,548.10 at 25%. This is an explicit conservative surrogate, not actual qualifying labour.

**OFTTC base:**
All-spend $11,183,654 × 35% = $3,914,278.90. OCASE similarly uses all spend at 18%, $2,013,057.72.

**assistance reduction:**
Correct relative to the flawed modeled bases. OFTTC assistance of $3,914,278.90 reduces the CPTC base; at 25% this reduces CPTC by $978,569.73 to $818,978.38. Combined incentive is $4,733,257.28.

**multi-program enumeration:**
ACTIVE.

**mutual exclusions:**
Calculation avoids double counting by zeroing mutually exclusive members, but still emits CPTC+OPSTC, OPSTC+OFTTC, and triple structures with violation traces. Structure enumeration/presentation is defective even where arithmetic suppression is safe.

**segments:**
Empty for combined structures.

**served QPE:**
$0 for combined structures despite non-zero incentive/NPC.

**classification:**
PRE-EXISTING CURRENT DEFECT / CALCULATION for labour bases; CORRECT CURRENT BEHAVIOR / STACKING for the assistance-reduction formula on its inputs; PRE-EXISTING CURRENT DEFECT / STACKING for invalid combination emission; PRE-EXISTING CURRENT DEFECT / PRESENTATION for empty segments/QPE.

## CHILE

**repository requirements:**
30% base; $3M production cap; 40% only for production entirely outside Santiago; competitive call and preapproval mandatory. The repository also contains a minimum-spend conflict ($2M in notes versus a $1M runtime threshold), which must be reconciled internally before canonical pricing.

**runtime rate:**
40% deterministic. The doctrine has only a `cl-ceiling-40` tier. `resolve_program_rate` uses that lone ceiling as `floor_rate`, and allocation pricing selects the resulting floor.

**cap:**
Not applied. LIPS happens to price $4,473,461.60, above the stored $3M cap.

**conditional gating:**
Outside-Santiago, competitive selection, and preapproval requirements do not block or condition the deterministic value.

**classification:**
Combination: DATA CONFLICT; RATE RESOLUTION DEFECT; CAP CONSUMPTION DEFECT; CONDITIONAL-GATING DEFECT. Primary current status: PRE-EXISTING CURRENT DEFECT / CALCULATION.

## CAPS / REQUIREMENTS / AUTHORITY

**dollar caps:**
Not consumed by canonical served pricing. `QPE_CAP_RULES` handles percentage-of-budget caps, but `DoctrineRecord.annual_cap_usd` and `ProgramRequirementsProfile.per_project_cap_usd` do not constrain the calculated incentive. Concrete priceable control: Cyprus prices $3,914,278.90 against a canonical $741,340.57 cap field; Fiji also prices above its stored $1.75M cap.

**requirements gating:**
Incomplete. `recommendation_confidence` reads local entity, preapproval, certification, audit, and related requirements for confidence disclosure, but those fields are not a comprehensive prerequisite to deterministic pricing. Rate-condition gating handles only limited condition types. Saudi prices at 60% with local-entity/preapproval/competitive/minimum-shoot conditions unconfirmed; Chile prices despite preapproval/competitive/regional conditions; Manitoba prices with rule data incomplete.

**authority gating:**
Incomplete and in direct conflict with project rules. At least `AUTHORITY_UNRESOLVED_NON_PRICEABLE` is deliberately classified as non-blocking by runtime coverage logic, allowing incentive/NPC.

**classification:**
PRE-EXISTING CURRENT DEFECT across CALCULATION, ELIGIBILITY, and AUTHORITY.

## GRANTS / FUNDS / CONDITIONALS

**deterministic safety:**
Correct. Conditional/competitive amounts are not silently treated as earned and do not enter deterministic Recommended NPC.

**conditional scenario generation:**
Conditional nodes and compatibility metadata are generated and attached rather than valued. That satisfies the current documented conditional-opportunity design. A separate grant-plus-credit structure with a numeric award is not justified until an award amount and stacking treatment are known.

**NPC consumption:**
Correctly false for unresolved conditional awards.

**ranking consumption:**
Correctly false for unresolved conditional awards.

**subnational attachment:**
Defective. Parent-country matching attaches other provinces' programs to Manitoba and fails to treat exact CA-MB participation as sufficient for the Manitoba node.

**classification:**
CORRECT CURRENT BEHAVIOR / CONDITIONAL ECONOMICS for numeric exclusion; PRE-EXISTING CURRENT DEFECT / CONDITIONAL ECONOMICS for attachment; PRE-EXISTING CURRENT DEFECT / PRESENTATION because served conditional metadata has no active frontend consumer; REQUIRES PRODUCT/ECONOMIC DOCTRINE DECISION if a separately valued conditional scenario is desired.

## CLAUDE PASS CLAIMS

**Producer display names:**
OVERSTATED. Direct fields were repaired, but known producer-visible raw backend strings remain:

- Inspector account cross-reference `c.structureLabel`.
- Inspector allocation-segment eyebrow `data.structureLabel`.
- Project Globe production-structure sidebar `s.label`.
- Qualification Assistant blocked-structure title `structure.label`.
- Any route that displays backend labels such as `Full relocation to CA-MB`, `US anchor — post routed to CA-MB`, or `CA-ON — ca_federal_cptc + on_ofttc (combined)` without `scenarioDisplay`/canonical program display metadata.

The Overview and Scenarios cards themselves generally use `scenarioDisplay` and are not the defect identified here.

**Finance persistence:**
SUPPORTED for the narrow persisted chain. The economics meaning and double-count guard are not complete, so the overall finance feature remains PARTIAL.

**No fake adjustment inputs:**
SUPPORTED. Reinvestment, local in-kind editing, manual labour normalization, and manual override inputs were removed. In-kind is rendered only when a real backend amount exists and is read-only. The remaining active economic inputs call the persisted assumptions path.

**Future project propagation:**
OVERSTATED. Generic architecture is supported; clean-slate propagation is unverified. Backend tests hardcode Little Utopia, while Lips was only a second existing runtime control. Frontend tests are static source scans.

**Protected systems unchanged:**
SUPPORTED with scope clarification. No jurisdiction authority data, program rules, parser, QPE doctrine tables, optimizer enumeration logic, project data, migrations, or Globe behavior changed in the commit. Canonical evaluation input/fingerprint/pricing plumbing and production/workspace read paths did change intentionally, and the latter introduced the side-effect defect.

## OVERVIEW DELTA

**Overview.jsx changed:**
YES.

**exact change:**
Seven added lines: read `facts.answers.financing_cost_usd`, normalize it to number/null, and pass `financingCostUsd` plus `onFinanceCostSaved={refetch}` into `BudgetRail`.

**Globe behavior changed:**
NO.

**hover changed:**
NO.

**scenario composition changed:**
NO.

**scroll architecture changed:**
NO.

**new regression:**
NO in `Overview.jsx`. The new regression is in backend read-path fingerprint reconstruction.

## REPAIR CLUSTERS

### CLUSTER 1 — Fail-closed authority and mandatory eligibility gates

- **ROOT CAUSE:** Authority dispositions and `ProgramRequirementsProfile` are confidence metadata or incomplete bridges rather than canonical prerequisites to deterministic pricing.
- **AFFECTED PIPELINE:** authority coverage → candidate eligibility → rate resolution → segment pricing → Recommendation/NPC.
- **FILES/MODULES:** `authority_coverage_registry.py`, canonical candidate discovery/evaluation, `program_requirements.py`, recommendation-confidence and role/cultural qualification bridges.
- **DOWNSTREAM IMPACT:** Manitoba, Saudi, Chile, and other unresolved/conditional programs can present deterministic economics before mandatory gates are supported.
- **RUNTIME ACCEPTANCE NEEDED:** An unresolved-non-priceable program contributes no incentive, NPC, stack, or rank; each mandatory requirement produces explicit qualified/failed/conditional trace; conditional disclosure remains visible without value.
- **RECOMPUTE/MIGRATION:** Recompute all affected current-engine structures after engine-version/fingerprint invalidation; no data migration unless authority dispositions are corrected.

### CLUSTER 2 — Canonical source-budget classification and persisted reparse

- **ROOT CAUSE:** Normalizer patterns do not recognize Lips' top-sheet ATL, finance, and residual-reserve descriptions; persisted parser version is stale.
- **AFFECTED PIPELINE:** PDF parse → BudgetLineItem categories → qualification register → QPE → incentive/NPC.
- **FILES/MODULES:** budget parser/classifier and canonical project economic-input assembly.
- **DOWNSTREAM IMPACT:** All spend-based and labour-sensitive program calculations consume the wrong base; finance can enter QPE; contingency is overstated.
- **RUNTIME ACCEPTANCE NEEDED:** Six ATL departments reconcile to $3,174,975 under defined semantics; accounts 6500/6600/6700 are finance and do not enter generic QPE by default; residual reserve is distinct from true contingency; leaf total remains $11,983,654.
- **RECOMPUTE/MIGRATION:** Reparse Lips and all documents affected by the classifier revision, retain old versions for provenance, then recompute all structures.

### CLUSTER 3 — Program-specific bases, rates, and dollar caps

- **ROOT CAUSE:** Open-default all-spend inclusion substitutes for labour bases; CPTC uses a gross-budget surrogate; lone rate ceilings become floors; dollar-cap metadata is disconnected.
- **AFFECTED PIPELINE:** normalized spend → program QPE/base → rate resolution → cap application → incentive trace.
- **FILES/MODULES:** canonical spend rules/QPE derivation, `rate_doctrine.py`/rate resolver, `allocation_pricing.py`, cap/requirements registries.
- **DOWNSTREAM IMPACT:** Manitoba and Ontario labour credits, Chile, Cyprus, Fiji, and any other capped program can be materially overstated.
- **RUNTIME ACCEPTANCE NEEDED:** Exact labour accounts and jurisdiction allocation are traceable; a ceiling cannot become a guaranteed floor; applicable dollar cap visibly clips the incentive; conflicts block rather than guess.
- **RECOMPUTE/MIGRATION:** Engine-version/fingerprint invalidation and full affected-result recompute. Canonical data changes only where existing internal records conflict.

### CLUSTER 4 — Multi-program structure validity and trace projection

- **ROOT CAUSE:** Enumeration emits mutually exclusive combinations and stack calculations are not projected into canonical segments/QPE.
- **AFFECTED PIPELINE:** program combination enumeration → compatibility/assistance → structure persistence → served segments/UI.
- **FILES/MODULES:** canonical evaluation multi-program enumeration/stacking, allocation-pricing result adapters, production view.
- **DOWNSTREAM IMPACT:** Misleading combined structures and $0 served QPE alongside non-zero incentives.
- **RUNTIME ACCEPTANCE NEEDED:** Invalid combinations are absent or explicitly non-priceable; CPTC/OFTTC adjustment remains correct on corrected bases; every priced combined structure has reconciled program and segment traces.
- **RECOMPUTE/MIGRATION:** Recompute affected stack structures; old rows may remain immutable but must not serve as current.

### CLUSTER 5 — Conditional-node territoriality and producer presentation

- **ROOT CAUSE:** Broad parent-country attachment and no frontend consumer for served conditional metadata.
- **AFFECTED PIPELINE:** conditional registry → candidate attachment → compatibility → production payload → Inspector/opportunity UI.
- **FILES/MODULES:** `conditional_programs.py`, conditional attachment/compatibility services, production-view schema, bounded producer-facing opportunity components.
- **DOWNSTREAM IMPACT:** Manitoba is shown unrelated provincial programs while its legitimate conditional support is effectively invisible.
- **RUNTIME ACCEPTANCE NEEDED:** CA-MB attaches exact Manitoba and expressly applicable national nodes, not Saskatchewan/PEI; uncertain amounts remain out of NPC/rank; producer can see requirements and unresolved stacking.
- **RECOMPUTE/MIGRATION:** Recompute conditional attachments; no monetary migration.

### CLUSTER 6 — Pure read freshness and leading-structure lineage

- **ROOT CAUSE:** GET views call write-capable input recovery; fallback can serve prior rows when current inputs cannot evaluate; leading pointer validity checks engine version but not fingerprint.
- **AFFECTED PIPELINE:** production/workspace GET → fingerprint selection → current result set; project summary → leading row.
- **FILES/MODULES:** `canonical_project_economics.py`, `canonical_production_view.py`, `project_workspace_view.py`, `canonical_evaluation._summarize_evaluation`, project-summary API.
- **DOWNSTREAM IMPACT:** Reads can mutate project state; summary metadata can reference a superseded row even while production economics are current.
- **RUNTIME ACCEPTANCE NEEDED:** Transaction snapshot proves GET produces zero inserts/updates/commits; change/revert picks the exact matching fingerprint; incomplete current inputs disclose unavailable rather than silently stale economics; manual-leading state is explicitly current, stale, or cleared.
- **RECOMPUTE/MIGRATION:** No calculation migration for read purity; stale leading pointers require safe reconciliation/backfill or explicit stale-state handling.

### CLUSTER 7 — Financing semantics, residual generic inputs, display, and propagation proof

- **ROOT CAUSE:** Finance field lacks incremental-vs-budget doctrine; in-kind/reinvestment have no complete generic input/economic contract; backend structure labels remain internal; tests do not create a clean-slate project.
- **AFFECTED PIPELINE:** producer assumptions → NPC; conditional adjustments → pricing; structure naming → UI; new-project inheritance → acceptance.
- **FILES/MODULES:** assumptions schema/API, Budget Rail, allocation-pricing caller, in-kind/reinvestment opportunity services, production-view display metadata, bounded Inspector/sidebar components, integration tests.
- **DOWNSTREAM IMPACT:** Possible finance double count, invisible/incomplete conditional tools, raw identifiers, and unsupported generic propagation claim.
- **RUNTIME ACCEPTANCE NEEDED:** Finance amount has explicit validated scope and cannot duplicate budgeted finance; negative/non-finite values fail; raw labels do not render where canonical metadata exists; a newly created title-only project persists, evaluates, refetches, and displays finance generically without project branches.
- **RECOMPUTE/MIGRATION:** Doctrine decision before finance migration. Recompute only projects with the assumption. No project should be created by this audit.

## FINAL DEFECT LEDGER

Only current open defects are listed.

| Severity | Domain | Root cause | Repair owner |
|---|---|---|---|
| P0 | AUTHORITY | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` is non-blocking and can receive deterministic incentive/NPC. | Claude |
| P0 | ELIGIBILITY | Mandatory program requirements are confidence metadata, not complete pricing gates. | Claude |
| P0 | CLASSIFICATION | Lips ATL, finance, and residual reserve are materially misclassified. | Claude + data recompute |
| P0 | CALCULATION | Manitoba and Ontario labour-based programs use all-spend/gross surrogates. | Claude |
| P0 | CALCULATION | Chile lone ceiling becomes a deterministic floor; cap and conditions are not consumed. | Claude |
| P0 | CALCULATION | Canonical dollar-cap metadata does not constrain served incentive values. | Claude |
| P1 | PERSISTENCE | Lips retains stale `budget-1.0.0` classification. | data recompute after Claude classifier repair |
| P1 | STACKING | Mutually exclusive Ontario combinations are emitted. | Claude |
| P1 | PRESENTATION | Combined structures carry incentive/NPC with empty segments and served QPE $0. | Claude |
| P1 | CONDITIONAL ECONOMICS | Parent-country matching attaches Saskatchewan/PEI nodes to Manitoba and misclassifies exact CA-MB compatibility. | Claude |
| P1 | PRESENTATION | Conditional program/compatibility metadata is not consumed by the frontend. | Claude |
| P1 | PERSISTENCE | New GET-side fingerprint reconstruction can persist budget/home-jurisdiction state. | Claude |
| P1 | PERSISTENCE | Persisted leading structure can point to a superseded current-engine fingerprint and affect project-summary metadata. | Claude |
| P1 | CALCULATION | `financing_cost_usd` can duplicate finance already inside gross budget. | doctrine decision, then Claude |
| P2 | CONDITIONAL ECONOMICS | Generic in-kind replacement remains hardcoded zero; reinvestment is metadata-only. | doctrine decision |
| P2 | PRESENTATION | Backend-authored structure labels expose raw jurisdiction codes/program slugs on bounded Inspector/sidebar surfaces. | Claude |
| P2 | PROPAGATION | Clean-slate future-project inheritance is not tested. | Claude |

The fixed unordered-current-fingerprint defect is not in this open ledger. Correct exclusion of uncertain conditional awards from deterministic NPC/ranking is not a defect.

## CODE CHANGED

NONE, except this audit report artifact.

## AUDIT HANDOFF

**AUDIT BRANCH:**
`codex/reconcile-bb4b6a2`

**AUDIT COMMIT:**
Recorded after commit in the task handoff.

**AUDIT FILE:**
`audit_reports/codex_reconciliation_bb4b6a2.md`

**BASE COMMIT:**
`bb4b6a25317e398be628c70a0c6899bff2fd8e44`

**FILES CHANGED:**
`audit_reports/codex_reconciliation_bb4b6a2.md`

only.

## FINAL GATE

**RECONCILIATION_COMPLETE:**
PASS

**STABLE_COMMIT_AUDITED:**
PASS

**PRIOR_CODEX_FINDINGS_RECONCILED:**
PASS

**CLAUDE_DELTA_RECONCILED:**
PASS

**CURRENT_DEFECT_LEDGER_COMPLETE:**
PASS

**PRODUCTION_CODE_CHANGED:**
NO

**AUDIT_ARTIFACT_AVAILABLE:**
PASS
