"""Tests for allocation_pricing — multi-register segment pricing over an
account->jurisdiction allocation, structure expressions, gating,
travel/FX single application, in-kind containment, ranking, and the
delegated program-stack enumeration."""
from __future__ import annotations

import pytest

from app.calculators.allocation_pricing import (
    enumerate_segment_program_stacks,
    price_allocated_structure,
    rank_allocated_structures,
)
from app.calculators.production_allocation import (
    MOVABLE_COMPONENTS,
    StructureSpec,
    derive_account_allocation,
)
from app.calculators.qualification_derivation import BudgetLine
from app.calculators.qualification_model import (
    QualificationState,
    build_little_utopia_real_register,
    build_little_utopia_register_for_jurisdiction,
)
from app.data.little_utopia_real_budget import (
    AUTHORITATIVE_GROSS_BUDGET_USD,
    LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_REAL_BUDGET_LINES,
    LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
    LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
)

GROSS = AUTHORITATIVE_GROSS_BUDGET_USD


def _lines() -> list[BudgetLine]:
    return [
        BudgetLine(
            account_code=c, description=d, amount_usd=a,
            spend_category=LITTLE_UTOPIA_REAL_SPEND_CATEGORY.get(c), is_memo=False,
        )
        for c, d, a, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES
    ]


def _price(spec: StructureSpec, **kwargs):
    allocation = derive_account_allocation(
        lines=_lines(),
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        spec=spec,
        stated_outside_accounts=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    )
    return price_allocated_structure(
        spec=spec, allocation=allocation,
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
        gross_budget_usd=GROSS,
        **kwargs,
    )


def _spec(structure_id, structure_type, participants, programs, **overrides):
    kwargs = dict(
        structure_id=structure_id, structure_type=structure_type,
        label=structure_id, primary_jurisdiction=participants[0],
        participants=participants, incentive_programs=programs,
    )
    kwargs.update(overrides)
    return StructureSpec(**kwargs)


BASELINE = _spec("P-BASE-MU", "single_country", ("MU",), {"MU": "mu_edb_incentive"})


# ── 1/7/8: baseline partial register matches the served register ────────────

def test_baseline_mu_segment_matches_served_register_qpe():
    pricing = _price(BASELINE)
    assert pricing.is_fully_priced
    mu = next(s for s in pricing.segments if s.jurisdiction_code == "MU")
    served = build_little_utopia_real_register(mu_rate=0.40)
    served_qpe = round(sum(a.amount_usd for a in served
                           if a.state == QualificationState.QUALIFIES), 2)
    assert mu.qpe_usd == served_qpe  # independent partial register, same truth
    assert mu.incentive_floor_usd == round(served_qpe * 0.30, 2)
    # the stated-LA editorial spend is a separate, non-incentive segment
    us = next(s for s in pricing.segments if s.jurisdiction_code == "US")
    assert us.claims_incentive is False and us.incentive_floor_usd == 0.0
    assert us.allocated_usd == 9_068.0


def test_full_relocation_matches_alternative_jurisdiction_register():
    spec = _spec("P-RELOC-GR", "full_relocation", ("GR",), {"GR": "gr_cash_rebate"})
    pricing = _price(spec)
    assert pricing.is_fully_priced
    gr = next(s for s in pricing.segments if s.jurisdiction_code == "GR")
    alt_register = build_little_utopia_register_for_jurisdiction("GR", "gr_cash_rebate", 0.0)
    alt_qpe = round(sum(a.amount_usd for a in alt_register
                        if a.state == QualificationState.QUALIFIES), 2)
    assert gr.qpe_usd == alt_qpe  # same truth as /economics.alternative_jurisdictions
    assert pricing.npc_verified_usd == round(GROSS - gr.qpe_usd * 0.40, 2)


# ── 3/6: component routing changes segment QPE and total NPC ────────────────

def test_component_route_changes_segment_qpe_and_npc():
    baseline = _price(BASELINE)
    routed = _price(_spec(
        "P-COMP-MT", "component_relocation", ("MU", "MT"),
        {"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate"},
        component_routes={c: "MT" for c in MOVABLE_COMPONENTS},
    ))
    assert routed.is_fully_priced
    mu_base = next(s for s in baseline.segments if s.jurisdiction_code == "MU")
    mu_routed = next(s for s in routed.segments if s.jurisdiction_code == "MU")
    mt = next(s for s in routed.segments if s.jurisdiction_code == "MT")
    # VFX (6100, $52,500) left MU; editorial ($9,068) moved from US to MT
    assert mu_routed.qpe_usd < mu_base.qpe_usd
    assert mt.qpe_usd > 0
    assert mt.executable
    # both segment QPE and total NPC moved (validation point 6)
    assert routed.npc_verified_usd != baseline.npc_verified_usd
    # no account is priced twice: segment account sets are disjoint
    seg_sets = [set(s.account_codes) for s in routed.segments]
    for i, a in enumerate(seg_sets):
        for b in seg_sets[i + 1:]:
            assert not (a & b)


def test_component_route_below_minimum_spend_blocks_honestly():
    # Greece's rebate has a minimum-spend condition the routed component
    # spend (~$61.6k) cannot meet — the structure must be excluded from
    # ranking with that exact blocker, never priced at a guessed rate.
    pricing = _price(_spec(
        "P-COMP-GR", "component_relocation", ("MU", "GR"),
        {"MU": "mu_edb_incentive", "GR": "gr_cash_rebate"},
        component_routes={c: "GR" for c in MOVABLE_COMPONENTS},
    ))
    assert not pricing.is_fully_priced
    assert any("did not resolve" in b for b in pricing.blockers)
    assert pricing.npc_verified_usd is None


# ── 4: genuine split production ──────────────────────────────────────────────

def test_split_production_prices_both_partial_registers():
    split = _price(_spec(
        "P-SPLIT-MU-GR", "split_production", ("MU", "GR"),
        {"MU": "mu_edb_incentive", "GR": "gr_cash_rebate"},
        account_splits={"3400": {"MU": 0.7, "GR": 0.3}},
    ))
    assert split.is_fully_priced
    mu = next(s for s in split.segments if s.jurisdiction_code == "MU")
    gr = next(s for s in split.segments if s.jurisdiction_code == "GR")
    assert gr.allocated_usd == round(496_232.0 * 0.3, 2)
    assert gr.qpe_usd > 0 and mu.qpe_usd > 0
    # the split account appears in both segments ONLY via its explicit portions
    assert "3400" in mu.account_codes and "3400" in gr.account_codes
    # conservation still exact
    assert split.allocation.conserves
    # changing the producer's split changes both segment QPE and NPC
    split2 = _price(_spec(
        "P-SPLIT-MU-GR-2", "split_production", ("MU", "GR"),
        {"MU": "mu_edb_incentive", "GR": "gr_cash_rebate"},
        account_splits={"3400": {"MU": 0.6, "GR": 0.4}},
    ))
    gr2 = next(s for s in split2.segments if s.jurisdiction_code == "GR")
    assert gr2.qpe_usd != gr.qpe_usd
    # The canonical (best-supported/modeled) NPC is rate-driven: MU and GR
    # share a 40% modeled rate, so re-splitting spend between them leaves the
    # modeled NPC unchanged — correct. The conservative (floor-rate) NPC does
    # move, because MU's 30% floor differs from GR's 40% floor.
    assert split2.npc_conservative_usd != split.npc_conservative_usd


# ── 5: treaty legality is evaluated, never forced ────────────────────────────

def test_treaty_coproduction_without_instrument_is_blocked():
    pricing = _price(_spec(
        "P-TREATY-MU-GR", "treaty_coproduction", ("MU", "GR"),
        {"MU": "mu_edb_incentive", "GR": "gr_cash_rebate"},
    ))
    assert not pricing.is_fully_priced
    assert any("treaty" in b.lower() for b in pricing.blockers)


def test_majority_claim_contradicted_by_allocation_is_blocked():
    pricing = _price(_spec(
        "P-MM-MU-MT", "majority_minority", ("MU", "MT"),
        {"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate"},
        ownership_shares={"MT": 0.8, "MU": 0.2},  # MT majority but ~no MT spend
    ))
    assert any("majority participation" in b for b in pricing.blockers)


# ── expressions: service / hybrid / multi-party through the same model ──────

def test_service_and_hybrid_and_multiparty_are_expressible_not_bespoke():
    service = _price(_spec(
        "P-SERVICE-MU", "service_production", ("MU",), {"MU": "mu_edb_incentive"},
    ))
    assert service.is_fully_priced  # single-jurisdiction service shoot prices
    hybrid = _price(_spec(
        "P-HYBRID", "hybrid", ("MU", "MT"),
        {"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate"},
        component_routes={c: "MT" for c in MOVABLE_COMPONENTS},
    ))
    assert any("treaty" in b.lower() for b in hybrid.blockers)  # honest gate
    multi = _price(_spec(
        "P-MULTI", "multi_party", ("MU", "MT", "GR"),
        {"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate", "GR": "gr_cash_rebate"},
    ))
    assert not multi.is_fully_priced  # no instrument covers the triple


# ── 9/10: travel & FX once; in-kind containment ─────────────────────────────

def test_travel_and_fx_apply_once_at_structure_level():
    pricing = _price(BASELINE, travel_incremental_delta_usd=1_000.0, fx_delta_usd=500.0)
    assert pricing.travel_incremental_delta_usd == 1_000.0
    assert pricing.fx_delta_usd == 500.0
    assert pricing.npc_with_adjustments_usd == round(pricing.npc_verified_usd + 1_500.0, 2)
    # segments never carry travel/FX fields — single application by construction
    for s in pricing.segments:
        assert not hasattr(s, "travel_incremental_delta_usd")
        assert not hasattr(s, "fx_delta_usd")


def test_fx_basis_threads_through_alongside_the_delta():
    # fx_basis is the provenance for fx_delta_usd — the caller's own
    # FXNormalizationResult (currency/rate/source/date/note), threaded
    # through unmodified so the served payload can explain WHY the delta
    # is what it is, not just the number.
    basis = {
        "jurisdiction_code": "MU", "local_currency": "MUR", "rate_used": 47.05,
        "rate_source": "live", "rate_date": "2026-07-13", "note": "Live sourced snapshot.",
    }
    pricing = _price(BASELINE, fx_delta_usd=0.0, fx_basis=basis)
    assert pricing.fx_basis == basis
    # Never fabricated: no fx_basis kwarg -> None, not a guessed default.
    pricing_no_fx = _price(BASELINE)
    assert pricing_no_fx.fx_basis is None


def test_inkind_post_never_enters_any_segment():
    # The off-budget MU in-kind post is never a budget line or QPE — it only
    # enters production economics as an NPC-level replacement normalization
    # (Phase 5): $0 when the post stays in MU, the replacement cost when it
    # moves out. Segment QPE never contains it.
    base = _price(BASELINE)
    assert base.allocation.total_allocated_usd == base.allocation.total_budget_lines_usd
    assert "never enters any segment" in base.inkind_note
    assert "NOT QPE" in base.inkind_note
    # MU-anchored baseline keeps the post in MU → no replacement cost.
    assert base.inkind_replacement_delta_usd == 0.0
    # A full relocation out of MU absorbs the replacement cost at NPC level,
    # still never touching any segment's QPE. (The orchestrator computes the
    # delta from the in-kind model; here it is supplied explicitly to the
    # pricer, which is what proves it enters NPC and not any segment.)
    reloc = _price(
        _spec("P-RELOC-MT", "full_relocation", ("MT",), {"MT": "mt_mfc_rebate"}),
        inkind_replacement_delta_usd=625_000.0,
    )
    assert reloc.allocation.total_allocated_usd == reloc.allocation.total_budget_lines_usd
    assert reloc.inkind_replacement_delta_usd == 625_000.0
    assert all(getattr(s, "qpe_usd", 0) < GROSS for s in reloc.segments)  # in-kind not in any segment
    # the replacement enters NPC, not any segment
    assert reloc.npc_with_adjustments_usd == pytest.approx(
        reloc.npc_verified_usd + (reloc.travel_incremental_delta_usd or 0.0)
        + (reloc.fx_delta_usd or 0.0) + reloc.inkind_replacement_delta_usd, abs=0.01,
    )


# ── ranking & gating ─────────────────────────────────────────────────────────

def test_unpriced_structures_excluded_from_ranking_with_blockers():
    priced = _price(BASELINE)
    blocked = _price(_spec(
        "P-TREATY-MU-GR", "treaty_coproduction", ("MU", "GR"),
        {"MU": "mu_edb_incentive", "GR": "gr_cash_rebate"},
    ))
    ranking = rank_allocated_structures([blocked, priced])
    ranked = [r for r in ranking if r["rank"] is not None]
    unranked = [r for r in ranking if r["rank"] is None]
    assert [r["structure_id"] for r in ranked] == ["P-BASE-MU"]
    assert unranked and unranked[0]["excluded_from_ranking_because"]


def test_structure_recommendation_is_deterministic_and_gated():
    pricing = _price(_spec(
        "P-COMP-MT", "component_relocation", ("MU", "MT"),
        {"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate"},
        component_routes={c: "MT" for c in MOVABLE_COMPONENTS},
    ))
    rec = pricing.recommendation
    assert rec.recommendation_id == "REC-STRUCT-P-COMP-MT"
    assert rec.approval_chain[0] == "producer"
    assert rec.reversibility == "reversible_before_execution"
    assert rec.gated  # unresolved relocation-confirmation requirements
    assert rec.dependency_group
    # explainability: structure / budget lines / authority / facts /
    # assumptions / calculations / approvals all present (validation 12)
    for key in ("structure", "allocated_budget_lines", "authority",
                "production_facts", "assumptions", "calculations",
                "approvals_and_actions"):
        assert key in rec.explanation
    assert rec.explanation["calculations"]["npc_verified_usd"] == pricing.npc_verified_usd
    treaty = _price(_spec(
        "P-TREATY-MU-MT", "treaty_coproduction", ("MU", "MT"),
        {"MU": "mu_edb_incentive", "MT": "mt_mfc_rebate"},
    ))
    assert treaty.recommendation.reversibility == "hard_to_reverse"
    assert "counsel" in treaty.recommendation.approval_chain


# ── delegated program-stack enumeration ──────────────────────────────────────

def test_stack_enumeration_returns_empty_for_single_program():
    assert enumerate_segment_program_stacks(
        jurisdiction={"id": "MU"}, line_items=[],
        candidate_programs=[{"program": {"slug": "mu_edb_incentive"}}],
        stacking_rules=[],
    ) == []


def test_stack_enumeration_delegates_to_generate_structure_scenarios(monkeypatch):
    import app.calculators.generate_structure_scenarios as gss
    calls = {}

    def _fake(**kwargs):
        calls.update(kwargs)
        return ["SENTINEL"]

    monkeypatch.setattr(gss, "generate_structure_scenarios", _fake)
    out = enumerate_segment_program_stacks(
        jurisdiction={"id": "IE"}, line_items=[{"x": 1}],
        candidate_programs=[{"program": {"slug": "a"}}, {"program": {"slug": "b"}}],
        stacking_rules=[{"r": 1}],
    )
    assert out == ["SENTINEL"]
    assert calls["jurisdiction"] == {"id": "IE"}
    assert len(calls["candidate_programs"]) == 2


# ── worldwide coverage: every category evaluated; zeros proven ──────────────

class TestWorldwideCoverage:
    """Acceptance: the served optimizer must EVALUATE every executable
    structure category by default (no producer election) and PROVE any
    category that legitimately produces zero priced candidates."""

    def _out(self):
        from app.demo.little_utopia_state import (
            build_allocated_structures, get_state, reset_fact_answers,
        )
        reset_fact_answers()
        return build_allocated_structures(get_state())

    def test_component_routing_auto_evaluated_for_every_executable_partner(self):
        out = self._out()
        comp = [p for p in out["structures"]
                if p["structure_type"] == "component_relocation"]
        targets = {p["structure_id"].rsplit("-", 1)[-1] for p in comp}
        # one anchor-component structure per discovery-retained partner:
        # incentive-ready (GR/IE/MT) AND capability-only (production-
        # capable, incentive pending — BE/CY/DE/ES/FR/HR/IT), evaluated
        # WITHOUT any producer election. Capability-only partners are
        # never silently dropped from structure generation.
        assert targets == {"GR", "IE", "MT", "BE", "CY", "DE", "ES", "FR", "HR", "IT"}
        # at least one prices (MT, above its min spend); the others block
        # honestly — GR/IE on their own minimum-spend rule, the
        # capability-only partners on missing doctrine/rate rules —
        # evaluated, never omitted, never guessed.
        assert any(p["is_fully_priced"] for p in comp)
        assert any((not p["is_fully_priced"]) and p["blockers"] for p in comp)

    def test_coverage_report_proves_every_category(self):
        cov = self._out()["coverage"]
        cats = {c["category"]: c for c in cov["categories"]}
        assert cats["single_jurisdiction"]["fully_priced"] == 4
        assert cats["component_routing_anchor"]["candidates_evaluated"] == 10
        # co-production is EVALUATED-as-zero with a proven reason (MU has no
        # treaty instrument) — never silently omitted
        assert cats["co_production_treaty"]["candidates_evaluated"] == 0
        assert "no co-production treaty instrument" in \
            cats["co_production_treaty"]["zero_reason"].lower()
        assert cov["reachable_treaty_partners"] == []
        # split is zero-by-design (needs an explicit producer split)
        assert cats["split_production"]["candidates_evaluated"] == 0
        assert "explicit producer" in cats["split_production"]["zero_reason"]

    def test_ranking_covers_all_priced_structures_globally_optimal_is_baseline_mu(self):
        out = self._out()
        ranked = [r for r in out["ranking"] if r["rank"] is not None]
        # 4 single + 1 priced component = 5 priced and ranked
        assert len(ranked) == 5
        # Canonical optimization contract (Phase 5): ranking uses the
        # BEST-SUPPORTED modeled incentive (MU reaches 40%, not its 30% floor)
        # AND normalizes the off-budget MU in-kind post — every non-MU-post
        # structure absorbs the replacement cost. Net result: staying in
        # Mauritius (baseline) is the global optimum, not relocating to Greece.
        assert ranked[0]["structure_id"] == "ALLOC-BASELINE-MU"
        assert ranked[0]["inkind_replacement_delta_usd"] == 0.0
        npcs = [r["npc_with_adjustments_usd"] for r in ranked]
        assert npcs == sorted(npcs)  # strictly ascending NPC

    def test_fx_basis_served_real_and_differentiated_per_structure(self):
        # FX is real per-structure economics, not decorative metadata: every
        # fully-priced structure carries its own sourced rate/currency/
        # source/date (never fabricated), and it differs by jurisdiction
        # currency (MUR vs EUR) — proving it is not a single hardcoded value.
        out = self._out()
        by_id = {p["structure_id"]: p for p in out["structures"]}
        mu = by_id["ALLOC-BASELINE-MU"]
        gr = by_id["ALLOC-RELOC-GR"]
        assert mu["is_fully_priced"] and gr["is_fully_priced"]
        assert mu["fx_basis"]["local_currency"] == "MUR"
        assert gr["fx_basis"]["local_currency"] == "EUR"
        assert mu["fx_basis"]["rate_used"] != gr["fx_basis"]["rate_used"]
        for p in (mu, gr):
            assert p["fx_basis"]["rate_source"] == "live"
            assert p["fx_basis"]["rate_date"]
            assert p["fx_basis"]["note"]
            # fx_delta_usd == 0.0 under the default (no currency-stress)
            # economics controls is the honest answer, not a missing field.
            assert p["fx_delta_usd"] == 0.0
        # Never priced -> never fabricated: no FX basis for a blocked
        # structure (e.g. a component route below its program's min spend).
        blocked = [p for p in out["structures"] if not p["is_fully_priced"]]
        assert blocked  # sanity: this fixture always has at least one
        for p in blocked:
            assert p["fx_basis"] is None
            assert p["fx_delta_usd"] is None
