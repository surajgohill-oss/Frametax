"""
Worldwide Jurisdiction National/Cultural Status + Incentive Pathway
Completion — focused prevention tests.

Proves the mandatory invariants: no cultural test for base incentive !=
no national status regime; service-production qualification != national-
content qualification; national status != official co-production;
official co-production may confer national treatment without being the
same object; national-status economic consequence must reference a
canonical program or explicitly state non-economic consequence;
point-bearing role != mandatory role (CAVCO alternative-group fix);
unresolved national-status opportunity does not enter ranking.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.canonical_opportunity_bridge import (
    FACT_USER_CONFIRMATION_REQUIRED,
    STATUS_REQUIRES_USER_FACT,
    TYPE_NATIONAL_STATUS_PATHWAY,
    discover_national_status_opportunity,
)
from app.data.cultural_qualification_model import evaluate_program_eligibility
from app.data.national_cultural_status import (
    CONSEQUENCE_IS_BASE_PROGRAM,
    CONSEQUENCE_NO_INCREMENTAL_BENEFIT,
    CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE,
    STATUS_AUTHORITY_UNRESOLVED,
    STATUS_NO_RELEVANT_REGIME_CONFIRMED,
    STATUS_REGIME_CONFIRMED,
    get_jurisdiction_national_status,
)
from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


def test_no_cultural_test_for_base_incentive_does_not_mean_no_national_status():
    """Canada's own served incentive (ca_federal_pstc) requires no
    cultural test, but Canada's JURISDICTION-level national status is
    still REGIME_CONFIRMED via a real, separate pathway (CPTC) -- the
    exact ontology correction this phase mandates."""
    status = get_jurisdiction_national_status("CA")
    assert status.status == STATUS_REGIME_CONFIRMED
    assert status.base_program_slug == "ca_federal_pstc"
    assert status.linked_program_slug == "ca_federal_cptc"
    assert status.linked_program_slug != status.base_program_slug


def test_service_qualification_never_equals_national_content_qualification():
    """Australia: au_location_offset (service, no cultural test) and
    au_producer_offset (national, SAC test) are genuinely different
    programs -- never merged into one record."""
    status = get_jurisdiction_national_status("AU")
    assert status.status == STATUS_REGIME_CONFIRMED
    assert status.base_program_slug == "au_location_offset"
    assert status.linked_program_slug == "au_producer_offset"


def test_national_status_economic_consequence_always_referenced_or_explicit():
    """Task 6 -- every CONFIRMED national-status record must either
    reference a real canonical program (linked_program_slug) or
    explicitly state a non-economic/no-incremental-benefit consequence --
    never a bare 'national status exists' with no consequence."""
    for code in ("CA", "AU", "NZ", "US"):
        status = get_jurisdiction_national_status(code)
        assert status.economic_consequence is not None
        if status.status == STATUS_REGIME_CONFIRMED:
            # Either a real canonical program is referenced, or a real,
            # cited quantified detail is on file, or the consequence is
            # explicitly non-economic -- never a bare unexplained claim.
            assert (
                status.linked_program_slug is not None
                or status.consequence_detail is not None
                or status.economic_consequence in (CONSEQUENCE_NO_INCREMENTAL_BENEFIT, CONSEQUENCE_IS_BASE_PROGRAM)
            )


def test_us_confirmed_no_relevant_national_status_regime():
    """A genuine, researched 'no relevant regime' finding -- distinct
    from AUTHORITY_UNRESOLVED (never researched)."""
    status = get_jurisdiction_national_status("US")
    assert status.status == STATUS_NO_RELEVANT_REGIME_CONFIRMED
    assert status.economic_consequence == CONSEQUENCE_NO_INCREMENTAL_BENEFIT
    assert status.sources


def test_unresearched_country_is_authority_unresolved_never_fabricated():
    """A country this pass did not research must be AUTHORITY_UNRESOLVED
    with an exact proposition -- never silently defaulted to CONFIRMED or
    NO_RELEVANT_REGIME."""
    status = get_jurisdiction_national_status("JP")
    assert status.status == STATUS_AUTHORITY_UNRESOLVED
    assert status.exact_unresolved_propositions
    assert "UNCONFIRMED" in status.exact_unresolved_propositions[0]


def test_base_incentive_cultural_test_true_countries_resolve_confirmed():
    """A country whose own served incentive already requires a real,
    cited cultural test (e.g. Ireland/France/UK -- resolved last pass)
    counts as its own national-status regime -- IS_BASE_PROGRAM
    consequence, no separate linked program invented."""
    status = get_jurisdiction_national_status("IE")
    assert status.status == STATUS_REGIME_CONFIRMED
    assert status.economic_consequence == CONSEQUENCE_IS_BASE_PROGRAM
    assert status.linked_program_slug == status.base_program_slug == "ie_section_481"


def test_terminal_accounting_covers_every_country_zero_unexplained():
    """Task 3/20 -- every unique country in the current canonical
    economic database resolves to exactly one terminal state."""
    from app.data.program_requirements import all_program_requirements
    profiles = all_program_requirements()
    countries = sorted(set(p.jurisdiction_code.split("-")[0] for p in profiles.values()))
    valid_states = {STATUS_REGIME_CONFIRMED, STATUS_NO_RELEVANT_REGIME_CONFIRMED, STATUS_AUTHORITY_UNRESOLVED}
    for code in countries:
        status = get_jurisdiction_national_status(code)
        assert status.status in valid_states, f"{code} has no valid terminal state"


# ── CAVCO alternative-group correctness (point-bearing != mandatory) ────

def test_cavco_point_bearing_role_alternative_never_double_mandatory():
    """CAVCO's real rule: director OR writer, never both independently
    mandatory. A production with a Canadian writer and non-Canadian
    director must not HARD_FAIL on the director alone."""
    gate = evaluate_program_eligibility(
        "ca_federal_cptc",
        {"director": ("FR",), "writer": ("CA",), "producer": ("CA",), "lead_cast": ("CA",)},
    )
    assert gate.passes
    assert not gate.has_failure


def test_cavco_both_non_canadian_genuinely_fails():
    gate = evaluate_program_eligibility(
        "ca_federal_cptc",
        {"director": ("FR",), "writer": ("GB",), "producer": ("CA",), "lead_cast": ("CA",)},
    )
    assert gate.has_failure
    assert not gate.passes


# ── National vs official co-production, never merged ────────────────────

def test_national_status_never_equals_official_coproduction_object():
    """coproduction_relationship is a distinct, optional field -- never
    the SAME field as status/pathway_type. Official co-production may be
    REFERENCED as conferring national treatment without being modeled as
    the same object."""
    status = get_jurisdiction_national_status("AU")
    assert status.coproduction_relationship is not None
    assert status.coproduction_relationship != status.status
    assert status.coproduction_relationship != status.pathway_type
    assert "automatically satisfy" in status.coproduction_relationship.lower() or \
        "co-production" in status.coproduction_relationship.lower()


# ── Opportunity wiring: disclosure only, never fabricated economics ─────

def test_national_status_opportunity_never_fabricates_economics():
    opp = discover_national_status_opportunity("CA", "ca_federal_pstc")
    assert opp is not None
    assert opp.opportunity_type == TYPE_NATIONAL_STATUS_PATHWAY
    assert opp.status == STATUS_REQUIRES_USER_FACT
    assert opp.fact_classification == FACT_USER_CONFIRMATION_REQUIRED
    assert opp.incremental_incentive_usd == 0.0
    assert opp.net_benefit_usd is None
    assert opp.required_facts


def test_national_status_opportunity_none_when_already_on_national_pathway():
    """A candidate already priced under ca_federal_cptc itself must not
    surface an opportunity pointing back at itself."""
    assert discover_national_status_opportunity("CA", "ca_federal_cptc") is None


def test_national_status_opportunity_none_when_no_confirmed_regime():
    assert discover_national_status_opportunity("JP", "jp_vipo_location_incentive") is None


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_national_status_opportunity_never_contaminates_ranking(db: AsyncSession):
    """Task 16 -- an unresolved/disclosure-only national-status
    opportunity must never change is_directly_comparable/ranking for the
    candidate it's attached to."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ranking = view["structures"]["allocated_structures"]["ranking"]
    by_id = {e["structure_id"]: e for e in entries}
    for r in ranking:
        e = by_id.get(r["structure_id"])
        if not e:
            continue
        has_national_opp = any(
            o["opportunity_type"] == TYPE_NATIONAL_STATUS_PATHWAY for o in (e.get("opportunities") or [])
        )
        if has_national_opp:
            assert r["is_directly_comparable"] == e["is_directly_comparable"]


async def test_baselines_unchanged_after_national_status_completion(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_baseline = next(e for e in lu_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(lu_baseline["npc_with_adjustments_usd"], 2) == 3057794.90

    await evaluate_project(db, FVD_PROJECT_ID)
    fvd_view = await build_production_and_structures(db, FVD_PROJECT_ID)
    fvd_baseline = next(e for e in fvd_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(fvd_baseline["npc_with_adjustments_usd"], 2) == 3072027.16
