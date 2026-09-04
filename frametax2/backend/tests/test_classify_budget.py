"""
Unit tests: budget line item classification.
Deterministic — no DB, no LLM, no network.
"""
import pytest
from app.calculators.classify_budget_line_items import classify_line_item, classify_atl_btl_split
from app.models.enums import ATLBTLCategory, CompensationType, SpendCategory


def test_director_fee_is_atl_fixed():
    r = classify_line_item("Director Fee")
    assert r.atl_btl == ATLBTLCategory.ATL
    assert r.is_fixed is True
    assert r.is_labor is True


def test_crew_labor_is_btl():
    r = classify_line_item("Crew labor")
    assert r.atl_btl == ATLBTLCategory.BTL
    assert r.is_fixed is False


def test_vfx_is_post():
    r = classify_line_item("VFX")
    assert r.atl_btl == ATLBTLCategory.POST
    assert r.spend_category == SpendCategory.VFX


def test_insurance_is_other():
    r = classify_line_item("Insurance")
    assert r.atl_btl == ATLBTLCategory.OTHER
    assert r.spend_category == SpendCategory.INSURANCE


def test_deferred_fee_compensation_type():
    r = classify_line_item("Director deferred fee")
    assert r.compensation_type == CompensationType.DEFERRED


def test_equity_compensation_type():
    # Use a description that doesn't trigger the higher-priority cast rule
    r = classify_line_item("equity participation backend deal")
    assert r.compensation_type == CompensationType.EQUITY


def test_classify_atl_btl_split_totals():
    items = [
        {"description": "Director Fee", "amount_usd": 200_000},
        {"description": "Lead Cast", "amount_usd": 400_000},
        {"description": "Crew labor", "amount_usd": 500_000},
        {"description": "Equipment Rental", "amount_usd": 100_000},
        {"description": "Insurance", "amount_usd": 50_000},
    ]
    result = classify_atl_btl_split(items)
    totals = result["totals"]
    assert totals["fixed_atl_usd"] == 600_000
    assert totals["variable_btl_usd"] == 600_000
    assert totals["other_total_usd"] == 50_000


def test_completion_bond_is_other():
    r = classify_line_item("Completion Bond Premium")
    assert r.atl_btl == ATLBTLCategory.OTHER
    assert r.spend_category == SpendCategory.COMPLETION_BOND


def test_writer_fee_is_atl():
    r = classify_line_item("Writer fee", "ATL")
    assert r.atl_btl == ATLBTLCategory.ATL
    assert r.spend_category == SpendCategory.ATL_WRITER


def test_contingency_correctly_spelled_is_classified():
    r = classify_line_item("Contingency reserve")
    assert r.spend_category == SpendCategory.CONTINGENCY


def test_contingency_real_misspelling_is_still_classified():
    """Little Utopia Economic Reconciliation: the real source budget PDF
    spells this line "Contigency" (missing the 'n', account 8300,
    $301,131.00) — a real, generic misspelling that silently defeated
    contingency detection for ANY production with this typo, not a
    Little Utopia-specific issue. Independently confirmed against this
    exact account's own hand-verified classification in
    app/data/little_utopia_real_budget.py (`"8300": "contingency"`)."""
    r = classify_line_item("8300 Contigency : 7.5%")
    assert r.spend_category == SpendCategory.CONTINGENCY


def test_contingency_misspelling_fix_does_not_over_match():
    """The fix (contin?gency) makes only the ONE real 'n' before 'g'
    optional — it must not turn into a loose wildcard that matches
    unrelated words."""
    r = classify_line_item("Continuity supervisor")
    assert r.spend_category != SpendCategory.CONTINGENCY


# ── Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 2 ──
#
# ROOT CAUSE FINDING: F#K Valentine's Day's real source budget line
# ("7901 FINANCE FEE : 12.5%", $453,583) was ALREADY correctly classified
# SpendCategory.FINANCE_COSTS at ingestion — confirmed against the live
# database, not assumed. This was never a classification/ingestion
# defect; the producer-facing "Finance costs $0" contradiction was a
# separate frontend label-collision bug (BudgetRail.jsx's editable
# financing_cost_usd row sharing the exact label "Finance costs" with
# the real classified amount) — see BudgetRail.jsx's SourceBudgetFinanceLine.
#
# The ONE real, PROVEN (not guessed) generic classification gap found
# while auditing this rule: "LENDER FEE" — one of the task's six named
# finance-cost synonyms — did not match the prior pattern
# ("financ|interest|loan fee|bank fee|banking|bridge"). Fixed generically
# via the canonical classifier architecture (never an F#K-only mapping).

@pytest.mark.parametrize("description", [
    "FINANCE FEE",
    "FINANCING FEE",
    "FINANCE COST",
    "FINANCING COST",
    "LENDER FEE",
    "LOAN FEE",
    "7901 FINANCE FEE  : 12.5%",  # F#K Valentine's Day's real source line
])
def test_finance_fee_synonyms_classify_as_finance_costs(description):
    r = classify_line_item(description)
    assert r.spend_category == SpendCategory.FINANCE_COSTS, (
        f"{description!r} is a plainly-labeled finance-cost line and must classify as FINANCE_COSTS"
    )
    assert r.atl_btl == ATLBTLCategory.OTHER


def test_lender_fee_word_boundary_does_not_over_match():
    """The fix for LENDER FEE is word-bounded (\\blend(er|ing)\\b), not a
    bare 'lend' substring search — an unbounded pattern would also match
    "Color Blending (post)" / "Blending suite rental", since "blending"
    contains the literal substring "lending". Proven false positive,
    fixed before landing; this test locks it out permanently."""
    r = classify_line_item("Color Blending (post)")
    assert r.spend_category != SpendCategory.FINANCE_COSTS
    assert r.spend_category == SpendCategory.POST_PRODUCTION

    r2 = classify_line_item("Blending suite rental")
    assert r2.spend_category != SpendCategory.FINANCE_COSTS
