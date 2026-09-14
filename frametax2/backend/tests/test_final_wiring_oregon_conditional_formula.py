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
    """Codex final three-program conservation repair (P0-OR-001, fifth
    pass): payroll is now built from MULTIPLE real per-payee lines
    (each capped at OAR 951-002-0010's real USD1,000,000 per-payee
    exclusion by the production pricing path itself), never one free
    scalar or one oversized single line standing in for a whole payroll
    pool."""
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind
    out = []
    remaining = payroll_usd
    i = 0
    while remaining > 0.005:
        chunk = min(remaining, 800_000.0)
        out.append(AccountAllocation(
            account_code="1", description=f"OR payroll payee {i}", amount_usd=chunk, component="payroll",
            jurisdiction_code="US-OR", assignment_kind=AssignmentKind.FIXED,
            rationale="OR conditional formula probe", governing_decision="codex-final-three-program-conservation-repair-p0-or-001",
            line_id=f"payroll-{i}", spend_category="btl_crew_labor",
        ))
        remaining -= chunk
        i += 1
    if other_usd:
        out.append(AccountAllocation(
            account_code="2", description="OR other", amount_usd=other_usd, component="production",
            jurisdiction_code="US-OR", assignment_kind=AssignmentKind.FIXED,
            rationale="OR conditional formula probe", governing_decision="codex-final-three-program-conservation-repair-p0-or-001",
            line_id="other-1", spend_category="production",
        ))
    return out


def _probe(payroll_usd: float, other_usd: float, evidenced=()):
    from app.calculators.allocation_pricing import price_segment
    return price_segment(
        jurisdiction_code="US-OR", program_slug="us_or_opif", allocations=_allocs(payroll_usd, other_usd),
        spend_category_by_code={"1": "btl_crew_labor", "2": "production"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=payroll_usd + other_usd,
        evidenced_requirement_facts=frozenset(evidenced),
    )


def _probe_asserted(payroll_usd: float, other_usd: float, asserted_payroll: float, asserted_other: float, evidenced=()):
    """A caller ASSERTS payroll/other figures that may not match the
    real, per-payee-capped traced lines -- proves the reconciliation
    gate rejects an unreconciled scalar."""
    from app.calculators.allocation_pricing import price_segment
    return price_segment(
        jurisdiction_code="US-OR", program_slug="us_or_opif", allocations=_allocs(payroll_usd, other_usd),
        spend_category_by_code={"1": "btl_crew_labor", "2": "production"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=payroll_usd + other_usd,
        amount_facts={"us_or_payroll_qpe_usd": asserted_payroll, "us_or_other_qpe_usd": asserted_other},
        evidenced_requirement_facts=frozenset(evidenced),
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


# ── Codex final three-program conservation repair (P0-OR-001, fifth
# pass): canonical-line / per-payee conservation ───────────────────────

def test_asserted_basis_mismatching_real_lines_rejects():
    """Codex's EXACT confirmed defect: composite component facts were
    accepted with NO relationship to this segment's own real canonical
    lines. An asserted payroll/other figure that does not EXACTLY match
    the real, per-payee-capped traced lines must reject BEFORE pricing —
    never persist a candidate."""
    mismatched = _probe_asserted(
        1_000_000.0, 1_000_000.0, asserted_payroll=5_000_000.0, asserted_other=5_000_000.0,
    )
    assert mismatched.executable is False, (
        f"an asserted USD5,000,000/USD5,000,000 basis against real lines totaling only "
        f"USD1,000,000 each must reject; observed incentive={mismatched.incentive_floor_usd}"
    )


def test_per_payee_cap_applied_before_rating_reduces_overstated_payee():
    """Codex requirement: 'per-payee QPE limitation applied before
    rates.' A single payee line at USD2,000,000 (over the real
    USD1,000,000 OAR 951-002-0010 exclusion) must contribute only
    USD1,000,000 toward the payroll basis — proven directly against the
    real price_segment kernel, not a hand-simulated stand-in."""
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    over_cap_payee = [
        AccountAllocation(
            account_code="1", description="OR overstated payee", amount_usd=2_000_000.0, component="payroll",
            jurisdiction_code="US-OR", assignment_kind=AssignmentKind.FIXED,
            rationale="OR per-payee cap probe", governing_decision="codex-final-three-program-conservation-repair-p0-or-001",
            line_id="payroll-overcap-1", spend_category="btl_crew_labor",
        ),
    ]
    result = price_segment(
        jurisdiction_code="US-OR", program_slug="us_or_opif", allocations=over_cap_payee,
        spend_category_by_code={"1": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=2_000_000.0,
    )
    assert result.executable is True, f"blockers={result.blockers}"
    # 20% of the per-payee-CAPPED USD1,000,000 -- never 20% of the real
    # USD2,000,000 line amount (which would wrongly be USD400,000).
    assert result.incentive_floor_usd == pytest.approx(200_000.0, abs=0.01), (
        f"the per-payee cap must reduce this ONE overstated payee's contribution to "
        f"USD1,000,000 BEFORE the 20% rate is applied; observed {result.incentive_floor_usd}"
    )

    # A caller who asserts the UNCAPPED USD2,000,000 as the payroll
    # basis must be rejected -- it does not match the real, per-payee-
    # capped USD1,000,000 subtotal.
    asserted_uncapped = price_segment(
        jurisdiction_code="US-OR", program_slug="us_or_opif", allocations=over_cap_payee,
        spend_category_by_code={"1": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=2_000_000.0,
        amount_facts={"us_or_payroll_qpe_usd": 2_000_000.0},
    )
    assert asserted_uncapped.executable is False, (
        "asserting the real uncapped USD2,000,000 payee amount as the payroll basis must "
        "reject -- the real per-payee-capped basis is USD1,000,000"
    )


def test_no_award_confirmation_never_reaches_rank_1_but_still_shows_provisional_economics():
    """Codex final wiring remediation (P0-OR-001): "Before actual award/
    contract/fund facts, show provisional economics only and exclude
    from verified winner/rank 1." Codex final three-program conservation
    repair (P0-OR-001, fifth pass): "Claude's purported DB-backed
    provisional test explicitly skips when no priced Oregon candidate
    exists." FIXED — this is now a deterministic, NEVER-skipping check
    against the real resolve_program_rate/price_segment kernel: a real,
    priced, provisional composite candidate (real canonical lines, real
    arithmetic) whose award/contract/fund confirmation is genuinely
    unevidenced must carry a real, unresolved (not True) condition —
    exactly the signal canonical_evaluation._rate_condition_qualification_impact
    reads to keep a candidate out of rank 1, proven directly rather than
    depending on which candidates happen to exist in any one project's
    current discovered universe."""
    from app.data.program_rate_rules import resolve_program_rate

    priced = _probe(1_200_000.0, 2_000_000.0)  # real composite candidate, no award facts at all
    assert priced.executable is True, (
        f"a real composite candidate with genuine canonical payroll/other lines must price "
        f"real provisional economics; blockers={priced.blockers}"
    )

    rr = resolve_program_rate(
        "us_or_opif", "feature_film", None,
        amount_facts={"us_or_payroll_qpe_usd": 1_200_000.0, "us_or_other_qpe_usd": 2_000_000.0},
    )
    assert rr is not None and rr.composite_incentive_usd is not None
    award_cond = next(
        c for c in rr.conditions_evaluated if c.condition_id == "us-or-award-contract-fund-confirmed"
    )
    assert award_cond.satisfied is not True, (
        "an unconfirmed award/contract/fund condition on a real, priced composite candidate "
        "must never read as satisfied -- this is the exact signal that keeps it out of "
        "verified-winner/rank-1 while still showing real provisional economics"
    )


async def test_fvd_current_universe_oregon_candidates_if_any_are_never_rank_1(db: AsyncSession):
    """Best-effort, non-skipping cross-check against FVD's real,
    currently-discovered candidate universe: IF it happens to contain a
    priced us_or_opif candidate, that candidate must never reach rank 1
    without evidenced award/contract/fund confirmation. Absence of such
    a candidate is not itself a failure (Oregon is never part of FVD's
    real, accepted baseline) -- the deterministic kernel-level proof
    above is the actual acceptance oracle for this requirement."""
    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import build_production_and_structures

    FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ranking = view["structures"]["allocated_structures"]["ranking"]

    or_entries = [e for e in entries if e.get("program_slug") == "us_or_opif" and e.get("is_fully_priced")]
    for e in or_entries:
        rq = e.get("role_qualification") or {}
        assert rq.get("state") not in (None, "QUALIFIES", "NOT_APPLICABLE"), (
            f"an Oregon candidate with no evidenced award/contract/fund confirmation must "
            f"carry a genuinely unresolved qualification state, observed {rq.get('state')!r}"
        )
    or_rank1 = [r for r in ranking if r.get("rank") == 1 and r.get("program_slug") == "us_or_opif"]
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
