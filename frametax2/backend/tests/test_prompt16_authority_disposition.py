"""
test_prompt16_authority_disposition.py

Prompt 16 (Final Authority Disposition) + its POLICY CORRECTION (Final
Canonical Backend Closeout): economics and provenance are separate
dimensions.

  * the provenance classifier verifies SUBSTANTIVELY -- a non-null
    SourceProvenance object alone can never mark a program verified
    (PROJECT_RULES.md §6);
  * `AUTHORITY_UNRESOLVED_NON_PRICEABLE` is a REPORTING-ONLY provenance
    state -- it must never appear in `BLOCKING_STATES`, so incomplete
    structured provenance can never by itself suppress a previously
    accepted program's deterministic economics;
  * a program that IS genuinely economically blocked (material rule
    unresolved, superseded, non-economic, selective) still fails closed by
    ANY route -- discovery, direct `price_segment`, stacking, ranking --
    for its real, economic reason, independent of provenance status.

All assertions walk the LIVE registry; none uses a copied static list.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from app.data.authority_coverage_registry import BLOCKING_STATES, blocks_economic_candidacy
from app.data.program_authority_provenance import (
    AUTHORITY_UNRESOLVED_NON_PRICEABLE,
    AUTHORITY_VERIFIED_PRICEABLE,
    ECONOMIC_STATE_DETERMINISTIC_PRICEABLE,
    ECONOMIC_STATE_MATERIAL_RULE_UNRESOLVED,
    PROVENANCE_EVIDENCE_NOT_RETAINED,
    PROVENANCE_RECOVERED,
    _is_substantively_supported,
    authority_disposition,
    authority_disposition_report,
    economic_state,
    provenance_cohort_disposition,
)
from app.data.program_rate_rules import _RULES_BY_PROGRAM


# ── THE policy correction, proven structurally ───────────────────────────

def test_provenance_incompleteness_never_blocks_economic_candidacy():
    """THE gate. Incomplete structured provenance alone must never suppress
    a previously accepted program's deterministic economics."""
    assert "AUTHORITY_UNRESOLVED_NON_PRICEABLE" not in BLOCKING_STATES


def test_a_program_can_be_provenance_unresolved_yet_economically_priceable():
    """The exact state Prompt 16 wrongly forbade. Proven against the real
    registry, not a synthetic example."""
    candidates = [
        s for s in _RULES_BY_PROGRAM
        if authority_disposition(s) == AUTHORITY_UNRESOLVED_NON_PRICEABLE
        and economic_state(s) == ECONOMIC_STATE_DETERMINISTIC_PRICEABLE
    ]
    assert candidates, "expected real programs that are provenance-unresolved but priceable"
    for slug in candidates:
        assert not blocks_economic_candidacy(slug)


# ── Terminal accounting on BOTH axes ──────────────────────────────────────

def test_every_registered_program_has_exactly_one_provenance_disposition():
    valid = {AUTHORITY_VERIFIED_PRICEABLE, AUTHORITY_UNRESOLVED_NON_PRICEABLE}
    for slug in _RULES_BY_PROGRAM:
        assert authority_disposition(slug) in valid


def test_provenance_accounting_reconciles_the_whole_registry():
    r = authority_disposition_report()
    assert (
        r["authority_verified_priceable"] + r["authority_unresolved_non_priceable"]
        == r["registered"] == len(_RULES_BY_PROGRAM)
    )


def test_economic_state_accounting_reconciles_the_whole_registry():
    r = authority_disposition_report()
    assert sum(r["economic_state_counts"].values()) == r["registered"]


# ── The provenance classifier must be substantive, not a non-null check ──

def test_a_non_null_but_empty_provenance_object_does_not_verify():
    from app.data.program_rate_rules import SourceProvenance

    verified_slug = next(
        s for s in _RULES_BY_PROGRAM if authority_disposition(s) == AUTHORITY_VERIFIED_PRICEABLE
    )
    real_rule = _RULES_BY_PROGRAM[verified_slug][0]
    assert _is_substantively_supported(real_rule)

    hollow = replace(real_rule, provenance=SourceProvenance(issuing_authority=""))
    assert not _is_substantively_supported(hollow)

    no_anchor = replace(
        real_rule, provenance=SourceProvenance(issuing_authority="Some Ministry"),
    )
    assert not _is_substantively_supported(no_anchor)


def test_a_secondary_source_named_as_issuing_authority_does_not_verify():
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


# ── Genuine economic blocks still fail closed, by every route ────────────

def _economically_blocked_slugs():
    return [s for s in _RULES_BY_PROGRAM if blocks_economic_candidacy(s)]


def test_economically_blocked_programs_all_have_a_real_non_provenance_reason():
    """Every program still blocked must be blocked for a genuine economic
    reason, never for AUTHORITY_UNRESOLVED_NON_PRICEABLE (which cannot
    block, per the first test above)."""
    from app.data.authority_coverage_registry import COVERAGE_REGISTRY

    for slug in _economically_blocked_slugs():
        rec = COVERAGE_REGISTRY[slug]
        assert rec.state != "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
        assert rec.state in BLOCKING_STATES


def test_economically_blocked_program_cannot_price_via_direct_price_segment():
    """The route that skips discovery entirely must still be closed for a
    genuinely blocked program (material rule unresolved, superseded,
    selective, etc.) -- provenance-only programs are explicitly EXCLUDED
    from this test since they must now price."""
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    blocked = _economically_blocked_slugs()
    assert blocked, "expected at least one genuinely economically-blocked program"
    checked = 0
    for slug in blocked[:12]:
        rules = _RULES_BY_PROGRAM.get(slug) or []
        ptype = next(iter(rules[0].production_types), "feature_film") if rules else "feature_film"
        alloc = AccountAllocation(
            account_code="2000", description="Production spend",
            amount_usd=5_000_000.0, component="production", jurisdiction_code="XX",
            assignment_kind=AssignmentKind.FIXED,
            rationale="direct-call economic-block probe",
            governing_decision="prompt16-policy-correction-test",
        )
        seg = price_segment(
            jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
            spend_category_by_code={"2000": "production"},
            offshore_payroll_accounts=frozenset(),
            production_type=ptype, gross_budget_usd=5_000_000.0,
        )
        assert seg.executable is False, f"{slug} priced despite economic block"
        assert seg.blockers, f"{slug} produced no blocker explanation"
        assert not getattr(seg, "selected_incentive_usd", 0.0)
        checked += 1
    assert checked


def test_economically_blocked_programs_never_appear_in_served_ranking_with_economics():
    """Ranking safety, resolved through structure segments (ranked entries
    carry no program_slug of their own) with a non-vacuousness assertion."""
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
    assert not offenders, f"economically-blocked programs carrying incentive in ranking: {offenders}"


def test_no_verified_program_is_blocked_for_the_provenance_reason_itself():
    """Inverse-error guard, correctly scoped: a program promoted to
    AUTHORITY_VERIFIED_PRICEABLE must never be blocked BY THE PROVENANCE
    STATE ITSELF (impossible in this codebase since that state cannot
    block at all -- proven above). It MAY still be economically blocked
    for a genuinely separate, independent reason (e.g. us_or_opif: real,
    pre-existing UNPRICEABLE_AUTHORITY_INSUFFICIENT predating this pass) --
    that is the correct, intended shape of two independent axes, not a
    bug. This test proves the independence, not that verified implies
    unblocked."""
    from app.data.authority_coverage_registry import COVERAGE_REGISTRY

    for slug in _RULES_BY_PROGRAM:
        if authority_disposition(slug) != AUTHORITY_VERIFIED_PRICEABLE:
            continue
        rec = COVERAGE_REGISTRY.get(slug)
        if rec is None:
            continue
        assert rec.state != "AUTHORITY_UNRESOLVED_NON_PRICEABLE", (
            f"{slug} is verified but its OWN provenance-quarantine row was never removed"
        )


# ── The internally-recovered cohort ───────────────────────────────────────

def test_provenance_cohort_disposition_is_recovered_or_not_retained_only():
    valid = {PROVENANCE_RECOVERED, PROVENANCE_EVIDENCE_NOT_RETAINED}
    for slug in _RULES_BY_PROGRAM:
        assert provenance_cohort_disposition(slug) in valid


def test_internally_recovered_programs_are_provenance_verified():
    """The 23 programs recovered this pass via cross-referencing
    program_requirements.py's own PRIMARY-tier EvidenceRecord store (a
    second existing canonical provenance location Prompt 16 never
    consulted) must verify. `us_or_opif` and `jp_vipo_location_incentive`
    are deliberately included even though both remain economically blocked
    for their own, separate, PRE-EXISTING reasons (UNPRICEABLE_AUTHORITY_
    INSUFFICIENT and NON_GUARANTEED_SELECTIVE respectively -- both predate
    this whole effort and are unrelated to structured provenance) -- see
    the independence test above; recovering their provenance is still real
    and correct work even though it does not unblock them."""
    recovered_this_pass = [
        "at_fisa_plus", "be_tax_shelter", "ca_ab_fttc", "dk_production_rebate",
        "fj_film_rebate", "is_film_reimbursement_scheme", "it_tax_credit_foreign",
        "lt_film_centre_cash_rebate", "lu_filmfund_tax_shelter_rebate", "ma_ccm_rebate",
        "my_finas_rebate", "nl_film_production_incentive", "pl_pisf_cash_rebate",
        "ro_film_office_cash_rebate", "rs_film_commission_cash_rebate", "us_or_opif",
        "us_pr_film_incentives_act", "us_wa_motion_picture_competitiveness",
        "cl_corfo_incentive", "il_foreign_production_fund", "jp_vipo_location_incentive",
        "ph_fdcp_flip", "th_boi_incentive",
    ]
    assert len(recovered_this_pass) == 23
    for slug in recovered_this_pass:
        assert authority_disposition(slug) == AUTHORITY_VERIFIED_PRICEABLE, slug
        assert provenance_cohort_disposition(slug) == PROVENANCE_RECOVERED, slug
        if slug not in ("us_or_opif", "jp_vipo_location_incentive"):  # real, independent, pre-existing exceptions
            assert not blocks_economic_candidacy(slug), slug


def test_material_economic_rule_unresolved_is_a_real_distinct_minority():
    """Confirms the fixed cohort is not being rubber-stamped: real
    programs with a genuine, unresolved economic gap (not merely
    under-sourced) still classify separately and still block."""
    unresolved_economics = [
        s for s in _RULES_BY_PROGRAM if economic_state(s) == ECONOMIC_STATE_MATERIAL_RULE_UNRESOLVED
    ]
    assert unresolved_economics
    for slug in unresolved_economics:
        assert blocks_economic_candidacy(slug)


def test_lu_baseline_program_is_authority_verified():
    assert authority_disposition("mu_edb_incentive") == AUTHORITY_VERIFIED_PRICEABLE


def test_fvd_baseline_program_is_authority_verified():
    assert authority_disposition("gr_cash_rebate") == AUTHORITY_VERIFIED_PRICEABLE
