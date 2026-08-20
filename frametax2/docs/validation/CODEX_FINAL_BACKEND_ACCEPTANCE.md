# CineGlobe Final Backend Knowledge + Optimizer Correctness Acceptance

**Baseline:** `8ccf30a2cf9f983473898277c18811a0f27bf693`

**Audit date:** 2026-08-19

**Mode:** independent read-only technical/correctness audit

**Decision:** `ONE_CONSOLIDATED_CORRECTION_PASS_REQUIRED`

## Executive conclusion

The current project-scoped UI reads a genuine canonical evaluation result, and the LU/FVD control NPCs reproduce. The backend is not acceptance-safe for an arbitrary newly ingested production, however. Its newly connected qualification knowledge is mostly a post-pricing disclosure: a candidate is priced, admitted to stacking, persisted as `PRICED`, categorized, and ranked without its `role_qualification` state governing any of those decisions. The rate resolver separately selects tiers while leaving material certification, cultural-test, narrower-base, total-budget, and other conditions unresolved. This permits unresolved or ineligible economics to appear as valid priced economics and permits a home-jurisdiction candidate to become `RECOMMENDED`.

The point-table path can also create a false `QUALIFIES` result from unrelated Script Analyzer facts. The canonical cache omits the same personnel, script, co-production, and rule-registry inputs that now affect the trace. Live alternate 0.1.0/legacy APIs remain mounted. These are correctness and served-lineage defects, not documentation polish.

## Evidence and controls

- Repository/branch and local/remote baseline were verified at the requested commit before the audit.
- Targeted runtime controls passed: LU canonical NPC `$3,057,794.90`; FVD canonical NPC `$3,072,027.16` (`3 passed in 3.64s`). These values are regression observations, not an endorsement of the LU contingency assumption.
- No external research was required. All findings use current runtime/code/data evidence at the baseline.
- No production code or canonical data was changed.

## Audit gates

| Audit | Verdict | Finding |
|---|---|---|
| 1. Served lineage | **ENGINE_WIRING_DEFECT** | The project-scoped UI uses `GET /api/v1/cineglobe/projects/{id}/state` and canonical persisted results, but mounted legacy calculation, optimization, and Little-Utopia-only endpoints remain reachable. |
| 2. Canonical consumption | **DEFECT** | `role_qualification` is computed after pricing and stored as disclosure only. It is not an admission, stacking, component, or ranking input. “Completed doctrine disconnected = 0” is not proven and is false in the decision-consumption sense. |
| 3. Cultural point-table safety | **DEFECT** | No completeness/headroom state exists in the table schema, several tables are aggregates/approximations, and any fact of a mapped script type satisfies every criterion of that type without semantic matching. |
| 4. Qualification ontology | **DEFECT** | PSTC and CPTC are separate records/rates, but the execution layer misclassifies PSTC and does not enforce CPTC’s points/base/certification mechanics. Program qualification and economics are therefore not safely separated at admission. |
| 5. Fact classification | **DEFECT** | Missing authority and missing facts have distinct labels, but 46 explicit no-cultural-test profiles emit `RULE_DATA_INCOMPLETE`; nationality and residency are merged; invalid boolean text becomes false. |
| 6. Co-production safety | **PARTIAL / DEFECT** | The bilateral adapter fails closed on absent shares/cultural result. Canonical inputs are global rather than route/party-specific, competent-authority approval is absent, and additional represented routes are not candidate-consumed. |
| 7. Multilateral frameworks | **DEFECT** | Eurimages is represented as a framework and unpriced opportunity, but European Convention and Ibermedia have no canonical adapter/generation path. Eurimages never receives country-share facts from canonical evaluation. |
| 8. Economic isolation | **PARTIAL / DEFECT** | Qualification/treaty code does not itself calculate QPE/NPC, which is correct. But economics is calculated before and independently of qualification admission, and narrower statutory bases are priced against total QPE. |
| 9. Ranking/admission | **DEFECT** | Ranking/category logic checks priceability/comparability/treaty signals only. It ignores `HARD_FAIL`, `USER_FACT_REQUIRED`, `SCRIPT_FACT_REQUIRED`, `AUTHORITY_UNRESOLVED`, and `RULE_DATA_INCOMPLETE`. |
| 10. Data durability/provenance | **DATA_DURABILITY_DEFECT** | Structured registries exist and are runtime-consumed, but provenance is incomplete and several point/treaty facts are secondary, aggregate, approximated, or disconnected. |
| 11. Database as runtime source | **VERIFIED WITH ARCHITECTURAL CAVEAT** | Ordinary evaluation performs no live web research. Runtime knowledge comes from checked-in Python registries plus the project database; web is maintenance-only. The registries are not one database/versioned snapshot. |
| 12. Project-specific contamination | **DEFECT** | The canonical evaluator has no title/ID conditional, but Little-Utopia-only in-memory endpoints and old generic engines remain live and mounted. Company/no-project calls still take the LU path. |
| 13. Contingency | **DEFECT** | Generic Mauritius hard-codes the full reserve as qualifying before expected deployment; this bypasses the intended projected expected-spend path. |
| 14. LU/FVD runtime | **CONTROL PASS** | Both current values reproduce. LU remains contingent on the known reserve-treatment defect. |
| 15. Deferred UI | **PRESERVED** | The required Inspector/sidebar closeout remains explicitly recorded in the capability ledger; it is not implemented by this audit. |

## 1. Served lineage

The principal current path is:

`frontend/src/api.js::getProjectState` → `backend/app/api/v1/cineglobe.py::get_project_state` → `backend/app/services/canonical_production_view.py::build_production_and_structures` → persisted `StructureCalculationResult` rows produced by `backend/app/services/canonical_evaluation.py::evaluate_project` → API payload → UI rendering.

The canonical evaluation entry is `POST /api/v1/projects/{id}/evaluation/begin` in `backend/app/api/v1/evaluation.py`, which calls `canonical_evaluation.evaluate_project()`.

Alternate live paths:

1. `backend/app/main.py:40` mounts `backend/app/api/v1/structures.py`. `POST /projects/{project_id}/structures/{structure_id}/calculate` calls `calculate_structure_impl()` and imports `run_full_analysis`, the superseded 0.1.0 engine. It persists results into the same production result domain.
2. `backend/app/main.py:41` mounts `backend/app/api/v1/optimization.py`, exposing separate `/optimization/gap-analysis`, `/recommendations`, `/generate-structures`, and `/maximize` engines that do not use the canonical evaluator/project knowledge path.
3. `backend/app/main.py:42` mounts unparameterized `/cineglobe/*` endpoints backed by `app.demo.little_utopia_state.get_state()`. `frontend/src/lib/useCineGlobe.js` still invokes those eight endpoints when no project ID is supplied; the legacy production redirect also uses the unparameterized production endpoint.
4. `canonical_production_view.build_production_and_structures()` follows the engine version stored on the project’s leading result instead of requiring current `ENGINE_VERSION`, so GET can continue serving an old generation until an explicit evaluation occurs.

## 2. Canonical consumption and admission

The decisive ordering is in `backend/app/services/canonical_evaluation.py`:

- candidate economics are priced at line 1060;
- opportunities and role/cultural qualification are evaluated at lines 1112–1113;
- the result is persisted with `candidate_status=PRICED` at lines 1151–1262;
- the source comment at lines 1255–1259 explicitly calls `role_qualification` “disclosure only” and “never a pricing/admission gate.”

The candidate is added to `priced_by_code` before persistence and qualification admission. Multi-program stacks (lines 1265–1415) consume those priced candidates without propagating or rechecking their qualification state. Component candidates (lines 1417–1573) do the same. `canonical_production_view._scenario_category()` and the ranking loops use `is_fully_priced`, direct comparability, treaty presence, and rank; neither reads `role_qualification`.

Consequently, all unresolved qualification states can remain `PRICED`; any such home candidate is directly comparable and can become rank 1/`RECOMMENDED`.

## 3. Cultural point-table inventory and safety

The schema in `backend/app/data/cultural_point_tables.py` has no field for `COMPLETE`, `PARTIAL_WITH_KNOWN_HEADROOM`, `PARTIAL_WITH_UNKNOWN_HEADROOM`, or `AUTHORITY_INCOMPLETE`. The evaluator infers numeric headroom from `total_points - sum(max_points)` but cannot distinguish a complete table from an aggregate approximation or unknown category allocation.

| Program | Declared / modeled / threshold | Required classification at this baseline | Reason |
|---|---:|---|---|
| `at_fisa_plus` | 80 / 34 / 40 | `PARTIAL_WITH_KNOWN_HEADROOM` | 46 official points are unitemized. |
| `cz_film_incentive` | 46 / 36 / 23 | `PARTIAL_WITH_KNOWN_HEADROOM` | 10 points are unitemized. |
| `fr_trip` | 38 / 37 / 18 | `PARTIAL_WITH_KNOWN_HEADROOM` | 1 point is unitemized. |
| `no_film_incentive` | 51 / 51 / 20 | `COMPLETE` | Itemized official table and sub-threshold are represented. |
| `my_finas_rebate` | 5 / 5 / optional | `COMPLETE` | Complete optional uplift table; not a base pass/fail gate. |
| `pl_pisf_cash_rebate` | 48 / 48 / 25 | `AUTHORITY_INCOMPLETE` | Four 12-point allocations are acknowledged approximations pending the official appendix. |
| `pt_scri_pt_cash_rebate` | 100 / 100 / 45 | `AUTHORITY_INCOMPLETE` | Only 60/40 aggregates are represented; a separate foreign-initiative 20/8 route is known but not selected/evaluated. |
| `gr_cash_rebate` | 50 / 50 / 20 | `AUTHORITY_INCOMPLETE` | One 50-point aggregate built from secondary sources; no criteria. |
| `hr_cash_rebate` | 34 / 34 / 12 | `AUTHORITY_INCOMPLETE` | One aggregate; category floors and allocations are not executable. |
| `hu_hipa_rebate` | unknown / 16 / 16 | `AUTHORITY_INCOMPLETE` | Unknown statutory maximum and one aggregate. |
| `it_tax_credit_foreign` | unknown / 50 / 50 | `AUTHORITY_INCOMPLETE` | Unknown statutory maximum and one aggregate. |
| `lt_film_centre_cash_rebate` | 8 / 8 / 2 | `AUTHORITY_INCOMPLETE` | Eight criteria collapsed into one all-or-nothing aggregate. |
| `mt_mfc_rebate` | 40 / 40 / 40 | `AUTHORITY_INCOMPLETE` | The general test is collapsed into one all-or-nothing aggregate. |

The false-qualification defect is independent of headroom. In `evaluate_point_table_qualification()` lines 316–321, a script criterion is satisfied when *any* extracted element exists for a broad mapped type. There is no semantic comparison with the jurisdiction or criterion. A direct execution with Tokyo location, US character nationality, and English language makes `fr_trip` return `QUALIFIES`, 18/18, crediting French locations, French characters/themes, and French language criteria. This is a demonstrated false positive.

Role criteria require only exact home-code membership and cannot implement EEA/CoE/treaty groups described by several tables. Format/route variants are not selected. Aggregate rows cannot be partially scored. These defects mean the current tables are not safe admission evidence.

## 4. Qualification ontology and Canada control

The data layer correctly creates separate programs:

- `ca_federal_pstc`: 16% service credit, no cultural test.
- `ca_federal_cptc`: 25% Canadian-content credit, CAVCO/cultural requirement.

Execution does not preserve that correctness:

- With empty facts, PSTC returns `RULE_DATA_INCOMPLETE` rather than `NOT_APPLICABLE`, despite `program_requirements.py` recording `cultural_test_required=False`.
- CPTC’s modeled role gates are not the full 6/10 points test. A direct execution with US director, Canadian writer/producer/one lead returns `QUALIFIES`, although those known point-bearing facts supply at most 3/10 and do not establish the 6/10 test.
- `program_rate_rules_worldwide.py` states CPTC is 25% of qualified Canadian labour, capped at 60% of net production cost. The rate resolver applies 25% to total QPE. Calling that “conservative” is mathematically incorrect: applying a rate to a superset of the statutory base can overstate the credit.

The same rate-condition defect is generic. Across the registered rules, 64 conditions in 15 unhandled `kind` values fall into `satisfied=None` but do not block tier selection. They include ten `cultural_test_required`, three `project_fact_dependent_eligibility`, three `rate_base_narrower_than_qpe`, seven `min_spend_pct_of_total_budget`, and material cap/exclusivity/funding-risk conditions. A non-band tier with such a condition remains executable and priced.

## 5. Fact classification

The vocabulary itself is useful, but runtime classification is not coherent across the 71-program universe. With empty project facts, direct execution emits:

- `RULE_DATA_INCOMPLETE`: 46
- `USER_FACT_REQUIRED`: 10
- `NOT_APPLICABLE`: 5
- `SCRIPT_FACT_REQUIRED`: 3
- `CURABLE_GAP`: 3
- `AUTHORITY_UNRESOLVED`: 3
- `QUALIFIES`: 1

The 46 rule-data results are profiles explicitly marked `cultural_test_required=False`. `_SPEND_ONLY_SLUGS` contains only Australia Location Offset and NZ international rebate. The “disconnected=0” test skips every profile where `cultural_test_required is False`, so it does not test the state the served bridge actually returns for those programs.

`role_known_codes_from_project()` merges `TalentProfile.primary_nationality` and `known_residencies` into one untyped code set. Downstream gates then treat either as satisfying the same identity rule. Nationality, residence, domicile, work location, and eligible labour status must remain typed facts.

`_coproduction_facts._bool()` returns `False` for any non-empty value other than true/1/yes. Invalid or “unknown” input therefore becomes a confirmed failed cultural test rather than unresolved input.

## 6–7. Co-production and multilateral safety

The bilateral bridge is correctly fail-closed for missing shares and an unresolved cultural result. It persists unpriced `CO_PRO_OPPORTUNITY` rows and does not inject treaty incentive economics. That limited behavior is safe.

Coverage is not complete or canonical enough for acceptance:

- `canonical_treaty_bridge.py` exposes only bilateral and Eurimages adapters/discovery helpers. European Convention and Ibermedia exist only in `treaty_engine.py`; they are never generated by `canonical_evaluation.py`.
- The eight additional represented bilateral routes in national-status data are not in the canonical candidate discovery used by the bridge.
- One global majority percentage, minority percentage, and cultural boolean is applied to every bilateral candidate. Facts are not bound to a partner, producer, contribution basis, ownership basis, or route.
- No competent-authority approval/certification fact is modeled.
- Eurimages evaluation is called without `country_pcts`, even though that is its required economic participation input, so it cannot resolve beyond opportunity status.
- Static treaty rows lack durable structured authority/version/effective-date/competent-authority provenance.
- Treaty candidates are arbitrarily truncated to five bilateral partners and ten displayed Eurimages members. This can hide relevant routes from a newly ingested production.

Route exists, route term unknown, route absent, and route qualified remain distinct in the bilateral wrapper; the claimed global framework/route coverage does not reach that wrapper.

## 8–9. Economics, ranking, and scenario categories

The canonical qualification/treaty modules do not independently calculate QPE, incentive, NPC, or stack economics. That isolation is structurally correct. The defect is ordering/admission: pricing occurs first and qualification cannot veto it.

`resolve_program_rate()` selects the highest tier using only production type and `min_qpe_usd`. Every other condition is merely serialized. `price_segment()` blocks an unresolved condition only when the selected tier is a discretionary band ceiling, and then only selects the floor rather than rejecting base-program eligibility. Non-band cultural/certification/base conditions do not block pricing.

The five scenario category constants exist and are wired:

`RECOMMENDED`, `ALTERNATIVE`, `CO_PRO_OPPORTUNITIES`, `PRICED_LOW_FIT`, `NOT_AVAILABLE`.

Their mapper ignores qualification state. Thus the labels are present but not semantically supportable for all candidates. `USER_FACT_REQUIRED`, `SCRIPT_FACT_REQUIRED`, `AUTHORITY_UNRESOLVED`, `HARD_FAIL`, and `RULE_DATA_INCOMPLETE` must be excluded from deterministic numeric recommendation. `CURABLE_GAP` may be presented as an opportunity, not as currently qualified economics.

## 10–11. Data durability and runtime source

Positive findings:

- Ordinary evaluation makes no network calls.
- Program, rate, spend, point-table, national-status, treaty, and stacking facts are checked-in structured objects; the runtime does not ask the web to evaluate a production.

Durability gaps:

- All 71 `ProgramRequirementsProfile.evidence` records lack an `effective_date`.
- 13 lack `access_date`; 3 lack `source_url` (`us_ga_film_credit`, `mu_edb_incentive`, `kr_kofic_location_incentive`).
- Seven profiles use secondary evidence: Korea KOFIC, Dubai DPIP, Sweden, Singapore, Qatar, Switzerland, and Taiwan.
- Cultural point tables store a prose `source_note`, not structured authority URL/version/effective/access fields.
- Several executable point rows explicitly use secondary evidence or approximated point allocation.
- Treaty rows and membership lists lack sufficient structured provenance/versioning.
- Rule-registry versions are not part of the evaluation fingerprint; manual `ENGINE_VERSION` bumps are used to invalidate persisted results.

Therefore the operating model “web for maintenance only” passes, while the stronger rule → structured canonical data → primary provenance → date/version → served consumption chain fails.

## 12. Project-specific contamination and stale state

The core `canonical_evaluation.evaluate_project()` is project-ID driven and contains no title/ID branch that changes its candidate logic. Its comments and some inherited patterns use LU/FVD as regression anchors, but that alone is not project-specific execution.

The served application still contains real contamination outside that function:

- `backend/app/api/v1/cineglobe.py` imports and serves the Little Utopia demo state and selects the project by `PRODUCTION_NAME` for legacy routes.
- `frontend/src/lib/useCineGlobe.js` intentionally falls back to those eight endpoints when no project ID is provided.
- Superseded calculators and LU-only data/functions remain mounted through live APIs.

Freshness is also unsafe:

- `_compute_fingerprint()` covers budget, home jurisdiction, production type, and two territorial account sets only. It omits personnel nationality/residency, Script Analyzer elements, co-production facts, expected contingency facts, and every canonical rule/table/treaty version.
- `evaluate_project()` therefore reuses rows after material qualification facts change.
- `canonical_production_view()` follows the leading row’s stored version and fingerprint, not current `ENGINE_VERSION`, permitting stale GET state until explicit reevaluation.

## 13. Contingency finding and exact handoff

**Hard-code exists:** yes.

**Location:** `backend/app/data/program_spend_rules.py::MU_EDB_RULES` sets `contingency=True`; `backend/app/calculators/qualification_derivation.py` immediately classifies an explicit true rule as qualifying before the generic undeployed-reserve branch. Tests at `backend/tests/test_contingency_treatment.py:191–212` lock full inclusion with `None` or empty allocations.

**Scope:** generic Mauritius, with LU as the concrete affected project.

**Bypass:** canonical generic inputs contain no user-controlled expected contingency utilization percentage; the full reserve enters QPE. The legacy demo has explicit deployment controls, but its tests preserve the undeployed remainder as qualifying for Mauritius.

**Impact path:** LU account 8300 is `$301,131`. At the current 40% modeled rate, full inclusion contributes `$120,452.40` incentive. If the expected-use fraction is `p`, corrected projected incentive is lower by `$120,452.40 × (1-p)` and projected NPC is higher by the same amount. At `p=0`, LU NPC would be `$3,178,247.30`; at `p=1`, it remains `$3,057,794.90`. These endpoints are impact bounds, not an assumed producer forecast.

Required correction:

1. Add a typed, persisted project/scenario expected contingency-spend percentage, distinct from actual deployment.
2. Include that fact and contingency treatment version in the evaluation fingerprint.
3. Expand the reserve into expected deployed amount before QPE qualification for projected optimization; qualify only the expanded destination categories.
4. Preserve an actual/incurred mode that includes only amounts actually deployed/incurred by the claim date.
5. Treat the Mauritius rule as category eligibility after realization, not proof that 100% of an unused reserve was incurred.
6. Replace the full-inclusion lock tests with 0%, partial, 100%, and actual-vs-projected runtime proofs, including LU reconciliation.

## 14. LU/FVD controls

- **LU:** current canonical runtime control passes at `$3,057,794.90`. It is not accepted as final truth because it assumes 100% of contingency qualifies.
- **FVD:** current canonical runtime control passes at `$3,072,027.16`. No project-title conditional was found in the canonical evaluator.

## 15. Deferred Inspector/UI ledger

`docs/architecture/CAPABILITY_LEDGER.md:2399` preserves the requested closeout: Inspect works; whole scenario row/card should open Inspector; territory names should be human-readable; anchor/stacked/component/co-pro/fund relationships require clear presentation; ambiguous duplicate program labels require resolution; and the five scenario buckets must remain. `Scenarios.jsx` currently opens Inspector from scenario headers, NPC cells, and review rows; the remaining whole-card/labeling work is still explicitly deferred. Verdict: **PRESERVED**.

## Consolidated correction pass

| ID | Severity | Correction |
|---|---|---|
| CBA-001 | P0 | Make canonical qualification a pre-pricing admission result and propagate it through single, stack, component, co-pro unlock, ranking, and scenario-category paths. |
| CBA-002 | P0 | Replace generic unresolved rate-condition serialization with typed executable condition semantics; block base eligibility and use the correct statutory rate base. Repair PSTC/CPTC controls. |
| CBA-003 | P0 | Add explicit point-table completeness classification and semantic criterion evaluation; quarantine aggregate/approximate tables from deterministic qualification. |
| CBA-004 | P0 | Separate nationality, residency, domicile, work location, eligible labour, entity control, and route-bound co-production facts. |
| CBA-005 | P1 | Derive no-cultural-test `NOT_APPLICABLE` directly from canonical program requirements and make the full 71-program invariant test actual served states. |
| CBA-006 | P1 | Complete official co-production framework adapters and route-specific fact/provenance modeling; remove arbitrary discovery truncation from correctness decisions. |
| CBA-007 | P0 | Retire or hard-isolate all mounted stale 0.1.0 and LU-only calculation/optimization endpoints from production state and persistence. |
| CBA-008 | P0 | Make cache identity cover all qualification/copro/script/contingency facts and canonical registry versions; refuse stale engine rows in GET. |
| CBA-009 | P1 | Implement projected expected contingency utilization separately from actual incurred/deployed QPE. |
| CBA-010 | P1 | Complete structured primary provenance, dates, versions, and authority anchors for executable program/point/treaty knowledge. |

## Required end-to-end acceptance proof after correction

The correction pass must demonstrate, from API runtime rather than isolated serialization:

1. A known `HARD_FAIL`, `USER_FACT_REQUIRED`, `SCRIPT_FACT_REQUIRED`, `AUTHORITY_UNRESOLVED`, and `RULE_DATA_INCOMPLETE` candidate cannot be `PRICED`, stacked, or `RECOMMENDED`.
2. A fact-complete qualified candidate unlocks the existing allocation/pricing calculator exactly once and can rank.
3. Canada PSTC is `NOT_APPLICABLE` for cultural qualification and prices only qualified Canadian labour; CPTC requires the complete current certification/points route and the statutory labour/base cap.
4. Tokyo/US/English facts cannot satisfy France-specific criteria; EEA/CoE/treaty and route/format semantics are tested.
5. Every one of the 71 program profiles emits an expected served qualification state, with zero skip-based “disconnected” proof.
6. Bilateral, Eurimages, European Convention, and Ibermedia controls distinguish absent, exists/terms unknown, fact-incomplete, ineligible, authority-approved, and eligible.
7. Changes to personnel, script, co-production, contingency, or rule versions invalidate evaluation state without manual intervention; GET never serves an older engine generation as current.
8. All production-facing APIs converge on the canonical evaluator and cannot persist 0.1.0 results.
9. LU contingency tests cover 0/partial/100% projected utilization and actual incurred treatment; FVD remains a generic-project control.
10. The Inspector/UI ledger remains preserved for its later dedicated closeout.

## Final decision

`ONE_CONSOLIDATED_CORRECTION_PASS_REQUIRED`
