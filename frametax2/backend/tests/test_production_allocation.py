"""Tests for production_allocation — the account->jurisdiction
allocation model. Conservation, uniqueness, explicit-split discipline,
assignment-kind semantics, and honest incompleteness."""
from __future__ import annotations

import pytest

from app.calculators.production_allocation import (
    AssignmentKind,
    MOVABLE_COMPONENTS,
    NON_PARTICIPANT_STATED_LOCATION,
    StructureSpec,
    component_for,
    derive_account_allocation,
)
from app.calculators.qualification_derivation import BudgetLine
from app.data.little_utopia_real_budget import (
    LEAF_ACCOUNT_SUM_USD,
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


def _baseline_spec(**overrides) -> StructureSpec:
    kwargs = dict(
        structure_id="T-BASE-MU",
        structure_type="single_country",
        label="test baseline",
        primary_jurisdiction="MU",
        participants=("MU",),
        incentive_programs={"MU": "mu_edb_incentive"},
    )
    kwargs.update(overrides)
    return StructureSpec(**kwargs)


def _allocate(spec, lines=None):
    return derive_account_allocation(
        lines=lines if lines is not None else _real_lines(),
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        spec=spec,
        stated_outside_accounts=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    )


# ── conservation & uniqueness ────────────────────────────────────────────────

def test_every_cash_dollar_allocated_exactly_once_baseline():
    result = _allocate(_baseline_spec())
    assert result.is_complete
    assert result.conserves
    assert result.total_allocated_usd == LEAF_ACCOUNT_SUM_USD
    assert result.total_budget_lines_usd == LEAF_ACCOUNT_SUM_USD
    # exactly once: no account appears in two jurisdictions absent a split
    codes = [a.account_code for a in result.assignments]
    assert len(codes) == len(set(codes)) == len(LITTLE_UTOPIA_REAL_BUDGET_LINES)
    assert result.unallocated_account_codes == ()
    assert result.duplicate_account_codes == ()


def test_no_account_silently_omitted_route_to_nonparticipant_is_incomplete():
    spec = _baseline_spec(account_routes={"6100": "FR"})  # FR not a participant
    result = _allocate(spec)
    assert "6100" in result.unallocated_account_codes
    assert not result.is_complete
    assert any("6100" in n for n in result.notes)


def test_memo_lines_excluded_from_conservation_with_note():
    lines = _real_lines() + [BudgetLine("9999", "VAT MEMO", 1000.0, None, is_memo=True)]
    result = _allocate(_baseline_spec(), lines=lines)
    assert result.is_complete
    assert result.total_allocated_usd == LEAF_ACCOUNT_SUM_USD  # memo not counted
    assert any("9999" in n and "memo" in n for n in result.notes)


def test_duplicate_input_lines_reported_never_double_counted():
    lines = _real_lines()
    lines.append(lines[0])  # duplicate account code
    result = _allocate(_baseline_spec(), lines=lines)
    assert lines[0].account_code in result.duplicate_account_codes
    assert not result.is_complete


# ── stated-location facts & assignment kinds ────────────────────────────────

def test_stated_location_accounts_fixed_to_stated_location():
    result = _allocate(_baseline_spec())
    by_code = {a.account_code: a for a in result.assignments}
    for code in LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU:
        a = by_code[code]
        assert a.jurisdiction_code == NON_PARTICIPANT_STATED_LOCATION
        assert a.assignment_kind == AssignmentKind.FIXED
        assert a.governing_decision == "stated_location_fact"


def test_location_bound_components_fixed_to_primary():
    result = _allocate(_baseline_spec())
    by_code = {a.account_code: a for a in result.assignments}
    marine = by_code["3300"]  # SPECIAL EFFECTS & MARINE — vessel_marine
    assert marine.component == "principal_photography"
    assert marine.jurisdiction_code == "MU"
    assert marine.assignment_kind == AssignmentKind.FIXED


def test_movable_component_defaults_recommended_to_primary():
    result = _allocate(_baseline_spec())
    by_code = {a.account_code: a for a in result.assignments}
    vfx = by_code["6100"]  # VFX, location unstated
    assert vfx.component == "vfx"
    assert vfx.jurisdiction_code == "MU"
    assert vfx.assignment_kind == AssignmentKind.RECOMMENDED


def test_component_route_overrides_stated_location_with_requirement():
    spec = _baseline_spec(
        structure_id="T-COMP-MT",
        structure_type="component_relocation",
        participants=("MU", "MT"),
        incentive_programs={"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate"},
        component_routes={c: "MT" for c in MOVABLE_COMPONENTS},
    )
    result = _allocate(spec)
    by_code = {a.account_code: a for a in result.assignments}
    edit = by_code["5000"]  # EDITORIAL — stated LA, now routed
    assert edit.jurisdiction_code == "MT"
    assert edit.unresolved_requirements  # confirm-the-change requirement
    assert any("stated location" in r for r in edit.unresolved_requirements)
    assert result.is_complete


# ── explicit splits ──────────────────────────────────────────────────────────

def test_explicit_split_is_user_elected_and_conserves():
    spec = _baseline_spec(
        structure_id="T-SPLIT",
        structure_type="split_production",
        participants=("MU", "GR"),
        incentive_programs={"MU": "mu_edb_incentive", "GR": "gr_cash_rebate"},
        account_splits={"3400": {"MU": 0.7, "GR": 0.3}},
    )
    result = _allocate(spec)
    portions = [a for a in result.assignments if a.account_code == "3400"]
    assert len(portions) == 2
    assert all(a.assignment_kind == AssignmentKind.USER_ELECTED for a in portions)
    assert sorted(a.split_pct for a in portions) == [0.3, 0.7]
    assert round(sum(a.amount_usd for a in portions), 2) == 496_232.0
    assert result.is_complete  # split portions still conserve the total


def test_split_percentages_must_sum_to_one():
    with pytest.raises(ValueError, match="summing to 1.0"):
        _allocate(_baseline_spec(
            structure_type="split_production",
            participants=("MU", "GR"),
            account_splits={"3400": {"MU": 0.5, "GR": 0.3}},
        ))


def test_split_to_nonparticipant_rejected():
    with pytest.raises(ValueError, match="non-participant"):
        _allocate(_baseline_spec(
            structure_type="split_production",
            participants=("MU",),
            account_splits={"3400": {"MU": 0.5, "FR": 0.5}},
        ))


# ── spec validation & component vocabulary ──────────────────────────────────

def test_unknown_structure_type_rejected():
    with pytest.raises(ValueError, match="structure_type"):
        _baseline_spec(structure_type="not_a_type")


def test_component_vocabulary_covers_movables():
    assert component_for("post_production") == "post"
    assert component_for("vfx") == "vfx"
    assert component_for("music") == "music"
    assert component_for("btl_crew_labor") == "principal_photography"
    assert component_for(None) == "principal_photography"
