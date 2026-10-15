# Additional failures in the isolated database found while scanning (NA-RECONCILIATION-25, 2026-10-15)

While preparing the real-anchor acceptance manifest, every test file that names an anchor and is neither in the real-production registry nor in the reconciled 42 was run once against the isolated `frametax2_pytest` database (`pytest <37 files> --junitxml`, 195 seconds, no anchor opened, nothing written to any anchor). Result: **149 failed and 29 errored (178)**, and the identical set fails at the committed parent `21fc69c6`, so none is caused by NA-RECONCILIATION-25. The earlier figure of 42 therefore under-counted the controls that cannot reach their assertion without the anchors. None is called harmless: each is listed with its exact first failure line. They are not registered, deselected, weakened or run against any anchor; classifying each as read-only / evaluating / mutating (as done for the 42 in `REAL_ANCHOR_ACCEPTANCE_MANIFEST_PROPOSED_20261015`) is the next step before any authorized run.

| File | Count |
|---|---|
| tests/test_bounded_evaluation_response.py | 6 |
| tests/test_bulk_evaluation_persistence.py | 5 |
| tests/test_canonical_budget_semantic_repair.py | 11 |
| tests/test_canonical_generation_freshness.py | 3 |
| tests/test_canonical_npc_trace_reconstruction.py | 3 |
| tests/test_canonical_pricing_path_and_discovery.py | 4 |
| tests/test_canonical_project_economics.py | 5 |
| tests/test_canonical_scenario_participants.py | 10 |
| tests/test_canonical_selection_consistency.py | 6 |
| tests/test_codex_bcd_generic_capability_restoration.py | 1 |
| tests/test_component_rejection_persistence.py | 2 |
| tests/test_component_relocation.py | 5 |
| tests/test_copro_conditional_pricing_bridge.py | 2 |
| tests/test_copro_opportunity_relevance_claude.py | 7 |
| tests/test_copro_qualification_wiring.py | 6 |
| tests/test_coproduction_optimizer_preservation.py | 14 |
| tests/test_final_wiring_oregon_conditional_formula.py | 2 |
| tests/test_final_wiring_selection_predicate.py | 3 |
| tests/test_fresh_project_economic_fidelity.py | 4 |
| tests/test_fvd_canonical_input_assembly_repair.py | 9 |
| tests/test_hybrid_anchor_relationship_types.py | 4 |
| tests/test_jurisdiction_preference.py | 10 |
| tests/test_leading_conditional_recommendation.py | 6 |
| tests/test_national_cultural_status.py | 2 |
| tests/test_opportunity_wiring.py | 5 |
| tests/test_optimizer_audit_defect_remediation.py | 11 |
| tests/test_optimizer_scenario_universe_accounting.py | 24 |
| tests/test_project_workspace_view.py | 3 |
| tests/test_treaty_coproduction_wiring.py | 5 |

| Node | Kind | First failure line | File names an anchor |
|---|---|---|---|
| tests/test_bounded_evaluation_response.py::test_evaluation_begin_payload_is_bounded_and_routes_reproduce_the_universe | failed | KeyError: 'unpriceable_count' | yes |
| tests/test_bounded_evaluation_response.py::test_ordinals_are_monotonic_across_chunk_boundaries_and_summary_counts_are_exact | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bounded_evaluation_response.py::test_page_limit_clamp_and_empty_generation | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bounded_evaluation_response.py::test_pages_are_bounded_deterministic_exact_and_complete | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bounded_evaluation_response.py::test_retained_rows_are_exactly_the_non_rejected_ones_plus_any_baseline | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bounded_evaluation_response.py::test_workspace_view_is_bounded_and_carries_the_same_accounting | failed | KeyError: 'evaluation' | yes |
| tests/test_bulk_evaluation_persistence.py::test_bounded_readback_accounts_for_every_row_of_the_orm_readback | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_bulk_evaluation_persistence.py::test_bulk_writer_fk_order_holds_at_every_chunk_boundary | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bulk_evaluation_persistence.py::test_bulk_writer_reads_see_buffered_rows_and_rollback_discards_everything | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bulk_evaluation_persistence.py::test_bulk_writer_writes_exactly_what_orm_add_flush_wrote | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 4355ae88-a636-4c18-af60-ad73b2646124 (a | yes |
| tests/test_bulk_evaluation_persistence.py::test_identical_input_rerun_creates_zero_rows | failed | AssertionError: assert 'PROJECT_NOT_FOUND' == 'EVALUATION_REUSED' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_art_direction_is_never_misclassified_as_the_atl_director_role | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_atl_producer_and_director_roles_classify_correctly | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_bad_hombres_contingency_survives_downstream_exactly_once | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_film_lab_dailies_and_titles_classify_post_production | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_fvd_bare_bond_account_classifies_completion_bond | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_fvd_finance_fee_exactly_once_as_source_finance | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_legal_accounting_classifies_correctly_bad_hombres_and_lips | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_lips_like_sugar_all_three_total_fringes_rows_classify_payroll_fringes | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_lips_like_sugar_duplicate_4900_rows_both_survive_with_correct_categories | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_production_sound_and_post_sound_never_collapse_into_each_other | failed | AttributeError: 'NoneType' object has no attribute 'id' | yes |
| tests/test_canonical_budget_semantic_repair.py::test_source_totals_unchanged_for_all_four_budgets | failed | AttributeError: 'NoneType' object has no attribute 'total_budget_raw' | yes |
| tests/test_canonical_generation_freshness.py::test_current_generation_fingerprint_is_the_single_shared_source | failed | AssertionError: 6c6f1c13-2d49-4bbc-bafb-2a12efa93112: expected a real current fingerprint | yes |
| tests/test_canonical_generation_freshness.py::test_fvd_and_lls_have_genuine_multi_fingerprint_history | failed | AssertionError: expected F#K Valentine's Day to have real multi-fingerprint history, got 0 | yes |
| tests/test_canonical_generation_freshness.py::test_structure_and_package_views_reconcile_across_locked_corpus | failed | KeyError: 'production' | yes |
| tests/test_canonical_npc_trace_reconstruction.py::test_component_adjusted_npc_reconstructs_exactly_from_verified_plus_deltas | failed | KeyError: 'structures' | yes |
| tests/test_canonical_npc_trace_reconstruction.py::test_component_npc_verified_and_adjusted_are_independent_real_values | failed | KeyError: 'structures' | yes |
| tests/test_canonical_npc_trace_reconstruction.py::test_single_and_full_relocation_npc_reconstruction_still_holds | failed | KeyError: 'structures' | yes |
| tests/test_canonical_pricing_path_and_discovery.py::test_fvd_evaluation_prices_all_three_ontario_programs_independently | failed | AssertionError: expected 3 independently priced Ontario candidates, got 0 | yes |
| tests/test_canonical_pricing_path_and_discovery.py::test_lu_and_fvd_share_the_same_canonical_evaluation_engine | failed | AttributeError: 'NoneType' object has no attribute 'leading_structure_id' | yes |
| tests/test_canonical_pricing_path_and_discovery.py::test_lu_reevaluates_through_canonical_engine_at_accepted_npc | failed | KeyError: 'base_jurisdiction_code' | yes |
| tests/test_canonical_pricing_path_and_discovery.py::test_npc_reconciles_exactly_for_lu_and_fvd_baselines | failed | KeyError: 'baseline' | yes |
| tests/test_canonical_project_economics.py::test_declared_grand_total_is_the_basis_not_the_leaf_sum | failed | AttributeError: 'NoneType' object has no attribute 'gross_budget_usd' | yes |
| tests/test_canonical_project_economics.py::test_generic_inputs_resolve_from_persisted_project_evidence_only | failed | AssertionError: ['Project not found.'] | yes |
| tests/test_canonical_project_economics.py::test_little_utopia_canonical_npc_reproduced_from_generic_inputs | failed | AttributeError: 'NoneType' object has no attribute 'contingency_expected_utilization_pct' | yes |
| tests/test_canonical_project_economics.py::test_little_utopia_contingency_election_is_a_real_persisted_fact_not_a_code_default | failed | AttributeError: 'NoneType' object has no attribute 'contingency_expected_utilization_pct' | yes |
| tests/test_canonical_project_economics.py::test_zero_percent_utilization_would_exclude_the_full_reserve | failed | AttributeError: 'NoneType' object has no attribute 'jurisdiction_code' | yes |
| tests/test_canonical_scenario_participants.py::test_bilateral_treaty_between_two_other_candidates_excludes_home | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_bilateral_treaty_with_home_as_a_party_includes_home_in_participants | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_component_participants_exactly_equal_claiming_segments_not_merely_at_least_two | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_component_relocation_participants_include_the_routed_destination | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_generated_participants_equal_persisted_trace_participants_cross_project | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_little_utopia_named_regression_structure_excludes_non_claiming_us | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_multilateral_treaty_opportunity_includes_home_as_a_genuine_member | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_p0_part_001_non_claiming_primary_excluded_across_broader_corpus | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_single_country_and_full_relocation_still_serve_exactly_one_participant | failed | KeyError: 'structures' | yes |
| tests/test_canonical_scenario_participants.py::test_single_country_and_treaty_participants_unaffected_by_p0_2_fix | failed | KeyError: 'structures' | yes |
| tests/test_canonical_selection_consistency.py::test_bad_hombres_and_lips_valid_canonical_selection_preserved | failed | KeyError: 'structures' | yes |
| tests/test_canonical_selection_consistency.py::test_canonical_field_correct_across_all_four_locked_corpus_productions | failed | KeyError: 'structures' | yes |
| tests/test_canonical_selection_consistency.py::test_canonical_field_is_none_only_when_no_comparable_winner_exists | failed | KeyError: 'structures' | yes |
| tests/test_canonical_selection_consistency.py::test_evaluator_persisted_and_served_selection_agree_across_full_corpus | failed | AttributeError: 'NoneType' object has no attribute 'leading_structure_id' | yes |
| tests/test_canonical_selection_consistency.py::test_little_utopia_and_fvd_never_surface_a_noncomparable_candidate_as_canonical | failed | KeyError: 'structures' | yes |
| tests/test_canonical_selection_consistency.py::test_no_baseline_projects_persist_null_leading_structure_id | failed | AssertionError: 10 Double Zero: project not found by id 3519feda-d280-435f-badc-1e4c788a2cb3 | yes |
| tests/test_codex_bcd_generic_capability_restoration.py::test_a_country_with_a_priced_provincial_leg_IS_a_treaty_partner | failed | AssertionError: Canada lost every bilateral treaty pairing | yes |
| tests/test_component_rejection_persistence.py::test_locked_corpus_produces_durable_component_rejections | failed | AssertionError: expected at least one real persisted component rejection across the locked corpus | yes |
| tests/test_component_rejection_persistence.py::test_rejection_rows_carry_full_reconstructible_disposition | failed | assert 0 > 0 | yes |
| tests/test_component_relocation.py::test_component_relocation_never_uses_default_domicile_for_routed_spend | failed | KeyError: 'structures' | yes |
| tests/test_component_relocation.py::test_fvd_component_relocation_allocation_conserves_gross_budget | failed | KeyError: 'structures' | yes |
| tests/test_component_relocation.py::test_fvd_component_relocation_candidates_exist_and_are_typed | failed | KeyError: 'structures' | yes |
| tests/test_component_relocation.py::test_fvd_component_relocation_traces_real_budget_spend_not_invented | failed | KeyError: 'structures' | yes |
| tests/test_component_relocation.py::test_little_utopia_baseline_unchanged_by_component_relocation | failed | KeyError: 'structures' | yes |
| tests/test_copro_conditional_pricing_bridge.py::test_conditional_scenario_routes_same_jurisdiction_multi_slug_through_stack_engine | failed | AssertionError: assert 'spend_reduction' == 'mutually_exclusive' | yes |
| tests/test_copro_conditional_pricing_bridge.py::test_little_utopia_real_gbie_treaty_allocation_conserves_one_budget | failed | AttributeError: 'NoneType' object has no attribute 'budget_lines' | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_bad_hombres_no_cultural_test_baseline_receives_a_real_leading_structure | failed | AttributeError: 'NoneType' object has no attribute 'leading_structure_id' | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_lips_like_sugar_unconfirmed_personnel_never_credited_in_the_real_served_view | failed | assert None is not None | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_little_utopia_and_fvd_baselines_are_genuinely_unresolved_not_a_ranking_defect | failed | AttributeError: 'NoneType' object has no attribute 'leading_structure_id' | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_little_utopia_gb_writer_and_au_director_are_transported_not_rule_consumed_except_for_uk_au | failed | AssertionError: assert (None is not None) | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_little_utopia_non_home_anchored_opportunities_are_never_labeled_project_compatible | failed | AssertionError: Little Utopia must have real treaty_coproduction rows to check | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_no_treaty_coproduction_row_ever_carries_priced_economics_on_its_own_result_row | failed | assert [] | yes |
| tests/test_copro_opportunity_relevance_claude.py::test_served_multilateral_opportunities_never_carry_a_bare_none_personnel_gate_state | failed | AssertionError: F#K Valentine's Day (Greece) must have real multilateral opportunities to check | yes |
| tests/test_copro_qualification_wiring.py::test_baselines_unchanged_after_qualification_reconnection | failed | KeyError: 'structures' | yes |
| tests/test_copro_qualification_wiring.py::test_component_stack_participant_qualification_aggregate_contract | failed | KeyError: 'structures' | yes |
| tests/test_copro_qualification_wiring.py::test_lu_real_personnel_hard_fails_ca_federal_cptc | failed | AssertionError: LU's real non-Canadian personnel must still hard-fail ca_federal_cptc, got USER_FACT_REQUIRED | yes |
| tests/test_copro_qualification_wiring.py::test_role_qualification_covers_only_real_registry_slugs | failed | KeyError: 'structures' | yes |
| tests/test_copro_qualification_wiring.py::test_role_qualification_never_contaminates_ranking_or_npc | failed | KeyError: 'structures' | yes |
| tests/test_copro_qualification_wiring.py::test_role_qualification_survives_persistence_and_api | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_a_blocked_constituent_does_not_destroy_the_capability | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_conditional_coproductions_stay_conditional[6c6f1c13-2d49-4bbc-bafb-2a12efa93112] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_conditional_coproductions_stay_conditional[ab10b319-978e-44d3-9331-af2a5f2cccc2] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_conditional_coproductions_stay_conditional[fa5cade5-0669-4816-bfe6-72146f8d3bae] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_coproduction_partners_are_named_not_raw_codes[6c6f1c13-2d49-4bbc-bafb-2a12efa93112] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_coproduction_partners_are_named_not_raw_codes[ab10b319-978e-44d3-9331-af2a5f2cccc2] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_coproduction_partners_are_named_not_raw_codes[fa5cade5-0669-4816-bfe6-72146f8d3bae] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_multi_program_stacking_and_component_routing_still_generate[6c6f1c13-2d49-4bbc-bafb-2a12efa93112] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_multi_program_stacking_and_component_routing_still_generate[ab10b319-978e-44d3-9331-af2a5f2cccc2] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_multi_program_stacking_and_component_routing_still_generate[fa5cade5-0669-4816-bfe6-72146f8d3bae] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_multilateral_frameworks_are_still_discovered | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_treaty_coproduction_generation_still_executes[6c6f1c13-2d49-4bbc-bafb-2a12efa93112] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_treaty_coproduction_generation_still_executes[ab10b319-978e-44d3-9331-af2a5f2cccc2] | failed | KeyError: 'structures' | yes |
| tests/test_coproduction_optimizer_preservation.py::test_treaty_coproduction_generation_still_executes[fa5cade5-0669-4816-bfe6-72146f8d3bae] | failed | KeyError: 'structures' | yes |
| tests/test_final_wiring_oregon_conditional_formula.py::test_fvd_baseline_unaffected_by_lifting_the_oregon_veto | failed | KeyError: 'structures' | yes |
| tests/test_final_wiring_oregon_conditional_formula.py::test_fvd_current_universe_oregon_candidates_if_any_are_never_rank_1 | failed | KeyError: 'structures' | yes |
| tests/test_final_wiring_selection_predicate.py::test_bad_hombres_and_lips_retain_exact_winners_no_competing_conditional | failed | KeyError: 'structures' | yes |
| tests/test_final_wiring_selection_predicate.py::test_fvd_leading_conditional_never_exposes_none_state_and_names_romania | failed | KeyError: 'structures' | yes |
| tests/test_final_wiring_selection_predicate.py::test_little_utopia_leading_conditional_never_exposes_none_state | failed | KeyError: 'structures' | yes |
| tests/test_fresh_project_economic_fidelity.py::test_allocation_conserves_for_a_single_jurisdiction_structure | failed | AttributeError: 'NoneType' object has no attribute 'budget_lines' | yes |
| tests/test_fresh_project_economic_fidelity.py::test_fresh_project_priced_and_top_scenario_fully_attributable | failed | AssertionError: assert 'PROJECT_NOT_FOUND' in ('EVALUATION_COMPLETE', 'EVALUATION_REUSED') | yes |
| tests/test_fresh_project_economic_fidelity.py::test_monetary_line_population_positive_and_no_stale_rebate_line | failed | assert None is not None | yes |
| tests/test_fresh_project_economic_fidelity.py::test_source_and_canonical_conservation_reconcile_exactly | failed | AssertionError: assert False | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_build_physical_requirements_reads_real_fvd_scripted_locations | failed | AssertionError: assert None is True | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_fvd_territorial_facts_are_unknown_not_known_empty | failed | AssertionError: assert False | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_landlocked_jurisdictions_remain_economically_discoverable | failed | KeyError: 'structures' | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_little_utopia_regression_unchanged_by_input_assembly_repair | failed | KeyError: 'engine_version' | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_marine_capable_jurisdictions_unaffected_by_capability_gate | failed | KeyError: 'structures' | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_no_fvd_candidate_is_blocked_on_local_entity_grounds | failed | KeyError: 'structures' | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_qpe_is_derived_from_real_account_universe_not_one_flattened_total | failed | AssertionError: assert False | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_representative_fvd_jurisdiction_traces | failed | KeyError: 'structures' | yes |
| tests/test_fvd_canonical_input_assembly_repair.py::test_unknown_territorial_facts_flag_priced_results_provisional | failed | KeyError: 'structures' | yes |
| tests/test_hybrid_anchor_relationship_types.py::test_component_relocation_never_carries_coproduction_relationship | failed | KeyError: 'structures' | yes |
| tests/test_hybrid_anchor_relationship_types.py::test_multi_program_stack_never_carries_component_or_coproduction_relationship | failed | KeyError: 'structures' | yes |
| tests/test_hybrid_anchor_relationship_types.py::test_relationship_types_is_always_a_list_never_none | failed | KeyError: 'structures' | yes |
| tests/test_hybrid_anchor_relationship_types.py::test_treaty_coproduction_carries_coproduction_and_conditional_fund_independently | failed | KeyError: 'structures' | yes |
| tests/test_jurisdiction_preference.py::test_excluded_jurisdiction_codes_reads_the_generic_fact | error | failed on teardown with "tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49- | yes |
| tests/test_jurisdiction_preference.py::test_excluded_jurisdiction_codes_reads_the_generic_fact | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49-4bbc-bafb-2a12efa93112 (a | yes |
| tests/test_jurisdiction_preference.py::test_excluded_jurisdiction_is_removed_from_evaluate_project_candidates | error | failed on teardown with "tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49- | yes |
| tests/test_jurisdiction_preference.py::test_excluded_jurisdiction_is_removed_from_evaluate_project_candidates | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49-4bbc-bafb-2a12efa93112 (a | yes |
| tests/test_jurisdiction_preference.py::test_home_jurisdiction_cannot_be_excluded_from_its_own_candidate_universe | error | failed on teardown with "tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49- | yes |
| tests/test_jurisdiction_preference.py::test_home_jurisdiction_cannot_be_excluded_from_its_own_candidate_universe | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49-4bbc-bafb-2a12efa93112 (a | yes |
| tests/test_jurisdiction_preference.py::test_regression_all_fingerprint_readers_agree_when_an_exclusion_is_set | error | failed on teardown with "tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49- | yes |
| tests/test_jurisdiction_preference.py::test_regression_all_fingerprint_readers_agree_when_an_exclusion_is_set | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49-4bbc-bafb-2a12efa93112 (a | yes |
| tests/test_jurisdiction_preference.py::test_reincluding_restores_the_candidate_with_unchanged_economics | error | failed on teardown with "tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49- | yes |
| tests/test_jurisdiction_preference.py::test_reincluding_restores_the_candidate_with_unchanged_economics | failed | tests.isolated_records.RealProjectWriteRefused: refused a write naming the real production 6c6f1c13-2d49-4bbc-bafb-2a12efa93112 (a | yes |
| tests/test_leading_conditional_recommendation.py::test_bad_hombres_and_lips_retain_verified_winners | failed | KeyError: 'structures' | yes |
| tests/test_leading_conditional_recommendation.py::test_fvd_returns_leading_conditional_not_hardcoded | failed | KeyError: 'structures' | yes |
| tests/test_leading_conditional_recommendation.py::test_little_utopia_returns_leading_conditional_not_hardcoded | failed | KeyError: 'structures' | yes |
| tests/test_leading_conditional_recommendation.py::test_rejected_and_fail_closed_entries_never_become_conditional | failed | KeyError: 'structures' | yes |
| tests/test_leading_conditional_recommendation.py::test_supplying_missing_fact_promotes_conditional_structure_to_winner | failed | KeyError: 'structures' | yes |
| tests/test_leading_conditional_recommendation.py::test_verified_structure_becomes_winner_real_projects | failed | KeyError: 'structures' | yes |
| tests/test_national_cultural_status.py::test_baselines_unchanged_after_national_status_completion | failed | KeyError: 'structures' | yes |
| tests/test_national_cultural_status.py::test_national_status_opportunity_never_contaminates_ranking | failed | KeyError: 'structures' | yes |
| tests/test_opportunity_wiring.py::test_baselines_unchanged_after_opportunity_reconnection | failed | KeyError: 'structures' | yes |
| tests/test_opportunity_wiring.py::test_fvd_discovers_cultural_gap_fails_closed | failed | KeyError: 'structures' | yes |
| tests/test_opportunity_wiring.py::test_fvd_no_longer_shows_fee_cap_headroom_once_its_real_atl_spend_is_counted | failed | KeyError: 'structures' | yes |
| tests/test_opportunity_wiring.py::test_opportunities_never_contaminate_ranking | failed | KeyError: 'structures' | yes |
| tests/test_opportunity_wiring.py::test_opportunities_survive_persistence_and_api | failed | KeyError: 'structures' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_bad_hombres_and_lls_recommendation_identity_unchanged | failed | KeyError: 'top_result' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_baseline_economics_byte_identical_under_completeness_closeout[4355ae88-a636-4c18-af60-ad73b2646124-596910.25-1885112.75] | failed | KeyError: 'baseline' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_baseline_economics_byte_identical_under_completeness_closeout[6c6f1c13-2d49-4bbc-bafb-2a12efa93112-1445659.84-3072027.16] | failed | KeyError: 'baseline' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_baseline_economics_byte_identical_under_completeness_closeout[ab10b319-978e-44d3-9331-af2a5f2cccc2-3459278.9-8524375.1] | failed | KeyError: 'baseline' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_baseline_economics_byte_identical_under_completeness_closeout[fa5cade5-0669-4816-bfe6-72146f8d3bae-573059.7-3791333.3] | failed | KeyError: 'baseline' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_dominated_with_proof_rows_carry_independently_checkable_proof | failed | AssertionError: no completeness-closeout rows found -- fixture/engine mismatch | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_every_fvd_dominated_with_proof_row_has_a_complete_true_proof | failed | AssertionError: no DOMINATED_WITH_PROOF rows found -- fixture/engine mismatch | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_integrity_gate_passes_with_no_false_positive_on_real_fvd_stacking | failed | KeyError: 'structures' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_lu_and_fvd_workspace_top_result_stays_null_while_unresolved | failed | KeyError: 'top_result' | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_ordinary_component_hybrid_rows_carry_administrative_risk_and_stacking_trace | failed | AssertionError: no priced ordinary_component_hybrid rows found -- fixture/engine mismatch | yes |
| tests/test_optimizer_audit_defect_remediation.py::test_workspace_returns_engine_version_and_fingerprint_matching_persisted_rows | failed | KeyError: 'evaluation' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_every_hybrid_search_accounts_for_its_whole_candidate_space[BH] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_every_hybrid_search_accounts_for_its_whole_candidate_space[FVD] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_every_hybrid_search_accounts_for_its_whole_candidate_space[LLS] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_every_hybrid_search_accounts_for_its_whole_candidate_space[LU] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_generated_equals_persisted_plus_aggregated[BH] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_generated_equals_persisted_plus_aggregated[FVD] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_generated_equals_persisted_plus_aggregated[LLS] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_generated_equals_persisted_plus_aggregated[LU] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_home_component_family_reaches_every_per_component_destination_program[BH] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_home_component_family_reaches_every_per_component_destination_program[FVD] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_home_component_family_reaches_every_per_component_destination_program[LLS] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_home_component_family_reaches_every_per_component_destination_program[LU] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_post_vfx_music_package_is_a_real_route_and_never_a_comparison_only_value[BH] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_post_vfx_music_package_is_a_real_route_and_never_a_comparison_only_value[FVD] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_post_vfx_music_package_is_a_real_route_and_never_a_comparison_only_value[LLS] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_post_vfx_music_package_is_a_real_route_and_never_a_comparison_only_value[LU] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_relocated_principal_routes_a_single_movable_unit[BH] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_relocated_principal_routes_a_single_movable_unit[FVD] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_relocated_principal_routes_a_single_movable_unit[LLS] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_relocated_principal_routes_a_single_movable_unit[LU] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_served_universe_reconciles_to_the_generation[BH] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_served_universe_reconciles_to_the_generation[FVD] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_served_universe_reconciles_to_the_generation[LLS] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_optimizer_scenario_universe_accounting.py::test_served_universe_reconciles_to_the_generation[LU] | error | failed on setup with "AssertionError: refusing to run against 'frametax2_pytest' | yes |
| tests/test_project_workspace_view.py::test_candidate_classification_is_generic_not_per_jurisdiction | failed | KeyError: 'evaluation' | yes |
| tests/test_project_workspace_view.py::test_fvd_workspace_view_is_correct_and_self_contained | failed | AssertionError: assert 'PROJECT_NOT_FOUND' == 'OK' | yes |
| tests/test_project_workspace_view.py::test_little_utopia_workspace_view_uses_the_same_adapter | failed | AssertionError: assert 'PROJECT_NOT_FOUND' == 'OK' | yes |
| tests/test_treaty_coproduction_wiring.py::test_fvd_eurimages_opportunity_reaches_co_pro_opportunities_category | failed | KeyError: 'structures' | yes |
| tests/test_treaty_coproduction_wiring.py::test_little_utopia_home_anchored_treaty_opportunity_is_still_honestly_zero | failed | KeyError: 'structures' | yes |
| tests/test_treaty_coproduction_wiring.py::test_lu_australia_uk_bilateral_opportunity_surfaces_independent_of_mauritius | failed | KeyError: 'structures' | yes |
| tests/test_treaty_coproduction_wiring.py::test_unresolved_treaty_opportunity_cannot_rank_as_recommended | failed | KeyError: 'structures' | yes |
| tests/test_treaty_coproduction_wiring.py::test_unresolved_treaty_opportunity_never_enters_npc | failed | KeyError: 'structures' | yes |
