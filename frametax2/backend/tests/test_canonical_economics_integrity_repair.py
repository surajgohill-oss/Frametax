"""
test_canonical_economics_integrity_repair.py

Regression coverage for the CineGlobe economics + wiring integrity repair.

Each test below pins one ROOT CAUSE from the reconciliation/external-control
audits of bb4b6a2, so a later change cannot silently reopen it:

  * CLUSTER 1  -- AUTHORITY must fail closed. An
    AUTHORITY_UNRESOLVED_NON_PRICEABLE program contributes no incentive, NPC,
    stack or ranking value (PROJECT_RULES.md final authority-safety gate),
    while remaining DISCOVERED and disclosed -- withheld, never erased.

  * CLUSTER 6  -- A CEILING IS A LIMIT, NEVER A GUARANTEED RATE. A program
    stating only "up to X%" with no floor tier, whose award condition cannot
    be pre-evaluated, has no deterministic rate and must fail closed rather
    than serve X% as guaranteed.

  * CLUSTER 13 -- READ PATH MUST BE PURE. A GET/read may reconstruct the
    canonical input fingerprint, but must produce ZERO inserts, ZERO updates,
    ZERO project-fact mutations and ZERO commits.

These walk the LIVE registry and the LIVE database; none asserts a
hard-coded historical economic total as if it were production law.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.db.session import engine
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures
from app.services.project_workspace_view import build_project_workspace_view

LIPS_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"

#: The read-purity control that actually EXERCISES the recovery path.
#: Lips and FVD already have a routed BudgetDocument and a resolved home
#: jurisdiction, so nothing would fire for them and a purity assertion on
#: those two alone would pass vacuously. "All My Friends Are Dead" has a
#: committed budget document but NO BudgetDocument row and NO
#: home_jurisdiction_id, so the pre-repair read path reached
#: ensure_current_budget_routed and committed a BudgetDocument plus 29
#: BudgetLineItems on a GET. That is the regression this guards.
UNROUTED_PROJECT_ID = "e3f50d06-68c5-4d36-8b3a-e1f87e5c7a44"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── CLUSTER 1 — authority fails closed ───────────────────────────────────

def test_unresolved_authority_is_a_blocking_state():
    """The registry-level gate. NON_PRICEABLE is the disposition, so it must
    block deterministic economics."""
    from app.data.authority_coverage_registry import BLOCKING_STATES

    assert "AUTHORITY_UNRESOLVED_NON_PRICEABLE" in BLOCKING_STATES


def test_every_authority_unresolved_program_is_barred_from_economics():
    from app.data.authority_coverage_registry import (
        COVERAGE_REGISTRY,
        blocks_economic_candidacy,
    )

    unresolved = [
        slug for slug, rec in COVERAGE_REGISTRY.items()
        if rec.state == "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
    ]
    assert unresolved, "expected real authority-unresolved programs in the registry"
    for slug in unresolved:
        assert blocks_economic_candidacy(slug), f"{slug} still economically priceable"


def test_authority_unresolved_program_cannot_price_via_direct_price_segment():
    """The route that bypasses discovery entirely must also fail closed, and
    must still ALLOCATE and DISCLOSE the segment rather than erase it."""
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind
    from app.data.authority_coverage_registry import COVERAGE_REGISTRY

    slug = next(
        s for s, rec in COVERAGE_REGISTRY.items()
        if rec.state == "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
    )
    alloc = AccountAllocation(
        account_code="2000", description="Production spend",
        amount_usd=5_000_000.0, component="production", jurisdiction_code="XX",
        assignment_kind=AssignmentKind.FIXED,
        rationale="authority fail-closed probe",
        governing_decision="cineglobe-economics-integrity-repair",
    )
    seg = price_segment(
        jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
        spend_category_by_code={"2000": "production"},
        offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=5_000_000.0,
    )
    assert seg.executable is False
    assert seg.blockers, "a withheld segment must explain itself"
    # Withheld, not erased: the spend is still located and disclosed.
    assert seg.allocated_usd == pytest.approx(5_000_000.0)


async def test_authority_unresolved_program_is_served_but_unpriced(db: AsyncSession):
    """End to end, on a real project: Manitoba is authority-unresolved, so it
    must appear in the served universe carrying its authority reason and
    contribute no deterministic incentive."""
    await evaluate_project(db, LIPS_PROJECT_ID)
    view = await build_production_and_structures(db, LIPS_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]

    mb = [e for e in entries if e["primary_jurisdiction"] == "CA-MB"]
    assert mb, "CA-MB must remain discovered and disclosed, never erased"
    for entry in mb:
        assert entry["is_fully_priced"] is False
        assert not entry.get("selected_incentive_usd")


# ── CLUSTER 13 — the read path must be pure ──────────────────────────────

async def _mutation_snapshot(session: AsyncSession, project_id: str) -> dict:
    """Everything a read was previously able to mutate FOR ONE PROJECT.

    Deliberately scoped to the project under test rather than the whole
    database: the regression being guarded (ensure_current_budget_routed /
    home-jurisdiction persistence) writes against the project being read, and
    a global snapshot would also register unrelated concurrent activity from
    other tests sharing this database.
    """
    facts = (await session.execute(
        select(ProjectFact.id, ProjectFact.value, ProjectFact.fact_key)
        .where(ProjectFact.project_id == project_id)
    )).all()
    home = (await session.execute(
        select(Project.home_jurisdiction_id).where(Project.id == project_id)
    )).scalar()
    counts = {}
    for table, col in (
        ("budget_documents", "project_id"),
        ("production_structures", "project_id"),
    ):
        counts[table] = (await session.execute(
            text(f"select count(*) from {table} where {col} = :p"), {"p": project_id}
        )).scalar()
    counts["budget_line_items"] = (await session.execute(
        text(
            "select count(*) from budget_line_items bli "
            "join budget_documents bd on bd.id = bli.budget_document_id "
            "where bd.project_id = :p"
        ), {"p": project_id}
    )).scalar()
    return {
        "facts": sorted((str(f[0]), f[1], f[2]) for f in facts),
        "home": str(home),
        "counts": counts,
    }


@pytest.mark.parametrize(
    "project_id", [LIPS_PROJECT_ID, FVD_PROJECT_ID, UNROUTED_PROJECT_ID]
)
async def test_production_view_get_performs_zero_writes(db: AsyncSession, project_id):
    before = await _mutation_snapshot(db, project_id)
    try:
        await build_production_and_structures(db, project_id)
    except Exception:
        # A project with no priceable inputs may legitimately raise or
        # report blockers. Purity is asserted either way -- a read must not
        # mutate even on the failure path.
        await db.rollback()
    after = await _mutation_snapshot(db, project_id)

    assert after["counts"] == before["counts"], (
        "a GET inserted or deleted rows: " f"{before['counts']} -> {after['counts']}"
    )
    assert after["facts"] == before["facts"], "a GET mutated ProjectFact state"
    assert after["home"] == before["home"], "a GET mutated Project.home_jurisdiction_id"


@pytest.mark.parametrize(
    "project_id", [LIPS_PROJECT_ID, FVD_PROJECT_ID, UNROUTED_PROJECT_ID]
)
async def test_workspace_view_get_performs_zero_writes(db: AsyncSession, project_id):
    before = await _mutation_snapshot(db, project_id)
    try:
        await build_project_workspace_view(db, project_id)
    except Exception:
        await db.rollback()
    after = await _mutation_snapshot(db, project_id)

    assert after["counts"] == before["counts"], (
        "a GET inserted or deleted rows: " f"{before['counts']} -> {after['counts']}"
    )
    assert after["facts"] == before["facts"], "a GET mutated ProjectFact state"
    assert after["home"] == before["home"], "a GET mutated Project.home_jurisdiction_id"


def test_read_only_builder_never_reaches_write_capable_recovery():
    """Structural guard: the two GET builders must call the economic-input
    builder in read-only mode. A future edit that drops the flag reopens the
    exact regression bb4b6a2 introduced."""
    import inspect

    from app.services import canonical_production_view, project_workspace_view

    for module in (canonical_production_view, project_workspace_view):
        src = inspect.getsource(module)
        assert "build_project_economic_inputs(session, project.id, read_only=True)" in src, (
            f"{module.__name__} must build economic inputs read-only on a GET"
        )


# ── CLUSTER 6 — a ceiling is a limit, never a guaranteed rate ────────────

def test_floorless_band_ceiling_is_reported_as_having_no_guaranteed_floor():
    """resolve_program_rate must tell the truth about whether a statutory
    FLOOR exists. When every eligible tier is a band ceiling, floor_rate is
    only the ceiling repeated and must not be read as guaranteed."""
    from app.data import program_rate_rules as prr

    floorless = [
        slug for slug, rules in prr._RULES_BY_PROGRAM.items()
        if rules and all(r.is_band_ceiling for r in rules)
    ]
    assert floorless, "expected real programs whose only tiers are band ceilings"
    for slug in floorless:
        rr = prr.resolve_program_rate(
            slug, production_type="feature_film", qpe_usd=5_000_000.0,
        )
        if rr is None:
            continue
        assert rr.has_guaranteed_floor is False, (
            f"{slug} has no non-band tier but claims a guaranteed floor"
        )


def test_a_program_with_a_real_floor_tier_still_reports_one():
    """The flag must not over-trigger: a program that genuinely has a
    non-band floor tier alongside a ceiling keeps its guaranteed floor."""
    from app.data import program_rate_rules as prr

    rr = prr.resolve_program_rate(
        "gr_cash_rebate", production_type="feature_film", qpe_usd=5_000_000.0,
    )
    assert rr is not None and rr.has_guaranteed_floor is True


def _probe_segment(slug: str):
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    alloc = AccountAllocation(
        account_code="2000", description="Production spend",
        amount_usd=5_000_000.0, component="production", jurisdiction_code="XX",
        assignment_kind=AssignmentKind.FIXED,
        rationale="conditional-ceiling probe",
        governing_decision="cineglobe-economics-integrity-repair",
    )
    return price_segment(
        jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
        spend_category_by_code={"2000": "production"},
        offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=5_000_000.0,
    )


def test_unconfirmed_conditional_ceiling_cannot_become_a_deterministic_rate():
    """Chile states only 'up to 40%' (tier cl-ceiling-40, condition
    cl-up-to-not-guaranteed). With no floor tier and an award condition that
    cannot be pre-evaluated, there is no deterministic rate -- the segment
    must fail closed, allocated and disclosed but carrying no incentive."""
    seg = _probe_segment("cl_corfo_incentive")
    assert seg.executable is False
    assert not seg.incentive_floor_usd
    # ITEM 5: cl_corfo_incentive is ALSO declared AllocationType.COMPETITIVE
    # ("only a small named set of projects win each call"), so the
    # NON_GUARANTEED_SELECTIVE gate now fires first. Both reasons are true and
    # both fail closed; this test's claim is that a non-deterministic rate
    # never becomes a priced number, so accept either stated reason.
    assert seg.blockers
    assert any(
        token in seg.blockers[0].lower()
        for token in ("ceiling", "non_guaranteed_selective")
    ), seg.blockers[0]
    # Withheld, not erased.
    assert seg.allocated_usd == pytest.approx(5_000_000.0)


def test_a_determinate_floorless_ceiling_still_prices():
    """No over-blocking. A program whose only tier is a band ceiling but
    whose conditions are ALL pre-evaluable is determinate and must keep
    pricing -- the repair targets unconfirmable discretion, not the shape."""
    from app.data import program_rate_rules as prr

    rr = prr.resolve_program_rate(
        "us_tx_miip", production_type="feature_film", qpe_usd=5_000_000.0,
    )
    assert rr is not None and rr.has_guaranteed_floor is False
    assert not any(e.satisfied is None for e in rr.conditions_evaluated)

    seg = _probe_segment("us_tx_miip")
    assert seg.executable is True
    assert seg.incentive_floor_usd > 0



def _probe_segment_amount(slug: str, amount_usd: float):
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    alloc = AccountAllocation(
        account_code="2000", description="Production spend",
        amount_usd=amount_usd, component="production", jurisdiction_code="XX",
        assignment_kind=AssignmentKind.FIXED,
        rationale="dollar-cap probe",
        governing_decision="cineglobe-economics-integrity-repair",
    )
    return price_segment(
        jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
        spend_category_by_code={"2000": "production"},
        offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=amount_usd,
    )


# ── CLUSTER 7 — dollar caps must constrain the served incentive ──────────

def test_dollar_cap_resolver_prefers_the_smallest_applicable_cap():
    """per_project_cap_usd and annual_cap_usd already existed as canonical
    fields. The binding cap is the smallest applicable one, and its type and
    provenance must be named -- never an invented ceiling."""
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap

    cap, kind, basis = _resolve_incentive_dollar_cap("cy_film_rebate")
    assert cap == pytest.approx(650_000.0)
    assert kind == "per_project"
    assert "per_project_cap_usd" in basis

    # A program with no declared dollar cap must report absence, not zero.
    cap, kind, basis = _resolve_incentive_dollar_cap("gr_cash_rebate")
    assert cap is None and kind is None and basis is None


def test_dollar_cap_clips_the_incentive_and_preserves_the_uncapped_amount():
    """Cyprus at an 11M segment resolves an incentive far above its own
    canonical per-project cap. The cap must bind, and the pre-cap figure must
    survive for audit."""
    seg = _probe_segment_amount("cy_film_rebate", 11_000_000.0)
    assert seg.executable is True
    assert seg.incentive_cap_usd == pytest.approx(650_000.0)
    assert seg.incentive_ceiling_usd == pytest.approx(650_000.0)
    assert seg.incentive_floor_usd <= 650_000.0
    assert seg.incentive_uncapped_usd > seg.incentive_ceiling_usd
    assert seg.incentive_cap_applied_usd == pytest.approx(
        seg.incentive_uncapped_usd - seg.incentive_ceiling_usd
    )
    assert seg.notes and "cap" in seg.notes[0].lower()


def test_a_non_binding_dollar_cap_does_not_clip():
    """No over-clipping: New Mexico declares a $140M annual allocation, which
    a single ordinary production never approaches.

    ITEM 5: this previously used California, which is now correctly blocked as
    a COMPETITIVE, non-entitlement award and so can no longer demonstrate a
    NON-binding cap on an EXECUTABLE segment. New Mexico is an entitlement
    credit with an even larger annual cap -- the same property, on a program
    that actually prices."""
    seg = _probe_segment_amount("us_nm_film_credit", 11_000_000.0)
    assert seg.executable is True
    assert seg.incentive_cap_usd == pytest.approx(140_000_000.0)
    assert seg.incentive_cap_applied_usd == 0.0
    assert seg.incentive_uncapped_usd is None


def test_a_program_without_a_dollar_cap_is_unaffected():
    seg = _probe_segment_amount("gr_cash_rebate", 11_000_000.0)
    assert seg.executable is True
    assert seg.incentive_cap_usd is None
    assert seg.incentive_cap_applied_usd == 0.0


def test_no_priced_segment_ever_exceeds_its_own_declared_dollar_cap():
    """Registry-wide invariant, not a single control: for every priceable
    program that declares a dollar cap, a deliberately oversized segment must
    still come back at or under that cap."""
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    from app.data.program_rate_rules import _RULES_BY_PROGRAM

    checked = 0
    for slug in _RULES_BY_PROGRAM:
        if blocks_economic_candidacy(slug):
            continue
        cap, _, _ = _resolve_incentive_dollar_cap(slug)
        if not cap:
            continue
        seg = _probe_segment_amount(slug, 500_000_000.0)
        if not seg.executable:
            continue
        assert seg.incentive_ceiling_usd <= cap + 0.01, (
            f"{slug} priced {seg.incentive_ceiling_usd:,.2f} above its cap {cap:,.2f}"
        )
        assert seg.incentive_floor_usd <= cap + 0.01
        checked += 1
    assert checked, "expected at least one capped priceable program"


# ── CLUSTER 5 — a labour base is not all-spend ───────────────────────────

def test_programs_declaring_a_narrower_rate_base_do_not_price_off_all_spend():
    """Canada's CPTC/PSTC family applies its rate to qualified LABOUR, and
    says so canonically via a rate condition of kind
    rate_base_narrower_than_qpe. The narrower base cannot be derived from the
    facts on file (BudgetLineItem.is_labor is populated on only a handful of
    lines per budget, and residency splits are absent), so these programs must
    fail closed rather than multiply the rate by the broad register."""
    from app.data.program_rate_rules import _RULES_BY_PROGRAM

    declaring = sorted({
        slug for slug, rules in _RULES_BY_PROGRAM.items()
        for rule in rules
        for condition in rule.conditions
        if condition.kind == "rate_base_narrower_than_qpe"
    })
    assert declaring, "expected real programs declaring a narrower rate base"
    for slug in declaring:
        seg = _probe_segment_amount(slug, 11_000_000.0)
        assert seg.executable is False, f"{slug} priced off the broad base"
        assert not seg.incentive_floor_usd
        assert seg.blockers and "narrower base" in seg.blockers[0].lower()
        # Withheld, not erased.
        assert seg.allocated_usd == pytest.approx(11_000_000.0)


def test_narrower_base_check_scans_every_tier_not_just_the_selected_one():
    """ca_bc_pstc declares ca-bc-labour-only-base on its 36% BASE tier while
    rate resolution selects the 48% regional-ceiling tier. A check that only
    inspected the resolved tier's evaluated conditions would miss it and still
    price the broad base -- the qualifying base is a property of the PROGRAM,
    not of whichever tier won selection."""
    from app.data.program_rate_rules import _RULES_BY_PROGRAM, resolve_program_rate

    rr = resolve_program_rate(
        "ca_bc_pstc", production_type="feature_film", qpe_usd=11_000_000.0,
    )
    assert rr is not None
    assert not any(
        e.kind == "rate_base_narrower_than_qpe" for e in rr.conditions_evaluated
    ), "precondition: the selected tier does NOT carry the narrower-base condition"
    assert any(
        c.kind == "rate_base_narrower_than_qpe"
        for rule in _RULES_BY_PROGRAM["ca_bc_pstc"] for c in rule.conditions
    ), "precondition: another tier does carry it"

    assert _probe_segment_amount("ca_bc_pstc", 11_000_000.0).executable is False


def test_a_broad_base_program_is_unaffected_by_the_narrower_base_guard():
    """No over-blocking: Greece prices its whole qualifying register."""
    seg = _probe_segment_amount("gr_cash_rebate", 11_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd > 0


# ── CLUSTER 9 — subnational conditional nodes must not cross provinces ───

def test_a_subnational_participant_gets_only_its_own_subnational_nodes():
    """A CA-MB structure previously attached EVERY Canadian subnational
    conditional node, so Manitoba was offered Saskatchewan's and PEI's
    province-only programs. Sharing a parent country is not participation."""
    from app.calculators.conditional_programs import conditional_nodes_for

    nodes = conditional_nodes_for(("CA-MB",))
    subnational = [n for n in nodes if n.scope == "subnational"]
    assert subnational, "Manitoba's own conditional node must still attach"
    for node in subnational:
        assert node.jurisdiction_code.upper() == "CA-MB", (
            f"{node.jurisdiction_code} is a sibling province, not a participant"
        )


def test_national_nodes_still_attach_to_a_subnational_participant():
    """The scoping must not over-correct: a national program applies across
    the whole country, so CA-MB still reaches Canada-wide funds."""
    from app.calculators.conditional_programs import conditional_nodes_for

    national = [n for n in conditional_nodes_for(("CA-MB",)) if n.scope == "national"]
    assert national, "Canada-wide national nodes must still attach to CA-MB"
    assert all(n.parent_country == "CA" for n in national)


def test_country_only_participant_gets_no_subnational_nodes():
    """Participating in 'CA' generally is not participation in any province."""
    from app.calculators.conditional_programs import conditional_nodes_for

    nodes = conditional_nodes_for(("CA",))
    assert nodes, "national nodes must attach"
    assert not [n for n in nodes if n.scope == "subnational"]


def test_each_subnational_participant_gets_its_own_node_generically():
    """Generic, not a Canada special case: the same rule holds province by
    province, for every subnational participant the catalog models."""
    from app.calculators.conditional_programs import (
        conditional_nodes_for,
        get_conditional_program_index,
    )

    index = get_conditional_program_index()
    subnational_codes = sorted({
        n.jurisdiction_code.upper() for n in index.nodes if n.scope == "subnational"
    })
    assert len(subnational_codes) > 1, "expected several modeled subnational nodes"
    for code in subnational_codes:
        attached = [
            n for n in conditional_nodes_for((code,)) if n.scope == "subnational"
        ]
        assert all(n.jurisdiction_code.upper() == code for n in attached), (
            f"{code} attached another jurisdiction's subnational node"
        )


# ── REGISTRY-WIDE CANONICAL -> EXECUTABLE CONFORMANCE ────────────────────

def test_every_registered_program_is_priceable_or_fails_closed_with_a_reason():
    """The invariant the whole repair rests on, asserted mechanically across
    the LIVE registry (no research, no invented rules): every program with
    registered rate rules must either expose a coherent executable pricing
    contract, or fail closed with an exact stated reason. A program that
    prices with an incoherent contract, or fails without a reason, is exactly
    the defect class this guards."""
    import sys
    from pathlib import Path

    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from canonical_executable_conformance import classify, incoherences

    from app.data.program_rate_rules import _RULES_BY_PROGRAM

    records = [classify(slug) for slug in sorted(_RULES_BY_PROGRAM)]
    assert records, "expected registered programs"

    problems = [(r["slug"], p) for r in records for p in incoherences(r)]
    assert problems == [], f"structural incoherences: {problems}"

    for record in records:
        if record["disposition"] == "FAILS_CLOSED":
            assert record["reasons"], f"{record['slug']} failed closed with no reason"
            assert ":" in record["reasons"][0], (
                f"{record['slug']} reason is not a typed kind:detail pair"
            )

    priceable = [r for r in records if r["disposition"] == "PRICEABLE"]
    failed = [r for r in records if r["disposition"] == "FAILS_CLOSED"]
    assert priceable and failed, "expected both dispositions to be represented"


# ── CLUSTER 8 — multi-program stacking validity and trace projection ─────

async def test_mutually_exclusive_combination_is_not_a_priced_structure(db: AsyncSession):
    """A combination the programs' own rules forbid must never be presented
    as a valid priced structure. The stacking engine already zeroed the
    suppressed member, so the arithmetic was safe -- but the STRUCTURE was
    still emitted PRICED. It is retained as an explicit incompatibility
    diagnostic, never deleted."""
    for project_id in (FVD_PROJECT_ID, LIPS_PROJECT_ID):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        entries = view["structures"]["allocated_structures"]["structures"]
        multi = [e for e in entries if e["structure_type"] == "multi_program"]
        for entry in multi:
            if entry.get("stacking_rule_type") != "mutually_exclusive":
                continue
            assert entry["is_fully_priced"] is False, (
                f"{entry['label']} is mutually exclusive yet priced"
            )
            assert not entry.get("selected_incentive_usd")
            assert entry.get("candidate_status") == "RULE_REJECTED"


async def test_combined_structures_carry_reconciled_segments_and_qpe(db: AsyncSession):
    """No combined structure may serve segments=[] with
    total_qualifying_spend_usd=0 beside a non-zero incentive."""
    for project_id in (FVD_PROJECT_ID, LIPS_PROJECT_ID):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        entries = view["structures"]["allocated_structures"]["structures"]
        for entry in [e for e in entries if e["structure_type"] == "multi_program"]:
            segments = entry.get("segments") or []
            assert segments, f"{entry['label']} served no segments"
            assert len(segments) == len(entry.get("program_slugs") or []), (
                "every constituent program must appear as its own segment"
            )
            assert sum(s.get("qpe_usd") or 0.0 for s in segments) > 0, (
                f"{entry['label']} served zero QPE across its segments"
            )
            for segment in segments:
                assert segment.get("program_slug")
                assert segment.get("program_display_name")


# ── CLUSTERS 10 / 15 / 17 — preservation, asserted not assumed ───────────

def test_conditional_awards_are_never_invented_as_economics():
    """CLUSTER 10 non-regression: a conditional/competitive award is an
    opportunity, never an assumed award. Its documented cap must not become
    a modeled incentive."""
    from app.calculators.conditional_programs import get_conditional_program_index

    index = get_conditional_program_index()
    assert index.nodes, "expected real conditional program nodes"
    for node in index.nodes:
        assert node.stacking in (
            "unknown_requires_evidence", "compatible", "incompatible",
        ), f"{node.node_id} carries an invented stacking claim"
        # A documented cap is evidence of a ceiling, never an award amount.
        assert not hasattr(node, "awarded_usd")
        assert not hasattr(node, "incentive_usd")


async def test_conditional_nodes_never_enter_deterministic_economics(db: AsyncSession):
    """CLUSTER 10 runtime: attached conditional programs are disclosed on a
    candidate but contribute nothing to its incentive or NPC."""
    await evaluate_project(db, LIPS_PROJECT_ID)
    view = await build_production_and_structures(db, LIPS_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    with_conditionals = [e for e in entries if e.get("conditional_programs")]
    assert with_conditionals, "expected conditional programs to be attached somewhere"
    for entry in with_conditionals:
        for node in entry["conditional_programs"]:
            assert not node.get("awarded_usd")
            assert not node.get("incentive_usd")


def test_contingency_doctrine_is_preserved():
    """CLUSTER 15 non-regression: contingency utilization stays generic and
    user-controlled -- no universal 0/50/100 default, and a residual reserve
    is not contingency."""
    import inspect

    from app.calculators import allocation_pricing

    source = inspect.getsource(allocation_pricing.price_segment)
    assert "contingency_expected_utilization_pct" in source
    signature = inspect.signature(allocation_pricing.price_segment)
    default = signature.parameters["contingency_expected_utilization_pct"].default
    assert default is None, (
        "contingency utilization must default to genuinely unset, never a "
        f"universal assumption (got {default!r})"
    )


async def test_in_kind_and_reinvestment_are_not_deterministic_benefits(db: AsyncSession):
    """CLUSTER 17 non-regression: in-kind replacement and reinvestment must
    never be silently treated as a deterministic economic benefit."""
    for project_id in (FVD_PROJECT_ID, LIPS_PROJECT_ID):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        entries = view["structures"]["allocated_structures"]["structures"]
        for entry in entries:
            delta = entry.get("inkind_replacement_delta_usd")
            assert delta in (None, 0, 0.0), (
                f"{entry['label']} carries an unproven in-kind economic benefit: {delta}"
            )


# ── CLUSTER 12 — result / fingerprint / leading-structure lineage ────────

async def test_leading_structure_is_current_by_engine_and_fingerprint(db: AsyncSession):
    """A leading structure is CURRENT only when its latest result matches the
    current engine version AND the current input fingerprint. Checking the
    engine version alone let a pointer survive against a superseded
    fingerprint -- the same engine, but inputs the project no longer has --
    and the project summary then read that stale row as current."""
    from sqlalchemy import text

    from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project

    for project_id in (LIPS_PROJECT_ID, FVD_PROJECT_ID):
        summary = await evaluate_project(db, project_id)
        current_fingerprint = summary["state_fingerprint"]

        row = (await db.execute(text("""
            select scr.engine_version, scr.input_fingerprint
            from projects p
            join structure_calculation_results scr
              on scr.structure_id = p.leading_structure_id
            where p.id = :p
            order by scr.created_at desc
            limit 1
        """), {"p": project_id})).first()
        if row is None:
            continue  # no leading selection is a legitimate state
        engine_version, fingerprint = row
        assert engine_version == ENGINE_VERSION, (
            f"leading structure is stale by engine: {engine_version}"
        )
        assert fingerprint == current_fingerprint, (
            "leading structure is stale by fingerprint -- a superseded row is "
            "being presented as current"
        )


# ── BASELINE PROVENANCE — a production's known baseline must survive ─────

BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"

#: Each production's REAL baseline production jurisdiction. These are
#: established project facts -- the source budgets were built around them.
KNOWN_BASELINES = {
    LITTLE_UTOPIA_PROJECT_ID: "MU",
    FVD_PROJECT_ID: "GR",
    LIPS_PROJECT_ID: "US-CA",
    BAD_HOMBRES_PROJECT_ID: "US-NM",
}


async def test_every_production_keeps_its_known_baseline_jurisdiction(db: AsyncSession):
    """comparable_count == 0 must never be read as "this production has no
    baseline". A currency-derived COUNTRY (USD -> "US") is not a production
    baseline: a federal country whose incentives are subnational can never be
    one, and once persisted it also short-circuited the resolver so better
    evidence could not supersede it."""
    from app.services.canonical_evaluation import evaluate_project

    for project_id, expected in KNOWN_BASELINES.items():
        summary = await evaluate_project(db, project_id)
        assert summary["base_jurisdiction_code"] == expected, (
            f"{project_id} lost its baseline: expected {expected}, got "
            f"{summary['base_jurisdiction_code']}"
        )


async def test_a_producer_stated_baseline_outranks_a_derived_one(db: AsyncSession):
    """A USER_OVERRIDE home_jurisdiction_code fact is authoritative and may
    name a SUBNATIONAL jurisdiction, superseding a low-confidence derivation
    already persisted on the project column."""
    from sqlalchemy import text

    for project_id in (LIPS_PROJECT_ID, BAD_HOMBRES_PROJECT_ID):
        row = (await db.execute(text("""
            select value, source_type from project_facts
            where project_id = :p and fact_key = 'home_jurisdiction_code'
        """), {"p": project_id})).first()
        assert row is not None, "a producer-stated baseline fact must exist"
        value, source = row
        assert "-" in value, "the baseline must be the subnational production jurisdiction"
        assert str(source).upper() == "USER_OVERRIDE"


async def test_an_incomparable_relocation_never_becomes_the_leader(db: AsyncSession):
    """Never elect the cheapest relocation as leader merely because its raw
    NPC is lowest. A leader must be the production's own baseline; where the
    baseline's qualification is unresolved there is honestly NO leader."""
    from app.services.canonical_evaluation import evaluate_project

    for project_id, expected in KNOWN_BASELINES.items():
        summary = await evaluate_project(db, project_id)
        top = summary.get("top_result")
        if top is None:
            continue  # honest "no recommendation" is allowed
        assert top.get("is_baseline") is True, (
            f"{project_id} elected a non-baseline leader: {top.get('name')}"
        )


# ── REJECTION TRACE IDENTITY — a reason must belong to ITS OWN program ───

def test_examinations_are_addressable_per_program_not_per_jurisdiction():
    """Discovery examines EVERY program in a jurisdiction (CA-ON alone has
    three). A rejection lookup keyed by jurisdiction alone returns whichever
    examination happens to be first, so one program could report another
    program's canonical reason. Prove the examination set is addressable by
    (jurisdiction_code, program_slug) and that multi-program jurisdictions
    really do produce several distinct examinations."""
    from app.calculators.production_discovery import discover_executable_jurisdictions
    from app.calculators.production_requirements import derive_production_requirements

    discovery = discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type="feature_film",
        qpe_usd=5_000_000.0,
        home_code="US-CA",
    )
    by_pair = {
        (e.jurisdiction_code, e.program_slug): e for e in discovery.examinations
    }
    assert len(by_pair) == len(discovery.examinations), (
        "(jurisdiction, program) must uniquely address every examination"
    )

    from collections import Counter

    per_jurisdiction = Counter(e.jurisdiction_code for e in discovery.examinations)
    multi = [code for code, n in per_jurisdiction.items() if n > 1]
    assert multi, "expected at least one jurisdiction examining several programs"

    for code in multi:
        slugs = {e.program_slug for e in discovery.examinations if e.jurisdiction_code == code}
        assert len(slugs) > 1, f"{code} collapsed its programs to one examination"
        for slug in slugs:
            examination = by_pair[(code, slug)]
            assert examination.program_slug == slug, (
                f"{code}/{slug} resolved to {examination.program_slug}'s examination"
            )


# ── ITEM 4 — budget classification is generic, not Lips-specific ─────────

def test_budget_classification_separates_reserves_finance_and_contingency():
    """Item 4. A residuals RESERVE is a distinct obligation, not contingency;
    financing / bridge / banking charges are finance costs, not
    miscellaneous. These are source-account semantics, so the rules are
    matched on generic wording only -- no project-specific rule exists."""
    from app.calculators.classify_budget_line_items import classify_line_item
    from app.models.enums import SpendCategory

    cases = {
        "Residuals Reserve": SpendCategory.RESIDUALS_RESERVE,
        "SAG residuals accrual": SpendCategory.RESIDUALS_RESERVE,
        "Contingency": SpendCategory.CONTINGENCY,
        "Financing Fees": SpendCategory.FINANCE_COSTS,
        "Bridge Loan Interest": SpendCategory.FINANCE_COSTS,
        "Banking Fees": SpendCategory.FINANCE_COSTS,
    }
    for description, expected in cases.items():
        result = classify_line_item(description)
        assert result.spend_category is expected, (
            f"{description!r} classified {result.spend_category} not {expected}"
        )

    assert (
        SpendCategory.RESIDUALS_RESERVE is not SpendCategory.CONTINGENCY
    ), "a residuals reserve must never collapse into contingency"


def test_atl_btl_follows_the_source_account_department():
    """Item 4. ATL/BTL is a property of the SOURCE account, so a line the
    budget itself files above the line must not be re-derived as BTL by a
    keyword rule."""
    from app.calculators.classify_budget_line_items import classify_line_item
    from app.models.enums import ATLBTLCategory

    above = classify_line_item("Writer -- screenplay", "Above the Line")
    assert above.atl_btl is ATLBTLCategory.ATL

    below = classify_line_item("Set construction labour", "Construction")
    assert below.atl_btl is ATLBTLCategory.BTL


def test_no_classification_rule_is_project_specific():
    """Item 4 explicitly forbids Lips-specific rules. The rule table must
    contain no project title, so the repair generalizes to every project."""
    from app.calculators.classify_budget_line_items import _RULES

    for rule in _RULES:
        pattern = rule.pattern.lower()
        for title in ("lips", "utopia", "hombres", "valentine", "sugar"):
            assert title not in pattern, (
                f"classification rule {rule.pattern!r} is project-specific"
            )


# ── ITEM 6 — finance semantics: source-budget vs incremental ─────────────

@pytest.mark.parametrize("project_id", [LIPS_PROJECT_ID, FVD_PROJECT_ID])
async def test_source_budget_finance_is_never_re_added_as_incremental(
    db: AsyncSession, project_id,
):
    """Item 6 (settled doctrine). Financing ALREADY inside the source budget
    is part of gross and therefore already in NPC. `financing_cost_usd` means
    INCREMENTAL / OFF-BUDGET financing only, so it must never be populated
    from budget lines -- that would charge the same money twice."""
    from app.services.canonical_project_economics import build_project_economic_inputs

    inputs = (await build_project_economic_inputs(db, project_id)).inputs
    if inputs is None:
        pytest.skip("project has no economics inputs")

    if inputs.source_budget_finance_usd:
        assert inputs.financing_cost_usd in (None, 0.0), (
            "source-budget financing was re-added as an incremental producer "
            f"assumption ({inputs.financing_cost_usd})"
        )


async def test_lips_source_budget_finance_is_disclosed_not_assumed(db: AsyncSession):
    """Item 6 runtime proof on the project that actually carries budgeted
    finance: it is disclosed on the served payload as source-budget finance,
    and the producer's incremental assumption stays absent."""
    from app.services.canonical_project_economics import build_project_economic_inputs

    inputs = (await build_project_economic_inputs(db, LIPS_PROJECT_ID)).inputs
    assert inputs is not None
    assert inputs.source_budget_finance_usd > 0, (
        "Lips' budgeted financing/bridge/banking charges are no longer "
        "classified as finance costs"
    )
    assert inputs.financing_cost_usd in (None, 0.0)

    view = await build_production_and_structures(db, LIPS_PROJECT_ID)
    semantics = view["production"]["finance_semantics"]
    assert semantics["source_budget_finance_usd"] == inputs.source_budget_finance_usd
    assert semantics["producer_assumption_scope"] == "INCREMENTAL_OFF_BUDGET"


def test_npc_adds_financing_cost_on_top_of_gross():
    """Item 6, the arithmetic half. NPC is gross - incentive +
    financing_cost_usd, so the field is unambiguously ADDITIVE. That is only
    correct because it carries off-budget financing exclusively."""
    import inspect

    from app.calculators import allocation_pricing

    source = inspect.getsource(allocation_pricing.price_allocated_structure)
    assert "gross_budget_usd - selected_incentive" in source
    assert "+ financing_cost_usd" in source
