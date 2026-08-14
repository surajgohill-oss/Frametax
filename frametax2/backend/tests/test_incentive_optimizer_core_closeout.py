"""Focused tests for the Incentive/Optimizer Core Closeout task:
- the discretionary-ceiling confirmation mechanism (MU/MT/GB no longer
  auto-serve a band ceiling with an unconfirmed condition, with an
  explicit per-scenario override available)
- the Australia A$20M QAPE hard gate (reusing the existing min_qpe_usd
  mechanism, never a new gating code path)
- the QPE eligible-spend cap mechanism (UK/Greece 80%)
- the Bridge package export fixes (adjusted NPC, non-claiming segments)
- the proven-zero structure-discovery surfacing

Uses the SAME real Little Utopia budget/allocation fixtures as
test_allocation_pricing.py — no synthetic data.
"""
from __future__ import annotations

from app.calculators.allocation_pricing import price_allocated_structure
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.data.little_utopia_real_budget import (
    AUTHORITATIVE_GROSS_BUDGET_USD,
    LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_REAL_BUDGET_LINES,
    LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
    LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
)
from app.calculators.qualification_derivation import BudgetLine
from app.data.program_rate_rules import get_qpe_cap, resolve_program_rate

GROSS = AUTHORITATIVE_GROSS_BUDGET_USD


def _lines() -> list[BudgetLine]:
    return [
        BudgetLine(
            account_code=c, description=d, amount_usd=a,
            spend_category=LITTLE_UTOPIA_REAL_SPEND_CATEGORY.get(c), is_memo=False,
        )
        for c, d, a, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES
    ]


def _spec(structure_id, structure_type, participants, programs, **overrides):
    kwargs = dict(
        structure_id=structure_id, structure_type=structure_type,
        label=structure_id, primary_jurisdiction=participants[0],
        participants=participants, incentive_programs=programs,
    )
    kwargs.update(overrides)
    return StructureSpec(**kwargs)


def _price(spec: StructureSpec, **kwargs):
    allocation = derive_account_allocation(
        lines=_lines(),
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        spec=spec,
        stated_outside_accounts=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    )
    return price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
        gross_budget_usd=GROSS,
        **kwargs,
    )


# ── Australia: A$20M QAPE hard gate ──────────────────────────────────────────

def test_australia_location_offset_does_not_resolve_below_conservative_threshold():
    """Little Utopia's real QPE (~$4M) is far below the $10M conservative
    USD bound of the AUD $20M threshold — the rate must not resolve."""
    rr = resolve_program_rate("au_location_offset", "feature_film", 4_054_196.0)
    assert rr is None


def test_australia_full_relocation_is_not_fully_priced():
    pricing = _price(_spec("P-AU", "full_relocation", ("AU",), {"AU": "au_location_offset"}))
    assert not pricing.is_fully_priced
    assert any("au_location_offset" in b and "did not resolve" in b for b in pricing.blockers)
    au = next(s for s in pricing.segments if s.jurisdiction_code == "AU")
    assert not au.executable


def test_australia_would_resolve_above_the_conservative_threshold():
    """Confirms the gate is a real threshold, not a permanent block —
    a hypothetically larger production clears it."""
    rr = resolve_program_rate("au_location_offset", "feature_film", 15_000_000.0)
    assert rr is not None
    assert rr.modeled_rate == 0.30


# ── Discretionary ceiling confirmation (MU / MT / GB VFX) ───────────────────

def test_mauritius_ceiling_requires_confirmation_and_serves_floor_by_default():
    pricing = _price(_spec("P-MU", "single_country", ("MU",), {"MU": "mu_edb_incentive"}))
    assert pricing.is_fully_priced
    mu = next(s for s in pricing.segments if s.jurisdiction_code == "MU")
    assert mu.is_band_ceiling is True
    assert mu.ceiling_requires_confirmation is True
    assert pricing.selected_incentive_usd == mu.incentive_floor_usd
    assert pricing.selected_incentive_usd < mu.incentive_ceiling_usd


def test_mauritius_ceiling_confirmed_by_explicit_project_override():
    pricing = _price(
        _spec("P-MU-CONFIRMED", "single_country", ("MU",), {"MU": "mu_edb_incentive"}),
        confirmed_ceiling_programs=frozenset({"mu_edb_incentive"}),
    )
    mu = next(s for s in pricing.segments if s.jurisdiction_code == "MU")
    assert mu.ceiling_requires_confirmation is False
    assert pricing.selected_incentive_usd == mu.incentive_ceiling_usd


def test_malta_ceiling_requires_confirmation_and_serves_floor_by_default():
    pricing = _price(_spec("P-MT", "full_relocation", ("MT",), {"MT": "mt_mfc_rebate"}))
    assert pricing.is_fully_priced
    mt = next(s for s in pricing.segments if s.jurisdiction_code == "MT")
    assert mt.is_band_ceiling is True
    assert mt.ceiling_requires_confirmation is True
    assert pricing.selected_incentive_usd == mt.incentive_floor_usd


def test_greece_flat_rate_has_no_discretionary_ceiling():
    """Greece's rate is flat (is_band_ceiling=False) — confirming the
    ceiling-confirmation mechanism never flips a jurisdiction that never
    had a discretionary condition in the first place."""
    pricing = _price(_spec("P-GR", "full_relocation", ("GR",), {"GR": "gr_cash_rebate"}))
    assert pricing.is_fully_priced
    gr = next(s for s in pricing.segments if s.jurisdiction_code == "GR")
    assert gr.is_band_ceiling is False
    assert gr.ceiling_requires_confirmation is False
    assert pricing.selected_incentive_usd == gr.incentive_ceiling_usd == gr.incentive_floor_usd


def test_uk_avec_is_now_canonically_unpriceable_and_cannot_price():
    """Global Data Application: the completed primary-authority corpus
    reclassified uk_avec as UNPRICEABLE_AUTHORITY_INSUFFICIENT (its canonical
    record carries rate_literals=[]), so it is disabled rather than allowed to
    inherit its stale stored rate.

    This test previously asserted uk_avec's VFX band-ceiling behavior. That
    MECHANISM is unchanged and still covered by
    test_mauritius_ceiling_requires_confirmation_and_serves_floor_by_default,
    test_mauritius_ceiling_confirmed_by_explicit_project_override and
    test_malta_ceiling_requires_confirmation_and_serves_floor_by_default -- only
    the UK vehicle for it was retired by canonical data."""
    from app.data.authority_coverage_registry import coverage_state

    assert coverage_state("uk_avec") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
    pricing = _price(_spec("P-GB", "full_relocation", ("GB",), {"GB": "uk_avec"}))
    assert pricing.is_fully_priced is False
    gb = next(s for s in pricing.segments if s.jurisdiction_code == "GB")
    assert gb.executable is False
    assert gb.incentive_floor_usd == 0.0
    assert gb.incentive_ceiling_usd == 0.0
    assert any("UNPRICEABLE_AUTHORITY_INSUFFICIENT" in b for b in gb.blockers)


# ── QPE eligible-spend caps (UK / Greece 80%) ────────────────────────────────

def test_qpe_cap_registered_for_uk_and_greece_only():
    assert get_qpe_cap("uk_avec") is not None
    assert get_qpe_cap("gr_cash_rebate") is not None
    assert get_qpe_cap("mu_edb_incentive") is None
    assert get_qpe_cap("mt_mfc_rebate") is None


def test_greece_qpe_capped_at_80pct_of_total_worldwide_budget():
    pricing = _price(_spec("P-GR-CAP", "full_relocation", ("GR",), {"GR": "gr_cash_rebate"}))
    gr = next(s for s in pricing.segments if s.jurisdiction_code == "GR")
    expected_cap = round(GROSS * 0.80, 2)
    assert gr.qpe_usd == expected_cap
    assert gr.qpe_cap_applied_usd > 0


def test_uk_qpe_cap_rule_is_retained_even_though_uk_avec_cannot_currently_price():
    """The UK's 80%-of-core-expenditure QpeCapRule is preserved as data so the
    program can be reactivated intact once authority is recaptured -- but with
    uk_avec now canonically UNPRICEABLE_AUTHORITY_INSUFFICIENT the cap is never
    reached, because the segment is blocked before QPE is computed.

    The cap MECHANISM itself remains covered by
    test_greece_qpe_capped_at_80pct_of_total_worldwide_budget."""
    assert get_qpe_cap("uk_avec") is not None  # rule data preserved for reactivation
    pricing = _price(_spec("P-GB-CAP", "full_relocation", ("GB",), {"GB": "uk_avec"}))
    gb = next(s for s in pricing.segments if s.jurisdiction_code == "GB")
    assert gb.executable is False
    assert gb.qpe_usd in (None, 0, 0.0)


# ── Bridge package export fixes ──────────────────────────────────────────────

def test_bridge_package_npc_usd_matches_adjusted_not_verified():
    from app.bridge.package_builder import build_package
    from app.bridge.schema import OperationType

    pkg = build_package(operation=OperationType.QPE_AUDIT, structure_id="ALLOC-RELOC-MT")
    # Malta has real, non-zero local_cost/travel deltas — npc_usd (adjusted)
    # must differ from npc_verified_usd (base), and must be the LARGER of
    # the two (deltas only ever add cost for a relocation away from MU).
    assert pkg.economics.npc_usd != pkg.economics.npc_verified_usd
    assert pkg.economics.npc_usd > pkg.economics.npc_verified_usd


def test_bridge_package_surfaces_non_claiming_us_segment():
    from app.bridge.package_builder import build_package
    from app.bridge.schema import OperationType

    pkg = build_package(operation=OperationType.QPE_AUDIT, structure_id="ALLOC-BASELINE-MU")
    assert len(pkg.non_claiming_segments) == 1
    seg = pkg.non_claiming_segments[0]
    assert seg.jurisdiction_code == "US"
    assert seg.allocated_usd == 9_068.0
    assert set(seg.account_codes) == {"5000", "5100", "5200", "5300", "5400", "5500", "6500"}


# ── Structure discovery: proven-zero categories surfaced ────────────────────

def test_proven_zero_categories_are_visible_in_ranking():
    from app.demo.little_utopia_state import build_allocated_structures, get_state

    served = build_allocated_structures(get_state())
    proven_zero_ids = {r["structure_id"] for r in served["ranking"]
                        if r["structure_id"].startswith("PROVEN-ZERO-")}
    assert "PROVEN-ZERO-CO_PRODUCTION_TREATY" in proven_zero_ids
    entry = next(r for r in served["ranking"] if r["structure_id"] == "PROVEN-ZERO-CO_PRODUCTION_TREATY")
    assert entry["rank"] is None
    assert entry["excluded_from_ranking_because"]
    assert "treaty" in entry["excluded_from_ranking_because"][0].lower()
