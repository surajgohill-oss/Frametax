"""Real-production regression tests: the tests that evaluate, read, or DELETE the stored facts of a real anchor production (Little Utopia, F#K Valentine's Day, Lips Like Sugar, Bad Hombres).

They are NOT run by default. PROJECT_RULES forbids evaluating or mutating a real production without explicit authorization, and the isolated ``frametax2_pytest`` database does not contain those
productions, so these tests could only fail or, worse, mutate real data on a shared database. ``conftest.pytest_collection_modifyitems`` deselects exactly the node ids below and prints their
count and files in the terminal summary; they run only when ``CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS`` names the productions (the same variable that lifts the conftest write guard) against a database
that contains them. The synthetic replacements live in ``test_na_synthetic_pipeline_controls.py``. ``test_real_production_isolation.py`` keeps this list honest (every entry exists and really
reaches a real production), so a test cannot be hidden here and a real-production test cannot be added elsewhere without being listed.
"""
from __future__ import annotations

import os

#: file -> test function names (parametrised cases share their function's entry)
REAL_PRODUCTION_TESTS: dict[str, tuple[str, ...]] = {
    "test_discretionary_program_policy.py": (
        "test_authority_requirements_are_never_relaxed_by_this_policy",
        "test_default_include_behavior_is_unchanged_from_before_this_policy_existed",
        "test_per_program_exclude_removes_only_saudi_case_2_leaves_universe",
        "test_project_default_exclude_removes_every_discretionary_program_at_once",
    ),
    "test_california_temporal_program_generations.py": (
        "test_lips_california_baseline_prices_its_deterministic_floor",
        "test_lips_california_discloses_administrative_and_competitive_risk",
    ),
    "test_canonical_authority_substrate.py": (
        "test_batch1_programs_price_with_real_numbers_in_fvd",
        "test_batch2_programs_price_with_real_numbers_in_fvd",
        "test_batch3_programs_price_with_real_numbers_in_fvd",
        "test_batch4_programs_price_with_real_numbers_in_fvd",
        "test_batch5_programs_price_with_real_numbers_in_fvd",
        "test_fvd_runtime_candidate_universe_restored",
        "test_georgia_prices_with_real_numbers_in_fvd",
        "test_little_utopia_exact_regression_after_authority_substrate_repair",
        "test_local_entity_assumption_remains_intact",
        "test_lu_mauritius_control_npc_unchanged",
        "test_on_ofttc_and_ocase_now_independently_served",
        "test_sa1_requirements_remain_consumed",
        "test_soft_feasibility_mismatch_does_not_reject_economic_candidate",
        "test_statutory_eligibility_failure_still_rejects_correctly",
    ),
    "test_canonical_economics_integrity_repair.py": (
        "test_a_producer_stated_baseline_outranks_a_derived_one",
        "test_authority_unresolved_program_is_served_and_priced",
        "test_combined_structures_carry_reconciled_segments_and_qpe",
        "test_conditional_nodes_never_enter_deterministic_economics",
        "test_every_production_keeps_its_known_baseline_jurisdiction",
        "test_in_kind_and_reinvestment_are_not_deterministic_benefits",
        "test_leading_structure_is_current_by_engine_and_fingerprint",
        "test_lips_source_budget_finance_is_disclosed_not_assumed",
        "test_mutually_exclusive_combination_is_not_a_priced_structure",
    ),
    "test_canonical_fx_context.py": (
        "test_cross_project_fx_isolation_two_real_projects",
    ),
    "test_canonical_served_wiring_repair.py": (
        "test_australia_location_offset_rule_rejected_with_program_identity",
        "test_australia_queensland_priced_flat_rate_not_comparable",
        "test_fvd_accounting_matches_codex_diagnosis",
        "test_fvd_unpriceable_causes_are_differentiated_not_flattened",
        "test_generic_pkg_and_economics_disclose_real_fvd_data",
        "test_greece_baseline_is_priced_and_directly_comparable",
        "test_malta_and_mauritius_priced_but_not_comparable_with_real_economics",
        "test_stale_engine_rows_never_leak_into_served_output",
    ),
    "test_final_formulaic_full_pipeline_consumption.py": (
        "test_ae_dpip_dubai_identity_serialized",
        "test_au_location_offset_full_pipeline",
        "test_cz_film_incentive_production_type_and_cap",
        "test_fr_trip_vfx_component_fact",
        "test_fvd_baseline_unchanged_after_full_file",
        "test_is_film_reimbursement_enhanced_conjunction",
        "test_ma_ccm_rebate_native_spend_and_shooting_days",
        "test_mt_mfc_rebate_general_branch_resolves",
        "test_nl_nfpi_points_independence_format_facts",
        "test_th_film_incentive_base_and_award_uplift",
        "test_th_film_incentive_exact_150m_boundary_is_exclusive_on_25pct_tier",
        "test_us_tx_miip_award_and_resident_threshold",
        "test_za_nfvf_rebate_accepted_gate_and_cap",
    ),
}


def is_real_production_test(nodeid: str) -> bool:
    """True when ``nodeid`` (``tests/test_x.py::test_y[param]``) is one of the listed real-production regression tests."""
    path, _, rest = nodeid.partition("::")
    name = rest.split("[", 1)[0].split("::")[-1]
    return name in REAL_PRODUCTION_TESTS.get(path.split("tests/", 1)[-1], ())


def authorization_given() -> bool:
    return bool(os.environ.get("CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS", "").strip())
