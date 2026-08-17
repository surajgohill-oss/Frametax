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
    NOT_APPLICABLE,
    PARTIAL,
    PRESENT,
    consolidate,
)
from app.services.canonical_residual_ledger import full_residual_ledger, ledger_entry_for
from app.services.canonical_publication_contract import (
    AUTHORITY_COMPLETE,
    AUTHORITY_INCOMPLETE,
    PRICEABLE,
    UNPRICEABLE,
    authority_completeness,
    priceability,
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
    # APPLICATION_TIMING is PRESENT, not MISSING, as of the Codex delta
    # recovery pass: program_requirements.py carries a real
    # audit_or_final_certification_deadline with basis=STATUTORY_DEADLINE
    # for uk_avec (PRIMARY_VERIFIED, CURRENT record, CREC080200) -- a
    # genuinely resolved statutory timing fact, correctly promoted rather
    # than left at the old false MISSING.
    assert c.status_for("APPLICATION_TIMING") == PRESENT
    # RESIDENT_NONRESIDENT_TREATMENT and PAYROLL_TREATMENT remain
    # genuinely MISSING for uk_avec -- no recovered source (program_
    # requirements, jurisdiction_comparison, doctrine) carries either fact
    # for this program, confirming they are not simply unwired.
    assert c.status_for("RESIDENT_NONRESIDENT_TREATMENT") == MISSING
    assert c.status_for("PAYROLL_TREATMENT") == MISSING


# ── Authority completeness contract correction — dimension-state
# resolution classification (items 3-8 of the task's focused test list) ────

def test_present_resolves_for_authority_completeness():
    from app.services.canonical_program_consolidation import RESOLVED_FOR_AUTHORITY_COMPLETENESS
    assert PRESENT in RESOLVED_FOR_AUTHORITY_COMPLETENESS


def test_not_applicable_resolves_for_authority_completeness():
    from app.services.canonical_program_consolidation import (
        NOT_APPLICABLE,
        RESOLVED_FOR_AUTHORITY_COMPLETENESS,
    )
    assert NOT_APPLICABLE in RESOLVED_FOR_AUTHORITY_COMPLETENESS


def test_authoritative_silence_confirmed_resolves_for_authority_completeness():
    from app.services.canonical_program_consolidation import (
        AUTHORITATIVE_SILENCE_CONFIRMED,
        RESOLVED_FOR_AUTHORITY_COMPLETENESS,
    )
    assert AUTHORITATIVE_SILENCE_CONFIRMED in RESOLVED_FOR_AUTHORITY_COMPLETENESS


def test_partial_remains_unresolved_for_authority_completeness():
    from app.services.canonical_program_consolidation import UNRESOLVED_FOR_AUTHORITY_COMPLETENESS
    assert PARTIAL in UNRESOLVED_FOR_AUTHORITY_COMPLETENESS


def test_missing_remains_unresolved_for_authority_completeness():
    from app.services.canonical_program_consolidation import UNRESOLVED_FOR_AUTHORITY_COMPLETENESS
    assert MISSING in UNRESOLVED_FOR_AUTHORITY_COMPLETENESS


def test_conflict_remains_unresolved_for_authority_completeness():
    from app.services.canonical_program_consolidation import CONFLICT, UNRESOLVED_FOR_AUTHORITY_COMPLETENESS
    assert CONFLICT in UNRESOLVED_FOR_AUTHORITY_COMPLETENESS


def test_resolved_and_unresolved_sets_are_disjoint_and_exhaustive():
    """No dimension status is ambiguous — every one of the five defined
    statuses is classified exactly once."""
    from app.services.canonical_program_consolidation import (
        AUTHORITATIVE_SILENCE_CONFIRMED,
        CONFLICT,
        MISSING as _M,
        NOT_APPLICABLE,
        PARTIAL as _P,
        PRESENT as _PR,
        RESOLVED_FOR_AUTHORITY_COMPLETENESS,
        UNRESOLVED_FOR_AUTHORITY_COMPLETENESS,
    )
    all_statuses = {_PR, _P, _M, NOT_APPLICABLE, AUTHORITATIVE_SILENCE_CONFIRMED, CONFLICT}
    assert RESOLVED_FOR_AUTHORITY_COMPLETENESS & UNRESOLVED_FOR_AUTHORITY_COMPLETENESS == set()
    assert RESOLVED_FOR_AUTHORITY_COMPLETENESS | UNRESOLVED_FOR_AUTHORITY_COMPLETENESS == all_statuses


# ── Task 6 — AUTHORITY_CLOSED != AUTHORITY_COMPLETE ─────────────────────────

def test_authority_closed_does_not_imply_authority_complete():
    """uk_avec is labeled AUTHORITY_CLOSED in the external validation
    artifact (research status) — this contract must not read that label at
    all, and must independently report AUTHORITY_INCOMPLETE from runtime
    consolidation data alone."""
    assert VALIDATION_JSON.exists(), f"expected validation artifact at {VALIDATION_JSON}"
    data = json.loads(VALIDATION_JSON.read_text())
    uk_avec_record = next(p for p in data["programs"] if p["program_slug"] == "uk_avec")
    assert uk_avec_record["canonical_disposition"] == "AUTHORITY_CLOSED"

    result = authority_completeness("uk_avec")
    assert result.gate == AUTHORITY_INCOMPLETE, (
        "AUTHORITY_CLOSED in the external validation artifact must not promote a program "
        "to AUTHORITY_COMPLETE"
    )


def test_authority_completeness_never_imports_authority_closed_concept():
    """Structural proof, not just behavioral: `authority_completeness()`'s
    OWN function body (the only way an external concept could actually
    influence its logic) never references authority_coverage_registry or
    any validation-artifact loader — so there is no code path for a
    research-status label to leak into the 14-dimension completeness gate.
    AUTHORITY_CLOSED must never imply AUTHORITY_COMPLETE.

    This is DELIBERATELY narrower than an earlier version of this test that
    asserted the whole MODULE never imports authority_coverage_registry.
    That premise no longer holds: the Global Priceability Optimizer
    Restoration task fixed `priceability()` to delegate to the SAME
    coverage-registry veto the served engine (production_discovery.py)
    actually calls -- that is the correct, intentional fix for the
    priceability/served-runtime divergence Codex traced, not a violation
    of this separation. The invariant that must never break is narrower
    and still absolute: `authority_completeness()` specifically must
    remain fully independent of coverage/validation status. `priceability
    ()` was never covered by that guarantee -- it has always been, by
    design, a statement about the SERVED engine, which the coverage
    registry is part of."""
    import ast
    import inspect

    from app.services import canonical_publication_contract as mod

    source = inspect.getsource(mod.authority_completeness)
    tree = ast.parse(source)
    referenced_names: set[str] = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    referenced_attrs: set[str] = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    imported_in_function: list[str] = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    ]

    assert "coverage_state" not in referenced_names | referenced_attrs
    assert "blocks_economic_candidacy" not in referenced_names | referenced_attrs
    assert not any("authority_coverage_registry" in n for n in imported_in_function)
    assert not any("validation" in n.lower() for n in imported_in_function)


def test_priceability_delegates_to_served_coverage_veto():
    """The complementary, intentional half: priceability() MUST read
    authority_coverage_registry.blocks_economic_candidacy() -- this is the
    Global Priceability Optimizer Restoration fix itself. Regression
    coverage that the delegation stays wired (if this import silently
    disappears, priceability() reverts to disagreeing with the served
    engine, exactly the bug this task fixed)."""
    import inspect

    from app.services import canonical_publication_contract as mod

    source = inspect.getsource(mod.priceability)
    assert "blocks_economic_candidacy" in source


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


def test_residual_ledger_is_exact_match_for_authority_incomplete_dimensions():
    """The ledger's residual-question set must be EXACTLY the same set
    authority_completeness() reports as unresolved -- no drift between the
    two views of the same consolidation."""
    for slug in (PRICEABLE_CONTROL, "uk_avec", "ca_federal_pstc", "us_ca_film_credit"):
        ledger = ledger_entry_for(slug)
        auth = authority_completeness(slug)
        ledger_dims = {q.dimension for q in ledger.residual_questions}
        assert ledger_dims == set(auth.unresolved_material_dimensions), (
            f"{slug}: ledger {ledger_dims} != authority_completeness "
            f"{set(auth.unresolved_material_dimensions)}"
        )


def test_full_residual_ledger_scoped_to_explicit_program_list():
    entries = full_residual_ledger(list(P0_CONTROLS) + [PRICEABLE_CONTROL])
    assert len(entries) == 4
    by_id = {e.canonical_program_id: e for e in entries}
    for slug in P0_CONTROLS:
        assert not by_id[slug].is_fully_resolved


# ── Task 6 — atomic publication contract ────────────────────────────────────

def test_incomplete_deterministic_program_cannot_publish_authority_complete():
    for slug in P0_CONTROLS:
        result = authority_completeness(slug)
        assert result.gate == AUTHORITY_INCOMPLETE, f"{slug} must not be AUTHORITY_COMPLETE"
        assert result.unresolved_material_dimensions, f"{slug} must report which dimensions are unresolved"


def test_priceable_control_is_priceable_but_authority_incomplete():
    """The core proof this correction exists for: PRICEABLE +
    AUTHORITY_INCOMPLETE is a valid, expected combination — Greece must
    NOT be forced to AUTHORITY_COMPLETE merely because it currently
    prices."""
    price_result = priceability(PRICEABLE_CONTROL)
    assert price_result.gate == PRICEABLE
    assert price_result.unresolved_required_dimensions == ()

    auth_result = authority_completeness(PRICEABLE_CONTROL)
    assert auth_result.gate == AUTHORITY_INCOMPLETE
    assert auth_result.unresolved_material_dimensions


def test_publication_contract_unknown_program_reports_unknown_not_a_crash():
    from app.services.canonical_publication_contract import UNKNOWN_PROGRAM
    assert priceability("not_a_real_program_slug_xyz").gate == UNKNOWN_PROGRAM
    assert authority_completeness("not_a_real_program_slug_xyz").gate == UNKNOWN_PROGRAM


# ── Task 8 — control program full proof ─────────────────────────────────────

@pytest.mark.parametrize("slug", [PRICEABLE_CONTROL, *P0_CONTROLS])
def test_control_programs_full_identity_consolidation_ledger_completeness(slug):
    identity = resolve_identity(slug)
    assert identity is not None, f"{slug}: IDENTITY"

    consolidation = consolidate(slug)
    assert len(consolidation.dimensions) > 0, f"{slug}: FIELD COMPLETENESS"

    ledger = ledger_entry_for(slug)
    assert ledger is not None, f"{slug}: RESIDUAL QUESTIONS"

    auth = authority_completeness(slug)
    # Every one of the four controls is AUTHORITY_INCOMPLETE today
    # (Greece included — priceable via doctrine fallback is not the same
    # as authority-complete; see test_priceable_control_is_priceable_but_
    # authority_incomplete for the explicit proof).
    assert auth.gate == AUTHORITY_INCOMPLETE
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
    """FVD's generated/priced/unpriceable counts. The candidate UNIVERSE
    (110) and the feasibility-disclosure controls below are unchanged —
    the feasibility/eligibility repair invariant this test originally
    proved still holds. The priced count legitimately moved 30 -> 31
    (Georgia, Global Priceability Optimizer Restoration) -> 39 (batch 1:
    8 programs whose existing PARSED-tier RateRule citations were
    individually re-examined and found to already meet the primary-source
    bar this project uses for VERIFIED) -> 41 (batch 2: sa_film_
    commission_rebate and si_cash_rebate, freshly re-verified this task
    against their official sources). See authority_coverage_registry.py's
    correction notes and test_batch1_programs_price_with_real_numbers_in_
    fvd / test_batch2_programs_price_with_real_numbers_in_fvd for the
    traced, real-number proof. No soft feasibility mismatch may remove a
    candidate from the economic universe."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    priced = [e for e in entries if e["is_fully_priced"]]
    unpriced = [e for e in entries if not e["is_fully_priced"]]
    assert len(entries) == 110
    assert len(priced) == 41
    assert len(unpriced) == 69

    for code in ("MN", "UZ", "AT"):
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["feasibility_status"] == FEASIBILITY_WEAK
        assert "MARINE_MISMATCH" in e["feasibility_reasons"]


# ── Historical authority source recovery — regression coverage for the
# general defect class exposed by Georgia in the prior task: a registered,
# program_slug-keyed authority source must not be silently invisible to
# consolidate(). Covers program_requirements.py and jurisdiction_
# comparison.py, the two additional sources wired in this pass. ──────────

def test_program_requirements_primary_current_promotes_to_present():
    """ca_federal_pstc has a real program_requirements.py profile:
    refundable=True, evidence.source_type=PRIMARY, evidence.status=CURRENT.
    consolidate() must read it and promote REFUNDABILITY to PRESENT --
    before this recovery pass it was silently invisible (MISSING)."""
    c = consolidate("ca_federal_pstc")
    d = next(x for x in c.dimensions if x.dimension == "REFUNDABILITY")
    assert d.status == PRESENT
    assert "program_requirements" in d.source


def test_program_requirements_secondary_or_stale_never_promotes_to_present():
    """A program_requirements profile that is not PRIMARY_VERIFIED+CURRENT
    must cap at PARTIAL, never PRESENT -- confidence tiers and record
    currentness must survive the wiring, not get silently upgraded."""
    from app.data.program_requirements import RecordStatus, VerificationState, all_program_requirements, verification_state
    secondary_or_stale = [
        slug for slug, profile in all_program_requirements().items()
        if verification_state(slug) != VerificationState.PRIMARY_VERIFIED
        or profile.evidence is None
        or profile.evidence.status != RecordStatus.CURRENT
    ]
    assert secondary_or_stale, "fixture assumption: at least one non-primary-current profile must exist"
    slug = secondary_or_stale[0]
    c = consolidate(slug)
    for dim_name in ("REFUNDABILITY", "TRANSFERABILITY", "CAP", "MINIMUM_SPEND", "APPLICATION_TIMING"):
        d = next(x for x in c.dimensions if x.dimension == dim_name)
        assert d.status != PRESENT or "program_requirements" not in d.source, (
            f"{slug}.{dim_name} was promoted to PRESENT from a non-primary-current "
            "program_requirements source"
        )


def test_jurisdiction_comparison_confidence_tier_gates_present_vs_partial():
    """jurisdiction_comparison profiles carry their own confidence_tier;
    only VERIFIED may promote a dimension to PRESENT via this source --
    PARSED/DISCOVERY (the overwhelming majority of the 110 profiles) must
    cap at PARTIAL."""
    from app.calculators import jurisdiction_comparison as jc
    non_verified_with_cultural_flag = [
        p for p in jc.ALL_PROFILES.values()
        if p.confidence_tier != "VERIFIED" and p.requires_cultural_test is not None
    ]
    assert non_verified_with_cultural_flag
    profile = non_verified_with_cultural_flag[0]
    c = consolidate(profile.program_slug)
    d = next(x for x in c.dimensions if x.dimension == "CULTURAL_OR_CONTENT_TEST")
    assert d.status != PRESENT or "jurisdiction_comparison" not in d.source


def test_monetization_reflects_post_recovery_refundability_and_transferability():
    """Regression for the MONETIZATION-staleness bug found while building
    this recovery pass: MONETIZATION was originally derived once, before
    the recovery pass could upgrade REFUNDABILITY/TRANSFERABILITY, and
    never recomputed -- uk_avec showed REFUNDABILITY=PRESENT,
    TRANSFERABILITY=PRESENT, but MONETIZATION stuck at MISSING. Must never
    regress: MONETIZATION always reflects the FINAL post-recovery state of
    its two component dimensions."""
    c = consolidate("uk_avec")
    refund = next(x for x in c.dimensions if x.dimension == "REFUNDABILITY")
    xfer = next(x for x in c.dimensions if x.dimension == "TRANSFERABILITY")
    monetization = next(x for x in c.dimensions if x.dimension == "MONETIZATION")
    assert refund.status == PRESENT
    assert xfer.status == PRESENT
    assert monetization.status == PRESENT


def test_no_recognized_authority_source_is_orphaned_from_consolidation():
    """Permanent prevention: every module listed in RECOGNIZED_AUTHORITY_
    SOURCE_MODULES must actually be imported by canonical_program_
    consolidation.py. This is the exact defect class both the doctrine-
    record bug (prior task) and the program_requirements/jurisdiction_
    comparison orphaning (this task) had in common -- a real,
    program-slug-keyed authority source existing in the repo while this
    module never reads it. A future source added to the recognized list
    without a corresponding import will fail this test immediately,
    instead of silently producing false MISSING dimensions for years."""
    import inspect
    from app.services import canonical_program_consolidation as consolidation_module
    from app.services.canonical_program_consolidation import RECOGNIZED_AUTHORITY_SOURCE_MODULES

    source = inspect.getsource(consolidation_module)
    for module_path, _reason in RECOGNIZED_AUTHORITY_SOURCE_MODULES:
        assert module_path in source, (
            f"{module_path} is listed as a recognized authority source but is not "
            "imported anywhere in canonical_program_consolidation.py -- it is orphaned "
            "from consolidation exactly like the doctrine-record and program_requirements "
            "bugs this test exists to prevent"
        )


# ── Codex authority delta recovery — regression coverage for the specific
# deltas consumed from docs/validation/CODEX_HISTORICAL_AUTHORITY_SOURCE_
# CROSS_REFERENCE.json (condition-kind mapping, monetization-recompute
# staleness fix, jurisdiction_comparison RATE_OR_AWARD_BASIS/QPE_DEFINITION,
# widened APPLICATION_TIMING field coverage). ────────────────────────────

def test_rate_condition_kind_maps_only_its_named_dimensions():
    """cultural_test_required conditions must promote CULTURAL_OR_CONTENT_
    TEST and never a dimension outside RATE_CONDITION_KIND_TO_DIMENSIONS'
    own mapping for that kind -- confirms the condition-level wiring is
    scoped to exactly what Codex's cross-reference proved, not a blanket
    RateRule promotion."""
    from app.services.canonical_program_consolidation import RATE_CONDITION_KIND_TO_DIMENSIONS
    from app.data.program_rate_rules import get_rate_rules
    assert RATE_CONDITION_KIND_TO_DIMENSIONS["cultural_test_required"] == ("CULTURAL_OR_CONTENT_TEST",)
    assert "CAP" not in RATE_CONDITION_KIND_TO_DIMENSIONS.get("cultural_test_required", ())
    # be_tax_shelter carries a cultural_test_required condition per the
    # Codex rate_condition_cross_reference -- verify the underlying
    # RateRule condition exists (the fact the wiring reads); a stronger
    # program_requirements source may still win the final aggregate for
    # this particular program via _upgrade()'s never-downgrade rule, so
    # this test checks the mapping mechanism directly rather than the
    # final precedence outcome.
    rules = get_rate_rules("be_tax_shelter")
    kinds = {cond.kind for rule in rules for cond in rule.conditions}
    assert "cultural_test_required" in kinds
    c = consolidate("be_tax_shelter")
    d = next(x for x in c.dimensions if x.dimension == "CULTURAL_OR_CONTENT_TEST")
    assert d.status in (PRESENT, PARTIAL)


def test_rate_condition_never_promotes_from_advisory_risk_kinds():
    """discretionary_band, material_funding_risk_not_modeled, atl_subcap_
    not_enforced, graduated_bracket_applied, mutually_exclusive_alternative_
    program and rate_base_narrower_than_qpe are deliberately excluded from
    RATE_CONDITION_KIND_TO_DIMENSIONS -- they are advisory/risk
    annotations about a rate's reliability, not an independent proposition
    proving a dimension resolved. Converting one into a resolved fact
    would invert its own meaning."""
    from app.services.canonical_program_consolidation import RATE_CONDITION_KIND_TO_DIMENSIONS
    for advisory_kind in (
        "discretionary_band", "material_funding_risk_not_modeled",
        "atl_subcap_not_enforced", "graduated_bracket_applied",
        "mutually_exclusive_alternative_program", "rate_base_narrower_than_qpe",
    ):
        assert advisory_kind not in RATE_CONDITION_KIND_TO_DIMENSIONS


def test_jurisdiction_comparison_rate_and_qpe_definition_confidence_gated():
    """jurisdiction_comparison's base_rate/max_rate and atl/btl/vfx/music_
    qualifies flags -- the two jc dimensions the prior recovery pass left
    unread -- must still respect the VERIFIED/PARSED confidence gate, not
    blanket-promote to PRESENT."""
    from app.calculators import jurisdiction_comparison as jc
    non_verified_with_rate = [
        p for p in jc.ALL_PROFILES.values()
        if p.confidence_tier != "VERIFIED" and (p.base_rate is not None or p.max_rate is not None)
    ]
    assert non_verified_with_rate
    profile = non_verified_with_rate[0]
    c = consolidate(profile.program_slug)
    d = next(x for x in c.dimensions if x.dimension == "RATE_OR_AWARD_BASIS")
    assert d.status != PRESENT or "jurisdiction_comparison" not in d.source


def test_monetization_recompute_never_stale_when_status_rank_unchanged():
    """Regression for the recompute-staleness bug found while wiring the
    Codex delta: _upgrade()'s never-downgrade rule left MONETIZATION's
    SOURCE STRING stale whenever the recomputed status happened to rank
    EQUAL to the pre-recovery status (e.g. PARTIAL-before vs
    PARTIAL-after) -- only the underlying REFUNDABILITY/TRANSFERABILITY
    reasoning text had changed, not the rank, so _upgrade silently kept
    the old text. ca_federal_pstc is the concrete case: REFUNDABILITY
    recovers to PRESENT but TRANSFERABILITY stays MISSING, so MONETIZATION
    stays PARTIAL either way -- the source string must still reflect the
    CURRENT REFUNDABILITY status, not a stale pre-recovery one."""
    c = consolidate("ca_federal_pstc")
    refund = next(x for x in c.dimensions if x.dimension == "REFUNDABILITY")
    monetization = next(x for x in c.dimensions if x.dimension == "MONETIZATION")
    assert refund.status == PRESENT
    assert monetization.status == PARTIAL
    assert f"refundability={refund.status}" in monetization.source


def test_application_timing_widened_field_coverage_preserves_distinct_facts():
    """uk_avec's application_deadline is absent but audit_or_final_
    certification_deadline (basis=STATUTORY_DEADLINE, PRIMARY_VERIFIED,
    CURRENT) and preapproval_mandatory=True both exist -- Codex's Task 5
    instruction was not to collapse unrelated timing concepts into one
    boolean; both distinct facts must be named in the source string, and
    the dimension must resolve PRESENT from the statutory-deadline fact."""
    c = consolidate("uk_avec")
    d = next(x for x in c.dimensions if x.dimension == "APPLICATION_TIMING")
    assert d.status == PRESENT
    assert "audit_or_final_certification_deadline" in d.source
    assert "preapproval_mandatory" in d.source


# ── Global Priceability Optimizer Restoration — priceability/served-runtime
# alignment, Georgia reconciliation, program-specific N/A, terminal
# accounting, LU/FVD control preservation. ──────────────────────────────

def test_priceability_matches_served_intrinsic_status():
    """The exact three cases Codex's optimizer lineage trace named:
    us_ga_film_credit was the sole false positive (publication PRICEABLE,
    served blocked by a stale coverage veto -- now corrected in both
    directions); au_location_offset was a false negative (served-
    priceable via a PARSED-tier RateRule, publication wrongly required
    VERIFIED); uk_avec has zero VERIFIED/PARSED-executable path and stays
    correctly UNPRICEABLE in both."""
    from app.services.canonical_publication_contract import priceability, PRICEABLE, UNPRICEABLE
    assert priceability("us_ga_film_credit").gate == PRICEABLE
    assert priceability("au_location_offset").gate == PRICEABLE
    assert priceability("uk_avec").gate == UNPRICEABLE


def test_georgia_no_annual_cap_recovered_as_not_applicable():
    """Task 3 (reconcile Georgia), generalized: CAP was falsely MISSING
    for Georgia despite its own VERIFIED RateRule citation explicitly
    stating 'No annual cap.' -- existing authority already answered the
    question; the consolidation view just never looked for the answer.
    Must resolve NOT_APPLICABLE (a confirmed absence), never PRESENT (that
    would imply a cap VALUE exists) and never stay MISSING."""
    c = consolidate("us_ga_film_credit")
    d = next(x for x in c.dimensions if x.dimension == "CAP")
    assert d.status == NOT_APPLICABLE
    assert "no annual cap" in d.source.lower()


def test_not_applicable_never_invented_from_bare_absence():
    """The Task 2 boundary: NOT_APPLICABLE must never be inferred merely
    because a field is empty -- ca_federal_pstc has no VERIFIED RateRule
    at all (so no citation text could possibly be searched), and its CAP
    must remain the honest MISSING, never promoted to NOT_APPLICABLE by
    absence alone."""
    c = consolidate("ca_federal_pstc")
    d = next(x for x in c.dimensions if x.dimension == "CAP")
    assert d.status == MISSING


def test_formulaic_terminal_accounting_sums_exactly():
    """Task 6/7: every formulaic canonical identity must terminate as
    exactly PRICEABLE or UNPRICEABLE -- no unclassified program, and the
    two counts must sum to the total formulaic universe size."""
    from app.services.canonical_program_identity import all_canonical_identities
    from app.services.canonical_publication_contract import priceability, PRICEABLE, UNPRICEABLE
    from app.data.authority_coverage_registry import coverage_state
    from app.data.program_rate_rules import get_rate_rules

    # Reconstruct the same formulaic-disposition slug set the closeout
    # artifact used: identities with a doctrine-resolvable RateRule OR a
    # recovered/known formulaic program type, excluding non-formulaic
    # coverage dispositions -- a lighter-weight proxy sufficient to prove
    # the accounting invariant holds over a large, real slice of the
    # universe without re-deriving the full Phase A classification here.
    identities = all_canonical_identities()
    sample = [
        i.canonical_program_id for i in identities
        if coverage_state(i.canonical_program_id) not in (
            "SUPERSEDED", "DUPLICATE", "NON_ECONOMIC", "NON_GUARANTEED_SELECTIVE",
            "CANONICAL_DATA_HANDOFF_DEFECT",
        )
        and len(get_rate_rules(i.canonical_program_id)) > 0
    ]
    assert sample, "fixture assumption: at least one program with rate rules must exist"
    for slug in sample:
        gate = priceability(slug).gate
        assert gate in (PRICEABLE, UNPRICEABLE), f"{slug} produced an unclassified gate: {gate!r}"


async def test_lu_mauritius_control_npc_unchanged(db: AsyncSession):
    """The single most load-bearing control value in this entire lineage:
    Little Utopia's baseline (Mauritius) true_net_cost_usd must remain
    EXACTLY $3,057,794.90 after every fix in this task. If this regresses,
    something touched served pricing logic, not just data/publication
    correctness."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    baseline = next(e for e in entries if e["is_baseline"])
    assert baseline["primary_jurisdiction"] == "MU"
    assert baseline["npc_verified_usd"] == pytest.approx(3057794.90, abs=0.01)


async def test_georgia_prices_with_real_numbers_in_fvd(db: AsyncSession):
    """Runtime proof (Task 9) that the coverage-registry correction reaches
    served state, not just the read-only publication layer: US-GA must now
    appear PRICED in FVD's candidate set with a real, traced incentive
    derived from O.C.G.A. Section 48-7-40.26, not a placeholder."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ga = next(e for e in entries if e["primary_jurisdiction"] == "US-GA")
    assert ga["is_fully_priced"] is True
    assert ga["candidate_status"] == "PRICED"
    assert ga["selected_incentive_usd"] > 0
    assert ga["npc_verified_usd"] is not None and ga["npc_verified_usd"] > 0


# ── Global Economic Data + Base Pricing — batch 1: recovered historical
# PARSED-tier data promoted to VERIFIED after individual re-examination,
# coverage vetoes removed. ───────────────────────────────────────────────

def test_batch1_doctrine_records_promoted_to_verified():
    """The exact confidence-tier promotion this batch made: each program's
    DoctrineRecord.confidence_tier must now read VERIFIED, not PARSED --
    regression coverage for the specific field edited in program_rate_
    rules_worldwide.py."""
    from app.data.executable_jurisdiction_registry import get_doctrine
    batch1 = (
        "ca_bc_pstc", "hr_cash_rebate", "nz_spg_international",
        "tt_production_expenditure_rebate", "us_la_film_incentive",
        "us_md_film_production_activity_credit", "us_nm_film_credit",
        "us_ri_film_credit",
    )
    for slug in batch1:
        doc = get_doctrine(slug)
        assert doc is not None, f"{slug} lost its DoctrineRecord"
        assert doc.confidence_tier == "VERIFIED", f"{slug} was not promoted"


def test_batch1_coverage_veto_removed_including_alias_spellings():
    """Both the canonical slug AND its known alias spelling must be
    unblocked -- the same defect class the alias rows exist to guard
    against (see the module's own 'neither spelling can price' design)."""
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    pairs = (
        ("ca_bc_pstc", "bc_pstc"),
        ("tt_production_expenditure_rebate", "tt_film_incentive"),
        ("us_la_film_incentive", "la_film_production"),
        ("us_md_film_production_activity_credit", "us_md_film_credit"),
        ("us_nm_film_credit", "nm_film_production"),
    )
    for canonical, alias in pairs:
        assert blocks_economic_candidacy(canonical) is False
        assert blocks_economic_candidacy(alias) is False


async def test_batch1_programs_price_with_real_numbers_in_fvd(db: AsyncSession):
    """Runtime proof (not just the read-only registries) that all 8 batch-1
    programs reach served state with real, distinct, non-zero numbers."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    codes = ("CA-BC", "HR", "NZ", "TT", "US-LA", "US-MD", "US-NM", "US-RI")
    seen_incentives = set()
    for code in codes:
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0
        seen_incentives.add(e["selected_incentive_usd"])
    assert len(seen_incentives) > 1, "all 8 programs priced identically -- suspicious, check for a copy-paste QPE bug"


# ── Global Economic Data + Base Pricing — batch 2: fresh primary-source
# re-verification (Saudi Arabia, Slovenia). ──────────────────────────────

def test_batch2_doctrine_records_promoted_to_verified():
    from app.data.executable_jurisdiction_registry import get_doctrine
    for slug in ("sa_film_commission_rebate", "si_cash_rebate"):
        doc = get_doctrine(slug)
        assert doc is not None
        assert doc.confidence_tier == "VERIFIED"


def test_batch2_coverage_veto_removed_including_alias_spellings():
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    for canonical, alias in (
        ("sa_film_commission_rebate", "sa_sfc_rebate"),
        ("si_cash_rebate", "si_film_incentive"),
    ):
        assert blocks_economic_candidacy(canonical) is False
        assert blocks_economic_candidacy(alias) is False


async def test_batch2_programs_price_with_real_numbers_in_fvd(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    for code in ("SA", "SI"):
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0
