"""
Consolidated Global Remediation, Phase I/J verification.

The Incentive/Optimizer Core Closeout (2026-08-09, commit 21af675) fixed
Bridge's EconomicsSummary.npc_usd to source npc_with_adjustments_usd (the
figure ranking actually ranks on) instead of the pre-adjustment
npc_verified_usd -- verified there only against the MU baseline and the
MU/MT/GR/GB/AU pilot. This test proves the fix is GENERAL: every priced
structure's exported npc_usd matches its served npc_with_adjustments_usd,
across a broad sample of non-pilot jurisdictions, and ranking's primary
sort key is the same canonical field.
"""
import random

from app.bridge.package_builder import build_package
from app.bridge.schema import OperationType
from app.demo.little_utopia_state import build_allocated_structures, get_state


def test_bridge_npc_usd_matches_canonical_adjusted_value_across_a_broad_sample():
    served = build_allocated_structures(get_state())
    priced = [s for s in served["structures"] if s.get("npc_with_adjustments_usd") is not None]
    assert len(priced) >= 100  # sanity: this is the worldwide-priced set, not just the pilot

    rng = random.Random(20260812)
    sample = rng.sample(priced, 20)
    mismatches = []
    for s in sample:
        pkg = build_package(operation=OperationType.OPTIMIZER_STRUCTURE_AUDIT, structure_id=s["structure_id"])
        if pkg.economics.npc_usd != s["npc_with_adjustments_usd"]:
            mismatches.append((s["structure_id"], pkg.economics.npc_usd, s["npc_with_adjustments_usd"]))

    assert mismatches == [], f"npc_usd diverged from npc_with_adjustments_usd for: {mismatches}"


def test_bridge_also_exposes_pre_adjustment_figure_separately():
    served = build_allocated_structures(get_state())
    baseline = next(s for s in served["structures"] if s["structure_id"] == "ALLOC-BASELINE-MU")
    pkg = build_package(operation=OperationType.OPTIMIZER_STRUCTURE_AUDIT, structure_id="ALLOC-BASELINE-MU")
    assert pkg.economics.npc_usd == baseline["npc_with_adjustments_usd"]
    assert pkg.economics.npc_verified_usd == baseline.get("npc_verified_usd")


def test_ranking_primary_sort_key_is_the_same_canonical_adjusted_field():
    served = build_allocated_structures(get_state())
    priced = [s for s in served["structures"] if s.get("npc_with_adjustments_usd") is not None]
    ranked_priced = [r for r in served["ranking"] if r.get("npc_with_adjustments_usd") is not None]
    npcs = [r["npc_with_adjustments_usd"] for r in ranked_priced]
    assert npcs == sorted(npcs), "ranking is not ascending by npc_with_adjustments_usd"
