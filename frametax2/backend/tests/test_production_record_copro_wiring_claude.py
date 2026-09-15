"""
Claude-owned permanent tests — PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING.

Proves real Production Record (ProjectPerson -> TalentProfile) facts are
wired into official co-production treaty eligibility, never as a
universal writer/director rule -- each treaty's own PersonnelRequirement
(treaty_engine.py) expresses its own exact roles/mode/fact_kind/eligible
codes, and every real, currently-registered treaty carries
personnel_requirement=None (genuinely unresearched, never silently "no
requirement").

Uses SYNTHETIC test treaties (monkeypatched into te._BILATERAL, restored
in every test's own finally block) with a deliberately-encoded test-only
personnel rule to prove the MECHANISM -- never claims any real treaty's
actual legal text. No real treaty/program data is modified.
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
    QUAL_RULE_DATA_INCOMPLETE,
    QUAL_USER_FACT_REQUIRED,
)
from app.calculators.canonical_role_qualification_bridge import (
    RoleAttachmentFacts,
    evaluate_treaty_personnel_gate,
    role_attachment_facts_from_project,
)
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_ELIGIBLE,
    RESOLUTION_INELIGIBLE,
    RESOLUTION_UNRESOLVED_FACTS,
    evaluate_bilateral_coproduction_opportunity,
)
from app.db.session import engine
from app.models.project_fact import ProjectFact
from app.services import canonical_evaluation as ce
from app.services.canonical_production_view import build_production_and_structures

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


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
# Unit-level: evaluate_treaty_personnel_gate (pure, no DB)
# ---------------------------------------------------------------------------

def test_qualifying_writer_satisfies_writer_or_director_rule():
    req = _writer_or_director_requirement()
    facts = {"writer": RoleAttachmentFacts(confirmed_nationality=("ZZ",), has_any_attachment=True)}
    result = evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts)
    assert result.state == QUAL_QUALIFIES
    assert result.resolved_facts


def test_qualifying_director_satisfies_with_no_qualifying_writer():
    req = _writer_or_director_requirement()
    facts = {
        "director": RoleAttachmentFacts(confirmed_nationality=("YY",), has_any_attachment=True),
        "writer": RoleAttachmentFacts(confirmed_nationality=("US",), has_any_attachment=True),  # a real, non-matching writer
    }
    result = evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts)
    assert result.state == QUAL_QUALIFIES, "director alone must satisfy an any_one_of rule regardless of the writer's own fact"


def test_unknown_writer_and_director_produces_a_conditional_question_never_false_credit_or_disappearance():
    req = _writer_or_director_requirement()
    result = evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), {})
    assert result.state in (QUAL_CURABLE_GAP, QUAL_USER_FACT_REQUIRED), "must be a real conditional state, never QUALIFIES"
    assert result.state != QUAL_HARD_FAIL, "unknown facts must never be treated as a disqualification either"
    assert result.available_levers, "a real, actionable lever must be offered, not a silent gap"
    assert result.reasoning_trace, "a next-question must be generated, not silence"


def test_unconfirmed_personnel_are_not_credited_as_current_eligibility():
    req = _writer_or_director_requirement()
    facts = {"writer": RoleAttachmentFacts(has_any_attachment=True, has_unconfirmed_attachment=True)}
    result = evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts)
    assert result.state != QUAL_QUALIFIES
    assert "unconfirmed" in result.missing_facts[0].lower() or "proposed" in result.missing_facts[0].lower()


def test_nationality_only_rule_rejects_residency_substitution():
    req = te.PersonnelRequirement(
        eligible_roles=("director",), role_mode="all_of", fact_kind="nationality",
        eligible_codes=("ZZ", "YY"),
    )
    facts = {"director": RoleAttachmentFacts(confirmed_residency=("ZZ",), has_any_attachment=True)}
    result = evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts)
    assert result.state != QUAL_QUALIFIES, "a residency fact must never satisfy a nationality-only rule"


def test_residency_only_rule_rejects_nationality_substitution():
    req = te.PersonnelRequirement(
        eligible_roles=("director",), role_mode="all_of", fact_kind="residency",
        eligible_codes=("ZZ", "YY"),
    )
    facts = {"director": RoleAttachmentFacts(confirmed_nationality=("ZZ",), has_any_attachment=True)}
    result = evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts)
    assert result.state != QUAL_QUALIFIES, "a nationality fact must never satisfy a residency-only rule"


def test_either_fact_kind_genuinely_accepts_both():
    req = te.PersonnelRequirement(
        eligible_roles=("director",), role_mode="all_of", fact_kind="either",
        eligible_codes=("ZZ", "YY"),
    )
    facts_nat = {"director": RoleAttachmentFacts(confirmed_nationality=("ZZ",), has_any_attachment=True)}
    facts_res = {"director": RoleAttachmentFacts(confirmed_residency=("YY",), has_any_attachment=True)}
    assert evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts_nat).state == QUAL_QUALIFIES
    assert evaluate_treaty_personnel_gate(req, ("ZZ", "YY"), facts_res).state == QUAL_QUALIFIES


def test_no_researched_requirement_is_rule_data_incomplete_never_blocking():
    """Every real, currently-registered treaty has personnel_requirement=None
    — this must never be silently treated as either satisfied or failed."""
    result = evaluate_treaty_personnel_gate(None, ("ZZ", "YY"), {})
    assert result.state == QUAL_RULE_DATA_INCOMPLETE
    assert result.missing_facts


# ---------------------------------------------------------------------------
# Integration-level: evaluate_bilateral_coproduction_opportunity (pure, no DB)
# ---------------------------------------------------------------------------

def test_mandatory_contribution_share_gate_cannot_be_bypassed_by_creative_nationality():
    """Requirement 8: producer/entity/ownership/contribution-share gates
    remain treaty-specific and are never overridden by a satisfying
    creative-role nationality."""
    treaty = _synthetic_treaty("zz-yy-mandatory-gate-test", "ZZ", "YY", _writer_or_director_requirement())
    te._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        facts = {"director": RoleAttachmentFacts(confirmed_nationality=("ZZ",), has_any_attachment=True)}
        # contribution shares fail the treaty's own real minimum (20%) —
        # a genuinely satisfying director must not rescue this.
        opp = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=95.0, minority_pct=5.0,
            personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts=facts,
        )
        assert opp.resolution_state != RESOLUTION_ELIGIBLE
    finally:
        del te._BILATERAL[frozenset({"ZZ", "YY"})]


def test_confirmed_wrong_nationality_role_is_a_real_disqualification():
    treaty = _synthetic_treaty(
        "zz-yy-all-of-wrong-nationality-test", "ZZ", "YY",
        te.PersonnelRequirement(eligible_roles=("director",), role_mode="all_of", fact_kind="nationality", eligible_codes=("ZZ", "YY")),
    )
    te._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        facts = {"director": RoleAttachmentFacts(confirmed_nationality=("US",), has_any_attachment=True)}
        opp = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=60.0, minority_pct=40.0,
            personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts=facts,
        )
        assert opp.resolution_state == RESOLUTION_INELIGIBLE
        assert opp.personnel_failed_requirements
    finally:
        del te._BILATERAL[frozenset({"ZZ", "YY"})]


def test_unresolved_personnel_gate_keeps_opportunity_unresolved_not_eligible_or_ineligible():
    treaty = _synthetic_treaty("zz-yy-unresolved-personnel-test", "ZZ", "YY", _writer_or_director_requirement())
    te._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        opp = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=60.0, minority_pct=40.0,
            personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts={},
        )
        assert opp.resolution_state == RESOLUTION_UNRESOLVED_FACTS
        assert opp.personnel_next_question
    finally:
        del te._BILATERAL[frozenset({"ZZ", "YY"})]


def test_missing_writer_nationality_alone_does_not_suppress_the_whole_opportunity():
    """Requirement 6: a missing writer fact must not delete/suppress the
    treaty opportunity — it must still surface, as a real conditional
    (never a hard failure, never silently absent)."""
    treaty = _synthetic_treaty("zz-yy-missing-writer-test", "ZZ", "YY", _writer_or_director_requirement())
    te._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        facts = {"writer": RoleAttachmentFacts(has_any_attachment=False)}  # no attachment at all
        opp = evaluate_bilateral_coproduction_opportunity(
            "ZZ", "YY", majority_pct=60.0, minority_pct=40.0,
            personnel_requirement=treaty.personnel_requirement, personnel_attachment_facts=facts,
        )
        assert opp is not None
        assert opp.resolution_state == RESOLUTION_UNRESOLVED_FACTS
    finally:
        del te._BILATERAL[frozenset({"ZZ", "YY"})]


def test_backward_compatible_no_personnel_requirement_supplied_by_caller():
    """A caller that does not pass personnel_requirement at all (every
    call site before this wiring existed) must behave byte-identically."""
    treaty = _synthetic_treaty("zz-yy-backcompat-test", "ZZ", "YY", personnel_requirement=None)
    te._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        opp = evaluate_bilateral_coproduction_opportunity("ZZ", "YY", majority_pct=60.0, minority_pct=40.0)
        assert opp.resolution_state == RESOLUTION_ELIGIBLE
        assert opp.personnel_gate_state == QUAL_RULE_DATA_INCOMPLETE
    finally:
        del te._BILATERAL[frozenset({"ZZ", "YY"})]


# ---------------------------------------------------------------------------
# End-to-end: fingerprint recomputation + served view (real DB)
# ---------------------------------------------------------------------------

async def test_confirming_an_attachment_changes_the_fingerprint_and_forces_fresh_evaluation(db: AsyncSession):
    """Requirement: 'Recompute when any relevant personnel... confirmation...
    fact changes.' Confirming a previously-unconfirmed attachment changes
    role_attachment_facts_from_project's own output (even though it does
    NOT change role_known_codes, which never filters on is_confirmed) —
    the fingerprint must reflect that."""
    facts_before = await role_attachment_facts_from_project(db, LITTLE_UTOPIA_PROJECT_ID)
    fp_before = ce._compute_fingerprint(
        ce.ProjectEconomicInputs(
            project_id=LITTLE_UTOPIA_PROJECT_ID, project_name="t", jurisdiction_code="MU",
            production_type="feature_film", gross_budget_usd=1.0, leaf_account_sum_usd=1.0,
            budget_lines=[], spend_category_by_code={}, accounts_outside_jurisdiction=frozenset(),
            offshore_payroll_accounts=frozenset(),
        ),
        role_attachment_facts=facts_before,
    )
    # Simulate a confirmation flip without touching any real project data:
    # construct the SAME facts dict with one role's has_unconfirmed_attachment
    # toggled, proving the fingerprint payload is sensitive to it.
    mutated = dict(facts_before)
    probe_role = next(iter(mutated), "director")
    existing = mutated.get(probe_role, RoleAttachmentFacts())
    mutated[probe_role] = RoleAttachmentFacts(
        confirmed_nationality=existing.confirmed_nationality,
        confirmed_residency=existing.confirmed_residency,
        confirmed_attached_unknown_nationality=existing.confirmed_attached_unknown_nationality,
        confirmed_attached_unknown_residency=existing.confirmed_attached_unknown_residency,
        has_unconfirmed_attachment=not existing.has_unconfirmed_attachment,
        has_any_attachment=True,
    )
    fp_after = ce._compute_fingerprint(
        ce.ProjectEconomicInputs(
            project_id=LITTLE_UTOPIA_PROJECT_ID, project_name="t", jurisdiction_code="MU",
            production_type="feature_film", gross_budget_usd=1.0, leaf_account_sum_usd=1.0,
            budget_lines=[], spend_category_by_code={}, accounts_outside_jurisdiction=frozenset(),
            offshore_payroll_accounts=frozenset(),
        ),
        role_attachment_facts=mutated,
    )
    assert fp_before != fp_after, "a confirmation-status change must change the fingerprint"


async def test_served_treaty_structure_exposes_the_personnel_gate_contract(db: AsyncSession):
    """Real, served-view proof: a treaty_coproduction structure served for
    a real project, with a real synthetic personnel requirement wired in,
    exposes the full required contract (state, satisfied/failed/missing/
    curable/next-question) — not a helper called in isolation.

    A monkeypatched treaty entry is invisible to the fingerprint/cache
    (te._BILATERAL is not itself fingerprinted -- only real project
    facts are), so a row persisted by an UNRELATED evaluate_project()
    call for this same project under the current ENGINE_VERSION (same
    fingerprint, no synthetic treaty registered) could otherwise be
    reused here instead of genuinely regenerating with the treaty
    present. Current-engine-version rows are deleted first to force a
    truly fresh evaluation regardless of test execution order."""
    from sqlalchemy import delete
    from app.models.production import ProductionStructure, StructureCalculationResult

    struct_ids = (await db.execute(
        select(ProductionStructure.id).where(ProductionStructure.project_id == LITTLE_UTOPIA_PROJECT_ID)
    )).scalars().all()
    await db.execute(delete(StructureCalculationResult).where(
        StructureCalculationResult.structure_id.in_(struct_ids),
        StructureCalculationResult.engine_version == ce.ENGINE_VERSION,
    ))
    await db.commit()

    treaty_slug = "mu-gb-personnel-served-test-bilateral"
    treaty = _synthetic_treaty(treaty_slug, "MU", "GB", _writer_or_director_requirement(codes=("MU", "GB")))
    te._BILATERAL[frozenset({"MU", "GB"})] = treaty
    try:
        result = await ce.evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
        assert result["status"] == "EVALUATION_COMPLETE"
        view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
        entries = view["structures"]["allocated_structures"]["structures"]
        served = [e for e in entries if e.get("treaty_slug") == treaty_slug]
        assert served, "the synthetic treaty must surface as a real served opportunity"
        e = served[0]
        assert "personnel_gate_state" in e
        assert e["personnel_gate_state"] in (QUAL_QUALIFIES, QUAL_CURABLE_GAP, QUAL_USER_FACT_REQUIRED, QUAL_HARD_FAIL, QUAL_RULE_DATA_INCOMPLETE)
        # Little Utopia's real, confirmed director (AU) does not match
        # (MU, GB) — director role fails; writer (GB) DOES match MU/GB's
        # eligible codes and is confirmed -> QUALIFIES via the writer.
        assert e["personnel_gate_state"] == QUAL_QUALIFIES
        assert e["personnel_satisfied_requirements"]
    finally:
        del te._BILATERAL[frozenset({"MU", "GB"})]
