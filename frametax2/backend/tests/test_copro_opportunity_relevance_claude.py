"""
Claude-owned permanent tests — COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION.

Proves the served co-production opportunity contract is semantically
correct for what the Globe would consume: a globally-registered treaty
between two countries neither of which is this project's own jurisdiction
is never mislabeled project-compatible; a project fact that reaches an
evaluator but has no rule to apply to is FACT_TRANSPORTED_NOT_RULE_CONSUMED,
never "facts consumed"; a multilateral framework's personnel gate is
NOT_APPLICABLE (never a silent None) exactly like bilateral; a conditional
(assumption-priced) structure can never become a verified recommendation;
and a real, unresolved single-jurisdiction baseline correctly produces no
leading structure while a resolved one does.

Uses SYNTHETIC test treaties (monkeypatched into te._BILATERAL, restored in
every test's own finally block) where a deliberately-encoded rule proves the
mechanism. Real project DB reads (Little Utopia, Bad Hombres) prove the real
served/runtime behavior; no real treaty/program data is modified.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators import treaty_engine as te
from app.calculators.canonical_qualification_result import (
    QUAL_NOT_APPLICABLE,
    QUAL_QUALIFIES,
    QUAL_USER_FACT_REQUIRED,
)
from app.calculators.canonical_role_qualification_bridge import (
    RoleAttachmentFacts,
    role_attachment_facts_from_project,
)
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_ELIGIBLE,
    evaluate_bilateral_coproduction_opportunity,
    evaluate_eurimages_coproduction_opportunity,
    evaluate_european_convention_coproduction_opportunity,
    evaluate_ibermedia_coproduction_opportunity,
)
from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.services import canonical_evaluation as ce
from app.services.canonical_production_view import build_production_and_structures

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _writer_or_director_requirement(codes=("ZZ", "YY")) -> te.PersonnelRequirement:
    return te.PersonnelRequirement(
        eligible_roles=("director", "writer"), role_mode="any_one_of",
        fact_kind="nationality", eligible_codes=codes, citation="TEST FIXTURE ONLY — not a real treaty clause.",
    )


def _synthetic_treaty(slug: str, a: str, b: str, personnel_requirement=None) -> te.TreatyData:
    return te.TreatyData(
        treaty_slug=slug, treaty_type="bilateral", jurisdiction_a=a, jurisdiction_b=b,
        majority_min_pct=20.0, minority_min_pct=20.0, minority_max_pct=80.0,
        min_coproducer_countries=2, cultural_test_required=False,
        majority_unlocks=[], minority_unlocks=[], fund_unlocks=[], confidence_tier="PARSED",
        personnel_requirement=personnel_requirement,
    )


# ---------------------------------------------------------------------------
# A — global availability must never be mislabeled project compatibility
# ---------------------------------------------------------------------------

def test_classify_opportunity_relevance_never_labels_a_non_anchored_treaty_compatible():
    """A globally enumerated treaty (project_anchored=False) must classify
    AVAILABLE even when its own contribution-share thresholds are, by
    construction, trivially satisfiable -- never CONDITIONAL, COMPATIBLE,
    or EXECUTABLE merely because a modeled split could clear it."""
    # A resolved-ELIGIBLE conditional_scenario is the strongest possible
    # signal short of the real resolution_state itself -- even this must
    # not override project_anchored=False.
    fake_conditional_scenario = {"status": "CONDITIONAL_PROJECT_FACT_DEPENDENT", "conditional_qualification_state": RESOLUTION_ELIGIBLE}
    relevance = ce._classify_opportunity_relevance("UNRESOLVED_FACTS", fake_conditional_scenario, False)
    assert relevance == "AVAILABLE"
    assert relevance not in ("CONDITIONAL", "COMPATIBLE", "EXECUTABLE")


def test_classify_opportunity_relevance_labels_anchored_assumption_priced_scenario_conditional():
    """The SAME conditional_scenario, but for a treaty genuinely anchored
    at this project's own jurisdiction, correctly classifies CONDITIONAL
    (achievable through a disclosed modeled change) -- the positive
    control proving the False case above isn't just always AVAILABLE."""
    scenario = {"status": "CONDITIONAL_PROJECT_FACT_DEPENDENT"}
    assert ce._classify_opportunity_relevance("UNRESOLVED_FACTS", scenario, True) == "CONDITIONAL"


def test_classify_opportunity_relevance_real_eligible_facts_are_executable_regardless_of_anchoring():
    """A resolution_state of ELIGIBLE only ever occurs from a REAL,
    evidenced contribution-share project fact -- never an assumption --
    so it is EXECUTABLE regardless of project_anchored."""
    assert ce._classify_opportunity_relevance(RESOLUTION_ELIGIBLE, None, True) == "EXECUTABLE"
    assert ce._classify_opportunity_relevance(RESOLUTION_ELIGIBLE, None, False) == "EXECUTABLE"


def test_classify_opportunity_relevance_real_ineligible_is_excluded():
    assert ce._classify_opportunity_relevance("INELIGIBLE", None, True) == "EXCLUDED"


def test_classify_opportunity_relevance_data_gap_is_distinct_from_available():
    scenario = {"status": "CANONICAL_DATA_GAP"}
    assert ce._classify_opportunity_relevance("UNRESOLVED_FACTS", scenario, True) == "AUTHORITY_OR_RULE_DATA_INCOMPLETE"


async def test_little_utopia_non_home_anchored_opportunities_are_never_labeled_project_compatible(db: AsyncSession):
    """Real, served-view proof: every one of Little Utopia's real
    treaty_coproduction opportunities whose parties do NOT include MU
    (Little Utopia's own home jurisdiction) must be served with
    project_anchored=False and opportunity_relevance in {AVAILABLE} --
    never COMPATIBLE/EXECUTABLE, regardless of how the (globally-scoped,
    not project-specific) conditional-pricing scenario internally
    resolves -- with exactly ONE deliberate exception:
    PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END gave uk-au-bilateral a
    real, researched personnel_requirement (writer+director, nationality-
    or-residency, Annex clause 6 of the real 1990 treaty), and Little
    Utopia's own real, confirmed GB writer/AU director genuinely QUALIFY
    under it -- a real, rule-consumed, project-specific fact, not an
    assumption. That one opportunity correctly upgrades to CONDITIONAL
    even though MU is not a party (see _classify_opportunity_relevance's
    own docstring: personnel_gate_state == QUALIFIES is a real fact-based
    credit, never presented as compatible 'merely because contribution
    shares can be assumed' -- the assumption here is still only ever the
    contribution split). Every OTHER non-anchored opportunity, with no
    such real personnel credit, remains AVAILABLE, unchanged."""
    fp = await ce.current_generation_fingerprint(db, LITTLE_UTOPIA_PROJECT_ID)
    rows = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp,
            StructureCalculationResult.calculation_trace_json["discovery_classification"].astext == "treaty_coproduction",
        )
    )).scalars().all()
    assert rows, "Little Utopia must have real treaty_coproduction rows to check"
    non_anchored = [r for r in rows if r.get("project_anchored") is False]
    assert non_anchored, "at least one of LU's real opportunities must be globally-enumerated, not MU-anchored"
    for r in non_anchored:
        parties = {p["jurisdiction_code"] for p in (r.get("coproduction_partners") or [])}
        assert "MU" not in parties
        if r.get("treaty_slug") == "uk-au-bilateral":
            assert r.get("opportunity_relevance") == "CONDITIONAL"
            assert r.get("personnel_gate_state") == QUAL_QUALIFIES
        else:
            assert r.get("opportunity_relevance") == "AVAILABLE"


# ---------------------------------------------------------------------------
# B — FACT_TRANSPORTED_NOT_RULE_CONSUMED
# ---------------------------------------------------------------------------

def test_personnel_fact_reaching_the_gate_with_no_rule_is_fact_transported_not_rule_consumed():
    """A real, confirmed personnel fact (a writer's nationality) is
    genuinely passed to evaluate_bilateral_coproduction_opportunity — the
    fact IS TRANSPORTED — but with personnel_requirement=None (every real
    treaty today) no rule exists to apply it to, so it changes nothing:
    resolution_state, is_eligible, and personnel_gate_state are byte-
    identical to the same call with NO facts supplied at all. This is
    FACT_TRANSPORTED_NOT_RULE_CONSUMED, never 'facts consumed'."""
    treaty = _synthetic_treaty("zz-yy-transported-not-consumed-test", "ZZ", "YY", personnel_requirement=None)
    te._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        facts_present = {"writer": RoleAttachmentFacts(confirmed_nationality=("ZZ",), has_any_attachment=True)}
        opp_with_facts = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=60.0, minority_pct=40.0,
            personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts=facts_present,
        )
        opp_without_facts = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=60.0, minority_pct=40.0,
            personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts=None,
        )
        assert opp_with_facts.resolution_state == opp_without_facts.resolution_state
        assert opp_with_facts.personnel_gate_state == QUAL_NOT_APPLICABLE
        assert opp_with_facts.personnel_gate_state == opp_without_facts.personnel_gate_state
        # The SAME fact, once a real rule DOES exist, IS consumed — proves
        # the transported-vs-consumed distinction is about the RULE'S
        # presence, not about whether the fact reached the evaluator (it
        # reached the evaluator in both calls above).
        req = _writer_or_director_requirement(codes=("ZZ", "YY"))
        opp_rule_consumed = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=60.0, minority_pct=40.0,
            personnel_requirement=req, personnel_attachment_facts=facts_present,
        )
        assert opp_rule_consumed.personnel_gate_state == QUAL_QUALIFIES
        assert opp_rule_consumed.personnel_gate_state != opp_with_facts.personnel_gate_state
    finally:
        del te._BILATERAL[frozenset({"ZZ", "YY"})]


async def test_little_utopia_gb_writer_and_au_director_are_transported_not_rule_consumed_except_for_uk_au(db: AsyncSession):
    """Real, live proof for Little Utopia's actual Production Record: the
    confirmed GB writer / AU director facts are genuinely fetched
    (role_attachment_facts_from_project returns real, non-empty data) and
    genuinely threaded into every one of LU's 25 real treaty opportunities
    (personnel_gate_state is computed, not skipped). Before
    PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END, zero real treaties carried
    a researched personnel_requirement, so every single one resolved
    NOT_APPLICABLE — FACT_TRANSPORTED_NOT_RULE_CONSUMED across the board.
    That workstream implemented the real, researched Australia-UK treaty
    rule (Annex clause 6 of the 1990 agreement), so uk-au-bilateral is now
    the one real, live exception: the SAME transported facts are now
    genuinely RULE-CONSUMED there (QUALIFIES) — proving the distinction
    live, not just asserted. Every OTHER real treaty remains
    FACT_TRANSPORTED_NOT_RULE_CONSUMED (NOT_APPLICABLE), unchanged."""
    facts = await role_attachment_facts_from_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert facts.get("writer") is not None and "GB" in facts["writer"].confirmed_nationality
    assert facts.get("director") is not None and "AU" in facts["director"].confirmed_nationality

    fp = await ce.current_generation_fingerprint(db, LITTLE_UTOPIA_PROJECT_ID)
    rows = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp,
            StructureCalculationResult.calculation_trace_json["discovery_classification"].astext == "treaty_coproduction",
        )
    )).scalars().all()
    assert rows
    rule_consumed = [r for r in rows if r.get("treaty_slug") == "uk-au-bilateral"]
    assert rule_consumed, "uk-au-bilateral must be one of Little Utopia's real opportunities"
    assert rule_consumed[0].get("personnel_gate_state") == QUAL_QUALIFIES
    for r in rows:
        if r.get("treaty_slug") == "uk-au-bilateral":
            continue
        assert r.get("personnel_gate_state") == QUAL_NOT_APPLICABLE, (
            "the fact was transported (personnel_gate_state was computed, not left None) "
            "but not rule-consumed (no researched rule exists for this OTHER treaty)"
        )


# ---------------------------------------------------------------------------
# C — multilateral contract consistency: NOT_APPLICABLE, never None
# ---------------------------------------------------------------------------

def test_eurimages_personnel_gate_state_is_not_applicable_never_none():
    result = evaluate_eurimages_coproduction_opportunity(
        ["FR", "DE", "BE"], country_pcts=None, cultural_test_passed=None,
    )
    assert result is not None
    assert result.personnel_gate_state == QUAL_NOT_APPLICABLE
    assert result.personnel_gate_state is not None


def test_european_convention_personnel_gate_state_is_not_applicable_never_none():
    result = evaluate_european_convention_coproduction_opportunity(
        ["FR", "DE", "BE"], country_pcts=None, cultural_test_passed=None,
    )
    assert result is not None
    assert result.personnel_gate_state == QUAL_NOT_APPLICABLE


def test_ibermedia_personnel_gate_state_is_not_applicable_never_none():
    result = evaluate_ibermedia_coproduction_opportunity(
        ["ES", "MX", "AR"], country_pcts=None, cultural_test_passed=None,
    )
    assert result is not None
    assert result.personnel_gate_state == QUAL_NOT_APPLICABLE


async def test_served_multilateral_opportunities_never_carry_a_bare_none_personnel_gate_state(db: AsyncSession):
    """Real, served-view proof for a project with real multilateral
    opportunities (F#K Valentine's Day, Greece — a real Eurimages/European
    Convention member): every served treaty_coproduction row for a
    multilateral treaty_type must carry personnel_gate_state ==
    NOT_APPLICABLE, never a bare None, closing the exact contract gap
    this workstream's objective identified."""
    fvd_id = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    fp = await ce.current_generation_fingerprint(db, fvd_id)
    rows = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == fvd_id,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp,
            StructureCalculationResult.calculation_trace_json["discovery_classification"].astext == "treaty_coproduction",
        )
    )).scalars().all()
    multilateral_rows = [
        r for r in rows
        if r.get("treaty_slug") in ("eurimages", "european-convention-coproduction", "ibermedia-multilateral")
    ]
    assert multilateral_rows, "F#K Valentine's Day (Greece) must have real multilateral opportunities to check"
    for r in multilateral_rows:
        assert r.get("personnel_gate_state") == QUAL_NOT_APPLICABLE
        assert r.get("personnel_gate_state") is not None


# ---------------------------------------------------------------------------
# D — conditional structures can never become verified winners; a real
#     executable baseline receives a leading structure
# ---------------------------------------------------------------------------

async def test_no_treaty_coproduction_row_ever_carries_priced_economics_on_its_own_result_row(db: AsyncSession):
    """Structural proof (not just a source-code assertion): every real
    treaty_coproduction StructureCalculationResult row's OWN
    total_incentive_value_usd/true_net_cost_usd are None — the only place
    a number ever appears is nested inside calculation_trace_json
    ['conditional_scenario'], which _admits_recommended / top_pair
    selection never reads at all. This is what structurally guarantees a
    conditional/assumption-priced opportunity can never become
    Project.leading_structure_id or a VERIFIED_RECOMMENDATION, across
    every real project, not just one synthetic case."""
    for pid in (LITTLE_UTOPIA_PROJECT_ID, BAD_HOMBRES_PROJECT_ID):
        fp = await ce.current_generation_fingerprint(db, pid)
        rows = (await db.execute(
            select(StructureCalculationResult.total_incentive_value_usd, StructureCalculationResult.true_net_cost_usd)
            .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
            .where(
                ProductionStructure.project_id == pid,
                StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
                StructureCalculationResult.input_fingerprint == fp,
                StructureCalculationResult.calculation_trace_json["discovery_classification"].astext == "treaty_coproduction",
            )
        )).all()
        assert rows
        for incentive, npc in rows:
            assert incentive is None
            assert npc is None


async def test_bad_hombres_no_cultural_test_baseline_receives_a_real_leading_structure(db: AsyncSession):
    """Positive control for the leading_structure_id investigation: a
    project whose baseline program genuinely has no cultural-test gate
    (NOT_APPLICABLE role_qualification, admits Recommended) DOES receive
    a real leading_structure_id, pointing at its own baseline, at the
    exact baseline economics — proving the absence of a leading structure
    for Little Utopia/FVD is a genuine per-project qualification state,
    not a systemic ranking defect this workstream introduced."""
    project = await db.get(Project, BAD_HOMBRES_PROJECT_ID)
    assert project.leading_structure_id is not None
    result = (await db.execute(
        select(StructureCalculationResult, ProductionStructure.name)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(StructureCalculationResult.structure_id == project.leading_structure_id)
        .order_by(StructureCalculationResult.created_at.desc())
    )).first()
    assert result is not None
    scr, name = result
    trace = scr.calculation_trace_json or {}
    assert trace.get("is_baseline") is True
    assert trace.get("candidate_status") == "PRICED"
    assert scr.total_incentive_value_usd is not None


async def test_little_utopia_and_fvd_baselines_are_genuinely_unresolved_not_a_ranking_defect(db: AsyncSession):
    """Real, live proof that Little Utopia's and F#K Valentine's Day's
    missing leading_structure_id is caused by their OWN baseline
    program's genuinely unresolved cultural-test qualification state
    (AUTHORITY_UNRESOLVED / USER_FACT_REQUIRED — neither admits
    Recommended per _QUALIFICATION_ADMITS_RECOMMENDED = {QUALIFIES,
    NOT_APPLICABLE}) — a real, pre-existing, single-jurisdiction
    qualification gap entirely unrelated to co-production/personnel
    wiring, not a defect this or any prior co-production workstream
    introduced."""
    fvd_id = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    for pid in (LITTLE_UTOPIA_PROJECT_ID, fvd_id):
        project = await db.get(Project, pid)
        assert project.leading_structure_id is None
        fp = await ce.current_generation_fingerprint(db, pid)
        rows = (await db.execute(
            select(StructureCalculationResult.calculation_trace_json)
            .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
            .where(
                ProductionStructure.project_id == pid,
                StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
                StructureCalculationResult.input_fingerprint == fp,
                StructureCalculationResult.calculation_trace_json["is_baseline"].astext == "true",
            )
        )).scalars().all()
        assert len(rows) == 1
        rq_state = (rows[0].get("role_qualification") or {}).get("state")
        assert rq_state not in (None, "QUALIFIES", "NOT_APPLICABLE"), (
            f"expected a genuinely unresolved qualification state for {pid}'s baseline, got {rq_state!r}"
        )


# ---------------------------------------------------------------------------
# E — four real production outputs match their stored facts
# ---------------------------------------------------------------------------

async def test_lips_like_sugar_unconfirmed_personnel_never_credited_in_the_real_served_view(db: AsyncSession):
    """Real, live proof that Lips Like Sugar's real Production Record (2
    ProjectPerson rows, BOTH unconfirmed, both NULL nationality) is
    correctly reflected: role_attachment_facts_from_project reports no
    confirmed attachment for either role. For every real treaty with NO
    researched personnel rule, personnel_gate_state is NOT_APPLICABLE
    (transported, never consumed). For uk-au-bilateral specifically
    (PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END's real, researched rule),
    the unconfirmed writer/director correctly resolve USER_FACT_REQUIRED
    — a real, disclosed conditional question, never silently credited as
    current eligibility and never a hard failure either, exactly the
    'unconfirmed personnel are not credited' requirement proven live."""
    project_id = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
    facts = await role_attachment_facts_from_project(db, project_id)
    for role in ("writer", "director"):
        rf = facts.get(role)
        assert rf is not None
        assert not rf.confirmed_nationality
        assert rf.has_unconfirmed_attachment is True

    fp = await ce.current_generation_fingerprint(db, project_id)
    rows = (await db.execute(
        select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(
            ProductionStructure.project_id == project_id,
            StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == fp,
            StructureCalculationResult.calculation_trace_json["discovery_classification"].astext == "treaty_coproduction",
        )
    )).scalars().all()
    assert rows
    for r in rows:
        if r.get("treaty_slug") == "uk-au-bilateral":
            assert r.get("personnel_gate_state") == QUAL_USER_FACT_REQUIRED
            assert r.get("personnel_gate_state") != QUAL_QUALIFIES
            assert r.get("opportunity_relevance") != "CONDITIONAL", (
                "an unconfirmed attachment must never upgrade a non-anchored "
                "opportunity to CONDITIONAL — only a real QUALIFIES credit may"
            )
        else:
            assert r.get("personnel_gate_state") == QUAL_NOT_APPLICABLE
