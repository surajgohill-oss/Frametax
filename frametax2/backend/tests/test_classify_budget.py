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
