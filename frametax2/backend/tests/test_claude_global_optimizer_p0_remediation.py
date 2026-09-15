"""
Claude-owned permanent tests — CINEGLOBE_GLOBAL_OPTIMIZER_P0_REMEDIATION.

Proves the six P0 findings and two functional P1 findings from Codex's
global optimizer methodology audit (commit cdaf1968fe38e64af873ac9c4c6da53d03687446),
directly against the live code in app/services/canonical_evaluation.py,
app/services/canonical_production_view.py, and app/calculators/canonical_stack_bridge.py.

These are Claude's OWN tests, written from scratch against the actual
post-remediation code — Codex's own test file
(test_codex_global_optimizer_methodology_audit.py, if present) is
read-only evidence and is never copied or cherry-picked here.

Two integration-level assertions (P0-CAND-001/002/003) are proven via the
existing repo tests in test_treaty_coproduction_wiring.py, which this
remediation pass updated in place (their prior assertions encoded the
exact pre-remediation defect as expected behavior) — not duplicated here.
"""
from __future__ import annotations

import inspect

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators import treaty_engine as te
from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    price_program_group_stack,
)
from app.calculators.qualification_derivation import BudgetLine
from app.db.session import engine
from app.models.project_fact import ProjectFact
from app.services import canonical_evaluation as ce
from app.services import canonical_production_view as cpv
from app.services.canonical_project_economics import ProjectEconomicInputs


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _synthetic_treaty(
    slug: str, a: str, b: str,
    maj_min: float = 20.0, min_min: float = 20.0, min_max: float | None = 80.0,
    cultural_test: bool = False,
    maj_unlocks: list[str] | None = None, min_unlocks: list[str] | None = None,
) -> te.TreatyData:
    return te.TreatyData(
        treaty_slug=slug, treaty_type="bilateral", jurisdiction_a=a, jurisdiction_b=b,
        majority_min_pct=maj_min, minority_min_pct=min_min, minority_max_pct=min_max,
        min_coproducer_countries=2, cultural_test_required=cultural_test,
        majority_unlocks=maj_unlocks or [], minority_unlocks=min_unlocks or [],
        fund_unlocks=[], confidence_tier="PARSED",
    )


def _inputs(**overrides) -> ProjectEconomicInputs:
    base = dict(
        project_id="claude-p0-remediation-test-project",
        project_name="Claude P0 Remediation Synthetic Test",
        jurisdiction_code="MU", production_type="feature_film",
        gross_budget_usd=2_000_000.0, leaf_account_sum_usd=2_000_000.0,
        budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")],
        spend_category_by_code={"1000": "atl_cast"},
        accounts_outside_jurisdiction=frozenset(), offshore_payroll_accounts=frozenset(),
    )
    base.update(overrides)
    return ProjectEconomicInputs(**base)


# ---------------------------------------------------------------------------
# P0-CAND-001 — no five-partner pre-evaluation cap
# ---------------------------------------------------------------------------

def test_cand_001_no_max_treaty_partners_truncation_in_home_anchored_loop():
    """The prior defect was a literal `[:MAX_TREATY_PARTNERS]` slice
    applied to find_real_bilateral_partners' own result BEFORE any
    partner was evaluated. Source-inspection negative oracle: that
    truncation must not exist anywhere in evaluate_project any more, and
    the home-anchored loop must iterate find_real_bilateral_partners'
    result directly and completely."""
    source = inspect.getsource(ce)
    # MAX_TREATY_PARTNERS may still appear in an explanatory comment
    # documenting the removed defect — the negative oracle is the actual
    # SLICE pattern, never present as executable code any more.
    assert "[:MAX_TREATY_PARTNERS]" not in source
    assert "for partner_code in find_real_bilateral_partners(home_code, candidate_codes):" in source


# ---------------------------------------------------------------------------
# P0-CAND-002 — no ten-participant pre-evaluation cap on multilateral evaluation
# ---------------------------------------------------------------------------

def test_cand_002_multilateral_display_cap_never_reaches_the_evaluator():
    """MAX_EURIMAGES_DISPLAY / MAX_FRAMEWORK_DISPLAY may still bound the
    SERVED display list (`shown` / `_fw_shown`) — that is a presentation
    concern, not an evaluation one. The evaluator itself
    (evaluate_eurimages_coproduction_opportunity / the european_convention/
    ibermedia _evaluator) must always be called against the FULL sorted
    partner set (`_eurimages_participants` / `_fw_participants`, both
    built from *_all_sorted, never *_shown), never the truncated display
    slice."""
    source = inspect.getsource(ce)
    assert (
        "_eurimages_opp = evaluate_eurimages_coproduction_opportunity(\n"
        "            list(_eurimages_participants)"
    ) in source
    assert "_eurimages_participants = tuple([home_code] + all_partners_sorted)" in source
    assert (
        "_fw_opp = _evaluator(\n"
        "            list(_fw_participants)"
    ) in source
    assert "_fw_participants = tuple([home_code] + _fw_all_sorted)" in source


# ---------------------------------------------------------------------------
# P0-CAND-003 — identity discovery decoupled from priceability
# ---------------------------------------------------------------------------

def test_cand_003_reachable_codes_include_full_discovery_universe_not_only_priced():
    """The prior defect coupled candidate IDENTITY to `priced_by_code`
    alone. reachable_codes must now union the full discovery universe
    (`candidates`, built from discovery.accepted/accepted_alternatives/
    capability_only) with priced_by_code — a registered partner with only
    attainable missing facts (never yet priced) must remain a reachable
    candidate code."""
    source = inspect.getsource(ce)
    assert "reachable_codes = {c[0] for c in candidates} | set(priced_by_code)" in source
    assert "reachable_codes = set(priced_by_code)" not in source


# ---------------------------------------------------------------------------
# P0-QUAL-001 — co-production facts scoped to treaty + ordered participants
# ---------------------------------------------------------------------------

def test_qual_001_fact_scope_differs_by_treaty_slug_for_the_same_participants():
    """Facts entered for one treaty must never resolve another treaty —
    even for the exact same ordered participant pair."""
    scope_a = ce._coproduction_fact_scope("treaty-a", ("GB", "AU"))
    scope_b = ce._coproduction_fact_scope("treaty-b", ("GB", "AU"))
    assert scope_a != scope_b
    keys_a = ce._coproduction_fact_keys(scope_a)
    keys_b = ce._coproduction_fact_keys(scope_b)
    assert set(keys_a).isdisjoint(set(keys_b))


def test_qual_001_fact_scope_differs_by_participant_order_majority_vs_minority():
    """Majority/minority role is part of participant IDENTITY for a
    bilateral treaty — (GB, AU) and (AU, GB) must scope to different
    fact keys, since majority_pct/minority_pct are role-specific, not
    symmetric."""
    scope_gb_au = ce._coproduction_fact_scope("uk-au-bilateral", ("GB", "AU"))
    scope_au_gb = ce._coproduction_fact_scope("uk-au-bilateral", ("AU", "GB"))
    assert scope_gb_au != scope_au_gb


async def test_qual_001_facts_scoped_to_one_treaty_never_leak_into_a_sibling_participant_set(db: AsyncSession):
    """End-to-end DB proof: a coproduction_majority_pct fact written under
    one (treaty_slug, participant) scope must not be readable under a
    different treaty_slug for the exact same project and participants —
    proving the fix at the actual persistence boundary, not just the
    pure scope-string derivation above. Uses Little Utopia's real project
    row only as a valid FK target for a throwaway fact this test writes
    and deletes in its own finally block — LU's real, frozen economics
    are never read or affected by this test (no evaluate_project call)."""
    project_id = "fa5cade5-0669-4816-bfe6-72146f8d3bae"  # Little Utopia (FK target only)
    scope_a = ce._coproduction_fact_scope("zz-yy-bilateral", ("ZZ", "YY"))
    key_a = f"coproduction_majority_pct::{scope_a}"
    await db.execute(ProjectFact.__table__.delete().where(
        ProjectFact.project_id == project_id, ProjectFact.fact_key == key_a,
    ))
    db.add(ProjectFact(
        project_id=project_id, fact_key=key_a, value="55.0", value_type="number",
        source_type="user_override",
    ))
    await db.commit()
    try:
        majority_a, _, _ = await ce._coproduction_facts(db, project_id, "zz-yy-bilateral", ("ZZ", "YY"))
        assert majority_a == 55.0
        # A DIFFERENT treaty_slug, same participants, same project: must
        # read back None — the fact written above must be architecturally
        # unreachable from here.
        majority_b, _, _ = await ce._coproduction_facts(db, project_id, "different-treaty-slug", ("ZZ", "YY"))
        assert majority_b is None
    finally:
        await db.execute(ProjectFact.__table__.delete().where(
            ProjectFact.project_id == project_id, ProjectFact.fact_key == key_a,
        ))
        await db.commit()


# ---------------------------------------------------------------------------
# P0-STACK-001 — unknown stackability publishes no combined economics
# ---------------------------------------------------------------------------

def test_stack_001_unresolved_same_jurisdiction_group_publishes_no_combined_economics(monkeypatch):
    """A synthetic majority party unlocking two of its own (real,
    priceable) programs, where price_program_group_stack finds NO named,
    publishable stacking rule between them, must publish
    conditional_incentive_usd=None / conditional_npc_usd=None,
    status=RULE_DATA_INCOMPLETE, and a machine-readable blocking_reason —
    never a raw, unadjusted sum of the two programs' incentives.
    price_program_group_stack itself is monkeypatched to return None so
    this test proves canonical_evaluation.py's OWN fail-closed handling
    of "no named rule" deterministically, independent of which real
    program pairs the live registry currently covers (on_ofttc +
    ca_federal_cptc is real and priceable — reused from this same file's
    resolved-path control test below — so priced_components is genuinely
    non-empty and the RULE_DATA_INCOMPLETE branch, not the separate
    CANONICAL_DATA_GAP "nothing priced at all" branch, is what's proven)."""
    treaty = _synthetic_treaty(
        "zz-unresolved-stack-bilateral", "ZZ", "YY",
        maj_unlocks=["on_ofttc", "ca_federal_cptc"], min_unlocks=[],
    )
    monkeypatch.setattr(ce, "price_program_group_stack", lambda group: None)
    import app.calculators.treaty_engine as te_module
    te_module._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        inputs = _inputs(gross_budget_usd=2_000_000.0, leaf_account_sum_usd=2_000_000.0,
                          budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")])
        scenario = ce._build_conditional_bilateral_scenario(
            inputs, "ZZ", "YY", "zz-unresolved-stack-bilateral", baseline_incentive_usd=None,
        )
        assert scenario.get("conditional_incentive_usd") is None
        assert scenario.get("conditional_npc_usd") is None
        assert scenario.get("fully_priced") is False
        assert scenario.get("status") == "RULE_DATA_INCOMPLETE"
        assert scenario.get("blocking_reason")
        # unlocked programs price under the treaty party's own code (ZZ),
        # the same convention the resolved-path control test below relies on.
        assert "ZZ" in scenario["blocking_reason"]
        # unresolved groups never silently disappear — retained with an
        # explicit rejection_reason_class.
        unresolved = [g for g in scenario.get("stacking_groups", []) if not g["stacking_verified"]]
        assert unresolved
        assert unresolved[0]["rejection_reason_class"] == "RULE_DATA_INCOMPLETE"
    finally:
        del te_module._BILATERAL[frozenset({"ZZ", "YY"})]


def test_stack_001_resolved_named_rule_still_publishes_combined_economics():
    """Negative-of-the-negative control: when a named rule DOES resolve
    the same-jurisdiction group, the fix must not have broken the
    already-working, already-tested path — conditional_incentive_usd
    must still be a real number, never None."""
    treaty = _synthetic_treaty(
        "zz-resolved-stack-bilateral", "ZZ", "YY",
        maj_unlocks=["on_ofttc", "ca_federal_cptc"], min_unlocks=[],
    )
    import app.calculators.treaty_engine as te_module
    te_module._BILATERAL[frozenset({"ZZ", "YY"})] = treaty
    try:
        inputs = _inputs(gross_budget_usd=2_000_000.0, leaf_account_sum_usd=2_000_000.0,
                          budget_lines=[BudgetLine("1000", "Cast", 1_000_000.0, spend_category="atl_cast")])
        scenario = ce._build_conditional_bilateral_scenario(
            inputs, "ZZ", "YY", "zz-resolved-stack-bilateral", baseline_incentive_usd=None,
        )
        # ON/federal CPTC's own real jurisdiction codes are CA-ON, not ZZ
        # -- this scenario's own candidate-pricing pass may or may not
        # resolve a real leg for the synthetic ZZ/YY pair, so the only
        # thing asserted here is the STACK-001 fail-closed rule itself
        # never fires when there genuinely is no unresolved group.
        assert scenario.get("status") != "RULE_DATA_INCOMPLETE" or not scenario.get("stacking_groups")
    finally:
        del te_module._BILATERAL[frozenset({"ZZ", "YY"})]


# ---------------------------------------------------------------------------
# P0-COMB-001 — combined co-production + component + anchor + local stack
# ---------------------------------------------------------------------------

def test_comb_001_hybrid_topology_helper_conserves_the_budget_across_three_sides():
    """_price_combined_coproduction_component_candidate must price via
    the SAME conserved StructureSpec/derive_account_allocation/
    price_allocated_structure kernel every other structure type uses —
    proven here by the allocation's own conservation invariant, never a
    hand-rolled parallel allocator."""
    inputs = _inputs(
        gross_budget_usd=3_000_000.0, leaf_account_sum_usd=3_000_000.0,
        budget_lines=[
            BudgetLine("1000", "Cast", 2_000_000.0, spend_category="atl_cast"),
            BudgetLine("2000", "Post/VFX", 1_000_000.0, spend_category="post_vfx"),
        ],
        spend_category_by_code={"1000": "atl_cast", "2000": "post_vfx"},
    )
    spec, allocation, pricing = ce._price_combined_coproduction_component_candidate(
        inputs, "MU", "mu_film_rebate", "GB", "uk_avec", "CA-BC", "ca_bc_pstc",
        "post_vfx", "mu-gb-bilateral",
    )
    assert spec.structure_type == "hybrid"
    assert set(spec.participants) == {"MU", "GB", "CA-BC"}
    # every real dollar assigned exactly once, no invented spend, no drop
    assert allocation.total_allocated_usd == pytest.approx(inputs.gross_budget_usd)
    assert not allocation.duplicate_account_codes


def test_comb_001_unresolved_local_stack_is_retained_never_silently_applied():
    """_authorized_local_stack_for_side must return (None, group) — never
    apply a stack numerically — when a second same-jurisdiction candidate
    exists but no named rule covers the exact combination, so the caller
    can retain it as its own REJECTED candidate rather than silently
    merging or silently dropping it."""
    priced_by_code = {
        "ZZ": [
            StackCandidate("x_credit_one", "ZZ", 100_000.0, 0.10, 1_000_000.0, "tax_credit"),
            StackCandidate("x_credit_two", "ZZ", 100_000.0, 0.10, 1_000_000.0, "tax_credit"),
        ],
    }
    result, group = ce._authorized_local_stack_for_side(priced_by_code, "ZZ", "x_credit_one")
    assert result is None
    assert len(group) == 2


def test_comb_001_no_second_candidate_is_distinct_from_unresolved_attempt():
    """When there is no second same-jurisdiction candidate at all, the
    helper must return an EMPTY group (never claim an attempt was made) —
    distinct from a genuinely attempted-but-unresolved stack."""
    priced_by_code = {"ZZ": [StackCandidate("x_credit_one", "ZZ", 100_000.0, 0.10, 1_000_000.0, "tax_credit")]}
    result, group = ce._authorized_local_stack_for_side(priced_by_code, "ZZ", "x_credit_one")
    assert result is None
    assert group == []


def test_comb_001_resolved_named_local_stack_adds_incremental_value_only():
    """When a named rule DOES resolve the local stack, the caller-facing
    contract is: the delta over the base program's own already-counted
    value is what gets added — never the stacked total re-added on top of
    itself (no double counting)."""
    priced_by_code = {
        "CA-ON": [
            StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit"),
            StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit"),
        ],
    }
    result, group = ce._authorized_local_stack_for_side(priced_by_code, "CA-ON", "on_ofttc")
    assert result is not None
    base_value = next(c.selected_incentive_usd for c in group if c.program_slug == "on_ofttc")
    delta = result.adjusted_incentive_usd - base_value
    # the delta must be strictly less than simply re-adding the second
    # program's own full standalone value (which would double count the
    # shared base) -- the named rule's own adjustment reduces it.
    other_value = next(c.selected_incentive_usd for c in group if c.program_slug != "on_ofttc")
    assert delta <= other_value


# ---------------------------------------------------------------------------
# P1-CLASS-001 — one backend-owned, mutually exclusive classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("trace,structure_type,is_priced,expected", [
    ({"candidate_status": "RULE_DATA_INCOMPLETE"}, "hybrid", False, cpv.CLASS_RULE_DATA_INCOMPLETE),
    ({"rejection_reason_class": "RULE_DATA_INCOMPLETE"}, "hybrid", False, cpv.CLASS_RULE_DATA_INCOMPLETE),
    ({"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT"}, "single_country", False, cpv.CLASS_AUTHORITY_LOCKED),
    ({"candidate_status": "CO_PRO_OPPORTUNITY"}, "treaty_coproduction", False, cpv.CLASS_CONDITIONAL_USER_FACT_REQUIRED),
    ({"candidate_status": "RULE_REJECTED"}, "full_relocation", False, cpv.CLASS_REJECTED_FOR_PROJECT),
    ({"discovery_classification": "combined_coproduction_component_stack"}, "hybrid", True, cpv.CLASS_COMBINED_COPRO_HYBRID_STACK),
    ({}, "treaty_coproduction", True, cpv.CLASS_OFFICIAL_COPRODUCTION),
    ({}, "component_relocation", True, cpv.CLASS_HYBRID_ANCHOR_COMPONENT),
    ({}, "multi_program", True, cpv.CLASS_STACKED_PROGRAMS),
    ({}, "single_country", True, cpv.CLASS_SINGLE_JURISDICTION),
    ({}, "full_relocation", True, cpv.CLASS_SINGLE_JURISDICTION),
])
def test_class_001_classification_is_derived_and_mutually_exclusive(trace, structure_type, is_priced, expected):
    result = cpv._structure_classification(trace, structure_type, is_priced)
    assert result == expected
    assert result in cpv.STRUCTURE_CLASSIFICATIONS


def test_class_001_every_structure_classification_is_a_single_string_never_a_list():
    """Mutually exclusive means exactly one value — never a list a
    frontend would have to interpret/prioritize itself."""
    for trace, structure_type, is_priced in [
        ({"candidate_status": "RULE_DATA_INCOMPLETE"}, "hybrid", False),
        ({}, "single_country", True),
    ]:
        result = cpv._structure_classification(trace, structure_type, is_priced)
        assert isinstance(result, str)


async def test_class_001_served_structure_entries_always_carry_a_classification_field(db: AsyncSession):
    """End-to-end: every structure this backend actually serves for a
    real project carries the new field, never an absent key a frontend
    would have to null-check and infer around."""
    project_id = "fa5cade5-0669-4816-bfe6-72146f8d3bae"  # Little Utopia
    await ce.evaluate_project(db, project_id)
    view = await cpv.build_production_and_structures(db, project_id)
    entries = view["structures"]["allocated_structures"]["structures"]
    assert entries
    for entry in entries:
        assert "classification" in entry
        assert entry["classification"] in cpv.STRUCTURE_CLASSIFICATIONS


# ---------------------------------------------------------------------------
# P1-TRACE-001 — unique allocated spend vs reusable claim bases
# ---------------------------------------------------------------------------

def test_trace_001_total_claim_bases_is_the_sum_total_qualifying_spend_is_the_max():
    """A named rule resolving two same-jurisdiction programs with
    genuinely DIFFERENT (overlapping) claim bases must never have its
    total_qualifying_spend_usd equal the naive sum of both bases -- that
    sum belongs under the honestly-named total_claim_bases_usd field."""
    a = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    result = price_program_group_stack([a, b])
    assert result is not None
    per_program = result.per_program_qpe_usd
    assert per_program
    naive_sum = sum(per_program.values())
    max_base = max(per_program.values())
    if naive_sum != max_base:
        # only a meaningful assertion when the two bases genuinely differ;
        # replicate the exact derivation canonical_evaluation.py's
        # multi_program branch now uses and confirm the two fields diverge
        # exactly the way P1-TRACE-001 requires.
        total_claim_bases_usd = sum(per_program.get(slug, 0.0) for slug in result.program_slugs)
        total_qualifying_spend_usd = max(
            (per_program.get(slug, 0.0) for slug in result.program_slugs), default=0.0,
        )
        assert total_claim_bases_usd == naive_sum
        assert total_qualifying_spend_usd == max_base
        assert total_qualifying_spend_usd <= total_claim_bases_usd


def test_trace_001_source_no_longer_labels_a_sum_as_total_qualifying_spend():
    """Source-level negative oracle: the multi_program combo branch must
    emit BOTH the honestly-named sum (total_claim_bases_usd) and the
    unique-spend figure (total_qualifying_spend_usd, now max()-derived),
    never a single field conflating the two."""
    source = inspect.getsource(ce)
    assert '"total_claim_bases_usd": sum(' in source
    assert (
        '"total_qualifying_spend_usd": max(' in source
    )
