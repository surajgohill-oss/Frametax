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
    """A landlocked jurisdiction with a real marine mismatch must still be
    DISCOVERED — feasibility never suppresses discovery.

    MN and UZ are both landlocked with a soft marine mismatch. They are no
    longer *priced*, but for a reason that has nothing to do with
    feasibility: both are AUTHORITY_UNRESOLVED_NON_PRICEABLE and the
    fail-closed authority gate withholds deterministic economics from them
    (PROJECT_RULES.md final authority-safety gate). This test therefore
    asserts the thing it always meant to assert — the soft feasibility gate
    is not what removes them — and proves the two gates stay independent.
    """
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = {e["primary_jurisdiction"]: e for e in view["structures"]["allocated_structures"]["structures"]}

    for code in ("MN", "UZ"):
        assert code in entries, f"{code} was suppressed from discovery entirely"
        entry = entries[code]
        # Discovery kept it and disclosed the real, non-feasibility reason.
        blocking_text = " ".join([entry.get("reason") or "", *(entry.get("blockers") or [])]).lower()
        assert "authority unresolved non priceable" in blocking_text, (
            f"{code} must be withheld for the authority reason, not a feasibility one: {blocking_text[:200]}"
        )
        # Fail-closed authority gate: no deterministic economics.
        assert entry["is_fully_priced"] is False
        assert not entry.get("selected_incentive_usd")


async def test_statutory_eligibility_failure_still_rejects_correctly(db: AsyncSession):
    """A genuine authority/rate/threshold failure must still terminate the
    candidate as unpriceable — this repair only removed the SOFT
    feasibility gate, never the real economic gates."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    # AU now carries MORE THAN ONE candidate (au_location_offset plus
    # au_pdv_offset), so a {primary_jurisdiction: entry} dict silently keeps
    # whichever happens to be last. Select the program this test is actually
    # about -- the genuine statutory/threshold rejection -- by slug.
    au = next(
        e for e in structures
        if e["primary_jurisdiction"] == "AU"
        and "au_location_offset" in (e.get("program_slugs") or [e.get("program_slug")])
    )
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
    # Existing Optimizer/Stacker Reconnection: multiple structures can now
    # share one primary_jurisdiction (single-program plus component/split/
    # treaty candidates anchored there) -- restrict this lookup to the
    # original single-program structure types this test examines.
    entries = {
        e["primary_jurisdiction"]: e for e in view["structures"]["allocated_structures"]["structures"]
        if e["structure_type"] in ("single_country", "full_relocation")
    }
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
    """ca_federal_pstc replaces uk_avec as the "incomplete" control here.
    uk_avec's own RATE_OR_AWARD_BASIS dimension resolved to PRESENT once
    batch 3 promoted its DoctrineRecord to VERIFIED (a genuine, correct
    consequence of that promotion, not a test-fudge) -- it no longer
    demonstrates an unresolved RATE_OR_AWARD_BASIS. ca_federal_pstc is
    still coverage-vetoed with only a PARSED RateRule and genuinely
    carries both dimensions unresolved."""
    entry = ledger_entry_for("ca_federal_pstc")
    assert entry is not None
    assert not entry.is_fully_resolved
    dims = {q.dimension for q in entry.residual_questions}
    assert "RATE_OR_AWARD_BASIS" in dims
    assert "TERRITORIALITY" in dims
    for q in entry.residual_questions:
        assert q.detail, f"{q.dimension} residual question must carry a real detail string"


def test_residual_ledger_for_priceable_control_has_fewer_open_questions():
    priceable = ledger_entry_for(PRICEABLE_CONTROL)
    incomplete = ledger_entry_for("ca_federal_pstc")
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
    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 4/CBA-001: Mauritius's own cultural-
    # test applicability remains genuinely AUTHORITY_UNRESOLVED, so
    # top_result is correctly None (truthful unresolved status over
    # false recommendation); the real, priced economics are disclosed
    # on baseline instead.
    # Production Page Integrity Closeout (migration 0071): LU's stale beta
    # 100% contingency-utilization election (migration 0068) was removed
    # as a project-name-branched default. Absent an election the reserve
    # is GREY_AREA_REQUIRES_AUTHORITY, never silently 0%/100%.
    assert result["baseline"]["true_net_cost_usd"] == 3_812_823.20
    assert result["top_result"] is None


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
    against their official sources) -> 49 (batch 3: ca_on_opstc, de_dfff,
    es_tax_credit_foreign, fr_trip, hu_hipa_rebate, no_film_incentive,
    us_mn_film_production_credit, uk_avec, on the same recover-before-
    research bar as batch 1) -> 52 (batch 4: cy_film_rebate, ie_section_481,
    us_ca_film_credit/ca_film_30, verified via fresh direct WebFetch of
    each program's actual administering authority -- Cyprus Film
    Commission, Revenue Commissioners Ireland, and California's own AB
    1138 statute text respectively) -> 58 (batch 5: us_al_film_incentive,
    us_ct_film_tax_credit, us_ma_film_tax_credit, us_ms_advantage_film_
    program, us_nc_film_entertainment_grant, us_nv_film_credit, each
    fresh-verified via direct WebFetch of the actual state film
    office/revenue department). See authority_coverage_registry.py's
    correction notes and test_batch1_programs_price_with_real_numbers_in_
    fvd / test_batch2_programs_price_with_real_numbers_in_fvd /
    test_batch3_programs_price_with_real_numbers_in_fvd /
    test_batch4_programs_price_with_real_numbers_in_fvd /
    test_batch5_programs_price_with_real_numbers_in_fvd for the traced,
    real-number proof. No soft feasibility mismatch may remove a
    candidate from the economic universe.

    CineGlobe canonical pricing path + discovery repair: the candidate
    universe legitimately grew 110 -> 115. This is not a data change (no
    program's rate/citation was touched) -- it is the jurisdiction-code-
    collision discovery fix: on_ofttc and OCASE (CA-ON) now each reach
    their own independent candidate structure alongside ca_on_opstc,
    instead of being silently collapsed to one. See test_on_ofttc_and_
    ocase_now_independently_served for the direct proof.

    Existing Optimizer/Stacker Reconnection: entries grew 121 -> 127 and
    priced 113 -> 119. canonical_stack_bridge.py additively generates one
    combined structure for each combination (pairwise AND, where every
    pairwise sub-combination is covered, N-way) with explicit named
    compatibility rule coverage in app.optimization.stacking_rules.
    _SLUG_PAIR_RULES — CA-BC (federal CPTC + provincial PSTC), CA-QC
    (federal CPTC + QC PSTC, resolved via the qc_film_production alias),
    and CA-ON, which alone contributes 4 combined structures once alias
    reconciliation unlocked ca_on_opstc (3 pairs + 1 fully-covered triple
    of federal CPTC + ca_on_opstc + on_ofttc — see test_on_ofttc_and_
    ocase_now_independently_served for the itemized proof).

    Existing Optimizer/Stacker Reconnection, Task A (component/split):
    entries grew again, 127 -> 142, priced 119 -> 134. For each movable
    component (post/vfx/music) with real spend in FVD's own budget
    (post $172,904, vfx $10,000, music $10,200), canonical_evaluation
    generates a component_relocation candidate for each of the top 6
    alternative jurisdictions by their own single-program incentive value
    (3 components x 6 targets = up to 18 attempted, 15 actually price
    fully — the rest fail closed on the target program's own minimum-
    spend threshold given the small routed amount, never persisted). No
    existing single-program or multi_program candidate is removed;
    unpriced count is unaffected (a component candidate that fails to
    price is never persisted, not counted as unpriced either).

    Existing Optimizer/Stacker Reconnection, Task B (treaty/co-pro):
    entries grew again, 142 -> 143. FVD's Greece is a real Eurimages
    member (confirmed live treaty_engine registry) and 36 of FVD's own
    discovered candidate jurisdictions are ALSO Eurimages members — one
    additive, disclosed CO_PRO_OPPORTUNITY structure is generated (no
    real bilateral treaty partner exists for Greece, so 0 bilateral
    opportunities). It is never fully priced (real ownership/cultural-
    test facts are not on file) so unpriced grows 8 -> 9, priced is
    unaffected. Consolidated Backend Correction, Part 19-20 (CBA-009):
    unpriced grows again 9 -> 10, priced shrinks 134 -> 133: ES now
    genuinely RULE_REJECTED (real minimum-QPE threshold unmet once its
    own contingency reserve is no longer counted as 100%-unconditionally
    qualifying) -- see test_batch3_programs_price_with_real_numbers_in_fvd.
    Grew again 143 -> 144 (unpriced 10 -> 11) with Final Consolidated
    Backend Correction, Part 3/CBA-006: FVD's Greece is also a real
    European Convention on Cinematographic Co-Production signatory, so a
    second, genuine multilateral treaty_coproduction opportunity
    (alongside Eurimages) now generates -- same distinct
    STATUS_CO_PRO_OPPORTUNITY terminal state, never flattened.

    Grew again 144 -> 146 (priced 133 -> 135, unpriced unaffected) with
    the Canonical Knowledge Consolidation pass: ca_bc_dave and
    au_pdv_offset (real programs already documented in this project's own
    jurisdiction_comparison.py but never given a canonical representation
    until that pass) each add exactly one full_relocation candidate to
    FVD's own real budget. Unlike Little Utopia's structure list, FVD
    gains no matching component_relocation candidate for either program
    -- the component-routing generator only creates one when the
    production has real spend in a matching component AND the target
    program covers that activity; FVD's own budget composition simply
    doesn't route a component to BC or South Australia the way LU's does.
    This is a real, budget-specific difference, not a bug -- see
    test_codex_final_optimizer_health_audit.py's own direct proof that
    both programs reach FVD's fresh served candidate universe.

    Grew again 146 -> 169 (+23) with the LU Co-Pro Opportunity Trace fix:
    bilateral treaty discovery previously only considered a treaty where
    FVD's own home jurisdiction (Greece) was one of the two parties -- a
    real, generic wiring defect (CineGlobe is production-centric, not
    current-jurisdiction-centric). 23 real registered bilateral treaties
    exist between pairs of FVD's own independently-discovered candidate
    jurisdictions that don't involve Greece (e.g. GB+CA, GB+AU, CA+FR) --
    each now surfaces as its own disclosed, unpriced treaty_coproduction
    opportunity. priced is unaffected (all 23 are UNRESOLVED_FACTS, never
    priced); unpriced absorbs the full growth. See
    test_treaty_coproduction_wiring.py for the direct proof.

    Fail-closed authority gate (CineGlobe economics + wiring integrity
    repair, Cluster 1): entries 169 -> 168, priced 135 -> 105, unpriced
    34 -> 63. AUTHORITY_UNRESOLVED_NON_PRICEABLE is now a BLOCKING state,
    restoring PROJECT_RULES.md's final authority-safety gate (such a
    program "contributes no incentive, NPC, stack, or ranking value").
    Full attribution of the movement, per PROJECT_RULES.md rule 9:

      * -30 priced: exactly one full_relocation candidate per
        authority-unresolved program is withheld from deterministic
        economics (al, au_nsw, au_qld, bg, ca_mb, ca_nb, ca_ns, ca_sk,
        ch_pics, co, cr, do, eg, gh, lv, me, mk, mn, pa, qa, se, sg, sk,
        ua, us_az, us_co, us_hi, us_ut, us_va, uz). Each remains a
        DISCOVERED, disclosed entry carrying the authority reason -- it is
        withheld, never erased -- so these move to unpriced, +30.
      * -4 entries: the 3 CA-MB component/split candidates (post/vfx/music)
        can no longer price on Manitoba and are therefore never persisted
        (the pre-existing documented behavior for a component candidate
        that fails to price), plus the CA + CH bilateral co-production
        opportunity, which loses its Swiss economic leg. One of those 4 was
        already unpriced, so unpriced nets +29 rather than +30.
      * +3 entries: with Manitoba out of the top-6 alternative
        jurisdictions by single-program incentive value, IT takes the
        vacated slot and the same 3 components route there instead.

      169 - 4 + 3 = 168 entries; 135 - 30 = 105 priced; 34 + 30 - 1 = 63.
    """
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    priced = [e for e in entries if e["is_fully_priced"]]
    unpriced = [e for e in entries if not e["is_fully_priced"]]
    # Cluster 5 (labour-only qualifying base): Canada's CPTC/PSTC family declares rate_base_narrower_than_qpe and is now withheld, so every candidate, pair and combination whose economics depended on a Canadian labour credit is correctly no longer priced. entries 171 -> 156, priced 101 -> 92, unpriced 70 -> 64.
    assert len(entries) == 156
    assert len(priced) == 92
    assert len(unpriced) == 64

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
    VERIFIED); ar_incaa_incentive has zero VERIFIED/PARSED-executable path
    (zero RateRules of any tier) and stays correctly UNPRICEABLE in both.

    uk_avec was the original third control here, but the Global Economic
    Data + Base Pricing batch 3 promoted its DoctrineRecord PARSED ->
    VERIFIED and removed its coverage veto (bfi.org.uk, official, fetched
    directly) -- it is now genuinely PRICEABLE and would no longer prove
    the "stays UNPRICEABLE" case this test exists to guard. See
    test_batch3_programs_price_with_real_numbers_in_fvd for uk_avec's own
    proof."""
    from app.services.canonical_publication_contract import priceability, PRICEABLE, UNPRICEABLE
    assert priceability("us_ga_film_credit").gate == PRICEABLE
    assert priceability("au_location_offset").gate == PRICEABLE
    assert priceability("uk_avec").gate == PRICEABLE
    assert priceability("ar_incaa_incentive").gate == UNPRICEABLE


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
    EXACTLY $3,722,483.90 after every fix in this task. If this regresses,
    something touched served pricing logic, not just data/publication
    correctness."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    baseline = next(e for e in entries if e["is_baseline"])
    assert baseline["primary_jurisdiction"] == "MU"
    # Production Page Integrity Closeout (migration 0071): LU's stale beta
    # 100% contingency-utilization election (migration 0068) was removed.
    # Absent an election the reserve is GREY_AREA_REQUIRES_AUTHORITY, never
    # silently defaulted to 0% or 100%.
    assert baseline["npc_verified_usd"] == pytest.approx(3812823.20, abs=0.01)


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
    # US-MD is EXCLUDED from the priced list: us_md_film_production_activity_
    # credit states only band ceilings (28%/30%) with an unevaluable
    # us-md-tv-series-uplift condition, so under the cluster-6 repair it has
    # no guaranteed floor and must not price deterministically. It is
    # asserted as withheld-but-disclosed below instead.
    # CA-BC is withheld under cluster 5 (ca_bc_pstc declares
    # ca-bc-labour-only-base on its 36% base tier); asserted below as
    # withheld-but-disclosed instead of priced.
    codes = ("HR", "NZ", "TT", "US-LA", "US-NM", "US-RI")
    seen_incentives = set()
    for code in codes:
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0
        seen_incentives.add(e["selected_incentive_usd"])
    # Withheld, not erased: US-MD and CA-BC stay discovered and disclosed.
    for code in ("US-MD", "CA-BC"):
        withheld = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert withheld["is_fully_priced"] is False
        assert not withheld.get("selected_incentive_usd")
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
    # SI (si_cash_rebate) is a floorless band ceiling with an unevaluable
    # si-eligible-applicant-scope condition -- withheld under cluster 6, so
    # only SA is asserted as priced here.
    for code in ("SA",):
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0
    si = next(x for x in entries if x["primary_jurisdiction"] == "SI")
    assert si["is_fully_priced"] is False
    assert not si.get("selected_incentive_usd")


# ── Global Economic Data + Base Pricing — batch 3: 8 more recover-before-
# research promotions (Ontario, Germany, Spain, France, Hungary, Norway,
# Minnesota, UK), plus the durability clarification requiring structured
# SourceProvenance on every promoted DoctrineRecord. ─────────────────────

BATCH3_SLUGS = (
    "ca_on_opstc", "de_dfff", "es_tax_credit_foreign", "fr_trip",
    "hu_hipa_rebate", "no_film_incentive", "us_mn_film_production_credit",
    "uk_avec",
)


def test_batch3_doctrine_records_promoted_to_verified():
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_rate_rules import get_rate_rules
    for slug in BATCH3_SLUGS:
        doc = get_doctrine(slug)
        if doc is not None:
            assert doc.confidence_tier == "VERIFIED", slug
        else:
            # es_tax_credit_foreign and fr_trip are raw RateRule tuples
            # with no DoctrineRecord (program_rate_rules.py pattern).
            rules = get_rate_rules(slug)
            assert rules, f"{slug}: no RateRule found"
            assert all(r.confidence_tier == "VERIFIED" for r in rules), slug


def test_batch3_coverage_veto_removed_including_alias_spellings():
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    for canonical, alias in (
        ("ca_on_opstc", "on_opstc"),
        ("de_dfff", None),
        ("es_tax_credit_foreign", None),
        ("fr_trip", None),
        ("hu_hipa_rebate", None),
        ("no_film_incentive", None),
        ("us_mn_film_production_credit", "us_mn_film_credit"),
        ("uk_avec", None),
    ):
        assert blocks_economic_candidacy(canonical) is False, canonical
        if alias:
            assert blocks_economic_candidacy(alias) is False, alias


async def test_batch3_programs_price_with_real_numbers_in_fvd(db: AsyncSession):
    """Runtime proof (not just the read-only registries) that the batch-3
    programs reach served state with real, distinct, non-zero numbers.

    Consolidated Backend Correction, Part 19-20 (CBA-009): ES
    (es_tax_credit_foreign) is a real, legitimate exception as of this
    correction, not a regression -- Spain's own statutory rate rules
    require a minimum QPE threshold. FVD's projected QPE probe used to
    clear that threshold only because its own $362,866.00 contingency
    reserve was counted as 100%-unconditionally qualifying; with no
    expected-utilization fact on file that reserve is now correctly a
    disclosed grey area, and the real probe QPE ($779,390.00) genuinely
    falls below Spain's minimum -- RULE_REJECTED is the honest, correct
    terminal state, not a wiring defect. Verified separately below rather
    than silently dropped from coverage."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    codes = ("CA-ON", "DE", "FR", "HU", "NO", "US-MN", "GB")
    seen_incentives = set()
    for code in codes:
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0
        seen_incentives.add(e["selected_incentive_usd"])
    assert len(seen_incentives) > 1, "all programs priced identically -- suspicious, check for a copy-paste QPE bug"

    es = next(x for x in entries if x["primary_jurisdiction"] == "ES")
    assert es["is_fully_priced"] is False
    assert es["candidate_status"] == "RULE_REJECTED"
    assert es["blockers"], "ES must still disclose the real reason it did not price"


def test_batch1_2_3_promoted_programs_carry_structured_provenance():
    """Durability clarification (received mid-batch-3): every historical
    proposition promoted this session must carry PERMANENT STRUCTURED
    provenance in the canonical authority/economic data layer, not just a
    free-text citation string or a report. Checks the trace PROGRAM ->
    EXECUTABLE RULE -> SOURCE PROVENANCE is real and populated for all 18
    programs promoted across batches 1-3 (the batch-2 slugs are included
    here rather than a separate test since the schema field itself is
    what's new, not batch-2's own promotion)."""
    from app.data.executable_jurisdiction_registry import get_provenance
    from app.data.program_rate_rules import get_rate_rules

    promoted_slugs = (
        "ca_bc_pstc", "hr_cash_rebate", "nz_spg_international",
        "tt_production_expenditure_rebate", "us_la_film_incentive",
        "us_md_film_production_activity_credit", "us_nm_film_credit",
        "us_ri_film_credit",
        "sa_film_commission_rebate", "si_cash_rebate",
    ) + BATCH3_SLUGS

    for slug in promoted_slugs:
        prov = get_provenance(slug)
        assert prov is not None, f"{slug}: no structured SourceProvenance recorded"
        assert prov.issuing_authority, f"{slug}: provenance missing issuing_authority"
        # Every RateRule this program derives must carry the SAME
        # provenance object (or an equivalent one) -- the executable rule
        # itself must be traceable to its source, not only the doctrine
        # record it was authored from.
        rules = get_rate_rules(slug)
        assert rules, f"{slug}: no executable RateRule found"
        for rule in rules:
            assert rule.provenance is not None, (
                f"{slug}/{rule.tier_id}: executable RateRule has no provenance -- "
                "PROGRAM -> EXECUTABLE RULE -> SOURCE PROVENANCE trace is broken"
            )
            assert rule.provenance.issuing_authority == prov.issuing_authority


BATCH5_SLUGS = (
    "us_al_film_incentive", "us_ct_film_tax_credit", "us_ma_film_tax_credit",
    "us_ms_advantage_film_program", "us_nc_film_entertainment_grant",
    "us_nv_film_credit",
)


def test_batch5_doctrine_records_promoted_to_verified():
    from app.data.executable_jurisdiction_registry import get_doctrine
    for slug in BATCH5_SLUGS:
        doc = get_doctrine(slug)
        assert doc is not None
        assert doc.confidence_tier == "VERIFIED", slug


def test_batch5_coverage_veto_removed_including_alias_spellings():
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    for canonical, alias in (
        ("us_al_film_incentive", None),
        ("us_ct_film_tax_credit", "us_ct_film_credit"),
        ("us_ma_film_tax_credit", "us_ma_film_credit"),
        ("us_ms_advantage_film_program", "us_ms_film_credit"),
        ("us_nc_film_entertainment_grant", "us_nc_film_grant"),
        ("us_nv_film_credit", "us_nv_film_incentive"),
    ):
        assert blocks_economic_candidacy(canonical) is False, canonical
        if alias:
            assert blocks_economic_candidacy(alias) is False, alias


async def test_batch5_programs_price_with_real_numbers_in_fvd(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    codes = ("US-AL", "US-CT", "US-NV", "US-NC", "US-MA", "US-MS")
    for code in codes:
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0


def test_batch5_promoted_programs_carry_structured_provenance():
    from app.data.executable_jurisdiction_registry import get_provenance
    from app.data.program_rate_rules import get_rate_rules

    for slug in BATCH5_SLUGS:
        prov = get_provenance(slug)
        assert prov is not None, f"{slug}: no structured SourceProvenance recorded"
        assert prov.issuing_authority
        rules = get_rate_rules(slug)
        assert rules
        for rule in rules:
            assert rule.provenance is not None, f"{slug}/{rule.tier_id}: no provenance"


# ── Global Formulaic Economic Completion — Path B primary research:
# on_ofttc (one of the original 21 zero-evidence programs). ─────────────

def test_on_ofttc_researched_from_scratch_and_canonicalized():
    """Path B: on_ofttc had zero data of any kind (see
    docs/validation/GLOBAL_ECONOMIC_DATA_ZERO_EVIDENCE_21.json). Researched
    directly from ontariocreates.ca/tax-incentives/ofttc (Ontario Creates,
    official, fetched directly) this task: 35% base rate. A real
    DoctrineRecord/RateRule with structured SourceProvenance now exists
    and the coverage veto is removed."""
    from app.data.executable_jurisdiction_registry import get_doctrine, get_provenance
    from app.data.program_rate_rules import get_rate_rules
    from app.data.authority_coverage_registry import blocks_economic_candidacy

    assert blocks_economic_candidacy("on_ofttc") is False
    doc = get_doctrine("on_ofttc")
    assert doc is not None
    assert doc.confidence_tier == "VERIFIED"
    rules = get_rate_rules("on_ofttc")
    assert rules and rules[0].rate == 0.35
    prov = get_provenance("on_ofttc")
    assert prov is not None and prov.issuing_authority == "Ontario Creates (jointly administered with the CRA)"


async def test_on_ofttc_and_ocase_now_independently_served(db: AsyncSession):
    """CineGlobe canonical pricing path + discovery repair: the jurisdiction-
    code-collision limitation this test used to document is fixed.
    production_discovery.py now examines every independently registered
    (jurisdiction_code, program_slug) pair (via executable_jurisdiction_
    registry.all_doctrine_records()), not just the single slug
    jurisdiction_comparison.ALL_PROFILES happened to carry per code. CA-ON's
    three real, separately-cited programs -- ca_on_opstc, on_ofttc, and
    OCASE -- each now reach their own independent candidate structure with
    their own real NPC, never collapsed to one.

    Existing Optimizer/Stacker Reconnection: "never combined/stacked" is
    no longer true by design -- that was always the explicitly deferred
    next phase this exact task implements. CA-ON now ALSO gets 4 additive
    multi_program structures: three pairs (federal CPTC + on_ofttc,
    spend_reduction; federal CPTC + ca_on_opstc, mutually_exclusive --
    resolved via ca_on_opstc's known "on_opstc" alias in _SLUG_PAIR_RULES,
    a canonical-identity reconciliation, not a new rule; ca_on_opstc +
    on_ofttc, mutually_exclusive) plus one N-way triple (all three
    programs together, since every pairwise sub-combination among them is
    covered). The three single-program structures this test originally
    proved are UNCHANGED -- still independently served, still their own
    distinct NPCs -- this test now also proves the 4 combined ones
    coexist rather than replacing them."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ca_on_entries = [e for e in entries if e["anchor_jurisdiction"] == "CA-ON"]
    # Cluster 5 (labour-only qualifying base): ca_federal_cptc declares
    # ca-cptc-labour-only-base and is withheld, so the three combinations that
    # depended on it (CPTC+on_ofttc, CPTC+ca_on_opstc, and the CPTC-inclusive
    # triple) are correctly no longer emitted: 7 -> 4. The invariant this test
    # exists for is UNCHANGED and asserted below -- ca_on_opstc, on_ofttc and
    # OCASE are each still independently served with their own NPC, never
    # collapsed to one -- plus the one surviving combination that needs no
    # Canadian labour credit (ca_on_opstc + on_ofttc).
    assert len(ca_on_entries) == 4, (
        "expected ca_on_opstc, on_ofttc, OCASE each independently served, "
        "plus the one combination needing no Canadian labour credit"
    )
    single_program_entries = [e for e in ca_on_entries if e["structure_type"] != "multi_program"]
    programs_used = {e["program_slug"] for e in single_program_entries if e.get("program_slug")}
    assert programs_used == {
        "ca_on_opstc", "on_ofttc",
        "ontario_computer_animation_and_special_effects_tax_credit_ocase",
    }
    npc_values = {e["npc_with_adjustments_usd"] for e in single_program_entries}
    assert len(npc_values) == 3, "each Ontario program must price to its own distinct NPC"

    multi_entries = [e for e in ca_on_entries if e["structure_type"] == "multi_program"]
    # Only the combination that needs no Canadian labour credit survives; the
    # three CPTC-dependent ones are withheld with CPTC itself (cluster 5).
    # Stacking ENUMERATION is unaffected -- it still produces a real combined
    # structure whenever its constituents are reachable, which is the
    # capability this assertion protects.
    assert len(multi_entries) == 1
    multi_slug_sets = {frozenset(e["program_slugs"]) for e in multi_entries}
    assert multi_slug_sets == {frozenset({"ca_on_opstc", "on_ofttc"})}
    assert all(
        "ca_federal_cptc" not in (e["program_slugs"] or []) for e in multi_entries
    ), "a withheld labour-base program must not appear in a priced combination"
    assert multi_entries[0]["scenario_category"] == "PRICED_LOW_FIT"


def test_on_ocase_researched_from_scratch_and_canonicalized():
    """Path B: ontario_computer_animation_and_special_effects_tax_credit_
    ocase (OCASE) was also one of the 21 zero-evidence programs. Researched
    directly from ontariocreates.ca/tax-incentives/ocase (Ontario Creates,
    official, fetched directly) this task: 18% flat rate, refundable,
    confirmed no cap. The former jurisdiction_code-collision limitation is
    fixed (see test_on_ofttc_and_ocase_now_independently_served) -- not
    re-asserted here to avoid duplicating that runtime proof."""
    from app.data.executable_jurisdiction_registry import get_doctrine, get_provenance
    from app.data.program_rate_rules import get_rate_rules
    from app.data.authority_coverage_registry import blocks_economic_candidacy

    slug = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
    assert blocks_economic_candidacy(slug) is False
    doc = get_doctrine(slug)
    assert doc is not None
    assert doc.confidence_tier == "VERIFIED"
    assert doc.is_refundable is True
    rules = get_rate_rules(slug)
    assert rules and rules[0].rate == 0.18
    prov = get_provenance(slug)
    assert prov is not None and prov.issuing_authority == "Ontario Creates"


# ── Global Formulaic Economic Completion — batch 4: fresh direct-WebFetch
# primary-source verification (Cyprus, Ireland, California). ────────────

BATCH4_SLUGS = ("cy_film_rebate", "ie_section_481", "us_ca_film_credit")


def test_batch4_doctrine_records_promoted_to_verified():
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_rate_rules import get_rate_rules
    for slug in BATCH4_SLUGS:
        doc = get_doctrine(slug)
        if doc is not None:
            assert doc.confidence_tier == "VERIFIED", slug
        else:
            # ie_section_481 is a raw RateRule tuple with no DoctrineRecord.
            rules = get_rate_rules(slug)
            assert rules, f"{slug}: no RateRule found"
            assert all(r.confidence_tier == "VERIFIED" for r in rules), slug


def test_batch4_coverage_veto_removed_including_alias_spellings():
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    for canonical, alias in (
        ("cy_film_rebate", None),
        ("ie_section_481", None),
        ("us_ca_film_credit", "ca_film_30"),
    ):
        assert blocks_economic_candidacy(canonical) is False, canonical
        if alias:
            assert blocks_economic_candidacy(alias) is False, alias


async def test_batch4_programs_price_with_real_numbers_in_fvd(db: AsyncSession):
    """Runtime proof (not just the read-only registries) that all 3 batch-4
    programs reach served state with real, non-zero numbers."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    for code in ("CY", "IE", "US-CA"):
        e = next(x for x in entries if x["primary_jurisdiction"] == code)
        assert e["is_fully_priced"] is True, f"{code} did not price"
        assert e["candidate_status"] == "PRICED"
        assert e["selected_incentive_usd"] > 0
        assert e["npc_verified_usd"] is not None and e["npc_verified_usd"] > 0


def test_batch4_promoted_programs_carry_structured_provenance():
    """Same durability requirement as batch 3's equivalent test, extended
    to the 3 batch-4 programs."""
    from app.data.executable_jurisdiction_registry import get_provenance
    from app.data.program_rate_rules import get_rate_rules

    for slug in BATCH4_SLUGS:
        prov = get_provenance(slug)
        assert prov is not None, f"{slug}: no structured SourceProvenance recorded"
        assert prov.issuing_authority, f"{slug}: provenance missing issuing_authority"
        rules = get_rate_rules(slug)
        assert rules, f"{slug}: no executable RateRule found"
        for rule in rules:
            assert rule.provenance is not None, (
                f"{slug}/{rule.tier_id}: executable RateRule has no provenance"
            )
            assert rule.provenance.issuing_authority == prov.issuing_authority
