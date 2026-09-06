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
    _check_participants_invariant,
    _check_program_onboarding_invariant,
    _check_treaty_allocation_invariant,
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


# ── PARTICIPANTS negative tests ──────────────────────────────────────────

def test_participants_gate_passes_on_correct_input():
    failures = _check_participants_invariant(_base_component_structure(), "label")
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
    conformance = {"some_program": "NONCONFORMANT"}
    failures = _check_program_onboarding_invariant(
        {"conditional_scenario": None}, "label", ["some_program"], conformance,
    )
    assert any("classified NONCONFORMANT" in f for f in failures), failures


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
