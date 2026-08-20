"""
Little Utopia Worldwide Runtime Acceptance — regression protection.

Locks in the three VERIFIED defects this acceptance run found and fixed, all
of the same root cause: a HEADLINE MAXIMUM encoded as a guaranteed flat rate.

  AC-1 (P0) Japan  — jp_vipo_location_incentive priced a flat guaranteed 50%
                     while its own citation says "up to 50%" and the canonical
                     corpus classifies Japan's location support as a COMPETITIVE
                     half-subsidy capped at JPY1.5bn. It ranked #2.
  AC-2 (P0) Kazakhstan — kz_investment_subsidy priced a flat 30% sourced to a
                     single uncorroborated secondary source, while the canonical
                     adjudication for Kazakhstan is authority-insufficient.
  AC-3 (P1) Thailand — th_boi_incentive priced a flat 30% (the canonical
                     MAXIMUM) instead of the canonical 15% base with 30% as a
                     non-guaranteed ceiling.

Plus the acceptance invariants themselves, so a future change cannot silently
reintroduce blocked-program leakage or break the calibrated baseline.
"""
import re

from app.calculators.jurisdiction_comparison import ALL_PROFILES
from app.data.authority_coverage_registry import BLOCKED_SLUGS, blocks_economic_candidacy, coverage_state
from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
from app.demo.little_utopia_state import build_allocated_structures, get_state

#: CBA-009 Part 19-21: Little Utopia's own real, persisted 100%
#: contingency-expected-utilization project election (migration 0068)
#: reproduces this historical baseline through the generic pipeline.
BASELINE_NPC = 3057794.90


def _served():
    return build_allocated_structures(get_state())


# ── AC-1 / AC-2 / AC-3 ──────────────────────────────────────────────────────

def test_ac1_japan_selective_half_subsidy_cannot_price_as_guaranteed():
    assert coverage_state("jp_vipo_location_incentive") == "NON_GUARANTEED_SELECTIVE"
    assert blocks_economic_candidacy("jp_vipo_location_incentive") is True
    served = _served()
    for s in served["structures"]:
        if s.get("npc_with_adjustments_usd") is None:
            continue
        for sg in s["segments"]:
            if sg.get("program_slug") == "jp_vipo_location_incentive":
                assert sg["executable"] is False


def test_ac2_kazakhstan_single_uncorroborated_source_is_authority_insufficient():
    assert coverage_state("kz_investment_subsidy") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
    assert blocks_economic_candidacy("kz_investment_subsidy") is True


def test_ac3_thailand_prices_its_canonical_base_not_its_headline_maximum():
    tiers = {r.tier_id: r for r in get_rate_rules("th_boi_incentive")}
    assert "th-base-15" in tiers and "th-uplift-ceiling-30" in tiers
    assert tiers["th-base-15"].rate == 0.15
    assert tiers["th-base-15"].is_band_ceiling is False
    assert tiers["th-uplift-ceiling-30"].rate == 0.30
    assert tiers["th-uplift-ceiling-30"].is_band_ceiling is True
    assert any(c.kind == "discretionary_band" for c in tiers["th-uplift-ceiling-30"].conditions)
    # and the ceiling is genuinely not treated as guaranteed at runtime
    res = resolve_program_rate("th_boi_incentive", production_type="feature_film", qpe_usd=4_000_000.0)
    assert res is not None
    assert any(ev.satisfied is None for ev in res.conditions_evaluated)


def test_no_still_priceable_program_encodes_an_up_to_maximum_as_a_flat_rate():
    """The generalised form of AC-1/AC-3 — the class, not the instances."""
    offenders = []
    for code, p in ALL_PROFILES.items():
        slug = getattr(p, "program_slug", None)
        if not slug or slug in BLOCKED_SLUGS:
            continue
        rules = get_rate_rules(slug)
        if not rules:
            continue
        if any(r.is_band_ceiling for r in rules) or any(r.conditions for r in rules):
            continue  # already modelled as a non-guaranteed band
        citation = " ".join((r.citation or "") for r in rules).lower()
        if re.search(r"up to \d|maximum of \d", citation):
            offenders.append((code, slug))
    assert offenders == [], (
        f"programs encoding an 'up to' maximum as a guaranteed flat rate: {offenders}"
    )


# ── acceptance invariants ───────────────────────────────────────────────────

def test_no_blocked_program_contributes_economics_to_any_priced_structure():
    served = _served()
    priced = [s for s in served["structures"] if s.get("npc_with_adjustments_usd") is not None]
    offenders = [
        (s["structure_id"], sg["program_slug"])
        for s in priced for sg in s["segments"]
        if sg.get("program_slug") and sg.get("executable") and blocks_economic_candidacy(sg["program_slug"])
    ]
    assert offenders == []


def test_candidate_accounting_reconciles_with_no_unexplained_loss():
    served = _served()
    S = served["structures"]
    priced = [s for s in S if s.get("npc_with_adjustments_usd") is not None]
    rejected = [s for s in S if s.get("npc_with_adjustments_usd") is None]
    assert len(S) == len(priced) + len(rejected)
    for s in rejected:
        blockers = list(s.get("blockers") or [])
        for sg in s["segments"]:
            blockers += list(sg.get("blockers") or [])
        assert blockers, f"{s['structure_id']} was rejected with no recorded reason"


def test_ranking_is_strictly_ascending_by_canonical_adjusted_npc():
    served = _served()
    ranked = [r for r in served["ranking"] if r.get("npc_with_adjustments_usd") is not None]
    npcs = [r["npc_with_adjustments_usd"] for r in ranked]
    assert npcs == sorted(npcs)
    assert [r["rank"] for r in ranked] == list(range(1, len(ranked) + 1))


def test_mauritius_baseline_regression_including_the_non_claiming_us_segment():
    served = _served()
    base = next(s for s in served["structures"] if s["structure_id"] == "ALLOC-BASELINE-MU")
    assert round(base["npc_with_adjustments_usd"], 2) == BASELINE_NPC
    assert served["ranking"][0]["structure_id"] == "ALLOC-BASELINE-MU"

    mu = next(sg for sg in base["segments"] if sg["jurisdiction_code"] == "MU")
    us = next(sg for sg in base["segments"] if sg["jurisdiction_code"] == "US")
    # the intentionally non-claiming LA/US post segment
    assert us["program_slug"] is None
    assert us["claims_incentive"] is False
    assert round(us["allocated_usd"], 2) == 9068.00
    assert us["qpe_usd"] == 0.0
    # MU's 40% ceiling is discretionary and must not price as guaranteed
    assert mu["rate_floor"] == 0.30
    assert mu["is_band_ceiling"] is True
    assert mu["ceiling_requires_confirmation"] is True
    assert round(base["selected_incentive_usd"], 2) == round(mu["qpe_usd"] * 0.30, 2)


def test_australia_hard_gate_still_binds_at_the_real_threshold():
    assert resolve_program_rate("au_location_offset", production_type="feature_film",
                                qpe_usd=4_355_327.0) is None
    assert resolve_program_rate("au_location_offset", production_type="feature_film",
                                qpe_usd=12_000_000.0) is not None


def test_mauritius_treaty_zero_is_proven_not_assumed():
    from app.calculators import treaty_engine as te
    assert [c for c in ALL_PROFILES if te.get_bilateral_treaty("MU", c) is not None] == []
    assert te.is_european_convention_signatory("MU") is False
    assert te.is_eurimages_member("MU") is False
    assert te.is_ibermedia_member("MU") is False
    served = _served()
    cat = next(c for c in served["coverage"]["categories"] if c["category"] == "co_production_treaty")
    assert cat["candidates_evaluated"] == 0
    assert cat["zero_reason"]


def test_bridge_matches_optimizer_and_ranking_for_the_top_ten():
    from app.bridge.package_builder import build_package
    from app.bridge.schema import OperationType

    served = _served()
    by_id = {s["structure_id"]: s for s in served["structures"]}
    ranked = [r for r in served["ranking"] if r.get("npc_with_adjustments_usd") is not None]
    for r in ranked[:10]:
        pkg = build_package(operation=OperationType.OPTIMIZER_STRUCTURE_AUDIT,
                            structure_id=r["structure_id"])
        s = by_id[r["structure_id"]]
        assert pkg.economics.npc_usd == s["npc_with_adjustments_usd"] == r["npc_with_adjustments_usd"]


def test_no_priced_structure_shows_an_impossible_effective_rate():
    """Anomaly guard: effective rate must never exceed the highest rate any
    single still-priceable program actually offers.

    The ceiling was 0.45 before the Global Economic Data + Base Pricing
    batch 2 individually re-verified sa_film_commission_rebate's real 60%
    flat rebate directly against film.sa/incentive-programs/ (Saudi Film
    Commission, official) and removed its coverage veto -- this is a
    genuine, verified rate, not an anomaly, so the ceiling is raised to
    match rather than the check being weakened structurally. If a future
    program is verified above 60%, raise this again with the same kind of
    citation-backed justification -- never silently."""
    served = _served()
    priced = [s for s in served["structures"] if s.get("npc_with_adjustments_usd") is not None]
    for s in priced:
        qpe = sum(sg["qpe_usd"] or 0 for sg in s["segments"] if sg.get("executable"))
        if qpe <= 0:
            continue
        eff = (s["selected_incentive_usd"] or 0) / qpe
        assert 0 <= eff <= 0.60, f"{s['structure_id']} effective rate {eff:.1%} is out of range"
        assert (s["selected_incentive_usd"] or 0) <= qpe, "benefit exceeds eligible spend"
