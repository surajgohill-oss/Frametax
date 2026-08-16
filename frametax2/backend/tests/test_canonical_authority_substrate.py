"""
Canonical authority substrate + feasibility boundary repair — targeted
regression tests.

Covers: the feasibility/eligibility repair (Tasks 1/2) and the four new
identity/consolidation/ledger/publication modules (Tasks 3-6), against the
control programs specified in the task (Task 8) and the real FVD/LU
projects (Tasks 9/10).

Read-only/idempotent against the real F#K Valentine's Day and Little
Utopia project rows — same convention as the other canonical_evaluation
test files.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import (
    FEASIBILITY_STRONG,
    FEASIBILITY_UNKNOWN,
    FEASIBILITY_WEAK,
    FEASIBILITY_WORKABLE,
    _feasibility_status,
    evaluate_project,
    ENGINE_VERSION,
)
from app.services.canonical_production_view import build_production_and_structures
from app.services.canonical_program_identity import (
    all_canonical_identities,
    resolve_identity,
)
from app.services.canonical_program_consolidation import (
    MISSING,
    PARTIAL,
    PRESENT,
    consolidate,
)
from app.services.canonical_residual_ledger import full_residual_ledger, ledger_entry_for
from app.services.canonical_publication_contract import (
    EXECUTABLE_COMPLETE,
    NOT_EXECUTABLE_COMPLETE,
    executable_completeness,
)

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"

#: Task 8 control programs.
PRICEABLE_CONTROL = "gr_cash_rebate"
P0_CONTROLS = ("uk_avec", "ca_federal_pstc", "us_ca_film_credit")

VALIDATION_JSON = (
    Path(__file__).resolve().parents[3]
    / "docs" / "validation" / "CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.json"
)


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── Test 1/2 (from the task's numbered list) — feasibility vs eligibility ──

async def test_soft_feasibility_mismatch_does_not_reject_economic_candidate(db: AsyncSession):
    """A landlocked jurisdiction with a real marine mismatch must remain a
    priced economic candidate — feasibility never suppresses discovery."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = {e["primary_jurisdiction"]: e for e in view["structures"]["allocated_structures"]["structures"]}
    assert "MN" in entries and entries["MN"]["is_fully_priced"] is True
    assert "UZ" in entries and entries["UZ"]["is_fully_priced"] is True


async def test_statutory_eligibility_failure_still_rejects_correctly(db: AsyncSession):
    """A genuine authority/rate/threshold failure must still terminate the
    candidate as unpriceable — this repair only removed the SOFT
    feasibility gate, never the real economic gates."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = {e["primary_jurisdiction"]: e for e in view["structures"]["allocated_structures"]["structures"]}
    au = entries["AU"]
    assert au["is_fully_priced"] is False
    assert au.get("candidate_status") == "RULE_REJECTED"


def test_unknown_production_feasibility_remains_unknown():
    """No capability profile at all -> feasibility_status is UNKNOWN, never
    guessed as WEAK or WORKABLE."""
    from app.calculators.production_requirements import ProductionRequirements
    reqs = ProductionRequirements(
        environments=frozenset({"open_water_filming"}),
        infrastructure=frozenset(),
        required_capabilities=frozenset({"open_water_filming"}),
        evidence={},
    )
    status, reasons = _feasibility_status(None, reqs)
    assert status == FEASIBILITY_UNKNOWN
    assert reasons == []


# ── SA-1 / local-entity preservation ────────────────────────────────────────

async def test_sa1_requirements_remain_consumed(db: AsyncSession):
    """Real SA-1 scripted-location evidence must still be reachable and
    disclosed as feasibility metadata, even though it no longer gates
    economic discovery."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = {e["primary_jurisdiction"]: e for e in view["structures"]["allocated_structures"]["structures"]}
    assert entries["MN"]["feasibility_status"] == FEASIBILITY_WEAK
    assert "MARINE_MISMATCH" in entries["MN"]["feasibility_reasons"]
    assert entries["GR"]["feasibility_status"] == FEASIBILITY_STRONG


async def test_local_entity_assumption_remains_intact(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    for e in view["structures"]["allocated_structures"]["structures"]:
        if e["is_fully_priced"]:
            continue
        reason_text = " ".join(e.get("blockers") or []) + " " + str(e.get("reason") or "")
        for kw in ("local entity", "local spv", "applicant company"):
            assert kw not in reason_text.lower()


# ── Task 3 — canonical identity manifest ────────────────────────────────────

def test_canonical_identity_resolves_aliases_consistently():
    direct = resolve_identity("ae_ad_film_rebate")
    via_alias = resolve_identity("proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate")
    assert direct is not None and via_alias is not None
    assert direct.canonical_program_id == via_alias.canonical_program_id == "ae_ad_film_rebate"
    assert via_alias.canonical_slug == direct.canonical_slug


def test_canonical_identity_unknown_spelling_returns_none():
    assert resolve_identity("not_a_real_program_slug_xyz") is None


def test_all_canonical_identities_cover_a_substantial_program_universe():
    identities = all_canonical_identities()
    assert len(identities) > 200
    slugs = [i.canonical_program_id for i in identities]
    assert len(slugs) == len(set(slugs)), "no duplicate canonical_program_id"


# ── Task 4 — field consolidation ────────────────────────────────────────────

def test_consolidation_exposes_field_provenance():
    c = consolidate(PRICEABLE_CONTROL)
    for dim in c.dimensions:
        assert dim.status in (PRESENT, PARTIAL, MISSING)
        assert dim.source, f"{dim.dimension} must carry a non-empty provenance source string"


def test_missing_fields_remain_missing_not_defaulted():
    c = consolidate("uk_avec")
    assert c.status_for("TERRITORIALITY") == MISSING
    assert c.status_for("APPLICATION_TIMING") == MISSING


# ── Task 6 — AUTHORITY_CLOSED != EXECUTABLE_COMPLETE ───────────────────────

def test_authority_closed_does_not_imply_executable_complete():
    """uk_avec is labeled AUTHORITY_CLOSED in the external validation
    artifact (research status) — this contract must not read that label at
    all, and must independently report NOT_EXECUTABLE_COMPLETE from
    runtime executable data alone."""
    assert VALIDATION_JSON.exists(), f"expected validation artifact at {VALIDATION_JSON}"
    data = json.loads(VALIDATION_JSON.read_text())
    uk_avec_record = next(p for p in data["programs"] if p["program_slug"] == "uk_avec")
    assert uk_avec_record["canonical_disposition"] == "AUTHORITY_CLOSED"

    result = executable_completeness("uk_avec")
    assert result.gate == NOT_EXECUTABLE_COMPLETE, (
        "AUTHORITY_CLOSED in the external validation artifact must not promote a program "
        "to EXECUTABLE_COMPLETE"
    )


def test_publication_contract_never_imports_authority_closed_concept():
    """Structural proof, not just behavioral: the module's IMPORTS (the
    only way an external concept could actually influence its logic) never
    touch authority_coverage_registry or any validation-artifact loader —
    so there is no code path for a research-status label to leak into the
    executable-completeness gate. (The module's own docstring names these
    concepts in prose, explaining exactly this exclusion — that is
    expected and is not what this test checks.)"""
    import ast
    import inspect

    from app.services import canonical_publication_contract as mod

    tree = ast.parse(inspect.getsource(mod))
    imported_modules: list[str] = []
    imported_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)

    assert not any("authority_coverage_registry" in m for m in imported_modules), (
        f"must not import authority_coverage_registry, found in: {imported_modules}"
    )
    assert not any("validation" in m.lower() for m in imported_modules)
    assert "coverage_state" not in imported_names
    assert "blocks_economic_candidacy" not in imported_names


# ── Task 5 — residual-question ledger ───────────────────────────────────────

def test_residual_ledger_captures_incomplete_fields():
    entry = ledger_entry_for("uk_avec")
    assert entry is not None
    assert not entry.is_fully_resolved
    dims = {q.dimension for q in entry.residual_questions}
    assert "RATE_OR_AWARD_BASIS" in dims
    assert "TERRITORIALITY" in dims
    for q in entry.residual_questions:
        assert q.detail, f"{q.dimension} residual question must carry a real detail string"


def test_residual_ledger_for_priceable_control_has_fewer_open_questions():
    priceable = ledger_entry_for(PRICEABLE_CONTROL)
    incomplete = ledger_entry_for("uk_avec")
    assert len(priceable.residual_questions) < len(incomplete.residual_questions)


def test_full_residual_ledger_scoped_to_explicit_program_list():
    entries = full_residual_ledger(list(P0_CONTROLS) + [PRICEABLE_CONTROL])
    assert len(entries) == 4
    by_id = {e.canonical_program_id: e for e in entries}
    for slug in P0_CONTROLS:
        assert not by_id[slug].is_fully_resolved


# ── Task 6 — atomic publication contract ────────────────────────────────────

def test_incomplete_deterministic_program_cannot_publish_executable_complete():
    for slug in P0_CONTROLS:
        result = executable_completeness(slug)
        assert result.gate == NOT_EXECUTABLE_COMPLETE, f"{slug} must not be EXECUTABLE_COMPLETE"
        assert result.unresolved_required_dimensions, f"{slug} must report which dimensions are unresolved"


def test_complete_control_program_satisfies_publication_contract():
    result = executable_completeness(PRICEABLE_CONTROL)
    assert result.gate == EXECUTABLE_COMPLETE
    assert result.unresolved_required_dimensions == ()


def test_publication_contract_unknown_program_reports_unknown_not_a_crash():
    from app.services.canonical_publication_contract import UNKNOWN_PROGRAM
    result = executable_completeness("not_a_real_program_slug_xyz")
    assert result.gate == UNKNOWN_PROGRAM


# ── Task 8 — control program full proof ─────────────────────────────────────

@pytest.mark.parametrize("slug", [PRICEABLE_CONTROL, *P0_CONTROLS])
def test_control_programs_full_identity_consolidation_ledger_completeness(slug):
    identity = resolve_identity(slug)
    assert identity is not None, f"{slug}: IDENTITY"

    consolidation = consolidate(slug)
    assert len(consolidation.dimensions) > 0, f"{slug}: FIELD COMPLETENESS"

    ledger = ledger_entry_for(slug)
    assert ledger is not None, f"{slug}: RESIDUAL QUESTIONS"

    completeness = executable_completeness(slug)
    if slug == PRICEABLE_CONTROL:
        assert completeness.gate == EXECUTABLE_COMPLETE
        assert ledger.is_fully_resolved is False  # optional dims (e.g. UPLIFT_RULES) remain open
    else:
        assert completeness.gate == NOT_EXECUTABLE_COMPLETE
        assert not ledger.is_fully_resolved


# ── Task 9 — Little Utopia exact regression ─────────────────────────────────

async def test_little_utopia_exact_regression_after_authority_substrate_repair(db: AsyncSession):
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["engine_version"] == ENGINE_VERSION
    assert result["base_jurisdiction_code"] == "MU"
    assert result["top_result"]["true_net_cost_usd"] == 3_057_794.90
    assert result["top_result"]["is_baseline"] is True


# ── Task 10 — FVD runtime candidate-universe regression ─────────────────────

async def test_fvd_runtime_candidate_universe_restored(db: AsyncSession):
    """FVD's generated/priced/unpriceable counts must match the accepted
    CODEX_PRICEABILITY_BLOCKER_RECONCILIATION.md maximum (110/30/80) after
    the feasibility/eligibility repair — no soft feasibility mismatch may
    remove a candidate from the economic universe."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    priced = [e for e in entries if e["is_fully_priced"]]
    unpriced = [e for e in entries if not e["is_fully_priced"]]
    assert len(entries) == 110
    assert len(priced) == 30
    assert len(unpriced) == 80

    for code in ("MN", "UZ", "AT"):
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["feasibility_status"] == FEASIBILITY_WEAK
        assert "MARINE_MISMATCH" in e["feasibility_reasons"]
