"""
FVD canonical input assembly repair — targeted regression tests.

Covers exactly what this repair changed (input assembly for the canonical
evaluator), not a broad re-audit: real SA-1 scripted-location/production-
requirement data reaching discovery's capability match, UNKNOWN-vs-known-
empty territorial-fact disclosure, the local-entity canonical assumption
never blocking a real candidate today, and the representative jurisdiction
traces from FVD_CANONICAL_INPUT_ASSEMBLY_REPAIR.md.

Read-only/idempotent against the real F#K Valentine's Day and Little
Utopia project rows — same convention as test_canonical_evaluation.py.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project
from app.services.canonical_production_view import build_production_and_structures
from app.services.canonical_project_economics import (
    FACT_STATE_UNKNOWN,
    _location_categories_from_descriptions,
    build_physical_requirements,
    build_project_economic_inputs,
)

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── Task 2: UNKNOWN vs known-empty territorial facts ───────────────────────

async def test_fvd_territorial_facts_are_unknown_not_known_empty(db: AsyncSession):
    """FVD genuinely has no budget_accounts_outside_base_jurisdiction or
    budget_offshore_payroll_accounts ProjectFact row on file -- the state
    must read UNKNOWN, never be silently reported as a confirmed empty set."""
    econ = await build_project_economic_inputs(db, FVD_PROJECT_ID)
    assert econ.ok
    assert econ.inputs.accounts_outside_jurisdiction_state == FACT_STATE_UNKNOWN
    assert econ.inputs.offshore_payroll_accounts_state == FACT_STATE_UNKNOWN
    # The qualification ladder itself still receives the only safe input a
    # set-membership check can be given without inventing evidence.
    assert econ.inputs.accounts_outside_jurisdiction == frozenset()
    assert econ.inputs.offshore_payroll_accounts == frozenset()


async def test_unknown_territorial_facts_flag_priced_results_provisional(db: AsyncSession):
    """Every FVD priced candidate must carry has_unverified_inputs=True and
    an explicit UNKNOWN-not-known-empty warning -- provisional/blocking in
    the served sense (requires confirmation), never silently absorbed as
    though a project fact had actually confirmed no accounts are outside
    the base jurisdiction."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    priced = [e for e in entries if e["is_fully_priced"]]
    assert len(priced) > 0
    for e in priced:
        assert e["warnings"], f"{e['primary_jurisdiction']} priced result must carry warnings"
        assert any("UNKNOWN, not KNOWN EMPTY" in w for w in e["warnings"]), (
            f"{e['primary_jurisdiction']} must disclose the UNKNOWN territorial-fact state"
        )


# ── Task 3: persisted SA-1 requirements reach discovery ─────────────────────

def test_location_categories_bridge_is_pure_deterministic_keyword_matching():
    """The abstract_location() <-> location_categories vocabulary bridge:
    real scripted-location text in, real category keys out, no invention."""
    out = _location_categories_from_descriptions([
        "MEDITERRANEAN SEA SHORE", "SECLUDED BEACH", "CITY STREET", "APARTMENT",
    ])
    assert out["marine_open_water"]["effective"] is True
    assert out["beach_coast"]["effective"] is True
    assert out["mediterranean"]["effective"] is True
    assert out["urban"]["effective"] is True
    assert "APARTMENT" not in str(out), "a location string with no ontology hit must not appear as a hit"
    # Real ontology hits with no location_categories key equivalent (e.g.
    # "harbor_marina" from a false-positive "PORT" substring match) must be
    # dropped, never fabricated into a category that doesn't exist.
    assert "harbor_marina" not in out


def test_location_categories_bridge_empty_input_stays_empty():
    assert _location_categories_from_descriptions([]) == {}
    assert _location_categories_from_descriptions(["", None]) == {}


async def test_build_physical_requirements_reads_real_fvd_scripted_locations(db: AsyncSession):
    """FVD's real 54 ProjectLocationRequirement rows include evidence-backed
    Mediterranean/marine scenes -- build_physical_requirements() must
    surface open-water capability from them, not return {}."""
    pr = await build_physical_requirements(db, FVD_PROJECT_ID)
    assert pr["location_categories"].get("marine_open_water", {}).get("effective") is True
    assert pr["location_categories"].get("beach_coast", {}).get("effective") is True


async def test_landlocked_jurisdictions_remain_economically_discoverable(db: AsyncSession):
    """Canonical authority substrate + feasibility boundary repair, Task 1/2
    (supersedes this file's original, since-reverted premise): FVD's real
    script (Mediterranean sea-shore/beach/harbor scenes) makes open-water
    filming a genuine soft PRODUCTION FEASIBILITY signal, never a hard
    ECONOMIC ELIGIBILITY gate. A landlocked jurisdiction (marine_suitability
    =NONE in the existing, unmodified jurisdiction_comparison profiles) must
    remain in the economic universe -- discoverable, and priced whenever
    authority/rate rules independently permit it -- with its real marine
    mismatch disclosed as feasibility metadata, never used to silently
    remove it."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    served_codes = {e["primary_jurisdiction"] for e in entries}
    by_code = {e["primary_jurisdiction"]: e for e in entries}

    from app.calculators import jurisdiction_comparison as jc
    for code in ("MN", "UZ", "AT", "CZ", "HU"):
        profile = jc.ALL_PROFILES.get(code)
        assert profile is not None, f"test precondition: {code} must have a real capability profile"
        assert str(getattr(profile, "marine_suitability", "")).lower().endswith("none"), (
            f"test precondition: {code} must genuinely be marine_suitability=NONE"
        )
        assert code in served_codes, (
            f"{code} is a soft marine mismatch, not a statutory eligibility failure -- "
            "it must remain in the economic universe"
        )

    # MN and UZ specifically retain their pre-regression PRICED status
    # (their program authority/rate rules independently resolve) --
    # feasibility never overrides an economic outcome that authority/rate
    # rules already determined.
    assert by_code["MN"]["is_fully_priced"] is True
    assert by_code["UZ"]["is_fully_priced"] is True


async def test_marine_capable_jurisdictions_unaffected_by_capability_gate(db: AsyncSession):
    """The capability gate must not over-reject: every jurisdiction with
    real marine/coastal capability data stays exactly as priced as before."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    priced = {
        e["primary_jurisdiction"] for e in view["structures"]["allocated_structures"]["structures"]
        if e["is_fully_priced"]
    }
    for code in ("GR", "MT", "MU", "AU-QLD", "CA-NL", "QA", "SG"):
        assert code in priced, f"{code} has real marine capability and must remain priced"


# ── Task 4: real budget account identity reaches allocation (verification) ──

async def test_qpe_is_derived_from_real_account_universe_not_one_flattened_total(db: AsyncSession):
    """Greece's 80%-cap and Mauritius's HYBRID_CONDITIONAL doctrine produce
    QPE figures that differ from the shared OPEN_DEFAULT_INCLUDE group --
    proof the qualification ladder is reading real, distinct budget-account
    treatment per program, not one flattened nominal spend pool applied
    identically regardless of doctrine."""
    econ = await build_project_economic_inputs(db, FVD_PROJECT_ID)
    assert econ.ok
    # The real FVD budget line count (not a generic/nominal single total).
    assert len(econ.inputs.budget_lines) > 20
    assert len({line.account_code for line in econ.inputs.budget_lines}) == len(econ.inputs.budget_lines)

    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    by_code = {e["primary_jurisdiction"]: e for e in entries if e["is_fully_priced"]}
    gr_qpe = sum(sg["qpe_usd"] for sg in by_code["GR"]["segments"])
    mu_qpe = sum(sg["qpe_usd"] for sg in by_code["MU"]["segments"])
    mt_qpe = sum(sg["qpe_usd"] for sg in by_code["MT"]["segments"])
    assert gr_qpe != mt_qpe, "GR's 80%-cap must genuinely differentiate its QPE"
    assert mu_qpe != mt_qpe, "MU's HYBRID_CONDITIONAL doctrine must genuinely differentiate its QPE"


# ── Task 5: local-entity/SPV canonical assumption never falsely blocks ──────

async def test_no_fvd_candidate_is_blocked_on_local_entity_grounds(db: AsyncSession):
    """Verification, not a fix: nothing in the canonical discovery/rate-
    resolution path currently gates on requires_local_entity at all (it is
    carried as descriptive JurisdictionExamination metadata only), so the
    canonical product assumption ("assume the production establishes the
    customary local structure") requires no active enforcement code today.
    If this regresses -- a real candidate blocked citing a local entity/SPV
    requirement -- that would violate the canonical product assumption."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    for e in view["structures"]["allocated_structures"]["structures"]:
        if e["is_fully_priced"]:
            continue
        reason_text = " ".join(e.get("blockers") or []) + " " + str(e.get("reason") or "")
        for kw in ("local entity", "local spv", "applicant company", "local applicant"):
            assert kw not in reason_text.lower(), (
                f"{e['primary_jurisdiction']} is blocked citing '{kw}' — violates the canonical "
                "product assumption that ordinary local structuring must not itself block pricing"
            )


# ── Task 8: representative jurisdiction traces ───────────────────────────────

async def test_representative_fvd_jurisdiction_traces(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = {
        e["primary_jurisdiction"]: e for e in view["structures"]["allocated_structures"]["structures"]
        if e["is_fully_priced"]
    }

    def seg(code):
        return entries[code]["segments"][0]

    gr = seg("GR")
    assert gr["qpe_usd"] == pytest.approx(3_614_149.60, abs=0.01)
    assert gr["qpe_cap_applied_usd"] == pytest.approx(540_671.40, abs=0.01)
    assert gr["rate_floor"] == gr["rate_ceiling"] == 0.4
    assert entries["GR"]["npc_with_adjustments_usd"] == pytest.approx(3_072_027.16, abs=0.01)

    ca_nl = seg("CA-NL")
    assert ca_nl["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    # Final-19 committee closeout: gov.nl.ca directly confirmed a flat 40%
    # rate (no separate ceiling tier) -- the prior 45%-ceiling entry was
    # carried forward unconfirmed from an older catalog figure and is now
    # corrected/removed per the official source.
    assert ca_nl["rate_floor"] == pytest.approx(0.40)
    assert ca_nl["rate_ceiling"] == pytest.approx(0.40)
    assert ca_nl["is_band_ceiling"] is False
    assert ca_nl["ceiling_requires_confirmation"] is False

    qa = seg("QA")
    assert qa["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    assert qa["rate_floor"] == pytest.approx(0.40)
    assert qa["rate_ceiling"] == pytest.approx(0.50)

    sg = seg("SG")
    assert sg["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    assert entries["SG"]["selected_incentive_usd"] == pytest.approx(1_661_928.40, abs=0.01), (
        "Singapore selects its modeled/discretionary ceiling rate, not the conservative floor"
    )

    mt = seg("MT")
    assert mt["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    assert mt["is_band_ceiling"] is True
    assert mt["ceiling_requires_confirmation"] is True

    mu = seg("MU")
    assert mu["qpe_usd"] == pytest.approx(1_132_056.00, abs=0.01)
    assert mu["doctrine"] == "hybrid_conditional"

    au_qld = seg("AU-QLD")
    assert au_qld["qpe_usd"] == pytest.approx(4_154_821.00, abs=0.01)
    assert au_qld["rate_floor"] == au_qld["rate_ceiling"] == 0.15
    assert au_qld["is_band_ceiling"] is False


# ── Task 10: Little Utopia narrow regression ─────────────────────────────────

async def test_little_utopia_regression_unchanged_by_input_assembly_repair(db: AsyncSession):
    """This repair's real effect (build_physical_requirements reading
    ProjectLocationRequirement/ProductionRequirement rows) is a genuine
    no-op for Little Utopia through this generic path: LU's own script data
    lives in little_utopia_state.py's hand-built Python constants, not in
    the generic SA-1 DB tables, so this query finds nothing new for it
    either way. LU's REAL served path is the separate in-memory demo state
    (app.demo.little_utopia_state), entirely untouched by this repair."""
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["engine_version"] == ENGINE_VERSION
    assert result["base_jurisdiction_code"] == "MU"
    assert result["top_result"]["true_net_cost_usd"] == 3_057_794.90
    assert result["top_result"]["is_baseline"] is True
