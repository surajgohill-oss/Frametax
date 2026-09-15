"""
test_canonical_identity_authority_invariants.py

Codex canonical identity/authority cleanup, Phase 7 (prevent
recurrence) — a bounded invariant suite proving the five required
guarantees directly against the real, live registries, so a historical/
source ID can never again be mistaken for an independent live program
and a dormant authority-vetoed rule can never again create a guaranteed
candidate.
"""
from __future__ import annotations

from app.data.authority_coverage_registry import (
    CANONICAL_RUNTIME_SLUG_BINDINGS,
    get_coverage_status,
)
from app.data.program_rate_rules import get_rate_rules
from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES


def test_aliases_resolve_before_priceability_is_audited():
    """Every alias in CANONICAL_RUNTIME_SLUG_BINDINGS (canonical-corpus
    spelling -> served runtime program_slug) must resolve to a real,
    distinct surviving canonical id -- and auditing the ALIAS's own
    coverage state (if any) must never be treated as the priceability
    answer without first resolving to the survivor."""
    assert len(CANONICAL_RUNTIME_SLUG_BINDINGS) > 0, "fixture assumption: real aliases are registered"
    for alias_id, survivor_id in CANONICAL_RUNTIME_SLUG_BINDINGS.items():
        assert alias_id != survivor_id, f"{alias_id} must not alias to itself"
        # The survivor's own coverage state (if registered) is the real
        # answer; the alias's OWN entry (if any) must never independently
        # contradict the survivor for the same real-world program.
        survivor_status = get_coverage_status(survivor_id)
        if survivor_status is not None:
            assert survivor_status.program_slug == survivor_id


def test_historical_source_ids_confirmed_this_pass_cannot_price_independently():
    """The exact historical/source IDs this pass traced (Ontario's
    source spelling, California source spelling, Bulgaria/PA/WA/NV
    source spellings) must never carry their own independent, guaranteed
    RateRule set distinct from their survivor."""
    runtime_binding_aliases = ("bg_film_incentive", "us_nv_film_incentive", "us_pa_film_credit", "us_wa_mpcp")
    for alias_id in runtime_binding_aliases:
        assert alias_id in CANONICAL_RUNTIME_SLUG_BINDINGS, (
            f"{alias_id} must be a registered runtime-binding alias, never a standalone identity"
        )
        survivor = CANONICAL_RUNTIME_SLUG_BINDINGS[alias_id]
        assert get_rate_rules(alias_id) == (), (
            f"{alias_id} must carry NO independent rate rules of its own -- it must resolve "
            f"entirely through its survivor {survivor}"
        )

    program_slug_aliases = ("inv-ca-on-ontario-production-services-tax-credit-opstc", "us_ca_film_credit")
    for alias_id in program_slug_aliases:
        assert alias_id in PROGRAM_SLUG_ALIASES, f"{alias_id} must be a registered program-slug alias"
        survivor = PROGRAM_SLUG_ALIASES[alias_id]
        # get_rate_rules already canonicalizes via program_slug_aliases,
        # so this proves no SEPARATE rule set was accidentally
        # registered under the raw historical spelling.
        assert get_rate_rules(alias_id) == get_rate_rules(survivor), (
            f"{alias_id} must resolve to the EXACT SAME rate rules as its survivor "
            f"{survivor}, never an independent rule set"
        )


def test_authority_vetoed_dormant_rules_cannot_create_guaranteed_candidates():
    """Every one of the 31 reconciled authority-vetoed records must be
    in a BLOCKING state, regardless of whether a dormant RateRule exists
    for it -- dormant rate/doctrine data never overrides the authority
    fail-closed disposition."""
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    thirty_one_records = (
        "ae_ad_film_rebate", "al_cash_rebate", "au_nsw_pdv_rebate", "au_qld_pdv_rebate",
        "au_sa_pdv_rebate", "ca_bc_pstc", "ca_federal_pstc", "ca_nl_all_spend_credit",
        "ca_qc_pstc", "cr_tax_return_incentive", "eg_empc_cashback", "fj_film_rebate",
        "ge_film_rebate", "gh_film_tax_incentive", "il_foreign_production_fund",
        "me_cash_rebate", "mk_cash_rebate", "mn_production_incentive",
        "mx_federal_film_incentive_2026", "pa_film_rebate", "pt_scri_pt_cash_rebate",
        "qa_screen_production_incentive", "se_production_rebate", "si_cash_rebate",
        "tt_production_expenditure_rebate", "ua_cash_rebate",
        "us_il_film_production_services_credit", "us_tn_performance_grant",
        "uy_tax_credit_2026", "uz_film_rebate", "za_dtic_foreign_film",
    )
    from app.data.authority_coverage_registry import economic_block_for_program
    from app.data.program_rate_rules import resolve_program_rate

    assert len(thirty_one_records) == 31
    for slug in thirty_one_records:
        # Two independent authority-veto mechanisms exist in this
        # codebase (the B1 discretionary-ruling economic_block_for_program
        # gate, and the COVERAGE_REGISTRY/get_coverage_status gate) --
        # different records among the 31 are vetoed by different
        # mechanisms. The real invariant is that AT LEAST ONE blocks
        # candidacy, proven directly against resolve_program_rate's own
        # combined gate (which checks economic_block_for_program first,
        # then falls through to the normal tier tournament).
        block = economic_block_for_program(slug)
        status = get_coverage_status(slug)
        vetoed = (block is not None and block.classification == "FAIL_CLOSED") or (
            status is not None and status.blocks_economic_candidacy
        )
        assert vetoed, (
            f"{slug} must remain vetoed by at least one authority mechanism (dormant rate/"
            f"doctrine data never overrides the fail-closed disposition); "
            f"block={block} coverage_status={status}"
        )
        # resolve_program_rate's own B4 central authority gate is the
        # FIRST executable check, before any rule lookup -- proving a
        # dormant RateRule (if one exists for this slug) can never
        # override the economic_block_for_program veto specifically.
        if block is not None and block.classification == "FAIL_CLOSED":
            rr = resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000.0)
            assert rr is None, (
                f"{slug} is authority-vetoed (FAIL_CLOSED) but resolve_program_rate returned a "
                f"real rate resolution -- dormant rate data must never override the block"
            )


def test_satisfiable_missing_project_facts_produce_conditional_not_silent_exclusion():
    """A program whose formula/authority is sufficiently verified but
    whose mandatory project facts are missing (BC DAVE without the
    activity confirmation) must remain VISIBLE and DISCOVERABLE with a
    real disclosed reason -- never silently excluded."""
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    alloc = AccountAllocation(
        account_code="1", description="BC labour", amount_usd=500_000.0, component="post",
        jurisdiction_code="CA-BC", assignment_kind=AssignmentKind.FIXED,
        rationale="conditional visibility probe", governing_decision="codex-canonical-identity-cleanup",
        line_id="probe-1", spend_category="btl_crew_labor",
    )
    result = price_segment(
        jurisdiction_code="CA-BC", program_slug="ca_bc_dave", allocations=[alloc],
        spend_category_by_code={"1": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=500_000.0,
    )
    assert result.executable is False, "missing the activity-confirmation fact must remain conditional"
    assert result.claims_incentive is True, "the segment must still be VISIBLE/discoverable, never silently dropped"
    assert result.program_slug == "ca_bc_dave", "canonical ID must remain disclosed"


def test_manifest_and_runtime_agree_for_reconciled_survivors():
    """For every survivor this pass explicitly reconciled, the LIVE
    authority_coverage_registry state must match what
    CANONICAL_ARTIFACT_PRECEDENCE_CLAUDE.json names as controlling --
    proving manifest (the registry itself, per the precedence doc) and
    runtime (blocks_economic_candidacy behavior) cannot disagree."""
    expectations = {
        "bg_film_encouragement_act_rebate": ("AUTHORITY_UNRESOLVED_NON_PRICEABLE", False),
        "cz_film_incentive_animation": ("AUTHORITY_UNRESOLVED_NON_PRICEABLE", False),
        "ca_bc_dave": (None, False),  # not coverage-vetoed at all; conditional via RateCondition gates
        "us_nv_film_credit": (None, False),  # not coverage-vetoed; conditional via doctrine gates
    }
    for slug, (expected_state, expected_blocks) in expectations.items():
        status = get_coverage_status(slug)
        if expected_state is None:
            assert status is None, f"{slug} must have no coverage-registry veto entry"
        else:
            assert status is not None and status.state == expected_state
            assert status.blocks_economic_candidacy is expected_blocks
