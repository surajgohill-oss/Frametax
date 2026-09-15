"""
test_us_nv_film_credit_cap.py

Codex canonical identity/authority cleanup (Phase 5, Nevada) — the real,
already-accepted USD6,000,000 per-project cap (film.nv.gov), applied to
the calculated incentive via the same dollar-cap mechanism every other
capped program already uses.

Scope note: this pass implements the $6,000,000 project cap only (the
single most severe accepted constraint -- an unbounded incentive). The
$750,000 per-person limit, the 60% spend ratio, and the 12% nonresident-
ATL narrower base require new per-payee/per-category component-basis
mechanics this bounded pass did not have time to safely design, wire and
test; they remain unmodeled and are disclosed as open items in this
workstream's closeout artifacts, not silently claimed complete.
"""
from __future__ import annotations

import pytest

from app.calculators.allocation_pricing import price_segment
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.data.program_rate_rules import convert_incentive_cap_to_usd, get_incentive_value_cap


def _probe(qpe_amount: float):
    alloc = AccountAllocation(
        account_code="2000", description="NV production spend", amount_usd=qpe_amount,
        component="production", jurisdiction_code="US-NV", assignment_kind=AssignmentKind.FIXED,
        rationale="NV cap probe", governing_decision="codex-canonical-identity-cleanup",
        line_id="nv-1",
    )
    return price_segment(
        jurisdiction_code="US-NV", program_slug="us_nv_film_credit", allocations=[alloc],
        spend_category_by_code={"2000": "production"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=qpe_amount,
    )


def test_cap_is_registered_at_the_real_6_million_figure():
    cap = get_incentive_value_cap("us_nv_film_credit")
    assert cap is not None and cap.cap_currency == "USD" and cap.cap_native_amount == 6_000_000.0
    cap_usd = convert_incentive_cap_to_usd(cap)[0].target_amount
    assert cap_usd == pytest.approx(6_000_000.0, abs=0.01), "US-domestic cap needs no FX conversion"


def test_positive_below_cap_prices_uncapped_real_figure():
    # 15% of $2,000,000 = $300,000, well under the $6,000,000 cap.
    result = _probe(2_000_000.0)
    assert result.executable is True
    assert result.incentive_floor_usd == pytest.approx(300_000.0, abs=0.01)
    assert result.incentive_cap_applied_usd in (0.0, None) or result.incentive_cap_applied_usd == 0.0


def test_incentive_never_exceeds_6_million_cap_boundary():
    # 15% of $50,000,000 = $7,500,000 -- must clip to exactly $6,000,000.
    result = _probe(50_000_000.0)
    assert result.executable is True
    assert result.incentive_floor_usd == pytest.approx(6_000_000.0, abs=0.01), (
        f"the calculated incentive must never exceed the real $6,000,000 project cap; "
        f"observed {result.incentive_floor_usd}"
    )
    assert result.incentive_cap_usd == pytest.approx(6_000_000.0, abs=0.01)


def test_negative_below_minimum_spend_rejects():
    # Below the real $500,000 statutory minimum -- must reject, never price.
    result = _probe(100_000.0)
    assert result.executable is False
