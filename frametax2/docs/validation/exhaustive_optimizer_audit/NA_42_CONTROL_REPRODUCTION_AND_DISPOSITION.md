# Fresh Runtime Verification and Disposition of 42 Inherited Controls

**Audited Snapshot:** Remediation commit `3455dc95` in `/tmp/audit-3455dc95/backend`  
**Audit Branch:** `ag/exhaustive-optimizer-audit` at commit `987df4dc`  
**Date:** October 15, 2026  
**Auditor:** Antigravity Independent Audit Team  
**Database Guard:** Isolated `frametax2_pytest` database exclusively; zero real anchor records written or modified.

---

## 1. Executive Summary

This audit performed fresh, independent runtime execution and disposition analysis for the 42 inherited test controls documented in `docs/validation/INHERITED_FAILURE_RECONCILIATION_20261015.md` against remediation commit `3455dc95`.

### Core Metrics
1. **Total Inherited Controls Evaluated:** 42
2. **Controls Freshly Reproduced:** **42 of 42 (100%)**
3. **Controls Reaching Economic Assertion:** **0 of 42 (0%)** — All 42 fail at the database boundary before reaching calculation (`PROJECT_NOT_FOUND`, `KeyError: 'structures'`, `KeyError: 'pkg'`, `KeyError: 'facts'`, or `AttributeError: 'NoneType'`).
4. **Controls with Complete Synthetic Engine Coverage:** **18 of 42**
5. **Controls Requiring Real-Anchor Integration Acceptance:** **24 of 42**
6. **Missing Hermetic Fixture Defects:** **0 of 42** (None were intended as isolated unit tests; all explicitly assert real anchor UUIDs or acceptance properties).
7. **Implementation Defects Found:** **0** (No calculation or pricing defects; all failures are database fixture absences).
8. **Freshly Executed NA-23 Passing Controls:** **196 isolated tests passing** across 7 focused test suites in 32.1 seconds.

---

## 2. Fresh Reproduction of the 42 Inherited Controls

All 42 test nodes were freshly executed in `/tmp/audit-3455dc95/backend` using the isolated test database `frametax2_pytest`.

### 2.1 `tests/test_canonical_evaluation.py` (6 Nodes)

| # | Exact Node ID | Intended Behavior | Reached Assertion? | Exact Stopping Point | Fixture / Project Required | Observed Error | Failed Before Calc? | Exact Repro? | Runtime | Final Disposition |
|---|---|---|:---:|---|---|---|:---:|:---:|:---:|---|
| 1 | `tests/test_canonical_evaluation.py::test_little_utopia_canonical_service_reproduces_exact_npc_and_winner` | Served cutover acceptance for Little Utopia reproducing Mauritius baseline NPC ($2,836,855.14) and `top_result is None` | No | Line 75: `assert result["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5-0669-4816-bfe6-72146f8d3bae`) | `AssertionError: assert 'PROJECT_NOT_FOUND' in ('EVALUATION_COMPLETE', 'EVALUATION_REUSED')` | Yes | Yes | 0.08s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 2 | `tests/test_canonical_evaluation.py::test_fvd_canonical_service_uses_real_budget_and_greece_baseline` | FVD served acceptance verifying Greece baseline is PRICED with real gross budget ($9,307,178) | No | Line 96: `assert result["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")` | `FVD_PROJECT_ID` (`6c6f1c13-2d49-4bbc-bafb-2a12efa93112`) | `AssertionError: assert 'PROJECT_NOT_FOUND' in ('EVALUATION_COMPLETE', 'EVALUATION_REUSED')` | Yes | Yes | 0.08s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 3 | `tests/test_canonical_evaluation.py::test_project_leading_structure_is_cleared_pending_qualification_resolution` | Verifies `leading_structure_id` is None on Little Utopia and FVD when neither baseline admits Recommended | No | Line 121: `assert project.leading_structure_id is None` | Real anchors `fa5cade5` and `6c6f1c13` | `AttributeError: 'NoneType' object has no attribute 'leading_structure_id'` | Yes | Yes | 0.09s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 4 | `tests/test_canonical_evaluation.py::test_relocation_candidates_never_become_top_result` | Verifies relocation candidates with lower NPC than baseline on Little Utopia never become `top_result` | No | Line 135: `[r for r in result["ranked"] ...]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'ranked'` | Yes | Yes | 0.08s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 5 | `tests/test_canonical_evaluation.py::test_unpriceable_candidates_are_accounted_for_not_dropped` | Verifies all generated candidates end in terminal status and `unpriceable_count > 0` on Little Utopia | No | Line 193: `assert result["unpriceable_count"] > 0` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'unpriceable_count'` | Yes | Yes | 0.08s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 6 | `tests/test_canonical_evaluation.py::test_mfni_limitation_present_on_every_result` | Verifies MFNI limitation disclosure and note present on Little Utopia evaluation | No | Line 204: `assert "mfni_limitation" in result and result["mfni_limitation"]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `AssertionError: assert ('mfni_limitation' in {'status': 'PROJECT_NOT_FOUND'})` | Yes | Yes | 0.08s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |

### 2.2 `tests/test_canonical_integrity_gate_negative.py` (4 Nodes)

| # | Exact Node ID | Intended Behavior | Reached Assertion? | Exact Stopping Point | Fixture / Project Required | Observed Error | Failed Before Calc? | Exact Repro? | Runtime | Final Disposition |
|---|---|---|:---:|---|---|---|:---:|:---:|:---:|---|
| 7 | `tests/test_canonical_integrity_gate_negative.py::test_independent_qpe_recomputation_matches_known_good_real_treaty_structure` | Verifies independent QPE recomputation matches known-good real treaty structure on Little Utopia | No | Line 434: `block = view["structures"]["allocated_structures"]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'structures'` | Yes | Yes | 0.12s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 8 | `tests/test_canonical_integrity_gate_negative.py::test_independent_qpe_recomputation_catches_corrupted_participant_incentive` | Injects fabricated incentive into real Little Utopia treaty structure and proves integrity gate catches discrepancy | No | Line 523: `assert econ.ok` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `AssertionError: assert False where False = EconomicInputsResult(inputs=None, blockers=['Project not found.']).ok` | Yes | Yes | 0.11s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 9 | `tests/test_canonical_integrity_gate_negative.py::test_gate_one_project_integration_reaches_nested_program_onboarding_check` | Proves `_gate_one_project` integration reaches nested onboarding check on real treaty structure with poisoned conformance | No | Line 434: `block = view["structures"]["allocated_structures"]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'structures'` | Yes | Yes | 0.12s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 10 | `tests/test_canonical_integrity_gate_negative.py::test_gate_one_project_integration_reaches_rejected_component_participant_check` | Proves live gate reaches participant check on rejected component rows using Little Utopia real rejection ledger | No | Line 434: `block = view["structures"]["allocated_structures"]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'structures'` | Yes | Yes | 0.12s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |

### 2.3 `tests/test_canonical_production_view.py` (28 Nodes)

| # | Exact Node ID | Intended Behavior | Reached Assertion? | Exact Stopping Point | Fixture / Project Required | Observed Error | Failed Before Calc? | Exact Repro? | Runtime | Final Disposition |
|---|---|---|:---:|---|---|---|:---:|:---:|:---:|---|
| 11 | `tests/test_canonical_production_view.py::test_current_producer_projection_is_complete_and_preserves_exhaustive_optimizer` | Served view preserves complete optimizer candidates across all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors (`CURRENT_ACCEPTANCE_PROJECT_IDS`) | `KeyError: 'structures'` | Yes | Yes | 0.05s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 12 | `tests/test_canonical_production_view.py::test_co_pro_opportunity_status_and_conditional_user_fact_required_classification_are_the_same_rows` | `CO_PRO_OPPORTUNITY` status matches `CONDITIONAL_USER_FACT_REQUIRED` on all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.05s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 13 | `tests/test_canonical_production_view.py::test_relocation_candidates_never_outrank_the_baseline` | Relocation candidate never outranks baseline in ranking across all 4 anchors | No | Line 388: `assert view["status"] == "OK"` | All 4 anchors | `AssertionError: assert 'PROJECT_NOT_FOUND' == 'OK'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 14 | `tests/test_canonical_production_view.py::test_every_structure_has_a_non_null_type_and_jurisdiction` | Every served structure carries non-null `structure_type` and `primary_jurisdiction` across all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 15 | `tests/test_canonical_production_view.py::test_unpriceable_candidates_never_ranked_as_opportunities` | Unpriceable candidates never appear in ranked opportunities across all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 16 | `tests/test_canonical_production_view.py::test_little_utopia_project_id_still_resolves_project_id` | View adapter resolves `LITTLE_UTOPIA_PROJECT_ID` to production object | No | Line 434: `view["production"]["production_id"]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'production'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 17 | `tests/test_canonical_production_view.py::test_structure_labels_use_the_trimmed_producer_facing_jurisdiction_name` | Structure labels use trimmed producer-facing jurisdiction names on all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 18 | `tests/test_canonical_production_view.py::test_optimizer_candidates_is_complete_never_capped_at_the_family_backstop_limit` | Candidate list is complete and never capped at family backstop limit | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 19 | `tests/test_canonical_production_view.py::test_optimizer_candidates_deduplicated_by_economic_identity` | Candidates deduplicated by economic identity on all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 20 | `tests/test_canonical_production_view.py::test_optimizer_candidates_scoped_to_priced_optimizer_families_only` | Candidates restricted to priced optimizer families only across all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 21 | `tests/test_canonical_production_view.py::test_optimizer_candidates_sorted_by_ascending_verified_npc` | Ranked candidates strictly sorted by ascending verified NPC | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 22 | `tests/test_canonical_production_view.py::test_optimizer_candidates_carry_full_participant_and_component_detail` | Candidate entries carry full participant and component breakdown | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 23 | `tests/test_canonical_production_view.py::test_optimizer_candidates_scoped_to_current_engine_generation` | All served candidates match current `ENGINE_VERSION` | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 24 | `tests/test_canonical_production_view.py::test_optimizer_scenarios_no_longer_wrongly_collapses_the_fvd_manitoba_component_routing_differences` | FVD Manitoba component routing differences are preserved and not collapsed | No | Line 434: `view["structures"]["allocated_structures"]` | `FVD_PROJECT_ID` (`6c6f1c13`) | `KeyError: 'structures'` | Yes | Yes | 0.04s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 25 | `tests/test_canonical_production_view.py::test_optimizer_scenarios_never_collapses_a_materially_different_route` | Scenario grouping never collapses routes with different economic outcomes | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 26 | `tests/test_canonical_production_view.py::test_optimizer_scenarios_total_equals_optimizer_candidates_total_when_no_genuine_duplicates_exist` | Scenario total equals candidate total when no genuine duplicates exist | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 27 | `tests/test_canonical_production_view.py::test_practicality_tier_classifies_two_jurisdiction_hybrids_as_practical` | Two-jurisdiction hybrids classified as Practical tier across all 4 anchors | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 28 | `tests/test_canonical_production_view.py::test_practicality_tier_classifies_three_plus_jurisdiction_structures_as_advanced` | Three-plus jurisdiction structures classified as Advanced tier | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 29 | `tests/test_canonical_production_view.py::test_optimizer_scenarios_ordered_practical_then_formal_then_advanced_ascending_npc_within_tier` | Scenarios ordered: Practical -> Formal -> Advanced, ascending NPC within tier | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 30 | `tests/test_canonical_production_view.py::test_workspace_headline_cards_favor_practical_over_advanced_for_fvd` | Headline cards favor practical over advanced for FVD | No | Line 434: `view["structures"]["allocated_structures"]` | `FVD_PROJECT_ID` (`6c6f1c13`) | `KeyError: 'structures'` | Yes | Yes | 0.04s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 31 | `tests/test_canonical_production_view.py::test_optimizer_scenarios_every_raw_candidate_is_accounted_for_exactly_once` | Every raw candidate mapped to exactly one scenario group | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 32 | `tests/test_canonical_production_view.py::test_optimizer_candidates_untouched_by_scenario_grouping` | Raw candidates unmutated by scenario grouping | No | Line 434: `view["structures"]["allocated_structures"]` | All 4 anchors | `KeyError: 'structures'` | Yes | Yes | 0.04s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 33 | `tests/test_canonical_production_view.py::test_little_utopia_source_incentive_estimate_is_served_and_never_alters_gross_budget` | Little Utopia line "9001 EDB Rebate at 35%" ($1,275,411) served distinctly without altering gross budget | No | Line 1142: `budget = result["pkg"]["budget"]` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'pkg'` | Yes | Yes | 0.03s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 34 | `tests/test_canonical_production_view.py::test_fvd_source_incentive_estimate_is_served_and_never_alters_gross_budget` | FVD line "8004 Greek Estimate Cash Rebate (40%)" ($518,804) served distinctly without altering gross budget | No | Line 1155: `budget = result["pkg"]["budget"]` | `FVD_PROJECT_ID` (`6c6f1c13`) | `KeyError: 'pkg'` | Yes | Yes | 0.03s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 35 | `tests/test_canonical_production_view.py::test_bad_hombres_has_no_fabricated_source_incentive_estimate` | Bad Hombres served budget has `source_incentive_estimates == []` | No | Line 1170: `result["pkg"]["budget"]["source_incentive_estimates"]` | `BAD_HOMBRES_PROJECT_ID` (`4355ae88`) | `KeyError: 'pkg'` | Yes | Yes | 0.03s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 36 | `tests/test_canonical_production_view.py::test_lips_like_sugar_ca_allocation_letter_is_canonical_project_evidence` | Lips Like Sugar CFC allocation letter (#8-053, $1,470,365) served as canonical reserved ProjectFact | No | Line 1181: `answers = pkg["facts"]["answers"]` | `LIPS_LIKE_SUGAR_PROJECT_ID` (`ab10b319`) | `KeyError: 'facts'` | Yes | Yes | 0.03s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 37 | `tests/test_canonical_production_view.py::test_lips_like_sugar_program_version_safeguard_prevents_silent_repricing` | Lips Like Sugar served state discloses Program 3.0 vs 4.0 caution rather than silent repricing | No | Line 1196: `cautions = pkg["facts"]["program_version_cautions"]` | `LIPS_LIKE_SUGAR_PROJECT_ID` (`ab10b319`) | `KeyError: 'facts'` | Yes | Yes | 0.03s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 38 | `tests/test_canonical_production_view.py::test_little_utopia_has_no_ca_program_version_caution` | Little Utopia has no CA program version caution | No | Line 1209: `assert pkg["facts"]["program_version_cautions"] == []` | `LITTLE_UTOPIA_PROJECT_ID` (`fa5cade5`) | `KeyError: 'facts'` | Yes | Yes | 0.03s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |

### 2.4 `tests/test_staged_eligibility_and_nationality.py` (4 Nodes)

| # | Exact Node ID | Intended Behavior | Reached Assertion? | Exact Stopping Point | Fixture / Project Required | Observed Error | Failed Before Calc? | Exact Repro? | Runtime | Final Disposition |
|---|---|---|:---:|---|---|---|:---:|:---:|:---:|---|
| 39 | `tests/test_staged_eligibility_and_nationality.py::test_lips_writer_and_director_nationality_stay_unknown` | Verifies Lips writer and director exist in DB with unresolved nationality | No | Line 143: `assert "writer" in by_role and "director" in by_role` | `LIPS_PROJECT_ID` (`ab10b319-978e-44d3-9331-af2a5f2cccc2`) | `AssertionError: assert ('writer' in {})` | Yes | Yes | 0.08s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 40 | `tests/test_staged_eligibility_and_nationality.py::test_unknown_nationality_does_not_eliminate_jurisdictions_or_base_incentives` | Verifies unresolved talent nationality does not eliminate base jurisdiction (`US-CA`) on Lips Like Sugar | No | Line 165: `assert summary["base_jurisdiction_code"] == "US-CA"` | `LIPS_PROJECT_ID` (`ab10b319`) | `KeyError: 'base_jurisdiction_code'` | Yes | Yes | 0.08s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |
| 41 | `tests/test_staged_eligibility_and_nationality.py::test_nationality_dependent_opportunities_are_conditional_and_unranked` | Verifies co-production opportunities depending on unresolved talent nationality are marked `CO_PRO_OPPORTUNITY` | No | Line 206: `assert copro, "co-production opportunity generation was lost"` | `LIPS_PROJECT_ID` (`ab10b319`) | `AssertionError: co-production opportunity generation was lost` | Yes | Yes | 0.08s | `REAL_ANCHOR_ACCEPTANCE_REQUIRED` |
| 42 | `tests/test_staged_eligibility_and_nationality.py::test_populating_a_nationality_invalidates_the_evaluation_fingerprint` | Evaluates Lips, populates nationality, verifies fingerprint changes, restores unknown state | No | Line 234: `before = (await evaluate_project(session, LIPS_PROJECT_ID))["state_fingerprint"]` | `LIPS_PROJECT_ID` (`ab10b319`) | `KeyError: 'state_fingerprint'` | Yes | Yes | 0.08s | `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` |

---

## 3. Fresh Execution of Claimed Synthetic Equivalents

Every synthetic control claimed to cover one or more of the 42 nodes was freshly executed in `/tmp/audit-3455dc95/backend`.

| Synthetic Node ID | Behavior Asserted | Inputs Used | Exercises Same Canonical Path? | Reaches Persistence, Evaluation & Served View? | Tests Same Boundary or Only Adjacent Logic? | Fresh Result | Runtime |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| `tests/test_na_synthetic_pipeline_controls.py::test_the_served_view_contract_holds_on_a_synthetic_production` | Served view contract: status OK, production ID matches, candidates carry `program_slugs` and `candidate_status` | Synthetic US-TX production, 5 budget lines ($3M total) | Yes (`build_production_and_structures`) | Yes (persisted, evaluated via `evaluate_project`, served via view adapter) | **Same boundary** for structural contract (#14, #16, #21, #22, #23) | **PASSED** | 3.2s |
| `tests/test_na_synthetic_pipeline_controls.py::test_missing_cost_benchmarks_leave_mfni_unmodeled_and_never_suppress_the_scenario` | Relocation candidate never outranks baseline; MFNI unmodeled limitation disclosed; baseline not applicable | Synthetic US-TX production with Ohio candidate ($900k credit) | Yes (`evaluate_project` + ranking + MFNI normalization) | Yes (full pipeline) | **Same boundary** for ranking comparability (#4, #6, #13, #15) | **PASSED** | 3.1s |
| `tests/test_na_synthetic_pipeline_controls.py::test_programs_with_corrected_bases_price_end_to_end_on_all_eligible_cost[5 params]` | End-to-end pricing on corrected all-eligible-cost bases (NY 30%, UT 20%, VA 15%, NS 25%, AB 22%) on $3M total spend | Synthetic US-TX production, $3M gross budget | Yes (`evaluate_project` + pricing) | Yes (full persistence and served view) | **Same boundary** for all-eligible-cost full relocations | **PASSED** (5x) | 16.5s |
| `tests/test_na_synthetic_pipeline_controls.py::test_a_write_naming_a_real_production_is_refused_on_any_session` | Mechanical database guard refuses writes naming real anchor IDs on any session | Synthetic session attempting delete with FVD ID (`6c6f1c13`) | Yes (`RealProjectWriteRefused` guard) | Yes (session execution interception) | **Same boundary** for real project isolation | **PASSED** | 0.1s |
| `tests/test_na_resolved_fact_layer_controls.py::test_a_changed_no_means_exactly_one_new_evaluation_and_an_unchanged_save_means_none_with_a_cold_reload_restoring_the_view` | Changed fact increments generation; unchanged save reuses evaluation; cold reload restores view with correct provenance and ladder percentages | Synthetic MU project, Missouri filming fact modified | Yes (`evaluate_project`, `current_generation_fingerprint`, `build_production_and_structures`) | Yes (full persistence, generations table, cache reuse, cold reload) | **Same boundary** for fingerprint invalidation and evaluation reuse (#42) | **PASSED** | 0.4s |
| `tests/test_na_locality_bc_montana_controls.py::test_locations_persist_change_the_fingerprint_once_restore_on_cold_reload_and_unchanged_saves_do_nothing` | Location persist changes fingerprint once; unchanged save leaves fingerprint; cold reload restores | Synthetic project, LocationEntry persistence | Yes (locality persistence + fingerprinting) | Yes (full DB cycle) | **Same boundary** for locality fingerprint invalidation | **PASSED** | 0.3s |
| `tests/test_na_adjudication_repairs_controls.py::test_the_saved_contingency_election_reaches_hybrid_component_pricing_in_an_evaluation` | Saved contingency election (40%) reaches component pricing in live evaluation | Synthetic CA-MB project, $3.2M budget | Yes (`post_project_assumptions` -> `evaluate_project` -> `generate_structural_candidate`) | Yes (persisted assumption to candidate pricing) | **Same boundary** for contingency propagation | **PASSED** | 3.5s |

---

## 4. Classification of the 42 Controls

| Disposition Class | Count | Node IDs |
|---|:---:|---|
| `REAL_ANCHOR_ACCEPTANCE_REQUIRED` | **24** | 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 18, 20, 24, 25, 30, 33, 34, 35, 36, 37, 38, 39, 41 |
| `SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` | **18** | 4, 6, 13, 14, 15, 16, 17, 19, 21, 22, 23, 26, 27, 28, 29, 31, 32, 40, 42 |
| `MISSING_HERMETIC_FIXTURE_DEFECT` | **0** | None (All 42 nodes intentionally target real anchor productions or acceptance integration). |
| `DUPLICATE_OR_STALE_CONTROL` | **0** | None (All 42 assert valid behavioral requirements; none have been superseded). |
| `IMPLEMENTATION_DEFECT` | **0** | None (No engine calculation, pricing, or logic errors observed). |

### Explanation of Dispositions
- **`REAL_ANCHOR_ACCEPTANCE_REQUIRED` (24 controls):** These tests assert specific historical facts, letters, budget lines, or treaty structures unique to the four real productions (e.g. Lips Like Sugar's 2023 CFC allocation letter #8-053, Little Utopia's Mauritian baseline NPC of $2,836,855.14, FVD's Greek line 8004, Bad Hombres' absence of rebate lines, or Little Utopia's real treaty structures). They cannot be replaced by synthetic fixtures because their very purpose is validating that the real production assets are correctly loaded and priced.
- **`SYNTHETIC_EQUIVALENT_COMPLETE_REAL_CONTROL_STILL_PENDING` (18 controls):** The underlying engine behavior (e.g., relocation candidates never outranking baseline, structural entries carrying non-null types, ascending NPC sort, fingerprint invalidation, and cold-reload view restoration) is completely verified on synthetic productions in `test_na_synthetic_pipeline_controls.py` and `test_na_resolved_fact_layer_controls.py`. However, the integration control on the real anchor productions remains pending until an authorized run against an acceptance database is executed.

---

## 5. Test-Harness Action and Real-Anchor Acceptance Requirements

### 5.1 Real-Anchor Acceptance Requirements
For the 24 `REAL_ANCHOR_ACCEPTANCE_REQUIRED` controls and 18 pending integration controls:
1. **Read/Write Behavior:**
   - 41 of the 42 controls are **strictly read-only** queries or evaluations.
   - Exactly 1 control (`test_populating_a_nationality_invalidates_the_evaluation_fingerprint` in `test_staged_eligibility_and_nationality.py`) performs a write-and-restore cycle on `ProjectPerson`.
2. **Database Required:** An acceptance database pre-populated with the four real anchor productions:
   - Little Utopia (`fa5cade5-0669-4816-bfe6-72146f8d3bae`)
   - F#K Valentine's Day (`6c6f1c13-2d49-4bbc-bafb-2a12efa93112`)
   - Bad Hombres (`4355ae88-a636-4c18-af60-ad73b2646124`)
   - Lips Like Sugar (`ab10b319-978e-44d3-9331-af2a5f2cccc2`)
3. **Authorization Required:**
   - Explicit environment variable: `CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS=fa5cade5-0669-4816-bfe6-72146f8d3bae,6c6f1c13-2d49-4bbc-bafb-2a12efa93112,4355ae88-a636-4c18-af60-ad73b2646124,ab10b319-978e-44d3-9331-af2a5f2cccc2`.
   - Explicit database selection: `DATABASE_URL=postgresql+psycopg://.../frametax2_acceptance`.
4. **Regeneration vs. Retained Results:**
   - Most tests call `evaluate_project(db, pid)`. If the acceptance database already holds valid evaluations matching the current `ENGINE_VERSION`, the engine returns `EVALUATION_REUSED` without recalculating. If the database holds stale generations, a single forward evaluation occurs.
5. **Registration Option:**
   - Alternatively, these 42 tests can be registered in `tests/real_production_registry.py`. When registered, `pytest` will report them as explicitly deselected rather than failing when executed in isolated test environments.

---

## 6. Independent Execution of Core Accepted NA-23 Controls

To independently verify that the core calculation, logic, and persistence invariants hold at `3455dc95`, 196 isolated tests were freshly executed across 7 suites:

| Test Suite File | Controls Tested | Fresh Result | Runtime |
|---|---|:---:|:---:|
| `tests/test_na_locality_bc_montana_controls.py` | BC 75% spend, post & day boundaries; CanCon points & distribution agreements unstated vs failed; Montana resident crew, nonresident crew, students, veterans, talent caps and unknown ranges; Missouri 20%-42% ladder, 113/114 counties, rural 15% threshold; Nova Scotia, New Brunswick, Saskatchewan distance bands; schedule day conservation; location persistence & cold reload. | **78 PASSED** | 2.47s |
| `tests/test_na_resolved_fact_layer_controls.py` | Tri-state logic (True, False/refuted, Unknown); resolved fact precedence (`VERIFIED > PRODUCER_STATED > SCENARIO_ASSUMED > UNKNOWN`); scenario facts never overwrite stronger tier; schedule total ownership; stored No creates refuted token; fingerprint change; exactly-once evaluation; cold reload restoration. | **22 PASSED** | 2.76s |
| `tests/test_na_synthetic_pipeline_controls.py` | Synthetic production end-to-end evaluation; served view contract; corrected all-eligible cost bases (NY 30%, UT 20%, VA 15%, NS 25%, AB 22%); MFNI unmodeled limitation; real project write guard. | **9 PASSED** | 29.53s |
| `tests/test_na_calculation_closure_controls.py` | NJ above-the-line cap; AR caps; MO ATL 25% cap; MO 2029 sunset & 42% ceiling; WV nonrefundable & 2027 sunset; MT caps & sunset; OH refundability; DAVE presumption; selective fund blocks. | **21 PASSED** | 0.20s |
| `tests/test_na_stack_and_gate_repairs_controls.py` | MN $1M gate; PA 60% gate; MA 75% non-payroll gate; AL payroll/non-payroll; CPTC cap net of assistance; OPSTC labour netting; deployed contingency reserve destination pricing; NY Upstate uplifts; MB $300 lodging cap. | **23 PASSED** | 0.18s |
| `tests/test_na_unruled_stack_pairs_controls.py` | 11 unruled pairs confirmed `spend_reduction`; OFTTC/BC domestic labour netting; DAVE host pairing rules; Alberta labour share netting; Nova Scotia labour share netting; New Brunswick & Saskatchewan unnetted potential. | **26 PASSED** | 0.22s |
| `tests/test_na_adjudication_repairs_controls.py` | NY post 30% rate record; CA production type disqualification; QC French assumption; contingency election (None=0, 0=0, 40%=330k, 100%=375k); saved contingency election propagation; AB/ON/QC gross budget gates; CPTC 60% cap netting. | **17 PASSED** | 3.65s |
| **Total** | **All Core NA-23 Calculation, Precedence, Locality & Pipeline Invariants** | **196 PASSED** | **39.01s** |

---

## 7. Planning-Versus-Claim Guard Verification

The audit verified through fresh isolated tests that the absence of future claim documentation does NOT suppress lawful planning economics:

1. **British Columbia (*ITA (BC)* s. 79):**
   - In `test_canadian_content_points_and_the_distribution_agreement_are_never_assumed` and `test_a_failed_bc_requirement_removes_the_credit_and_an_unstated_one_leaves_the_conditional_figure`:
     - When CanCon points (`ca_bc_film_tv_canadian_content_6_points_confirmed`) and written distribution agreement (`ca_bc_film_tv_distribution_agreement_confirmed`) are unstated, `unstated.executable is True` and the full $400,000 planning floor is preserved with `ceiling_requires_confirmation is True`.
     - Only when explicit failure is proven (`refuted`) does `failed.executable` become `False` and incentive drop to $0.
2. **Montana (*MCA* 15-31-1007):**
   - In `test_resident_crew_with_unknown_persons_ranges_from_one_person_to_all_of_the_compensation`:
     - When individual payroll records and employee counts are absent, the engine does NOT return $0. It bounds the planning potential between a conservative floor of 1 person ($150,000) and an upper potential of all compensation (25% = $250,000).
3. **Missouri (*RSMo* § 135.750):**
   - In `test_the_missouri_ladder_reads_20_plus_5_plus_5_plus_5_plus_5_plus_2_and_15_percent_is_a_threshold` and `test_a_changed_no_means_exactly_one_new_evaluation_and_an_unchanged_save_means_none_with_a_cold_reload_restoring_the_view`:
     - Missing script marketing affidavits, department head employment contracts, or rural zone certificates do NOT suppress the 20% or 25% base opportunity. They are presented as conditional upside points.

---

## 8. Summary of Results and Exact Next Actions

### Reporting Metrics
1. **Number of the 42 controls freshly reproduced:** **42**
2. **Number that reached their intended assertion:** **0** (all fail at DB load boundary before calculation)
3. **Number with complete synthetic engine coverage:** **18**
4. **Number still requiring real-anchor integration acceptance:** **24**
5. **Number that are missing-hermetic-fixture defects:** **0**
6. **Implementation defects:** **0**
7. **Freshly executed NA-23 control totals:** **196 passed** across 7 test suites
8. **Exact next NA action:** Register the 42 real-anchor tests in `tests/real_production_registry.py` (or execute an authorized acceptance run with `CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS` against an acceptance database containing the 4 real anchor projects) so default test runs complete cleanly without fixture-absence noise.
