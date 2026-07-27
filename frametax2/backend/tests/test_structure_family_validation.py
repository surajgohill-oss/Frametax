"""
Backend-completion tranche, Objective 3: structure-family validation
with controlled inputs.

Prior coverage exercised single_country, component_relocation, and
split_production structure types directly (test_production_allocation.py,
test_allocation_pricing.py, test_phase_f.py); the treaty-adjacent
families (treaty_coproduction, hybrid, majority_minority, multi_party)
were exercised at the treaty_engine.py registry level
(test_treaty_coproduction.py) but not through the full
StructureSpec -> derive_account_allocation -> price_allocated_structure
pipeline with a controlled, real-treaty-pair input. This file closes
that specific gap — it does not re-test what test_production_allocation.py
or test_treaty_coproduction.py already cover.
"""
from __future__ import annotations

from app.calculators.allocation_pricing import price_allocated_structure
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.qualification_derivation import BudgetLine
from app.data.little_utopia_real_budget import (
    LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_REAL_BUDGET_LINES,
    LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
)


def _real_lines() -> list[BudgetLine]:
    return [
        BudgetLine(
            account_code=c, description=d, amount_usd=a,
            spend_category=LITTLE_UTOPIA_REAL_SPEND_CATEGORY.get(c), is_memo=False,
        )
        for c, d, a, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES
    ]


def _price(spec: StructureSpec):
    allocation = derive_account_allocation(
        lines=_real_lines(),
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        spec=spec,
        stated_outside_accounts=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    )
    assert allocation.is_complete and allocation.conserves, (
        f"controlled-input allocation itself is broken for {spec.structure_type} — "
        "fix the test fixture before trusting any pricing assertion below"
    )
    return price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        offshore_payroll_accounts=frozenset(),
        gross_budget_usd=allocation.total_budget_lines_usd,
    )


class TestTreatyCoproductionFamily:
    """CA-FR is a REAL, registered bilateral treaty pair
    (treaty_engine.get_bilateral_treaty) — a controlled positive input."""

    def test_covered_treaty_pair_is_not_blocked_on_treaty_grounds(self):
        spec = StructureSpec(
            structure_id="T-TREATY-CA-FR", structure_type="treaty_coproduction",
            label="CA-FR treaty test", primary_jurisdiction="CA",
            participants=("CA", "FR"),
            incentive_programs={"CA": "ca_federal_pstc", "FR": "fr_trip"},
        )
        pricing = _price(spec)
        treaty_blockers = [b for b in pricing.blockers if "co-production treaty instrument" in b]
        assert treaty_blockers == []
        assert pricing.treaty_slug == "ca-fr-bilateral"

    def test_uncovered_pair_blocks_with_the_exact_treaty_reason(self):
        """MU has no bilateral treaty with any partner in this registry —
        a deliberately uncovered pair."""
        spec = StructureSpec(
            structure_id="T-TREATY-MU-JP", structure_type="treaty_coproduction",
            label="MU-JP treaty test (uncovered)", primary_jurisdiction="MU",
            participants=("MU", "JP"),
            incentive_programs={"MU": "mu_edb_incentive", "JP": "jp_vipo_location_incentive"},
        )
        pricing = _price(spec)
        assert any("No co-production treaty instrument is registered" in b for b in pricing.blockers)
        assert pricing.is_fully_priced is False


class TestOwnershipShareValidation:
    """hybrid / majority_minority / multi_party all route through the same
    _treaty_requirements ownership-share check — one controlled input per
    failure mode, not per structure_type label (the check is identical
    code for all four families)."""

    def test_shares_not_summing_to_one_blocks(self):
        spec = StructureSpec(
            structure_id="T-HYBRID-BADSHARES", structure_type="hybrid",
            label="hybrid bad shares", primary_jurisdiction="CA",
            participants=("CA", "FR"),
            incentive_programs={"CA": "ca_federal_pstc", "FR": "fr_trip"},
            ownership_shares={"CA": 0.6, "FR": 0.6},  # sums to 1.2, not 1.0
        )
        pricing = _price(spec)
        assert any("must sum to 1.0" in b for b in pricing.blockers)

    def test_claimed_majority_unsupported_by_real_spend_blocks(self):
        """CA claims 60% ownership (majority) but the real Little Utopia
        budget's spend, once allocated to a CA/FR structure, does not
        actually place 20%+ of cash in CA — a real, controlled
        participation-vs-spend mismatch."""
        spec = StructureSpec(
            structure_id="T-MAJMIN-CLAIM", structure_type="majority_minority",
            label="majority/minority claim test", primary_jurisdiction="FR",
            participants=("FR", "CA"),
            incentive_programs={"FR": "fr_trip", "CA": "ca_federal_pstc"},
            ownership_shares={"FR": 0.4, "CA": 0.6},
            account_routes={code: "FR" for code, *_ in LITTLE_UTOPIA_REAL_BUDGET_LINES},
        )
        pricing = _price(spec)
        assert any("claims majority participation" in b for b in pricing.blockers)

    def test_valid_shares_summing_to_one_do_not_trigger_the_sum_blocker(self):
        spec = StructureSpec(
            structure_id="T-MULTIPARTY-VALID", structure_type="multi_party",
            label="multi-party valid shares", primary_jurisdiction="CA",
            participants=("CA", "FR"),
            incentive_programs={"CA": "ca_federal_pstc", "FR": "fr_trip"},
            ownership_shares={"CA": 0.5, "FR": 0.5},
        )
        pricing = _price(spec)
        assert not any("must sum to 1.0" in b for b in pricing.blockers)


class TestNonTreatyFamiliesUnaffectedByTreatyLogic:
    """single_country / full_relocation / component_relocation /
    split_production must never invoke the treaty-requirements check —
    _treaty_requirements's own early-return on structure_type is the
    guard; this proves it holds for full_relocation specifically (the
    other three already have direct coverage elsewhere)."""

    def test_full_relocation_never_produces_a_treaty_blocker(self):
        spec = StructureSpec(
            structure_id="T-FULLRELOC-CA", structure_type="full_relocation",
            label="full relocation, no treaty claim", primary_jurisdiction="CA",
            participants=("CA",),
            incentive_programs={"CA": "ca_federal_pstc"},
        )
        pricing = _price(spec)
        assert not any("treaty" in b.lower() for b in pricing.blockers)
        assert pricing.treaty_slug is None
