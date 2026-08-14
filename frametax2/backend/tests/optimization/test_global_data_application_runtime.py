"""
Global Data Application — served-runtime verification.

Proves, against the ACTUAL served pipeline, that applying the canonical
corpus closed the runtime leak the Little Utopia acceptance entry-check
found (22 canonically-unpriceable programs still pricing, ranks 6/7
contaminated), and that it did so without disturbing the calibrated
Mauritius baseline.

Regression protection for the three VERIFIED defects fixed this pass:
  1. blocked programs still priced (no coverage gate in the pricing kernel)
  2. blocked programs still entered optimization (no gate in discovery)
  3. blocked programs escaped under a DIFFERENT runtime slug spelling
     (Saudi rank 2, Dubai DPIP rank 8, BC PSTC rank 10)
"""
from app.calculators.allocation_pricing import price_segment
from app.data.authority_coverage_registry import (
    BLOCKED_SLUGS,
    blocks_economic_candidacy,
    coverage_state,
)
from app.demo.little_utopia_state import build_allocated_structures, get_state


def _served():
    return build_allocated_structures(get_state())


def test_no_priced_structure_contains_a_blocked_program():
    """THE gate assertion: canonical blocked set INTERSECT priced economics
    must be empty."""
    served = _served()
    priced = [s for s in served["structures"] if s.get("npc_with_adjustments_usd") is not None]
    assert priced, "expected a non-empty priced set"
    offenders = [
        (s["structure_id"], seg["program_slug"])
        for s in priced
        for seg in s["segments"]
        if seg.get("program_slug") and blocks_economic_candidacy(seg["program_slug"])
    ]
    assert offenders == [], f"blocked programs present in priced structures: {offenders[:10]}"


def test_no_blocked_program_is_ranked_as_an_economic_candidate():
    served = _served()
    ranked = [r for r in served["ranking"] if r.get("npc_with_adjustments_usd") is not None]
    by_id = {s["structure_id"]: s for s in served["structures"]}
    offenders = []
    for r in ranked:
        st = by_id.get(r["structure_id"])
        if not st:
            continue
        for seg in st["segments"]:
            if seg.get("program_slug") and blocks_economic_candidacy(seg["program_slug"]):
                offenders.append((r["rank"], r["structure_id"], seg["program_slug"]))
    assert offenders == [], f"blocked programs in the ranking: {offenders[:10]}"


def test_price_segment_hard_blocks_a_covered_program_even_when_directly_specified():
    """The pricing kernel is the authoritative gate -- a StructureSpec that
    names a blocked program directly (bypassing discovery) must still not
    price. uk_avec retains live doctrine AND rate rules, so this proves the
    block is the coverage registry, not an absence of data."""
    from app.data.program_rate_rules import get_rate_rules

    assert len(get_rate_rules("uk_avec")) > 0, "fixture assumption: uk_avec still holds rate rules"
    seg = price_segment(
        jurisdiction_code="GB",
        program_slug="uk_avec",
        allocations=[],
        spend_category_by_code={},
        offshore_payroll_accounts=frozenset(),
    )
    assert seg.executable is False
    assert seg.incentive_floor_usd == 0.0
    assert seg.incentive_ceiling_usd == 0.0
    assert any("UNPRICEABLE_AUTHORITY_INSUFFICIENT" in b for b in seg.blockers)


def test_the_three_slug_spelling_escapes_are_closed():
    """Saudi (rank 2), Dubai DPIP (rank 8) and BC PSTC (rank 10) priced under
    a runtime slug spelling that differed from the canonical_id."""
    assert coverage_state("sa_film_commission_rebate") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
    assert coverage_state("ae_dxb_dpip") == "SUPERSEDED"
    assert coverage_state("ca_bc_pstc") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"

    served = _served()
    ranked_ids = {
        r["structure_id"] for r in served["ranking"]
        if r.get("npc_with_adjustments_usd") is not None
    }
    by_id = {s["structure_id"]: s for s in served["structures"]}
    for sid in ("ALLOC-RELOC-SA", "ALLOC-RELOC-AE-DXB", "ALLOC-RELOC-CA-BC"):
        if sid in ranked_ids:
            st = by_id[sid]
            claimed = [
                sg["program_slug"] for sg in st["segments"]
                if sg.get("program_slug") and sg.get("executable")
            ]
            assert not (set(claimed) & BLOCKED_SLUGS), (
                f"{sid} still derives economics from a blocked program: {claimed}"
            )


def test_mauritius_calibration_is_byte_identical_after_application():
    """The canonical corpus did not touch mu/mt/gr/au, so the calibrated
    baseline must not move."""
    served = _served()
    baseline = next(
        s for s in served["structures"] if s["structure_id"] == "ALLOC-BASELINE-MU"
    )
    assert round(baseline["npc_with_adjustments_usd"], 2) == 3057794.90
    assert served["ranking"][0]["structure_id"] == "ALLOC-BASELINE-MU"
    assert len(served["structures"]) == 177


def test_selective_programs_contribute_zero_guaranteed_value():
    """ENCODE_SELECTIVE_ZERO_GUARANTEED: a competitive award never prices as a
    guaranteed rate, even where the canonical record carries a headline rate."""
    for slug in ("jo_rfc_rebate", "kr_film_incentive", "il_film_incentive", "jp_film_incentive"):
        assert coverage_state(slug) == "NON_GUARANTEED_SELECTIVE"
        assert blocks_economic_candidacy(slug) is True


def test_treaty_candidate_generation_still_functions_after_application():
    """The candidate-generation repair from the prior pass must survive."""
    from app.calculators import treaty_engine as te

    assert te.get_bilateral_treaty("CA", "FR") is not None
    assert te.get_bilateral_treaty("CA", "JP") is None
    served = _served()
    assert served["coverage"]["reachable_treaty_partners"] == []  # MU proven-zero, unchanged
