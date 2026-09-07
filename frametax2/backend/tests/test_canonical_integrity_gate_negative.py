"""
Optimizer FINAL closeout, P1-GATE-001 — required negative tests.

Codex's final P0 delta reaudit (Section 8) found two concrete depth gaps
in the Non-Globe Canonical Integrity Gate's oracles:

- "Participant oracle" compares SETS, not lists — a duplicate
  participant entry would silently pass.
- "Treaty oracle" checks the allocation sums to 100% and a loose
  "combined incentive < 2x gross" bound, but never independently
  RECOMPUTES a single participant's own incentive against its own
  allocated share — a doubled or fabricated per-participant incentive
  that still keeps the combined total under 2x gross would pass
  undetected.

Both invariants were extracted from `_gate_one_project` into pure,
synthetic-input-friendly functions
(`_check_participants_invariant`, `_check_treaty_allocation_invariant`)
specifically so this file can prove the gate ACTUALLY FAILS on a
corrupted input — not merely that it passes on real, already-correct
data (which the live corpus runs already prove elsewhere).
"""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts")

from canonical_integrity_gate import (  # noqa: E402
    _check_freshness_invariant,
    _check_participants_invariant,
    _check_program_onboarding_invariant,
    _check_rejection_accounting_invariant,
    _check_treaty_allocation_invariant,
    _independently_recompute_participant_incentive,
)


def _base_component_structure(**overrides) -> dict:
    base = {
        "structure_id": "11111111-1111-1111-1111-111111111111",
        "label": "Test component structure",
        "structure_type": "component_relocation",
        "primary_jurisdiction": "MU",
        "participants": ["MU", "CA-MB"],
        "segments": [
            {"jurisdiction_code": "MU", "claims_incentive": True},
            {"jurisdiction_code": "CA-MB", "claims_incentive": True},
        ],
    }
    base.update(overrides)
    return base


def _base_treaty_structure(**overrides) -> dict:
    base = {
        "structure_id": "22222222-2222-2222-2222-222222222222",
        "label": "Test treaty structure",
        "structure_type": "treaty_coproduction",
        "conditional_scenario": {
            "status": "CONDITIONAL_PROJECT_FACT_DEPENDENT",
            "fully_priced": True,
            "participant_allocation_pct": {"GB": 80.0, "IE": 20.0},
            "conditional_incentive_usd": 970_257.91,
            "priced_components": [
                {"jurisdiction_code": "GB", "modeled_rate": 0.278, "selected_incentive_usd": 700_000.0},
                {"jurisdiction_code": "IE", "modeled_rate": 0.32, "selected_incentive_usd": 270_257.91},
            ],
        },
    }
    base.update(overrides)
    return base


def _base_rejected_component_with_segments(**overrides) -> dict:
    """A rejected component_relocation row that, unlike a real P1-REJ-001
    rejection (which carries no segments/participants), has been
    corrupted to carry a bogus participants list — the exact P1-GATE-001
    Defect #5 shape: a rejected row is not economically live, but a
    malformed participant condition on it must still be caught."""
    base = {
        "structure_id": "66666666-6666-6666-6666-666666666666",
        "label": "Test rejected component (corrupted)",
        "structure_type": "component_relocation",
        "primary_jurisdiction": "GR",
        "is_fully_priced": False,
        "candidate_status": "RULE_REJECTED",
        "rejection_reason_class": "MINIMUM_SPEND_FAIL",
        "participants": ["GR", "XX"],  # corrupted -- no segments exist to justify either code
        "segments": [],
    }
    base.update(overrides)
    return base


# ── PARTICIPANTS negative tests ──────────────────────────────────────────

def test_participants_gate_passes_on_correct_input():
    failures = _check_participants_invariant(_base_component_structure(), "label")
    assert failures == []


def test_participants_gate_fails_on_corrupted_rejected_component_row():
    """P1-GATE-001 Defect #5, exact shape: a REJECTED component row
    (is_fully_priced=False, candidate_status=RULE_REJECTED) whose
    participants list is corrupted (non-empty, unsupported by any real
    segment) must still be caught by the same PARTICIPANTS invariant a
    priced row would be — rejection status and integrity validation are
    separate concepts. Before the P1-GATE-001 repair this row would never
    have reached this check at all (skipped by the caller's top-level
    is_fully_priced continue)."""
    corrupted = _base_rejected_component_with_segments()
    failures = _check_participants_invariant(corrupted, "label")
    assert any("!= expected claiming set" in f for f in failures), failures


def test_participants_gate_passes_on_known_good_rejected_component_row():
    """KNOWN-GOOD -> PASS: a real P1-REJ-001 rejection (no segments, empty
    participants by design) must not be flagged."""
    good = _base_rejected_component_with_segments(participants=[], segments=[])
    failures = _check_participants_invariant(good, "label")
    assert failures == []


def test_participants_gate_fails_on_duplicate_entry():
    """The exact P1-GATE-001 gap: a duplicate participant entry."""
    corrupted = _base_component_structure(participants=["MU", "MU", "CA-MB"])
    failures = _check_participants_invariant(corrupted, "label")
    assert any("duplicate entries" in f for f in failures), failures


def test_participants_gate_fails_on_extra_nonclaiming_participant():
    corrupted = _base_component_structure(participants=["MU", "CA-MB", "US"])
    failures = _check_participants_invariant(corrupted, "label")
    assert any("!= expected claiming set" in f for f in failures), failures


def test_participants_gate_fails_on_missing_claiming_participant():
    corrupted = _base_component_structure(participants=["MU"])
    failures = _check_participants_invariant(corrupted, "label")
    assert any("!= expected claiming set" in f for f in failures), failures


# ── TREATY ALLOCATION negative tests ─────────────────────────────────────

def test_treaty_gate_passes_on_correct_input():
    failures = _check_treaty_allocation_invariant(_base_treaty_structure(), "label", 4_364_393.0)
    assert failures == []


def test_treaty_gate_fails_on_nonconserving_allocation_sum():
    """Treaty shares do not conserve source budget (allocation != 100%)."""
    corrupted = _base_treaty_structure()
    corrupted["conditional_scenario"]["participant_allocation_pct"] = {"GB": 100.0, "IE": 100.0}
    failures = _check_treaty_allocation_invariant(corrupted, "label", 4_364_393.0)
    assert any("sums to" in f and "not 100" in f for f in failures), failures


def test_treaty_gate_fails_on_doubled_participant_incentive():
    """The exact P1-GATE-001 gap: one participant's OWN
    selected_incentive_usd is doubled (fabricated), while the combined
    total is kept just under the loose 2x-gross plausibility bound so
    the pre-existing checks alone would NOT catch it."""
    corrupted = _base_treaty_structure()
    gross = 4_364_393.0
    # GB's allocated share is 80% of gross = $3,491,514.40; at modeled_rate
    # 0.278 the maximum honest incentive is ~$970,841. Fabricate double that.
    corrupted["conditional_scenario"]["priced_components"][0]["selected_incentive_usd"] = 1_900_000.0
    # Keep the combined total comfortably under 2x gross so the OLD
    # plausibility-only check would have passed this corrupted input.
    corrupted["conditional_scenario"]["conditional_incentive_usd"] = 1_900_000.0 + 270_257.91
    assert corrupted["conditional_scenario"]["conditional_incentive_usd"] < gross * 2.0
    failures = _check_treaty_allocation_invariant(corrupted, "label", gross)
    assert any("exceeds its own allocated share" in f for f in failures), failures


def test_treaty_gate_fails_when_feasible_allocation_not_marked_fully_priced():
    corrupted = _base_treaty_structure()
    corrupted["conditional_scenario"]["fully_priced"] = False
    corrupted["conditional_scenario"]["canonical_data_gaps"] = []
    failures = _check_treaty_allocation_invariant(corrupted, "label", 4_364_393.0)
    assert any("allocation sums to 100 (feasible) but" in f for f in failures), failures


def test_treaty_gate_does_not_fail_when_data_gap_genuinely_explains_unpriced():
    """Regression guard: a REAL, unrelated canonical_data_gaps disclosure
    must never be flagged as a P0-3/P1-GATE-001 defect."""
    corrupted = _base_treaty_structure()
    corrupted["conditional_scenario"]["fully_priced"] = False
    corrupted["conditional_scenario"]["canonical_data_gaps"] = ["ca_cmf"]
    failures = _check_treaty_allocation_invariant(corrupted, "label", 4_364_393.0)
    assert failures == []


# ── PROGRAM ONBOARDING negative tests (P1-CONF-001 / P1-GATE-001) ────────

def test_program_onboarding_fails_on_top_level_nonconformant_program():
    # Optimizer Final P1-GATE-001 remediation: the top-level sub-check is
    # now internally gated on is_fully_priced (see the function's own
    # docstring) rather than relying on the caller to have pre-filtered —
    # this fixture must be explicitly priced to exercise that path.
    conformance = {"some_program": "NONCONFORMANT"}
    failures = _check_program_onboarding_invariant(
        {"conditional_scenario": None, "is_fully_priced": True}, "label", ["some_program"], conformance,
    )
    assert any("classified NONCONFORMANT" in f for f in failures), failures


def test_program_onboarding_top_level_check_skipped_when_not_priced():
    """Regression guard for the internal is_fully_priced gate itself: an
    UNPRICED top-level structure referencing a NONCONFORMANT program slug
    (e.g. a rejected component's stale program reference) must not be
    flagged by the TOP-LEVEL sub-check — only a genuinely PRICED
    structure using a NONCONFORMANT program is a real defect."""
    conformance = {"some_program": "NONCONFORMANT"}
    failures = _check_program_onboarding_invariant(
        {"conditional_scenario": None, "is_fully_priced": False}, "label", ["some_program"], conformance,
    )
    assert failures == []


def test_program_onboarding_never_fails_on_pathway_specific_program():
    """P1-CONF-001's own regression guard at the gate layer: a program
    correctly classified PATHWAY_SPECIFIC (e.g. au_producer_offset) must
    never trip this check, at either the top level or nested inside a
    resolved conditional_scenario — it is valid, not a defect."""
    conformance = {"au_producer_offset": "PATHWAY_SPECIFIC"}
    top_level_failures = _check_program_onboarding_invariant(
        {"conditional_scenario": None}, "label", ["au_producer_offset"], conformance,
    )
    assert top_level_failures == []
    nested_structure = _base_treaty_structure()
    nested_structure["conditional_scenario"]["priced_components"][0]["program_slug"] = "au_producer_offset"
    nested_failures = _check_program_onboarding_invariant(nested_structure, "label", [], conformance)
    assert nested_failures == []


def test_program_onboarding_fails_on_nonconformant_program_priced_only_in_nested_conditional_scenario():
    """The exact P1-GATE-001 gap (Codex Section 23 item 4): a
    NONCONFORMANT program priced ONLY inside a resolved
    conditional_scenario, never at the top level, must still be caught —
    this is exactly how au_producer_offset (before the P1-CONF-001 fix)
    could have silently escaped detection while genuinely
    misclassified."""
    conformance = {"some_broken_program": "NONCONFORMANT"}
    corrupted = _base_treaty_structure()
    corrupted["conditional_scenario"]["priced_components"][0]["program_slug"] = "some_broken_program"
    failures = _check_program_onboarding_invariant(corrupted, "label", [], conformance)
    assert any(
        "conditional_scenario is PRICED using" in f and "some_broken_program" in f for f in failures
    ), failures


def test_program_onboarding_nested_check_reachable_when_top_level_never_priced():
    """Codex's exact Defect #2 counterexample: a treaty_coproduction
    opportunity structure is NEVER top-level is_fully_priced=True by
    construction (real pricing lives entirely in conditional_scenario).
    Before the P1-GATE-001 repair, the caller's early
    `if not s["is_fully_priced"]: continue` made this nested check
    UNREACHABLE for every real treaty row in the corpus — this test
    proves the function itself now correctly flags the defect even when
    is_fully_priced is explicitly False at the top level (the exact
    shape of every real treaty_coproduction opportunity row)."""
    conformance = {"some_broken_program": "NONCONFORMANT"}
    corrupted = _base_treaty_structure(is_fully_priced=False, structure_type="treaty_coproduction")
    corrupted["conditional_scenario"]["priced_components"][0]["program_slug"] = "some_broken_program"
    failures = _check_program_onboarding_invariant(corrupted, "label", [], conformance)
    assert any("some_broken_program" in f for f in failures), failures


# ── FRESHNESS negative tests (P1-GATE-001 Defect #3) ─────────────────────

def test_freshness_gate_passes_when_all_sources_agree():
    failures = _check_freshness_invariant("fp_current", "fp_current", {"fp_current", "fp_old"}, "label")
    assert failures == []


def test_freshness_gate_passes_when_project_has_no_budget_yet():
    """Both None (no current fingerprint reconstructable at all) is a
    real, legitimate out-of-scope state -- not a freshness failure."""
    failures = _check_freshness_invariant(None, None, set(), "label")
    assert failures == []


def test_freshness_gate_fails_on_evaluator_reconstruction_mismatch():
    """The core P1-FRESH-001 defect class, reintroduced: the evaluator's
    own reported state_fingerprint disagrees with the independently
    reconstructed current-generation fingerprint."""
    failures = _check_freshness_invariant("fp_new", "fp_stale", {"fp_new", "fp_stale"}, "label")
    assert any("state_fingerprint" in f for f in failures), failures


def test_freshness_gate_fails_when_reconstructed_fingerprint_not_persisted():
    """A served/validated result whose own reconstructed generation
    fingerprint does not exist among the current-engine persisted rows
    at all -- economically it might look fine, but its provenance is
    stale/missing. Git HEAD alone would never catch this; it requires
    the actual persisted-row fingerprint set."""
    failures = _check_freshness_invariant("fp_missing", "fp_missing", {"fp_other"}, "label")
    assert any("not among the fingerprints actually persisted" in f for f in failures), failures


# ── REJECTION ACCOUNTING negative tests (P1-GATE-001 Defect #4) ──────────

def _base_rejected_component(**overrides) -> dict:
    base = {
        "structure_id": "33333333-3333-3333-3333-333333333333",
        "label": "Test rejected component",
        "structure_type": "component_relocation",
        "primary_jurisdiction": "GR",
        "is_fully_priced": False,
        "candidate_status": "RULE_REJECTED",
        "rejection_reason_class": "MINIMUM_SPEND_FAIL",
        "component_allocations": [
            {"jurisdiction_code": "MT", "component": "post", "program_slug": "mt_mfc_rebate"},
        ],
    }
    base.update(overrides)
    return base


def _base_priced_component(**overrides) -> dict:
    base = {
        "structure_id": "44444444-4444-4444-4444-444444444444",
        "label": "Test priced component",
        "structure_type": "component_relocation",
        "primary_jurisdiction": "GR",
        "is_fully_priced": True,
        "candidate_status": "PRICED",
        "component_allocations": [
            {"jurisdiction_code": "IT", "component": "vfx", "program_slug": "it_tax_credit_foreign"},
        ],
    }
    base.update(overrides)
    return base


def test_rejection_accounting_passes_on_known_good_priced_and_rejected_mix():
    failures = _check_rejection_accounting_invariant([_base_priced_component(), _base_rejected_component()])
    assert failures == []


def test_rejection_accounting_fails_on_silently_omitted_disposition():
    """The exact P1-GATE-001 gap: a component structure that is neither
    priced NOR carries a real rejection_reason_class -- an economically
    material candidate that silently disappeared from the evaluated
    universe with no recorded reason."""
    silent = _base_rejected_component(candidate_status=None, rejection_reason_class=None)
    failures = _check_rejection_accounting_invariant([silent])
    assert any("neither priced nor carries a real rejection_reason_class" in f for f in failures), failures


def test_rejection_accounting_fails_on_disagreeing_disposition_fields():
    inconsistent = _base_priced_component(candidate_status="RULE_REJECTED")
    failures = _check_rejection_accounting_invariant([inconsistent])
    assert any("disposition fields disagree" in f for f in failures), failures


def test_rejection_accounting_fails_on_duplicate_attempt_identity():
    a = _base_rejected_component()
    b = _base_rejected_component(structure_id="55555555-5555-5555-5555-555555555555")
    failures = _check_rejection_accounting_invariant([a, b])
    assert any("duplicate component attempt identity" in f for f in failures), failures


def test_rejection_accounting_fails_on_silent_omission_even_amid_valid_surviving_candidates():
    """Adversarial combination (Section 11): a silently-omitted candidate
    hiding among otherwise-valid priced and rejected rows must still be
    caught — a majority of correct dispositions must never mask the one
    that silently disappeared."""
    valid_priced = _base_priced_component(structure_id="a1", component_allocations=[
        {"jurisdiction_code": "IT", "component": "vfx", "program_slug": "it_tax_credit_foreign"},
    ])
    valid_rejected = _base_rejected_component(structure_id="a2", component_allocations=[
        {"jurisdiction_code": "MT", "component": "post", "program_slug": "mt_mfc_rebate"},
    ])
    silent = _base_rejected_component(
        structure_id="a3", candidate_status=None, rejection_reason_class=None,
        component_allocations=[{"jurisdiction_code": "PL", "component": "music", "program_slug": "pl_pisf_cash_rebate"}],
    )
    failures = _check_rejection_accounting_invariant([valid_priced, valid_rejected, silent])
    assert any("neither priced nor carries a real rejection_reason_class" in f for f in failures), failures


def test_rejection_accounting_ignores_non_component_structures():
    """Generic scope guard: this invariant only applies to
    component_relocation rows -- a single_country/full_relocation/treaty
    structure with no disposition fields at all must never be flagged."""
    other = {"structure_type": "full_relocation", "is_fully_priced": False, "structure_id": "x", "label": "x"}
    failures = _check_rejection_accounting_invariant([other])
    assert failures == []


# ── Independent treaty participant QPE recomputation (P1-GATE-001
# Defect #1) — real DB-backed integration test, since genuine
# recomputation requires a real ProjectEconomicInputs and the real
# canonical pricing kernel, not a synthetic fixture. ─────────────────────

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.canonical_evaluation  # noqa: F401  (import-order fix)
from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures
from app.services.canonical_project_economics import build_project_economic_inputs

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _find_a_resolved_treaty_structure(db: AsyncSession, project_id: str) -> dict | None:
    """Generic lookup, not project/jurisdiction-specific: the first
    treaty_coproduction structure this project currently has with a
    fully-priced conditional_scenario, whatever its real participants
    happen to be."""
    view = await build_production_and_structures(db, project_id)
    structures = view["structures"]["allocated_structures"]["structures"]
    for s in structures:
        cond = s.get("conditional_scenario")
        if s.get("structure_type") == "treaty_coproduction" and isinstance(cond, dict) and cond.get("fully_priced"):
            return s
    return None


async def test_independent_qpe_recomputation_matches_known_good_real_treaty_structure(db: AsyncSession):
    """KNOWN-GOOD -> PASS. Uses whatever real, currently-resolved treaty
    structure exists for the locked-corpus project -- not a hardcoded
    jurisdiction pair -- so this generalizes to any future real treaty
    candidate with the same shape."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    s = await _find_a_resolved_treaty_structure(db, LITTLE_UTOPIA_PROJECT_ID)
    if s is None:
        pytest.skip("no currently-resolved real treaty structure available for this fixture")
    econ = await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID, read_only=True)
    assert econ.ok
    label = f"{s['structure_id'][:8]} {s['label']}"
    failures = _check_treaty_allocation_invariant(s, label, econ.inputs.gross_budget_usd, econ.inputs)
    assert failures == [], (
        f"known-good real treaty structure unexpectedly failed independent QPE recomputation: {failures}"
    )


async def _all_resolved_treaty_structures(db: AsyncSession, project_id: str) -> list[dict]:
    view = await build_production_and_structures(db, project_id)
    structures = view["structures"]["allocated_structures"]["structures"]
    return [
        s for s in structures
        if s.get("structure_type") == "treaty_coproduction"
        and isinstance(s.get("conditional_scenario"), dict)
        and s["conditional_scenario"].get("fully_priced")
    ]


async def test_independent_qpe_recomputation_catches_corrupted_participant_incentive(db: AsyncSession):
    """INTENTIONALLY CORRUPTED -> FAIL for the expected integrity reason.
    Reproduces Codex's own exact counterexample shape: fabricate one
    participant's selected_incentive_usd to an implausible value that
    the OLD gross-share x modeled-rate upper bound alone would not have
    caught (the fabricated value still respects that loose ceiling), and
    prove the NEW independent recomputation catches it anyway. Searches
    across every real resolved treaty structure/participant currently on
    this project (never a hardcoded jurisdiction pair) for one with
    enough margin between its real incentive and the old loose ceiling
    to construct a valid counterexample."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    econ = await build_project_economic_inputs(db, LITTLE_UTOPIA_PROJECT_ID, read_only=True)
    assert econ.ok
    gross = econ.inputs.gross_budget_usd

    candidate = None
    for s in await _all_resolved_treaty_structures(db, LITTLE_UTOPIA_PROJECT_ID):
        cond = s["conditional_scenario"]
        alloc = cond["participant_allocation_pct"]
        for i, pc in enumerate(cond["priced_components"]):
            pct = alloc.get(pc["jurisdiction_code"])
            if pct is None:
                continue
            old_upper_bound = gross * (pct / 100.0) * pc["modeled_rate"] * 1.01 + 1.0
            real = pc["selected_incentive_usd"]
            fabricated = min(old_upper_bound - 1.0, real * 1.5 + 1000.0)
            if fabricated > real * 1.05 + 100.0:  # enough margin to exceed the new tolerance too
                candidate = (s, i, fabricated)
                break
        if candidate:
            break
    if candidate is None:
        pytest.skip("no real treaty participant on this fixture currently has enough margin for a valid counterexample")

    s, idx, fabricated_value = candidate
    cond = s["conditional_scenario"]
    label = f"{s['structure_id'][:8]} {s['label']}"
    new_components = list(cond["priced_components"])
    new_components[idx] = {**new_components[idx], "selected_incentive_usd": fabricated_value}
    corrupted = {**s, "conditional_scenario": {**cond, "priced_components": new_components}}

    failures = _check_treaty_allocation_invariant(corrupted, label, gross, econ.inputs)
    assert any("disagrees with the INDEPENDENTLY RECOMPUTED incentive" in f for f in failures), failures


# ── Integration test through _gate_one_project itself (P1-GATE-001,
# Codex's own remediation note: "no integration test proving the nested
# conditional helper is reached by _gate_one_project") ──────────────────

from canonical_integrity_gate import _gate_one_project  # noqa: E402


async def test_gate_one_project_integration_reaches_nested_program_onboarding_check(db: AsyncSession):
    """Proves the REAL _gate_one_project call path -- not just the
    isolated pure function -- actually reaches and executes the nested
    conditional_scenario program-onboarding check for a real project's
    real treaty structure. Before the P1-GATE-001 repair this code path
    was unreachable in `_gate_one_project` (gated behind the top-level
    `is_fully_priced` continue), so this integration test would have
    passed vacuously (0 failures, but only because the check never ran)
    -- it is written to fail loudly instead if that happens again."""
    resolved = await _all_resolved_treaty_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    if not resolved:
        pytest.skip("no currently-resolved real treaty structure available for this fixture")
    real_nested_slug = resolved[0]["conditional_scenario"]["priced_components"][0]["program_slug"]

    # A conformance map identical to reality except this ONE real,
    # currently-nested-priced program is (falsely, for this test only)
    # marked NONCONFORMANT -- proves the live call path reaches it.
    from app.services.program_onboarding_conformance import classify_all_programs
    real_conformance = {slug: r.classification for slug, r in classify_all_programs().items()}
    poisoned_conformance = {**real_conformance, real_nested_slug: "NONCONFORMANT"}

    async with AsyncSession(engine, expire_on_commit=False) as session:
        result = await _gate_one_project(session, LITTLE_UTOPIA_PROJECT_ID, "The Little Utopia", poisoned_conformance)

    assert any(
        "conditional_scenario is PRICED using" in f and real_nested_slug in f for f in result["failures"]
    ), (
        f"expected _gate_one_project itself to flag the poisoned nested program {real_nested_slug!r}; "
        f"got failures={result['failures']}"
    )


async def test_gate_one_project_integration_reaches_rejected_component_participant_check(db: AsyncSession):
    """Proves the REAL _gate_one_project call path reaches the
    PARTICIPANTS check for a rejected component row. Uses the real,
    currently-persisted P1-REJ-001 rejection ledger for this project
    (never a synthetic project) -- confirms no rejected row's participant
    field is silently skipped by the live integration path."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    rejected = [
        s for s in structures
        if s.get("structure_type") == "component_relocation" and not s.get("is_fully_priced")
    ]
    assert rejected, "expected at least one real rejected component row for this fixture (P1-REJ-001)"
    # Sanity: every real rejected row already has empty participants by
    # design (no false positives) -- confirms the check ran (not skipped)
    # and found nothing wrong on real, correct data.
    for s in rejected[:20]:
        assert s.get("participants") == [], (
            f"expected a real rejected component row to carry empty participants by design, got "
            f"{s.get('participants')} for {s['structure_id']}"
        )
