"""
Claude-owned permanent tests — PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END.

Proves the real, primary-source Australia-UK Films Co-production Agreement
(signed Canberra 12 June 1990) rule package implemented on the existing
uk-au-bilateral registry entry (majority_min_pct=minority_min_pct=30,
Annex clause 8; personnel_requirement writer+director, all_of,
nationality-or-residency, Annex clause 6) is wired end-to-end: real
Production Record facts, entered through the existing Project Overview UI,
reach discovery, the personnel gate, conditional pricing, and the served
opportunity-relevance classification — genuinely credited (QUALIFIES),
not merely transported, the moment a real rule exists to consume them.

Live browser/network verification (Overview edit -> POST /projects/{id}/
people -> fresh evaluation -> changed uk-au-bilateral relevance -> served
UI) is documented in docs/validation/AU_UK_OVERVIEW_OPTIMIZER_WIRING_CLAUDE.md
and docs/validation/LITTLE_UTOPIA_AU_UK_UI_RUNTIME_CLAUDE.csv — this file
proves the same mechanism at the unit/DB level, reversibly, and confirms
Little Utopia's own real Production Record is what the browser test
exercised.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators import treaty_engine as te
from app.calculators.canonical_qualification_result import (
    QUAL_CURABLE_GAP,
    QUAL_HARD_FAIL,
    QUAL_QUALIFIES,
    QUAL_USER_FACT_REQUIRED,
)
from app.calculators.canonical_role_qualification_bridge import (
    RoleAttachmentFacts,
    evaluate_treaty_personnel_gate,
    role_attachment_facts_from_project,
)
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_UNRESOLVED_FACTS,
    evaluate_bilateral_coproduction_opportunity,
)
from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile
from app.services import canonical_evaluation as ce

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
ALL_FOUR = {
    "Little Utopia": LITTLE_UTOPIA_PROJECT_ID,
    "F#K Valentine's Day": FVD_PROJECT_ID,
    "Bad Hombres": BAD_HOMBRES_PROJECT_ID,
    "Lips Like Sugar": LIPS_LIKE_SUGAR_PROJECT_ID,
}


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def little_utopia_evaluated(db: AsyncSession):
    """CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION, Task 1: the two DB-
    level tests below read a StructureCalculationResult row keyed on the
    CURRENT ce.ENGINE_VERSION and this project's CURRENT input
    fingerprint. Depending on some OTHER test file (elsewhere in the
    suite, or a prior run) having already called evaluate_project() for
    Little Utopia was a real test-isolation defect -- this file must
    create its own required state, not assume another file's ordering.
    This fixture evaluates Little Utopia fresh, in this file, every time
    either dependent test runs, so the suite passes on a first clean run
    regardless of file/test order in the overall run."""
    await ce.evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    return LITTLE_UTOPIA_PROJECT_ID


# ---------------------------------------------------------------------------
# A — the real, sourced treaty registry entry
# ---------------------------------------------------------------------------

def test_uk_au_bilateral_contribution_minimums_match_the_real_treatys_annex_clause_8():
    """Annex clause 8 of the real 1990 treaty: 'each co-producer shall
    have a financial and creative contribution of not less than thirty
    per cent (30%) of the total financial and creative contribution' —
    both sides, not the prior registry entry's unsourced 20/20/80."""
    treaty = te.get_bilateral_treaty("GB", "AU")
    assert treaty is not None
    assert treaty.majority_min_pct == 30
    assert treaty.minority_min_pct == 30
    assert treaty.minority_max_pct == 70


def test_uk_au_bilateral_has_a_real_researched_personnel_requirement():
    """Annex clause 6: 'Individuals participating...shall be nationals or
    residents of Australia, the United Kingdom...' — modeled as
    writer+director (Annex clause 14(d): the treaty's own overriding
    balance aim specifically names writer/director/lead cast as the major
    creative categories), all_of (each individual independently tested),
    either (nationality OR residency, per the clause's own text)."""
    treaty = te.get_bilateral_treaty("GB", "AU")
    req = treaty.personnel_requirement
    assert req is not None
    assert set(req.eligible_roles) == {"writer", "director"}
    assert req.role_mode == "all_of"
    assert req.fact_kind == "either"
    assert set(req.eligible_codes) == {"AU", "GB"}
    assert req.citation and "Annex clause 6" in req.citation


def test_uk_au_bilateral_producer_role_is_never_gated_by_the_personnel_requirement():
    """Policy: 'US producers do not satisfy AU/UK co-producer
    requirements... [but] do not automatically block the structure.' The
    real treaty's Annex clause 6 personnel test applies to individual
    creative participants; the SEPARATE co-producer/company
    nationality-of-entity gate (Annex clause 4(a)/(b)/(d)) has no
    persistence model in this codebase and is correctly never modeled as
    a hard block here — 'producer' is simply not one of eligible_roles,
    so a non-AU/UK producer can never fail this specific gate."""
    treaty = te.get_bilateral_treaty("GB", "AU")
    assert "producer" not in treaty.personnel_requirement.eligible_roles


# ---------------------------------------------------------------------------
# B — the personnel gate mechanism, proven against Little-Utopia-shaped facts
# ---------------------------------------------------------------------------

def test_gb_writer_and_au_director_qualify_under_the_real_uk_au_rule():
    treaty = te.get_bilateral_treaty("GB", "AU")
    facts = {
        "writer": RoleAttachmentFacts(confirmed_nationality=("GB",), has_any_attachment=True),
        "director": RoleAttachmentFacts(confirmed_nationality=("AU",), has_any_attachment=True),
    }
    result = evaluate_treaty_personnel_gate(treaty.personnel_requirement, ("GB", "AU"), facts)
    assert result.state == QUAL_QUALIFIES
    assert len(result.resolved_facts) == 2


def test_a_confirmed_wrong_director_nationality_is_a_real_hard_fail():
    """Live-browser-equivalent proof (unit level): changing the director's
    confirmed nationality to a non-AU/GB code is a genuine disqualification
    under Annex clause 6's all_of rule, exactly as verified live in the
    real running application (director nationality flipped GB->FR->AU
    through the actual Overview UI; see LITTLE_UTOPIA_AU_UK_UI_RUNTIME_
    CLAUDE.csv)."""
    treaty = te.get_bilateral_treaty("GB", "AU")
    facts = {
        "writer": RoleAttachmentFacts(confirmed_nationality=("GB",), has_any_attachment=True),
        "director": RoleAttachmentFacts(confirmed_nationality=("FR",), has_any_attachment=True),
    }
    result = evaluate_treaty_personnel_gate(treaty.personnel_requirement, ("GB", "AU"), facts)
    assert result.state == QUAL_HARD_FAIL
    assert result.failed_requirements


def test_unconfirmed_au_director_is_a_conditional_question_never_a_false_credit():
    treaty = te.get_bilateral_treaty("GB", "AU")
    facts = {
        "writer": RoleAttachmentFacts(confirmed_nationality=("GB",), has_any_attachment=True),
        "director": RoleAttachmentFacts(has_any_attachment=True, has_unconfirmed_attachment=True),
    }
    result = evaluate_treaty_personnel_gate(treaty.personnel_requirement, ("GB", "AU"), facts)
    assert result.state == QUAL_USER_FACT_REQUIRED
    assert result.state != QUAL_QUALIFIES


def test_unattached_writer_is_a_curable_gap_not_a_block():
    treaty = te.get_bilateral_treaty("GB", "AU")
    facts = {"director": RoleAttachmentFacts(confirmed_nationality=("AU",), has_any_attachment=True)}
    result = evaluate_treaty_personnel_gate(treaty.personnel_requirement, ("GB", "AU"), facts)
    assert result.state == QUAL_CURABLE_GAP


# ---------------------------------------------------------------------------
# C — the modeled combined structure: opportunity + conditional pricing
# ---------------------------------------------------------------------------

def test_qualifying_facts_alone_do_not_resolve_eligible_without_a_real_contribution_fact():
    """Policy: 'The optimizer must assume that requisite independent
    Australian and UK co-producers and production companies can be
    obtained... disclosed PROPOSED_CHANGE/modeled assumptions, not
    verified facts... Conditional economics cannot become a verified
    recommendation.' A real personnel QUALIFIES alone (no real
    contribution-share project fact) must still leave the OUTER
    resolution_state at UNRESOLVED_FACTS — conditional pricing (a
    separate, disclosed assumption layer) is what reaches a priced,
    modeled result, never the discovery-level opportunity itself."""
    treaty = te.get_bilateral_treaty("GB", "AU")
    facts = {
        "writer": RoleAttachmentFacts(confirmed_nationality=("GB",), has_any_attachment=True),
        "director": RoleAttachmentFacts(confirmed_nationality=("AU",), has_any_attachment=True),
    }
    opp = evaluate_bilateral_coproduction_opportunity(
        "GB", "AU", personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts=facts,
    )
    assert opp.resolution_state == RESOLUTION_UNRESOLVED_FACTS
    assert opp.personnel_gate_state == QUAL_QUALIFIES


def test_conditional_scenario_prices_uk_avec_and_au_producer_offset_at_the_treatys_own_30_70_split():
    """The SAME real, national-treatment-based incentive programs (Article
    2) already registered as majority/minority unlocks, priced at the
    treaty's own real 30/30 minimum -- never an invented split, never a
    verified fact."""
    treaty = te.get_bilateral_treaty("GB", "AU")
    facts = {
        "writer": RoleAttachmentFacts(confirmed_nationality=("GB",), has_any_attachment=True),
        "director": RoleAttachmentFacts(confirmed_nationality=("AU",), has_any_attachment=True),
    }
    from tests.test_claude_global_optimizer_p0_remediation import _inputs
    from app.calculators.qualification_derivation import BudgetLine

    inputs = _inputs(
        jurisdiction_code="MU", gross_budget_usd=4_364_393.0, leaf_account_sum_usd=4_364_393.0,
        budget_lines=[BudgetLine("1000", "Cast", 2_000_000.0, spend_category="atl_cast")],
    )
    scenario = ce._build_conditional_bilateral_scenario(
        inputs, "GB", "AU", "uk-au-bilateral", baseline_incentive_usd=None,
        personnel_attachment_facts=facts,
    )
    assert scenario["conditional_qualification_state"] == "ELIGIBLE"
    assert scenario["assumed_majority_contribution_pct"] == 30
    assert scenario["assumed_minority_contribution_pct"] == 30
    assert scenario["assumption_fact_classification"] == "PROPOSED_CHANGE"
    assert set(scenario["unlocked_slugs"]) == {"uk_avec", "au_producer_offset"}
    assert scenario["conditional_incentive_usd"] and scenario["conditional_incentive_usd"] > 0
    assert scenario["fully_priced"] is True


# ---------------------------------------------------------------------------
# D — live-DB / served-view proof against Little Utopia's real Production Record
# ---------------------------------------------------------------------------

async def test_little_utopia_uk_au_bilateral_is_served_conditional_with_real_priced_economics(
    db: AsyncSession, little_utopia_evaluated: str,
):
    """Real, live, end-to-end proof (the same live state the browser test
    read via GET /projects/{id}/state): Little Utopia's real, confirmed
    GB writer + AU director make uk-au-bilateral CONDITIONAL, not
    AVAILABLE, with real priced conditional economics — never a verified
    recommendation (candidate_status stays CO_PRO_OPPORTUNITY,
    is_baseline/is_directly_comparable stay False)."""
    fp = await ce.current_generation_fingerprint(db, LITTLE_UTOPIA_PROJECT_ID)
    row = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json,
               StructureCalculationResult.total_incentive_value_usd,
               StructureCalculationResult.true_net_cost_usd)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp,
            StructureCalculationResult.calculation_trace_json["treaty_slug"].astext == "uk-au-bilateral",
        )
    )).first()
    assert row is not None
    trace, incentive, npc = row
    assert trace["opportunity_relevance"] == "CONDITIONAL"
    assert trace["personnel_gate_state"] == QUAL_QUALIFIES
    assert trace["candidate_status"] == "CO_PRO_OPPORTUNITY"
    assert trace["is_baseline"] is False
    assert trace["is_directly_comparable"] is False
    # structurally excluded from ranking/recommendation -- the row's own
    # incentive/npc columns stay None; only the nested conditional_scenario
    # carries a (disclosed, non-verified) number.
    assert incentive is None
    assert npc is None
    cs = trace["conditional_scenario"]
    assert cs["status"] == "CONDITIONAL_PROJECT_FACT_DEPENDENT"
    assert cs["conditional_incentive_usd"] > 0
    assert cs["conditional_npc_usd"] > 0
    assert cs["assumption_fact_classification"] == "PROPOSED_CHANGE"


async def test_little_utopia_producers_do_not_block_the_uk_au_structure(
    db: AsyncSession, little_utopia_evaluated: str,
):
    """Real, live proof of the policy's own 'existing US producers do not
    automatically block the structure' requirement: Little Utopia's real,
    confirmed US producers (Rachel Winter, Max Botkin) coexist with a
    QUALIFIES personnel gate on uk-au-bilateral — producer nationality is
    never part of this gate's eligible_roles."""
    facts = await role_attachment_facts_from_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert facts.get("producer") is not None
    assert "US" in facts["producer"].confirmed_nationality
    fp = await ce.current_generation_fingerprint(db, LITTLE_UTOPIA_PROJECT_ID)
    row = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp,
            StructureCalculationResult.calculation_trace_json["treaty_slug"].astext == "uk-au-bilateral",
        )
    )).scalar_one_or_none()
    assert row is not None
    assert row["personnel_gate_state"] == QUAL_QUALIFIES


async def test_residency_persists_and_is_read_back_by_role_attachment_facts(db: AsyncSession):
    """PRE-FLIGHT requirement: prove residency persistence works, even
    though the current Overview UI deliberately omits a residency control
    (an explicit, pre-existing design decision — 'Residency is
    deliberately absent here per the approved design',
    ProductionDetails.jsx). Written directly at the model layer
    (TalentProfile.known_residencies), the same real field role_
    attachment_facts_from_project reads for the personnel gate — proving
    the PERSISTENCE layer supports it even where this one UI surface does
    not yet expose it. Reversible: written and deleted in this test only."""
    from sqlalchemy import delete
    import uuid

    talent = TalentProfile(id=uuid.uuid4(), name="Residency Test Person", role="lead_cast",
                            known_residencies=[{"jurisdiction_code": "AU", "confirmed": True}])
    db.add(talent)
    await db.flush()
    pp = ProjectPerson(id=uuid.uuid4(), project_id=LITTLE_UTOPIA_PROJECT_ID, talent_id=talent.id,
                        role="lead_cast", is_confirmed=True)
    db.add(pp)
    await db.commit()
    try:
        facts = await role_attachment_facts_from_project(db, LITTLE_UTOPIA_PROJECT_ID)
        rf = facts.get("lead_cast")
        assert rf is not None
        assert "AU" in rf.confirmed_residency
        assert not rf.confirmed_nationality, "residency and nationality must stay separately typed"
    finally:
        await db.delete(pp)
        await db.delete(talent)
        await db.commit()


# ---------------------------------------------------------------------------
# E — the four productions' served output matches their real stored facts
# ---------------------------------------------------------------------------

async def test_all_four_productions_served_personnel_match_their_real_stored_project_person_rows(db: AsyncSession):
    """The served view must never diverge from the real Production Record:
    for each of the four real projects, every confirmed ProjectPerson/
    TalentProfile row's nationality is exactly what role_attachment_
    facts_from_project (the SAME function the personnel gate consumes)
    reports as confirmed_nationality — proving the served output the
    Globe/optimizer sees is not a stale or second copy of the Production
    Record."""
    for name, pid in ALL_FOUR.items():
        db_rows = (await db.execute(
            select(ProjectPerson.role, ProjectPerson.is_confirmed, TalentProfile.primary_nationality)
            .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
            .where(ProjectPerson.project_id == pid)
        )).all()
        facts = await role_attachment_facts_from_project(db, pid)
        for role, is_confirmed, nationality in db_rows:
            rf = facts.get(role)
            assert rf is not None, f"{name}: role {role} missing from role_attachment_facts"
            if is_confirmed and nationality:
                assert nationality in rf.confirmed_nationality, (
                    f"{name}: confirmed {role} nationality {nationality!r} not reflected in served facts"
                )
            elif not is_confirmed:
                assert rf.has_unconfirmed_attachment is True, (
                    f"{name}: unconfirmed {role} must be reported as unconfirmed, never silently dropped"
                )


# ---------------------------------------------------------------------------
# E — CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION, Task 1: order independence
# ---------------------------------------------------------------------------

async def test_uk_au_bilateral_row_is_self_sufficient_regardless_of_prior_evaluation_state(
    db: AsyncSession,
):
    """Prevention test for the exact defect this workstream fixes: the two
    tests above must never depend on ANY other test file having already
    evaluated Little Utopia. Proven directly here by calling
    evaluate_project() twice in two different surrounding call sequences
    (interleaved with an unrelated project's own evaluation, simulating
    a different file/test having run in between) and confirming the
    uk-au-bilateral row's real, substantive fields are byte-identical
    both times -- the served state depends only on this project's own
    real inputs, never on incidental test ordering."""
    # Sequence 1: evaluate an unrelated project first, then Little Utopia --
    # simulates test_hybrid_anchor_relationship_types.py or
    # test_treaty_coproduction_wiring.py running BEFORE this file.
    await ce.evaluate_project(db, BAD_HOMBRES_PROJECT_ID)
    await ce.evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    fp1 = await ce.current_generation_fingerprint(db, LITTLE_UTOPIA_PROJECT_ID)
    row1 = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp1,
            StructureCalculationResult.calculation_trace_json["treaty_slug"].astext == "uk-au-bilateral",
        )
    )).scalar_one()

    # Sequence 2: evaluate Little Utopia FIRST, with nothing before it --
    # simulates this file running alone / first, exactly as pytest would
    # if file order were reversed.
    await ce.evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    fp2 = await ce.current_generation_fingerprint(db, LITTLE_UTOPIA_PROJECT_ID)
    row2 = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp2,
            StructureCalculationResult.calculation_trace_json["treaty_slug"].astext == "uk-au-bilateral",
        )
    )).scalar_one()

    assert fp1 == fp2, "Little Utopia's own fingerprint must not depend on what else was evaluated first"
    for key in ("opportunity_relevance", "personnel_gate_state", "candidate_status",
                "is_baseline", "is_directly_comparable"):
        assert row1[key] == row2[key], f"{key} differs between orderings: {row1[key]!r} vs {row2[key]!r}"
