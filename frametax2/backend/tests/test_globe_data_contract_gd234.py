"""
CINEGLOBE_ACCOUNT_HANDOFF_GD234_REMEDIATION -- Claude-owned permanent tests.

Proves GD-2/GD-3/GD-4 from docs/validation/CODEX_OPTIMIZER_GLOBE_DATA_CONTRACT_DELTA.md
(audited at SHA 08060f99e7c0faa036bd5ad3fb9e13ec75f885a3) directly against the live code
in app/services/canonical_production_view.py, app/services/candidate_retention.py, and
app/services/candidate_aggregation.py.

Synthetic only -- no DB, no cold evaluation of a real production. Every fixture here is a
plain in-memory object built by this file, never a fixture reused from another lineage.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.services import candidate_aggregation as ca
from app.services import candidate_retention as cr
from app.services import canonical_production_view as cpv


def _fake_structure(sid: str, *, name: str = "fake", claimed=None, allocations=None):
    return SimpleNamespace(
        id=sid, name=name, description="synthetic fixture",
        claimed_program_ids=claimed or [], jurisdiction_allocations=allocations or [],
    )


def _fake_result(*, trace: dict, structure_type: str, npc: float | None, incentive: float | None):
    return SimpleNamespace(
        calculation_trace_json=trace, structure_type=structure_type,
        true_net_cost_usd=npc, risk_adjusted_net_cost_usd=npc,
        total_incentive_value_usd=incentive, warnings=[],
    )


# ---------------------------------------------------------------------------
# GD-2 -- every canonical family is classified; ordinary hybrids are never
# SINGLE_JURISDICTION. (Table-driven cases already added to
# test_claude_global_optimizer_p0_remediation.py's test_class_001 table --
# this file adds the cross-cutting invariants the delta audit's own six-item
# matrix requires.)
# ---------------------------------------------------------------------------

_ALL_STRUCTURAL_FAMILIES = (
    "ordinary_component_hybrid",
    "combined_coproduction_pair_stack",
    "combined_coproduction_component_stack",
    "combined_coproduction_multi_component_stack",
    "combined_multilateral_coproduction_stack",
)


def test_gd2_every_structural_family_is_classified_and_never_the_generic_default():
    """Every real, persisted structural_family value the structural
    generator emits under structure_type="hybrid" resolves to a real,
    non-default classification -- never silently falls through to
    SINGLE_JURISDICTION (the exact GDC-001 defect)."""
    for family in _ALL_STRUCTURAL_FAMILIES:
        result = cpv._structure_classification({"structural_family": family}, "hybrid", True)
        assert result != cpv.CLASS_SINGLE_JURISDICTION, family
        assert result in cpv.STRUCTURE_CLASSIFICATIONS


def test_gd2_combined_and_multilateral_families_are_distinguishable():
    """The delta audit explicitly requires 'multi-principal/multilateral'
    to be its own family, distinct from the pair/component/multi-component
    combined co-production families -- never folded into one bucket."""
    multilateral = cpv._structure_classification(
        {"structural_family": "combined_multilateral_coproduction_stack"}, "hybrid", True,
    )
    for family in (
        "combined_coproduction_pair_stack",
        "combined_coproduction_component_stack",
        "combined_coproduction_multi_component_stack",
    ):
        combined = cpv._structure_classification({"structural_family": family}, "hybrid", True)
        assert combined == cpv.CLASS_COMBINED_COPRO_HYBRID_STACK
        assert combined != multilateral
    assert multilateral == cpv.CLASS_MULTI_PRINCIPAL_MULTILATERAL


# ---------------------------------------------------------------------------
# GD-3 -- participant jurisdictions exactly match routed jurisdictions.
# ---------------------------------------------------------------------------

def test_gd3_ordinary_hybrid_participants_exactly_match_routed_jurisdictions():
    """A three-jurisdiction ordinary hybrid (anchor + two routed
    components) must serve all three jurisdictions in `participants` --
    the exact defect the delta audit found on all four real productions
    (served only the anchor, e.g. `participants=["CA-MB"]`)."""
    trace = {
        "candidate_status": "PRICED",
        "structural_family": "ordinary_component_hybrid",
        "structure_type": "hybrid",
        "primary_jurisdiction": "CA-MB",
        "anchor_jurisdiction": "CA-MB",
        "anchor_program": "ca_mb_film_tax_credit",
        "program_slugs": ["ca_mb_film_tax_credit", "nz_screen_grant", "it_tax_credit"],
        "jurisdiction_codes": ["CA-MB", "NZ", "IT"],
        "component_allocations": [
            {"component": "post", "jurisdiction_code": "NZ", "program_slug": "nz_screen_grant", "allocated_usd": 500_000.0},
            {"component": "vfx", "jurisdiction_code": "IT", "program_slug": "it_tax_credit", "allocated_usd": 300_000.0},
        ],
        "is_baseline": False,
    }
    structure = _fake_structure("s-ordinary-hybrid")
    result = _fake_result(trace=trace, structure_type="hybrid", npc=1_000_000.0, incentive=400_000.0)
    entry = cpv._empty_structure_entry(structure, result, jurisdiction_code_by_id={})
    assert set(entry["participants"]) == {"CA-MB", "NZ", "IT"}


def test_gd3_combined_pair_stack_participants_include_treaty_partner_and_routed_component():
    """A combined co-production pair-stack candidate (treaty partner +
    one routed component beyond the two treaty parties) must serve all
    three real jurisdictions."""
    trace = {
        "candidate_status": "PRICED",
        "structural_family": "combined_coproduction_pair_stack",
        "structure_type": "hybrid",
        "primary_jurisdiction": "CA-MB",
        "anchor_jurisdiction": "CA-MB",
        "anchor_program": "ca_mb_film_tax_credit",
        "treaty_slug": "ca-fr-bilateral",
        "coproduction_partners": [
            {"jurisdiction_code": "CA-MB", "allocated_usd": 700_000.0},
            {"jurisdiction_code": "FR", "allocated_usd": 300_000.0},
        ],
        "component_allocations": [
            {"component": "post", "jurisdiction_code": "IT", "program_slug": "it_tax_credit", "allocated_usd": 200_000.0},
        ],
        "is_baseline": False,
    }
    structure = _fake_structure("s-combined-pair")
    result = _fake_result(trace=trace, structure_type="hybrid", npc=900_000.0, incentive=450_000.0)
    entry = cpv._empty_structure_entry(structure, result, jurisdiction_code_by_id={})
    assert set(entry["participants"]) == {"CA-MB", "FR", "IT"}


def test_gd3_unpriced_hybrid_never_fabricates_participants_from_an_attempted_route():
    """A REJECTED hybrid candidate's component_allocations describe an
    ATTEMPTED route, never a real economic claim -- the primary jurisdiction
    fallback claim signal must not fire for a non-priced row."""
    trace = {
        "candidate_status": "RULE_REJECTED",
        "rejection_reason_class": "THRESHOLD_NOT_MET",
        "structural_family": "ordinary_component_hybrid",
        "structure_type": "hybrid",
        "primary_jurisdiction": "CA-MB",
        "anchor_jurisdiction": "CA-MB",
        "anchor_program": "ca_mb_film_tax_credit",
        "component_allocations": [
            {"component": "post", "jurisdiction_code": "NZ", "program_slug": "nz_screen_grant", "allocated_usd": 500_000.0},
        ],
        "is_baseline": False,
    }
    structure = _fake_structure("s-rejected-hybrid")
    result = _fake_result(trace=trace, structure_type="hybrid", npc=None, incentive=None)
    entry = cpv._empty_structure_entry(structure, result, jurisdiction_code_by_id={})
    assert entry["is_fully_priced"] is False
    assert "NZ" not in entry["participants"]


def test_gd3_component_relocation_participants_unchanged_already_correct():
    """component_relocation's existing segments-based participant
    derivation ("already correct -- do not reopen" per the delta audit)
    must be unaffected by broadening the branch to also cover "hybrid"."""
    trace = {
        "candidate_status": "PRICED",
        "structure_type": "component_relocation",
        "primary_jurisdiction": "MU",
        "segments": [
            {"jurisdiction_code": "MU", "claims_incentive": True},
            {"jurisdiction_code": "US", "claims_incentive": False},
        ],
        "is_baseline": False,
    }
    structure = _fake_structure("s-component-relocation")
    result = _fake_result(trace=trace, structure_type="component_relocation", npc=500_000.0, incentive=200_000.0)
    entry = cpv._empty_structure_entry(structure, result, jurisdiction_code_by_id={})
    assert entry["participants"] == ["MU"]


# ---------------------------------------------------------------------------
# GD-4 -- bounded retention preserves a per-structural-family winner, not
# only a per-structure_type winner; the served block honestly discloses an
# empty family.
# ---------------------------------------------------------------------------

def _held(seq, sid, *, npc, family, stype="hybrid"):
    return cr.Held(
        seq, _fake_structure(sid), _fake_result(trace={}, structure_type=stype, npc=npc, incentive=npc / 2),
        npc=npc, adjusted=npc, incentive=npc / 2, identity=f"identity-{sid}", stype=stype,
        jurisdiction="", refs=[sid], baseline=False, family=family,
    )


def test_gd4_family_winner_survives_aggregation_even_when_squeezed_by_a_different_familys_type_lane():
    """Every family sharing structure_type="hybrid" competes for the same
    per-type lane -- without a dedicated per-family lane, a combined or
    multilateral candidate can be evicted purely because an UNRELATED
    ordinary-hybrid candidate has a better NPC. type_top=1/global_top=1
    forces exactly this contention deterministically."""
    br = cr.BoundedRetention(global_top=1, type_top=1, jurisdiction_top=1)
    ordinary_best = _held(1, "ordinary-best", npc=10.0, family="ordinary_component_hybrid")
    ordinary_worse = _held(2, "ordinary-worse", npc=20.0, family="ordinary_component_hybrid")
    combined_pair = _held(3, "combined-pair", npc=15.0, family="combined_coproduction_pair_stack")
    multilateral = _held(4, "multilateral", npc=25.0, family="combined_multilateral_coproduction_stack")

    dropped: list[cr.Held] = []
    for h in (ordinary_best, ordinary_worse, combined_pair, multilateral):
        dropped.extend(br.consider(h))
    retained, to_aggregate = br.finalize()
    dropped.extend(to_aggregate)

    retained_ids = {h.structure.id for h in retained}
    aggregated_ids = {h.structure.id for h in dropped}

    # The combined-pair and multilateral candidates are each their family's
    # ONLY member -- each must survive via its own family lane even though
    # neither would win the shared type("hybrid")/global lane against
    # ordinary_best (npc=10.0).
    assert "combined-pair" in retained_ids
    assert "multilateral" in retained_ids
    assert "ordinary-best" in retained_ids
    # ordinary_worse loses on every axis (global, type, and its OWN family
    # lane, which ordinary_best already occupies) -- it is the one real
    # candidate this fixture expects to be aggregated away.
    assert "ordinary-worse" in aggregated_ids
    assert "ordinary-worse" not in retained_ids

    dominating = br.dominating_by_family
    assert dominating["ordinary_component_hybrid"] == "ordinary-best"
    assert dominating["combined_coproduction_pair_stack"] == "combined-pair"
    assert dominating["combined_multilateral_coproduction_stack"] == "multilateral"


def test_gd4_aggregate_group_dominator_prefers_the_family_winner_over_the_type_winner():
    """An aggregated candidate's `dominating_structure_id` must be reconciled
    against ITS OWN family's winner, never a different family's winner that
    happens to share the same broad structure_type -- the exact GDC-002
    'aggregate groups... reconciled against the family winner' requirement."""
    aggregator = ca.CandidateAggregator()
    aggregated_trace = {
        "candidate_status": "RULE_REJECTED",
        "rejection_reason_class": "THRESHOLD_NOT_MET",
        "structural_family": "combined_multilateral_coproduction_stack",
        "structure_type": "hybrid",
        "primary_jurisdiction": "CA-MB",
    }
    aggregator.observe(
        seq=1, status="RULE_REJECTED", structure_type="hybrid", trace=aggregated_trace,
        warnings=[], structure=_fake_structure("agg-1"),
    )
    rows = list(aggregator.rows(
        dominating_by_type={"hybrid": "ordinary-best"},
        dominating_by_family={
            "combined_multilateral_coproduction_stack": "multilateral-best",
            "ordinary_component_hybrid": "ordinary-best",
        },
    ))
    assert len(rows) == 1
    # RULE_REJECTED groups never carry a dominating_structure_id at all
    # (only PRICED groups do) -- confirm that invariant is untouched, then
    # prove the family-precedence directly on a PRICED group below.
    assert rows[0]["dominating_structure_id"] is None

    aggregator_priced = ca.CandidateAggregator()
    priced_trace = dict(aggregated_trace, candidate_status="PRICED", rejection_reason_class=None)
    aggregator_priced.observe(
        seq=1, status="PRICED", structure_type="hybrid", trace=priced_trace,
        warnings=[], structure=_fake_structure("agg-2"), npc=999.0, incentive=1.0, identity="agg-2-identity",
    )
    priced_rows = list(aggregator_priced.rows(
        dominating_by_type={"hybrid": "ordinary-best"},
        dominating_by_family={
            "combined_multilateral_coproduction_stack": "multilateral-best",
            "ordinary_component_hybrid": "ordinary-best",
        },
    ))
    assert len(priced_rows) == 1
    # Must pick the MULTILATERAL family's own winner, never the generic
    # "hybrid" type winner (which is a different family's candidate).
    assert priced_rows[0]["dominating_structure_id"] == "multilateral-best"


def test_gd4_aggregate_group_falls_back_to_type_dominator_when_family_has_none():
    """A group with no real structural_family (every non-hybrid
    structure_type, unchanged behavior) still resolves its dominator from
    the type-level map exactly as before this remediation."""
    aggregator = ca.CandidateAggregator()
    trace = {"candidate_status": "PRICED", "structure_type": "multi_program", "primary_jurisdiction": "US-NY"}
    aggregator.observe(
        seq=1, status="PRICED", structure_type="multi_program", trace=trace,
        warnings=[], structure=_fake_structure("agg-3"), npc=1.0, incentive=1.0, identity="agg-3-identity",
    )
    rows = list(aggregator.rows(dominating_by_type={"multi_program": "stack-best"}, dominating_by_family={}))
    assert rows[0]["dominating_structure_id"] == "stack-best"


def test_gd4_served_family_block_is_pre_seeded_so_an_absent_family_is_an_honest_empty_list():
    """Every priced-eligible canonical family must be a key in the fixed
    family set this module exposes -- the served block's own pre-seeding
    contract (an absent real candidate serves `[]`, never a missing key)."""
    assert cpv.CLASS_MULTI_PRINCIPAL_MULTILATERAL in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_COMBINED_COPRO_HYBRID_STACK in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_HYBRID_ANCHOR_COMPONENT in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_SINGLE_JURISDICTION in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_STACKED_PROGRAMS in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_OFFICIAL_COPRODUCTION in cpv._PRICED_STRUCTURE_FAMILIES
    # Non-priced/blocked classes never compete for a "best priced
    # candidate" family slot -- they must not appear in this set.
    assert cpv.CLASS_CONDITIONAL_USER_FACT_REQUIRED not in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_RULE_DATA_INCOMPLETE not in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_AUTHORITY_LOCKED not in cpv._PRICED_STRUCTURE_FAMILIES
    assert cpv.CLASS_REJECTED_FOR_PROJECT not in cpv._PRICED_STRUCTURE_FAMILIES
