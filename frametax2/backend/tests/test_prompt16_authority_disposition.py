"""
test_prompt16_authority_disposition.py

Prompt 16 — Final Authority Disposition. Enforces PROJECT_RULES.md's
"Final authority-safety gate":

  * every registered program reaches exactly ONE terminal disposition;
  * `priceable_partial_authority == 0` (the acceptance invariant);
  * the classifier verifies SUBSTANTIVELY -- a non-null SourceProvenance
    object alone can never promote a program (PROJECT_RULES.md §6);
  * a quarantined program contributes no economics by ANY route --
    discovery, direct `price_segment`, stacking, or ranking.

All assertions walk the LIVE registry; none uses a copied static list.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from app.data.authority_coverage_registry import blocks_economic_candidacy
from app.data.program_authority_provenance import (
    AUTHORITY_UNRESOLVED_NON_PRICEABLE,
    AUTHORITY_VERIFIED_PRICEABLE,
    PROVENANCE_INCOMPLETE_EXISTING_RECORD,
    _is_substantively_supported,
    authority_disposition,
    authority_disposition_report,
)
from app.data.program_rate_rules import _RULES_BY_PROGRAM


# ── The acceptance invariant ─────────────────────────────────────────────

def test_zero_priceable_partial_authority_programs():
    """THE Prompt 16 gate. A program that is only partially supported must
    never remain priceable in a production-accepted build."""
    report = authority_disposition_report()
    assert report["priceable_partial_authority"] == 0, (
        "priceable programs with partial authority support: "
        f"{report['priceable_partial_authority_slugs']}"
    )


def test_every_registered_program_has_exactly_one_terminal_disposition():
    valid = {AUTHORITY_VERIFIED_PRICEABLE, AUTHORITY_UNRESOLVED_NON_PRICEABLE}
    for slug in _RULES_BY_PROGRAM:
        assert authority_disposition(slug) in valid, (
            f"{slug} has no terminal disposition (still "
            f"{PROVENANCE_INCOMPLETE_EXISTING_RECORD})"
        )


def test_terminal_accounting_reconciles_the_whole_registry():
    """verified + unresolved == registered. No record may disappear."""
    r = authority_disposition_report()
    assert (
        r["authority_verified_priceable"] + r["authority_unresolved_non_priceable"]
        == r["registered"] == len(_RULES_BY_PROGRAM)
    )


# ── The classifier must be substantive, not a non-null check ─────────────

def test_a_non_null_but_empty_provenance_object_does_not_verify():
    """PROJECT_RULES.md §6 / Prompt 16 §6: 'A program cannot satisfy the
    verified state solely because an object exists.'"""
    from app.data.program_rate_rules import SourceProvenance

    verified_slug = next(
        s for s in _RULES_BY_PROGRAM if authority_disposition(s) == AUTHORITY_VERIFIED_PRICEABLE
    )
    real_rule = _RULES_BY_PROGRAM[verified_slug][0]
    assert _is_substantively_supported(real_rule)

    # Same rule, but provenance stripped to a bare non-null object.
    hollow = replace(real_rule, provenance=SourceProvenance(issuing_authority=""))
    assert not _is_substantively_supported(hollow)

    # An authority with no proposition anchor also fails.
    no_anchor = replace(
        real_rule, provenance=SourceProvenance(issuing_authority="Some Ministry"),
    )
    assert not _is_substantively_supported(no_anchor)


def test_a_secondary_source_named_as_issuing_authority_does_not_verify():
    """Secondary sources may LOCATE an official source; they may never
    independently justify deterministic pricing."""
    from app.data.program_rate_rules import SourceProvenance

    verified_slug = next(
        s for s in _RULES_BY_PROGRAM if authority_disposition(s) == AUTHORITY_VERIFIED_PRICEABLE
    )
    real_rule = _RULES_BY_PROGRAM[verified_slug][0]
    secondary = replace(real_rule, provenance=SourceProvenance(
        issuing_authority="Baker McKenzie (law firm summary)",
        citation_detail="'30% of qualifying spend'",
    ))
    assert not _is_substantively_supported(secondary)


def test_every_verified_program_names_a_real_authority_and_an_anchor():
    for slug in _RULES_BY_PROGRAM:
        if authority_disposition(slug) != AUTHORITY_VERIFIED_PRICEABLE:
            continue
        for rule in _RULES_BY_PROGRAM[slug]:
            p = rule.provenance
            assert p is not None and p.issuing_authority.strip() and p.citation_detail.strip(), (
                f"{slug}/{rule.tier_id} verified without substantive provenance"
            )


# ── Fail-closed enforcement: quarantine blocks every economic route ──────

def _unresolved_slugs():
    return [s for s in _RULES_BY_PROGRAM if authority_disposition(s) == AUTHORITY_UNRESOLVED_NON_PRICEABLE]


def test_every_unresolved_program_is_actually_blocked_in_the_canonical_registry():
    """A record marked unresolved but NOT blocked would still be priceable --
    the exact unsafe state this phase exists to eliminate."""
    for slug in _unresolved_slugs():
        assert blocks_economic_candidacy(slug), f"{slug} is unresolved but NOT quarantined"


def test_quarantined_program_cannot_price_via_direct_price_segment():
    """Prompt 16 §5: 'prevent direct price_segment calls from bypassing the
    block.' This is the route that skips discovery entirely."""
    from app.calculators.allocation_pricing import price_segment

    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    unresolved = _unresolved_slugs()
    assert unresolved, "expected at least one quarantined program"
    checked = 0
    for slug in unresolved[:12]:
        rules = _RULES_BY_PROGRAM[slug]
        ptype = next(iter(rules[0].production_types), "feature_film")
        alloc = AccountAllocation(
            account_code="2000", description="Production spend",
            amount_usd=5_000_000.0, component="production", jurisdiction_code="XX",
            assignment_kind=AssignmentKind.FIXED,
            rationale="direct-call quarantine probe",
            governing_decision="prompt16-test",
        )
        seg = price_segment(
            jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
            spend_category_by_code={"2000": "production"},
            offshore_payroll_accounts=frozenset(),
            production_type=ptype, gross_budget_usd=5_000_000.0,
        )
        assert seg.executable is False, f"{slug} priced despite quarantine"
        assert seg.blockers, f"{slug} produced no blocker explanation"
        assert not getattr(seg, "selected_incentive_usd", 0.0), (
            f"{slug} produced incentive value despite quarantine"
        )
        checked += 1
    assert checked


def test_quarantined_programs_never_appear_in_served_ranking_with_economics():
    """Ranking safety: no quarantined program may carry incentive value
    anywhere in the served, ranked output.

    NOTE ON THE ASSERTION'S REACH: ranked entries and structures carry no
    `program_slug` of their own -- program identity lives on each
    structure's SEGMENTS. An earlier draft of this test read
    `entry["program_slug"]` and therefore matched nothing and proved
    nothing. It now resolves ranked entry -> structure -> segments, and
    asserts a non-zero number of segments was actually inspected so the
    test can never silently go vacuous again."""
    from app.demo.little_utopia_state import build_allocated_structures, get_state

    served = build_allocated_structures(get_state())
    by_id = {s["structure_id"]: s for s in served["structures"]}
    offenders, segments_checked = [], 0
    for entry in served["ranking"]:
        structure = by_id.get(entry["structure_id"])
        if structure is None:
            continue
        for seg in structure.get("segments") or ():
            slug = seg.get("program_slug")
            if not slug:
                continue
            segments_checked += 1
            if blocks_economic_candidacy(slug) and (seg.get("selected_incentive_usd") or 0):
                offenders.append((entry["structure_id"], slug, seg["selected_incentive_usd"]))

    assert segments_checked > 0, "test went vacuous — no priced segments inspected"
    assert not offenders, f"quarantined programs carrying incentive in ranking: {offenders}"


def test_no_verified_program_is_left_quarantined_by_prompt16():
    """Consistency guard for the inverse error: promoting a program to
    verified but leaving its quarantine row in place would silently keep it
    unpriceable while the accounting claimed it was available."""
    from app.data.authority_coverage_registry import COVERAGE_REGISTRY

    for slug in _RULES_BY_PROGRAM:
        if authority_disposition(slug) != AUTHORITY_VERIFIED_PRICEABLE:
            continue
        rec = COVERAGE_REGISTRY.get(slug)
        if rec is None:
            continue
        assert rec.state != "AUTHORITY_UNRESOLVED_NON_PRICEABLE", (
            f"{slug} is authority-verified but still carries a Prompt 16 "
            "quarantine row — remove the row or withdraw the verification."
        )


def test_lu_baseline_program_is_authority_verified():
    """LU's own baseline must be priced on verified authority, not merely
    grandfathered -- otherwise the control proves nothing."""
    assert authority_disposition("mu_edb_incentive") == AUTHORITY_VERIFIED_PRICEABLE


def test_fvd_baseline_program_is_authority_verified():
    assert authority_disposition("gr_cash_rebate") == AUTHORITY_VERIFIED_PRICEABLE
