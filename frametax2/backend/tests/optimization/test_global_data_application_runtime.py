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
    price. us_or_opif retains live doctrine AND a PARSED-tier rate
    rule, so this proves the block is the coverage registry, not an
    absence of data.

    uk_avec, then ca_federal_pstc, were the original fixtures here, but
    both were individually recovered/verified in later batches (batch 3
    for uk_avec; the Historical-37 recovery/adjudication pass for
    ca_federal_pstc, which found its existing PARSED-tier data already
    substantively sufficient to calculate) and removed from the coverage
    veto -- neither would still prove this gate. See
    DELIBERATELY_PROMOTED_CANONICAL_IDS in
    tests/data/test_authority_coverage_registry.py. us_or_opif (Oregon
    Production Investment Fund) remains one of the few programs still
    genuinely UNPRICEABLE_AUTHORITY_INSUFFICIENT while holding real
    RateRule data, per a live check of COVERAGE_REGISTRY at the time this
    fixture was chosen."""
    from app.data.program_rate_rules import get_rate_rules

    assert len(get_rate_rules("us_or_opif")) > 0, "fixture assumption: us_or_opif still holds rate rules"
    seg = price_segment(
        jurisdiction_code="US-OR",
        program_slug="us_or_opif",
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
    a runtime slug spelling that differed from the canonical_id.

    Saudi (batch 2) and BC PSTC (batch 1) were later individually
    re-verified and promoted -- they are now genuinely, correctly
    priceable under their canonical slug (see
    DELIBERATELY_PROMOTED_CANONICAL_IDS in
    tests/data/test_authority_coverage_registry.py). Dubai DPIP is
    unaffected and remains SUPERSEDED. The escape this test guards --
    that a runtime slug spelling could bypass the veto that WAS in
    force -- is still closed; it just no longer applies to these two
    slugs since the veto itself was deliberately lifted."""
    assert coverage_state("sa_film_commission_rebate") == "PRICEABLE_VALIDATED"
    assert coverage_state("ae_dxb_dpip") == "SUPERSEDED"
    assert coverage_state("ca_bc_pstc") == "PRICEABLE_VALIDATED"

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
    baseline must not move.

    Structure count legitimately grew 177 -> 185: the CineGlobe canonical
    pricing path + discovery repair fixed discover_executable_jurisdictions()
    to examine every independently registered (jurisdiction_code,
    program_slug) pair rather than collapsing to one program per code —
    this shared discovery function backs BOTH Little Utopia's legacy
    build_allocated_structures() and the generic canonical_evaluation.py
    path, so both gained the same newly-discoverable candidates (e.g.
    CA-ON's on_ofttc and OCASE, previously invisible alongside
    ca_on_opstc). Mauritius itself is untouched — asserted below."""
    served = _served()
    baseline = next(
        s for s in served["structures"] if s["structure_id"] == "ALLOC-BASELINE-MU"
    )
    assert round(baseline["npc_with_adjustments_usd"], 2) == 3057794.90  # CBA-009 Part 19-21: LU's own persisted 100% contingency-utilization project election (migration 0068) reproduces the historical $3,057,794.90 baseline through the generic pipeline
    assert served["ranking"][0]["structure_id"] == "ALLOC-BASELINE-MU"
    # 197 -> 201: canonical knowledge consolidation recovered two real,
    # already-researched programs stranded in noncanonical locations
    # (ca_bc_dave — "A separate 16% DAVE (animation/VFX/post) credit
    # exists, not modeled"; au_pdv_offset — "PDV Offset ... not modeled as
    # alternative programs"), both quoted verbatim from
    # jurisdiction_comparison.py's own profiles. Each adds one
    # full_relocation + one component_relocation candidate = +4, fully
    # attributed. Mauritius itself is untouched (asserted above).
    assert len(served["structures"]) == 201


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
