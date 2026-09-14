"""
test_final_wiring_oregon_conditional_formula.py

Codex final wiring remediation (P0-OR-001) — independent, literal-value
coverage for Oregon's disposition-B conditional formula opportunity:
20% payroll / 25% other Oregon-expense split bases, the USD1,000,000
minimum, the multiplicative 10% regional uplift, the USD10,600,000
(50% of the current USD21,200,000 annual fund) final project cap, and
the real award/contract/fund-confirmation gate that keeps this program
PROVISIONAL (never a verified winner) until evidenced.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _allocs(payroll_usd: float, other_usd: float):
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind
    out = []
    if payroll_usd:
        out.append(AccountAllocation(
            account_code="1", description="OR payroll", amount_usd=payroll_usd, component="payroll",
            jurisdiction_code="US-OR", assignment_kind=AssignmentKind.FIXED,
            rationale="OR conditional formula probe", governing_decision="codex-final-wiring-p0-or-001",
            line_id="payroll-1",
        ))
    if other_usd:
        out.append(AccountAllocation(
            account_code="2", description="OR other", amount_usd=other_usd, component="other",
            jurisdiction_code="US-OR", assignment_kind=AssignmentKind.FIXED,
            rationale="OR conditional formula probe", governing_decision="codex-final-wiring-p0-or-001",
            line_id="other-1",
        ))
    return out


def _probe(payroll_usd: float, other_usd: float, evidenced=()):
    from app.calculators.allocation_pricing import price_segment
    facts = {}
    if payroll_usd:
        facts["us_or_payroll_qpe_usd"] = payroll_usd
    if other_usd:
        facts["us_or_other_qpe_usd"] = other_usd
    return price_segment(
        jurisdiction_code="US-OR", program_slug="us_or_opif", allocations=_allocs(payroll_usd, other_usd),
        spend_category_by_code={"1": "production", "2": "production"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=payroll_usd + other_usd,
        amount_facts=facts, evidenced_requirement_facts=frozenset(evidenced),
    )


def test_veto_lifted_and_both_canonical_spellings_unblocked():
    from app.data.authority_coverage_registry import economic_block_for_program
    assert economic_block_for_program("us_or_opif") is None
    assert economic_block_for_program("or_opif") is None


def test_literal_split_basis_arithmetic_each_component_alone():
    payroll_only = _probe(2_000_000.0, 0.0)
    assert payroll_only.executable is True
    assert payroll_only.incentive_floor_usd == pytest.approx(400_000.0, abs=0.01), "20% of $2,000,000 payroll"

    other_only = _probe(0.0, 2_000_000.0)
    assert other_only.executable is True
    assert other_only.incentive_floor_usd == pytest.approx(500_000.0, abs=0.01), "25% of $2,000,000 other"


def test_below_and_at_the_usd1m_threshold():
    below = _probe(999_999.99, 0.0)
    assert below.executable is False, "below the USD1,000,000 minimum must reject"

    at_threshold = _probe(1_000_000.0, 0.0)
    assert at_threshold.executable is True, "exactly at the USD1,000,000 minimum must price"
    assert at_threshold.incentive_floor_usd == pytest.approx(200_000.0, abs=0.01)


def test_multiplicative_regional_uplift_never_additive():
    base = _probe(0.0, 2_000_000.0)
    uplifted = _probe(0.0, 2_000_000.0, evidenced=("us_or_opif_regional_uplift_confirmed",))
    assert base.incentive_floor_usd == pytest.approx(500_000.0, abs=0.01)
    assert uplifted.incentive_floor_usd == pytest.approx(550_000.0, abs=0.01), (
        "500000 * 1.10 = 550000 -- a MULTIPLICATIVE uplift on the incentive, "
        "never +10 percentage points on the 25% rate (which would be 35% -> $700,000, wrong)"
    )
    assert uplifted.incentive_floor_usd != pytest.approx(2_000_000.0 * 0.35, abs=0.01), (
        "must never equal the wrong additive-percentage-point figure"
    )


def test_fifty_percent_fund_boundary_caps_at_10_6_million():
    huge = _probe(0.0, 100_000_000.0)
    assert huge.executable is True
    assert huge.incentive_floor_usd == pytest.approx(10_600_000.0, abs=0.01), (
        "50% of the current USD21,200,000 annual fund = USD10,600,000 project cap"
    )
    assert huge.incentive_cap_usd == pytest.approx(10_600_000.0, abs=0.01)

    # Just under the cap boundary must NOT be clipped.
    just_under = _probe(0.0, 10_000_000.0)  # 25% * 10,000,000 = 2,500,000, well under cap
    assert just_under.incentive_floor_usd == pytest.approx(2_500_000.0, abs=0.01)


def test_missing_component_facts_rejects_not_guessed():
    neither = _probe(0.0, 0.0)
    assert neither.executable is False


async def test_no_award_confirmation_never_reaches_rank_1_but_still_shows_provisional_economics(
    db: AsyncSession,
):
    """Codex final wiring remediation (P0-OR-001): "Before actual award/
    contract/fund facts, show provisional economics only and exclude
    from verified winner/rank 1." Proven against the real, DB-backed
    canonical pipeline (evaluate_project -> build_production_and_
    structures), using FVD's real project (which has real Oregon-
    relocation candidates in its own discovered universe)."""
    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import build_production_and_structures

    FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ranking = view["structures"]["allocated_structures"]["ranking"]

    or_entries = [e for e in entries if e.get("program_slug") == "us_or_opif" and e.get("is_fully_priced")]
    if not or_entries:
        pytest.skip("no priced us_or_opif candidate in FVD's current discovered universe")

    for e in or_entries:
        rq = e.get("role_qualification") or {}
        assert rq.get("state") not in (None, "QUALIFIES", "NOT_APPLICABLE"), (
            f"an Oregon candidate with no evidenced award/contract/fund confirmation must "
            f"carry a genuinely unresolved qualification state, observed {rq.get('state')!r}"
        )

    or_rank1 = [
        r for r in ranking
        if r.get("rank") == 1 and r.get("program_slug") == "us_or_opif"
    ]
    assert or_rank1 == [], "an unconfirmed Oregon candidate must never reach rank 1 (verified winner)"


async def test_fvd_baseline_unaffected_by_lifting_the_oregon_veto(db: AsyncSession):
    """The four locked real-project anchors must remain exactly stable —
    lifting Oregon's veto must never change FVD's own Greece baseline."""
    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import build_production_and_structures

    FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    baseline = next(e for e in entries if e["is_baseline"])
    assert baseline["program_slug"] == "gr_cash_rebate"
    assert baseline["selected_incentive_usd"] == pytest.approx(1_445_659.84, abs=0.01)
    assert baseline["npc_with_adjustments_usd"] == pytest.approx(3_072_027.16, abs=0.01)
