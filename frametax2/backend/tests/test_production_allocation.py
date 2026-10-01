"""Tests for production_allocation — the account->jurisdiction
allocation model. Conservation, uniqueness, explicit-split discipline,
assignment-kind semantics, and honest incompleteness."""
from __future__ import annotations

import pytest

from app.calculators.production_allocation import (
    AssignmentKind,
    COMPONENT_BUNDLE_MEMBERS,
    MOVABLE_COMPONENTS,
    NON_PARTICIPANT_STATED_LOCATION,
    StructureSpec,
    component_bundle_for,
    component_for,
    derive_account_allocation,
    spend_categories_for_component,
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


# ── non-unique account codes (Fresh Project Budget Normalization) ───────────
# Real budgets legitimately reuse an account code across distinct lines
# (e.g. Lips Like Sugar's real "4900" appearing on both a Production-section
# fringes line and a Post-Production titles line). account_code is a
# classification field, never the identity of a line — BudgetLine.line_id is.

def test_two_distinct_spend_lines_sharing_an_account_code_both_survive():
    lines = [
        BudgetLine(account_code="4900", description="TOTAL FRINGES",
                   amount_usd=1_023_115.0, spend_category="btl_crew_labor"),
        BudgetLine(account_code="4900", description="MAIN AND END TITLES",
                   amount_usd=10_500.0, spend_category="post_production"),
    ]
    assert lines[0].line_id != lines[1].line_id  # distinct identity despite equal code

    result = derive_account_allocation(
        lines=lines,
        spend_category_by_code={},
        spec=_baseline_spec(),
    )

    # both lines survive — no silent drop, no duplicate-code rejection
    assert len(result.assignments) == 2
    assert result.duplicate_account_codes == ()
    by_desc = {a.description: a for a in result.assignments}
    assert set(by_desc) == {"TOTAL FRINGES", "MAIN AND END TITLES"}

    # account code preserved as a classification attribute on both
    assert all(a.account_code == "4900" for a in result.assignments)
    # each assignment traces back to its own distinct source line
    assert by_desc["TOTAL FRINGES"].line_id == lines[0].line_id
    assert by_desc["MAIN AND END TITLES"].line_id == lines[1].line_id
    assert by_desc["TOTAL FRINGES"].line_id != by_desc["MAIN AND END TITLES"].line_id

    # source amounts preserved exactly
    assert by_desc["TOTAL FRINGES"].amount_usd == 1_023_115.0
    assert by_desc["MAIN AND END TITLES"].amount_usd == 10_500.0

    # conservation: total allocated == total budget lines, no code-collision
    # blocker remains
    assert result.total_budget_lines_usd == 1_033_615.0
    assert result.total_allocated_usd == 1_033_615.0
    assert result.conserves
    assert result.is_complete


def test_subtotal_header_and_real_spend_line_sharing_a_code_are_not_conflated():
    """A subtotal/header line is excluded upstream (budget_parser's own
    _GROUP_SUBTOTAL_RE sentinel semantics) before it ever reaches
    derive_account_allocation as a BudgetLine — so by the time two lines
    share a code here, both are, by construction, real monetary lines.
    This test proves the allocator itself never treats a shared code as a
    signal to collapse/drop one line: total conservation is the only
    correctness check it performs, and it must hold even when one of the
    two same-coded lines is a much smaller "administrative" amount that
    could be mistaken for a subtotal remainder."""
    lines = [
        BudgetLine(account_code="8300", description="CONTINGENCY RESERVE",
                   amount_usd=200_000.0, spend_category="contingency"),
        BudgetLine(account_code="8300", description="CONTINGENCY — DEPLOYED TO POST",
                   amount_usd=25_000.0, spend_category="post_production"),
    ]
    result = derive_account_allocation(
        lines=lines,
        spend_category_by_code={},
        spec=_baseline_spec(),
    )
    assert len(result.assignments) == 2
    assert result.duplicate_account_codes == ()
    assert round(result.total_allocated_usd, 2) == 225_000.0
    assert round(result.total_budget_lines_usd, 2) == 225_000.0
    assert result.conserves
    assert result.is_complete
    # neither line is dropped in favor of the other
    amounts = sorted(a.amount_usd for a in result.assignments)
    assert amounts == [25_000.0, 200_000.0]


# ---------------------------------------------------------------------------
# COMPONENT-BUNDLE CORRECTION (2026-09-30): post+vfx bundle into
# POST_VFX_PACKAGE by default; music remains its own bundle; a bundle member
# is independently routable (in ADDITION to its bundle) only when a real
# destination program specifically distinguishes its spend category.
# ---------------------------------------------------------------------------

def test_component_bundle_for_groups_post_and_vfx_music_separate():
    assert component_bundle_for("post") == "post_vfx_package"
    assert component_bundle_for("vfx") == "post_vfx_package"
    assert component_bundle_for("music") == "music_package"


def test_component_bundle_for_is_identity_for_unregistered_components():
    assert component_bundle_for("overhead") == "overhead"
    assert component_bundle_for("principal_photography") == "principal_photography"


def test_component_bundle_members_matches_bundle_for_both_directions():
    for bundle, members in COMPONENT_BUNDLE_MEMBERS.items():
        for member in members:
            assert component_bundle_for(member) == bundle


def test_spend_categories_for_component_returns_real_categories_never_the_label():
    # "post" the component label is never itself a real spend_category --
    # its real categories are "post_production" and "sound".
    assert set(spend_categories_for_component("post")) == {"post_production", "sound"}
    # "vfx" and "music" happen to share their literal string with their own
    # single spend category -- confirmed, not assumed.
    assert spend_categories_for_component("vfx") == ("vfx",)
    assert spend_categories_for_component("music") == ("music",)


def test_spend_categories_for_component_empty_for_unregistered_component():
    assert spend_categories_for_component("nonexistent_component") == ()


def test_derive_account_allocation_routes_bundle_key_for_all_member_lines():
    """A component_routes entry keyed by the BUNDLE ("post_vfx_package")
    routes every line whose own fine-grained component is a bundle member
    (post OR vfx) -- never requiring the caller to name each member
    individually."""
    lines = [
        BudgetLine(account_code="4100", description="EDITORIAL", amount_usd=50_000.0,
                   spend_category="post_production"),
        BudgetLine(account_code="4200", description="VFX VENDOR", amount_usd=30_000.0,
                   spend_category="vfx"),
    ]
    result = derive_account_allocation(
        lines=lines, spend_category_by_code={},
        spec=_baseline_spec(
            participants=("MU", "CA-ON"),
            incentive_programs={"MU": "mu_edb_incentive", "CA-ON": "on_ofttc"},
            component_routes={"post_vfx_package": "CA-ON"},
        ),
    )
    assert result.conserves
    jurisdictions = {a.account_code: a.jurisdiction_code for a in result.assignments}
    assert jurisdictions["4100"] == "CA-ON"
    assert jurisdictions["4200"] == "CA-ON"
    # the real, fine-grained component is still recorded on each line --
    # bundling is a routing decision, never a relabeling of the real spend.
    components = {a.account_code: a.component for a in result.assignments}
    assert components["4100"] == "post"
    assert components["4200"] == "vfx"


def test_derive_account_allocation_fine_grained_route_overrides_bundle_for_that_member_only():
    """A combination naming BOTH the bundle and one specific member splits
    that member out to its own target while the bundle continues to cover
    the rest -- never a parallel allocation mechanism, never double-routing."""
    lines = [
        BudgetLine(account_code="4100", description="EDITORIAL", amount_usd=50_000.0,
                   spend_category="post_production"),
        BudgetLine(account_code="4200", description="VFX VENDOR", amount_usd=30_000.0,
                   spend_category="vfx"),
    ]
    result = derive_account_allocation(
        lines=lines, spend_category_by_code={},
        spec=_baseline_spec(
            participants=("MU", "CA-ON", "CA-NL"),
            incentive_programs={"MU": "mu_edb_incentive", "CA-ON": "on_ofttc", "CA-NL": "ca_nl_all_spend_credit"},
            component_routes={"post_vfx_package": "CA-ON", "vfx": "CA-NL"},
        ),
    )
    assert result.conserves
    jurisdictions = {a.account_code: a.jurisdiction_code for a in result.assignments}
    assert jurisdictions["4100"] == "CA-ON"  # post stays with the bundle route
    assert jurisdictions["4200"] == "CA-NL"  # vfx independently split out
