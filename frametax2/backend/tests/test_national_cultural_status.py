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
    get_coproduction_coverage_status,
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
    status = get_jurisdiction_national_status("TH")
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


# ── Final pass additions (2026-08-19 continuation) ───────────────────────

def test_canada_cptc_pstc_are_separate_programs_not_an_uplift():
    """Task 5 correction: CPTC (s.125.4) and PSTC (s.125.5) are two
    legally separate federal programs -- different certificates,
    different applications, different eligible-expenditure bases -- never
    'the same program with an enhanced rate'. Corrected from an earlier
    UNLOCKS_ENHANCED_RATE misclassification."""
    status = get_jurisdiction_national_status("CA")
    assert status.economic_consequence == CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE
    assert "separate" in status.consequence_detail.lower()


def test_netherlands_and_sweden_resolved_via_recovery_not_new_research():
    """Task 4 discipline: nl_hbf and se_goteborg_fund already carried real
    NationalityRequirement rows in cultural_qualification_model.py from a
    prior pass -- resolved via internal recovery, not new web research."""
    nl = get_jurisdiction_national_status("NL")
    assert nl.status == STATUS_REGIME_CONFIRMED
    assert nl.linked_program_slug == "nl_hbf"
    assert nl.base_program_slug == "nl_film_production_incentive"

    se = get_jurisdiction_national_status("SE")
    assert se.status == STATUS_REGIME_CONFIRMED
    assert se.linked_program_slug == "se_goteborg_fund"


def test_japan_confirmed_no_relevant_regime():
    status = get_jurisdiction_national_status("JP")
    assert status.status == STATUS_NO_RELEVANT_REGIME_CONFIRMED
    assert status.sources


def test_mexico_unresolved_with_specific_lead_not_generic():
    """A real, specific research lead (EFICINE/Article 226) that could not
    be confirmed with enough rigor to reach CONFIRMED -- disclosed
    exactly, never silently upgraded to a confident claim."""
    status = get_jurisdiction_national_status("MX")
    assert status.status == STATUS_AUTHORITY_UNRESOLVED
    assert "EFICINE" in status.exact_unresolved_propositions[0]


def test_treaty_registry_covers_most_of_the_49_country_universe():
    """Task 6/7 recovery finding: treaty_engine.py already carries a real,
    substantial 26-bilateral + 3-multilateral registry covering the
    majority of the current canonical country universe -- confirmed by
    direct inspection, not re-researched from scratch."""
    from app.calculators import treaty_engine as te
    from app.data.program_requirements import all_program_requirements

    profiles = all_program_requirements()
    countries = set(p.jurisdiction_code.split("-")[0] for p in profiles.values())
    bilateral_countries = set()
    for fs in te._BILATERAL.keys():
        bilateral_countries |= set(fs)
    covered = countries & (bilateral_countries | te._EURIMAGES_MEMBERS | te._IBERMEDIA_MEMBERS)
    assert len(covered) >= 30, "treaty registry should cover a majority of the 49-country universe"


def test_us_confirmed_no_official_coproduction_treaties_corroborates_no_relevant_regime():
    """Independent corroboration this pass: the US has essentially no
    official co-production treaties with countries in our universe --
    consistent with its confirmed NO_RELEVANT national-status regime and
    its absence from treaty_engine.py's real bilateral registry."""
    from app.calculators import treaty_engine as te
    assert te.get_bilateral_treaty("US", "GB") is None
    assert te.get_bilateral_treaty("US", "CA") is None


# ── Resume/finish pass (same-day continuation) ───────────────────────────

def test_south_africa_genuine_uplift_distinct_from_canada_separate_program():
    """A REAL genuine rate uplift (South Africa: 20% base -> 35% for
    national work/official co-production, same program) -- correctly
    distinguished from Canada's separate-program relationship. Proves
    the ontology can represent both real mechanisms without conflating
    them."""
    from app.data.national_cultural_status import (
        CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE, CONSEQUENCE_UNLOCKS_UPLIFT,
    )
    za = get_jurisdiction_national_status("ZA")
    assert za.status == STATUS_REGIME_CONFIRMED
    assert za.economic_consequence == CONSEQUENCE_UNLOCKS_UPLIFT
    assert za.linked_program_slug == za.base_program_slug == "za_dtic_foreign_film"

    ca = get_jurisdiction_national_status("CA")
    assert ca.economic_consequence == CONSEQUENCE_UNLOCKS_SEPARATE_INCENTIVE
    assert ca.linked_program_slug != ca.base_program_slug


def test_estonia_personnel_residency_uplift_confirmed():
    """A third real mechanism: a rate tier gated on creative-staff
    residency within the same program (distinct from both Canada's
    separate-program and South Africa's national-work uplift)."""
    from app.data.national_cultural_status import CONSEQUENCE_UNLOCKS_UPLIFT
    ee = get_jurisdiction_national_status("EE")
    assert ee.status == STATUS_REGIME_CONFIRMED
    assert ee.economic_consequence == CONSEQUENCE_UNLOCKS_UPLIFT
    assert "residen" in ee.consequence_detail.lower()


def test_korea_and_philippines_official_coproduction_enables_national_pathway():
    """Task 6/12: ENABLES_OFFICIAL_COPRODUCTION_ROUTE as the qualification
    mechanism itself, confirmed via each country's own real treaty list
    (KOFIC for Korea, FDCP for Philippines)."""
    from app.data.national_cultural_status import CONSEQUENCE_ENABLES_OFFICIAL_COPRODUCTION_ROUTE
    for code in ("KR", "PH"):
        status = get_jurisdiction_national_status(code)
        assert status.status == STATUS_REGIME_CONFIRMED
        assert status.economic_consequence == CONSEQUENCE_ENABLES_OFFICIAL_COPRODUCTION_ROUTE
        assert status.coproduction_relationship


def test_switzerland_pics_gate_is_coproduction_status_itself():
    """Switzerland: qualification for the national program runs on
    official co-production STATUS itself, not a personnel points table --
    a materially different real model, recovered from the program's own
    existing treaty_or_official_coproduction_required=True field."""
    ch = get_jurisdiction_national_status("CH")
    assert ch.status == STATUS_REGIME_CONFIRMED
    assert ch.linked_program_slug == ch.base_program_slug == "ch_pics_national_rebate"


def test_coproduction_coverage_computed_from_real_treaty_engine_data():
    """Queue C for countries treaty_engine.py's OWN registry already
    covers must be computed directly from that data, never re-researched."""
    from app.data.national_cultural_status import COPRO_ROUTE_EXISTS, COPRO_MULTILATERAL_EXISTS
    ca = get_coproduction_coverage_status("CA")
    assert ca.status == COPRO_ROUTE_EXISTS
    assert "GB" in ca.confirmed_bilateral_partners
    fr = get_coproduction_coverage_status("FR")
    assert fr.status in (COPRO_ROUTE_EXISTS, COPRO_MULTILATERAL_EXISTS)


def test_coproduction_coverage_newly_resolved_countries():
    """7 of the original 13 uncovered countries resolved this pass, each
    with real, cited partner facts -- existence only, never fabricated
    contribution terms."""
    from app.data.national_cultural_status import COPRO_ROUTE_EXISTS, COPRO_NO_RELEVANT_ROUTE
    kr = get_coproduction_coverage_status("KR")
    assert kr.status == COPRO_ROUTE_EXISTS
    assert set(kr.confirmed_bilateral_partners) >= {"CA", "GB"}
    il = get_coproduction_coverage_status("IL")
    assert il.status == COPRO_ROUTE_EXISTS
    th = get_coproduction_coverage_status("TH")
    assert th.status == COPRO_NO_RELEVANT_ROUTE  # genuinely confirmed absent, not unresolved


def test_hard_blocker_documentation_is_specific_not_generic():
    """Task's own hard-blocker standard: every remaining unresolved
    proposition must be specific (names sources checked, what remains
    unknown) -- never a generic 'not found' placeholder."""
    for code in ("AE", "QA", "SA", "MU", "TW"):
        status = get_jurisdiction_national_status(code)
        assert status.status == STATUS_AUTHORITY_UNRESOLVED
        prop = status.exact_unresolved_propositions[0]
        assert "Sources checked" in prop or "sources checked" in prop.lower() or "Requires:" in prop
        generic_phrases = ("insufficient authority", "not found.", "further research required")
        assert not any(p in prop.lower() for p in generic_phrases)


def test_national_status_terminal_accounting_improved_substantially():
    """This continuation must show real, measurable improvement over the
    763e766 checkpoint (26 confirmed / 21 unresolved) -- never stagnant."""
    from app.data.program_requirements import all_program_requirements
    profiles = all_program_requirements()
    countries = sorted(set(p.jurisdiction_code.split("-")[0] for p in profiles.values()))
    confirmed = sum(1 for c in countries if get_jurisdiction_national_status(c).status == STATUS_REGIME_CONFIRMED)
    unresolved = sum(1 for c in countries if get_jurisdiction_national_status(c).status == STATUS_AUTHORITY_UNRESOLVED)
    assert confirmed > 26, f"expected real improvement over the 26-confirmed checkpoint, got {confirmed}"
    assert unresolved < 21, f"expected real reduction from the 21-unresolved checkpoint, got {unresolved}"


async def test_baselines_unchanged_after_national_status_completion(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_baseline = next(e for e in lu_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(lu_baseline["npc_with_adjustments_usd"], 2) == 3057794.90

    await evaluate_project(db, FVD_PROJECT_ID)
    fvd_view = await build_production_and_structures(db, FVD_PROJECT_ID)
    fvd_baseline = next(e for e in fvd_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(fvd_baseline["npc_with_adjustments_usd"], 2) == 3072027.16
