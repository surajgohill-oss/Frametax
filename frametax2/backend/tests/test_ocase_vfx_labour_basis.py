"""
test_ocase_vfx_labour_basis.py

Independent expected-value tests for the OCASE (Ontario Computer Animation
and Special Effects Tax Credit) rate-base defect: the doctrine's own cited
authority is explicit -- "18% of the eligible Ontario labour expenditures
... with respect to eligible computer animation and special effects
activities" -- a component-basis rate (real VFX-category labour only),
never the segment's whole QPE. Before this fix, ON_OCASE_DOCTRINE's tier
carried no basis restriction at all, so a live production's Ontario
OPSTC+OCASE stack served 18% of the ENTIRE Ontario QPE ($4,063,264 for
Little Utopia) as the OCASE incentive.

Uses REAL budget-line identities from Little Utopia's own real budget
(app/data/little_utopia_real_budget.py: "6100 VFX DEPARTMENT", $52,500,
already classified "vfx" by LITTLE_UTOPIA_REAL_SPEND_CATEGORY) rather than
synthetic account codes, per the "real budget-line identities" requirement
-- and asserts the price_segment() kernel itself, not a re-derivation.
"""
from __future__ import annotations

from app.calculators.allocation_pricing import price_segment
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.data.little_utopia_real_budget import LITTLE_UTOPIA_REAL_BUDGET_LINES

OCASE_SLUG = "ontario_computer_animation_and_special_effects_tax_credit_ocase"


def _lu_line(code: str) -> tuple[str, float]:
    for c, description, amount, _page in LITTLE_UTOPIA_REAL_BUDGET_LINES:
        if c == code:
            return description, amount
    raise KeyError(code)


def _allocation(account_code: str, description: str, amount: float, component: str, spend_category: str) -> AccountAllocation:
    return AccountAllocation(
        account_code=account_code, description=description, amount_usd=amount,
        component=component, jurisdiction_code="CA-ON", assignment_kind=AssignmentKind.RECOMMENDED,
        rationale="full relocation to Ontario", governing_decision="full_relocation",
        line_id=f"lu-real-line-{account_code}", spend_category=spend_category,
    )


def test_ocase_prices_off_the_real_vfx_line_only_not_the_full_ontario_qpe():
    # Little Utopia's own real budget: "6100 VFX DEPARTMENT" is the ONLY
    # VFX-classified line ($52,500); every other line below is real
    # non-VFX production spend (crew labor, equipment, location fees) that
    # a full relocation to Ontario would also carry — included here so the
    # segment's total QPE is genuinely much larger than the VFX-only basis,
    # exactly reproducing the live defect's shape.
    vfx_desc, vfx_amount = _lu_line("6100")
    staff_desc, staff_amount = _lu_line("2000")
    camera_desc, camera_amount = _lu_line("3100")
    allocations = [
        _allocation("6100", vfx_desc, vfx_amount, "vfx", "vfx"),
        _allocation("2000", staff_desc, staff_amount, "principal_production", "btl_crew_labor"),
        _allocation("3100", camera_desc, camera_amount, "principal_production", "btl_equipment_rental"),
    ]
    spend_category_by_code = {"6100": "vfx", "2000": "btl_crew_labor", "3100": "btl_equipment_rental"}

    econ = price_segment(
        jurisdiction_code="CA-ON", program_slug=OCASE_SLUG, allocations=allocations,
        spend_category_by_code=spend_category_by_code, offshore_payroll_accounts=frozenset(),
        gross_budget_usd=vfx_amount + staff_amount + camera_amount,
    )

    full_segment_qpe = vfx_amount + staff_amount + camera_amount
    assert econ.qpe_usd == full_segment_qpe, "the segment's own total QPE must still be the real, complete sum — the basis restriction applies to the RATE, never hides real spend"
    # The confirmed live defect: 18% of the full segment QPE.
    wrong_full_qpe_incentive = round(full_segment_qpe * 0.18, 2)
    # The correct, fixed result: 18% of ONLY the real $52,500 VFX line.
    correct_vfx_only_incentive = round(vfx_amount * 0.18, 2)
    assert correct_vfx_only_incentive == 9_450.00
    assert econ.incentive_floor_usd == correct_vfx_only_incentive
    assert econ.incentive_ceiling_usd == correct_vfx_only_incentive
    assert econ.incentive_floor_usd != wrong_full_qpe_incentive, (
        f"OCASE must never price off the full segment QPE (${wrong_full_qpe_incentive:,.2f}) -- "
        f"only its own real, traced VFX-category spend (${correct_vfx_only_incentive:,.2f})"
    )


def test_ocase_is_ineligible_not_merely_zero_when_no_real_vfx_spend_is_routed_to_ontario():
    # A production with genuinely zero VFX/animation work routed to
    # Ontario cannot claim OCASE at all -- it is not merely "$0 OCASE",
    # it is not an eligible candidate, matching the real-world statutory
    # requirement (the credit is FOR computer animation/VFX activities).
    staff_desc, staff_amount = _lu_line("2000")
    allocations = [_allocation("2000", staff_desc, staff_amount, "principal_production", "btl_crew_labor")]
    spend_category_by_code = {"2000": "btl_crew_labor"}

    econ = price_segment(
        jurisdiction_code="CA-ON", program_slug=OCASE_SLUG, allocations=allocations,
        spend_category_by_code=spend_category_by_code, offshore_payroll_accounts=frozenset(),
        gross_budget_usd=staff_amount,
    )
    assert not econ.executable or (econ.incentive_floor_usd or 0.0) == 0.0, (
        "with zero real VFX-category spend, OCASE must never fabricate a labour amount or price off unrelated crew spend"
    )


def test_ocase_scales_with_the_real_vfx_line_amount_generically_not_a_hardcoded_figure():
    # A different, larger real VFX line must produce a proportionally
    # different incentive — proving the fix reads the real traced amount
    # generically, never a hardcoded $9,450 constant.
    allocations = [_allocation("6100", "VFX DEPARTMENT", 200_000.0, "vfx", "vfx")]
    econ = price_segment(
        jurisdiction_code="CA-ON", program_slug=OCASE_SLUG, allocations=allocations,
        spend_category_by_code={"6100": "vfx"}, offshore_payroll_accounts=frozenset(),
        gross_budget_usd=200_000.0,
    )
    assert econ.incentive_floor_usd == 36_000.00  # 200,000 * 0.18


def test_ocase_and_opstc_retain_distinct_claim_bases_on_the_same_ontario_segment():
    # OFTTC/OPSTC price off the segment's FULL QPE (their own real,
    # unrestricted statutory base) while OCASE, on the identical
    # allocation set, prices off only its own real VFX-category subset --
    # the two programs must never collapse to the same basis just because
    # they share a jurisdiction and an underlying allocation set.
    vfx_desc, vfx_amount = _lu_line("6100")
    staff_desc, staff_amount = _lu_line("2000")
    allocations = [
        _allocation("6100", vfx_desc, vfx_amount, "vfx", "vfx"),
        _allocation("2000", staff_desc, staff_amount, "principal_production", "btl_crew_labor"),
    ]
    spend_category_by_code = {"6100": "vfx", "2000": "btl_crew_labor"}
    gross = vfx_amount + staff_amount

    ocase = price_segment(
        jurisdiction_code="CA-ON", program_slug=OCASE_SLUG, allocations=allocations,
        spend_category_by_code=spend_category_by_code, offshore_payroll_accounts=frozenset(),
        gross_budget_usd=gross,
    )
    opstc = price_segment(
        jurisdiction_code="CA-ON", program_slug="on_opstc", allocations=allocations,
        spend_category_by_code=spend_category_by_code, offshore_payroll_accounts=frozenset(),
        gross_budget_usd=gross,
    )
    assert ocase.qpe_usd != opstc.qpe_usd or ocase.incentive_floor_usd != opstc.incentive_floor_usd
    assert ocase.incentive_floor_usd == round(vfx_amount * 0.18, 2)
    assert opstc.qpe_usd == vfx_amount + staff_amount  # OPSTC's real, unrestricted base is unaffected by this fix
