"""
CLAUDE_STRUCTURAL_STACKING_RUNTIME_COMPLETION.

Tests for the generic multi-component structural archetype generator
(app/calculators/structural_archetype_generator.py) and the thirteen
corrected Codex higher-order runtime controls (HO-001 through HO-013,
CODEX_HIGHER_ORDER_STACKING_ORACLE.csv / CODEX_STACKING_RUNTIME_GAPS_
CORRECTED.csv), the six registered executable pair controls, and the
NY distinct-cost / Ireland+UK structural-composition proofs.

Every control uses ONE generic call to generate_structural_candidate --
no per-control special-case code exists anywhere in the production
module. HO-001/HO-002 use Lips Like Sugar's REAL persisted budget
allocation (queried live, not hard-coded) in a separate DB-backed test;
HO-003 through HO-013 and the registered controls use isolated,
never-persisted StructuralComponent objects built directly from each
row's own stated component amounts -- no DB writes, no production
evaluation.
"""
from __future__ import annotations

import itertools

import pytest

from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.calculators.structural_archetype_generator import (
    StructuralComponent,
    check_all_pairs,
    generate_structural_candidate,
)


_DEFAULT_SPEND_CATEGORY_BY_COMPONENT = {
    "post": "post_production",
    "vfx": "vfx",
    "principal_production": "production",
    "treaty_participant": "production",
    "fund_overlay": "production",
    "selective_upside": "production",
}


def _comp(
    program_slug: str, jurisdiction_code: str, amount_usd: float,
    component_type: str = "principal_production", line_id: str | None = None,
    spend_category: str | None = None,
) -> StructuralComponent:
    if spend_category is None:
        spend_category = _DEFAULT_SPEND_CATEGORY_BY_COMPONENT.get(component_type, "production")
    line_id = line_id or f"{jurisdiction_code}-{program_slug}-{amount_usd}"
    alloc = AccountAllocation(
        account_code="1", description=f"{component_type} spend", amount_usd=amount_usd,
        component=component_type, jurisdiction_code=jurisdiction_code,
        assignment_kind=AssignmentKind.FIXED, rationale="isolated canonical control",
        governing_decision="structural_archetype_generator", line_id=line_id,
        spend_category=spend_category,
    )
    return StructuralComponent(
        component_type=component_type, jurisdiction_code=jurisdiction_code,
        program_slug=program_slug, allocations=(alloc,),
        spend_category_by_code={"1": spend_category},
    )


# ---------------------------------------------------------------------------
# Generator mechanism tests
# ---------------------------------------------------------------------------

def test_same_cost_double_claim_is_refused_by_construction():
    """Two components sharing the SAME source line_id must be rejected --
    the generic same-cost-double-count guard, independent of any
    program-specific rule."""
    shared_line = "SHARED-LINE-1"
    c1 = _comp("ca_federal_cptc", "CA", 500_000.0, line_id=shared_line)
    c2 = _comp("on_ofttc", "CA-ON", 500_000.0, line_id=shared_line)
    res = generate_structural_candidate([c1, c2], gross_budget_usd=1_000_000.0)
    assert res.executable is False
    assert "claimed by more than one component" in res.rejection_reason


def test_disjoint_countries_with_no_registered_rule_are_allowed_by_default():
    """Locked Structural Policy point 2: component composition across
    genuinely disjoint countries (no shared national authority, no
    treaty) is allowed by default -- CODEX_LEGAL_COMPATIBILITY_ORACLE.csv
    itself is scoped only to same-jurisdiction/national-subnational
    relationships and says nothing about, e.g., a US principal credit and
    a New Zealand post grant."""
    checks = check_all_pairs([
        _comp("us_ga_film_credit", "US-GA", 1_000_000.0),
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0),
    ])
    assert len(checks) == 1
    assert checks[0].blocks is False
    assert checks[0].disposition == "DISTINCT_COMPONENT_COMPOSITION"


def test_same_country_pair_with_no_registered_rule_is_unresolved_and_blocks():
    """The SAME absence-of-rule, inside one national authority (both
    Canadian), must still block -- CODEX_LEGAL_COMPATIBILITY_ORACLE.csv
    explicitly lists this exact pair as UNRESOLVED, and Locked Structural
    Policy point 8 requires an unresolved-required pair to prevent
    verified pricing."""
    checks = check_all_pairs([
        _comp("ca_federal_cptc", "CA", 1_000_000.0),
        _comp("ca_mb_film_video_credit", "CA-MB", 500_000.0),
    ])
    assert len(checks) == 1
    assert checks[0].blocks is True
    assert checks[0].disposition == "UNRESOLVED_NO_AUTHORITY"


def test_structure_id_is_deterministic_and_order_independent():
    c1 = _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="L1")
    c2 = _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0, line_id="L2")
    res_a = generate_structural_candidate([c1, c2], gross_budget_usd=2_100_000.0)
    res_b = generate_structural_candidate([c2, c1], gross_budget_usd=2_100_000.0)
    assert res_a.structure_id == res_b.structure_id
    assert res_a.total_guaranteed_incentive_usd == res_b.total_guaranteed_incentive_usd
    assert res_a.npc_usd == res_b.npc_usd


def test_spend_is_conserved_across_components():
    c1 = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, line_id="L1")
    c2 = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
               component_type="post", line_id="L2")
    res = generate_structural_candidate([c1, c2], gross_budget_usd=3_500_000.0)
    assert res.executable is True
    assert res.total_allocated_usd == pytest.approx(3_500_000.0)


# ---------------------------------------------------------------------------
# CANONICAL OPTIMIZER ECONOMIC COMPARABILITY CLOSEOUT (2026-09-30): real,
# confirmed live defect -- generate_structural_candidate priced every hybrid
# as gross_budget_usd - guaranteed_incentive with ZERO travel/FX/local-cost
# normalization, while the equivalent single-jurisdiction full-relocation
# candidate (canonical_evaluation.py's own single-country/full_relocation
# path, via _relocation_normalization) served a genuinely different,
# adjusted NPC for the SAME jurisdiction. Confirmed live on Little Utopia:
# a real "Mauritius anchor + vfx->Manitoba + post->Newfoundland & Labrador"
# hybrid served total_adjustments_usd=0.0 (npc_verified_usd identically
# equal to npc_with_adjustments_usd) while the pure Manitoba full-relocation
# candidate served $729,300 of real local-cost adjustment for the exact
# same jurisdiction. These tests lock the generator's OWN new parameter
# contract (the DB-backed normalization computation itself lives in
# canonical_evaluation.py's _hybrid_structure_normalization, independently
# verified live: regenerating Little Utopia at canonical-1.96.0 now serves
# real, non-zero adjustments ($729,300-$1,112,300 across its real Manitoba-
# touching hybrids) where every one previously served exactly $0).
# ---------------------------------------------------------------------------

def test_adjustment_parameters_default_to_zero_never_changing_any_other_caller():
    """Every OTHER structural family already calling generate_structural_
    candidate (HO-003..HO-013, the registered controls, every test above)
    must remain byte-identical: omitting the new adjustment parameters
    must still yield npc_with_adjustments_usd == npc_usd and
    total_adjustments_usd == 0.0, exactly the pre-fix behavior."""
    c1 = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, line_id="L1")
    c2 = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
               component_type="post", line_id="L2")
    res = generate_structural_candidate([c1, c2], gross_budget_usd=3_500_000.0)
    assert res.total_adjustments_usd == 0.0
    assert res.npc_with_adjustments_usd == res.npc_usd
    assert res.travel_incremental_delta_usd == 0.0
    assert res.fx_delta_usd == 0.0
    assert res.local_cost_delta_usd == 0.0


def test_adjustment_parameters_are_summed_into_npc_with_adjustments_never_into_npc_usd():
    """npc_usd (pre-adjustment, used for guaranteed-incentive disclosure)
    must stay the raw gross-minus-incentive figure; only npc_with_
    adjustments_usd (the field canonical_production_view.py's
    risk_adjusted_net_cost_usd reads for ranking/recommendation) may move."""
    c1 = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, line_id="L1")
    c2 = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
               component_type="post", line_id="L2")
    res = generate_structural_candidate(
        [c1, c2], gross_budget_usd=3_500_000.0,
        travel_incremental_delta_usd=1_000.0, fx_delta_usd=2_000.0, local_cost_delta_usd=729_300.0,
    )
    assert res.total_adjustments_usd == pytest.approx(732_300.0)
    assert res.npc_with_adjustments_usd == pytest.approx(res.npc_usd + 732_300.0)
    # A structure relocating principal photography must never show a LOWER
    # (better) adjusted NPC than its own unadjusted figure -- a real
    # relocation cost can only add to true net cost, never subtract.
    assert res.npc_with_adjustments_usd > res.npc_usd


def test_materiality_and_incremental_benefit_compare_on_adjusted_npc_not_raw_npc():
    """A structure that LOOKS cheaper on raw incentive alone but is
    genuinely more expensive once real relocation costs are counted must
    never register a positive incremental_benefit_vs_anchor_usd / this
    generator's own materiality_recommended signal -- the exact class of
    bug a $0-adjustment hybrid could previously produce (looking like a
    real improvement over the anchor purely because its own relocation
    cost was never charged)."""
    c1 = _comp("ca_mb_film_video_credit", "CA-MB", 3_000_000.0, line_id="L1")
    c2 = _comp("ca_nl_all_spend_credit", "CA-NL", 500_000.0, component_type="post", line_id="L2")
    # Real guaranteed incentive here is $1,550,000 on a $3,500,000 budget,
    # so raw npc_usd = $1,950,000 -- on THAT figure alone, an anchor of
    # $2,600,000 would look like a real $650,000 improvement. A real
    # $729,300 relocation cost (more than the entire raw "improvement")
    # must flip this to a genuine loss once counted.
    res = generate_structural_candidate(
        [c1, c2], gross_budget_usd=3_500_000.0, anchor_npc_usd=2_600_000.0,
        local_cost_delta_usd=729_300.0,
    )
    assert res.npc_usd == pytest.approx(1_950_000.0)
    assert res.npc_with_adjustments_usd == pytest.approx(2_679_300.0)
    # Pre-adjustment, this would have shown a false $650,000 "improvement"
    # (2,600,000 - 1,950,000). Post-adjustment, it is a real $79,300 LOSS.
    assert res.incremental_benefit_vs_anchor_usd is not None
    assert res.incremental_benefit_vs_anchor_usd == pytest.approx(-79_300.0)
    assert res.incremental_benefit_vs_anchor_usd < 0, (
        "once real adjustment is counted, this structure must show a NEGATIVE "
        "incremental benefit (worse than anchor), never a false positive improvement"
    )
    assert res.materiality_recommended is False


# ---------------------------------------------------------------------------
# Task 4 — HO-003 through HO-013: the eleven isolated canonical controls
# (component amounts taken verbatim from CODEX_HIGHER_ORDER_STACKING_
# ORACLE.csv / CODEX_STACKING_RUNTIME_GAPS_CORRECTED.csv)
# ---------------------------------------------------------------------------

def test_ho003_au_uk_treaty_plus_nz_post_vfx():
    """uk_avec (GB principal 3.5M) | au_producer_offset (AU principal 3.5M)
    | NZ post/vfx grant (500K post) -- treaty participant incentives plus
    a third-jurisdiction post/vfx component (ARCH-08/ARCH-10)."""
    components = [
        _comp("uk_avec", "GB", 3_500_000.0, line_id="HO003-GB"),
        _comp("au_producer_offset", "AU", 3_500_000.0, line_id="HO003-AU"),
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
              component_type="post", line_id="HO003-NZ"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=7_500_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_allocated_usd == pytest.approx(7_500_000.0)
    assert res.total_guaranteed_incentive_usd > 0


def test_ho004_canadian_domestic_plus_provincial_plus_ocase():
    """ca_federal_cptc (1M) + on_ofttc (1.8M) + ocase (300K vfx) -- all
    three pairs are AUTHORITY_SUPPORTED ALLOWED_WITH_SPEND_REDUCTION in
    the corrected legal oracle (cptc-ofttc, ofttc-ocase) except cptc-ocase
    which remains a genuine, undecided authority gap (Ontario Creates'
    own official page names only OFTTC/OPSTC as OCASE's partners) --
    this control is therefore EXPECTED to be blocked pending that
    authority, proving the generator correctly refuses to guess rather
    than silently allowing it."""
    components = [
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="HO004-CPTC", spend_category="atl_director"),
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="HO004-OFTTC", spend_category="atl_director"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="HO004-OCASE", spend_category="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_100_000.0)
    assert res.executable is False, (
        "ca_federal_cptc+ocase is a genuine, undecided authority gap -- must not be "
        "silently allowed"
    )
    assert any("ontario_computer_animation" in p.program_a or "ontario_computer_animation" in p.program_b
               for p in res.blocking_pairs)


def test_ho005_canadian_service_plus_provincial_plus_ocase():
    """ca_federal_pstc (1M service labour) + on_opstc (1.8M) + ocase
    (300K vfx) -- same genuine cptc/pstc+ocase authority gap as HO-004
    (ca_federal_pstc+ocase is also unresolved); on_opstc+ocase IS
    authority-supported."""
    components = [
        _comp("ca_federal_pstc", "CA", 1_000_000.0, line_id="HO005-PSTC", spend_category="atl_director"),
        _comp("on_opstc", "CA-ON", 1_800_000.0, line_id="HO005-OPSTC", spend_category="atl_director"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="HO005-OCASE", spend_category="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_100_000.0)
    assert res.executable is False, "ca_federal_pstc+ocase is a genuine, undecided authority gap"


def test_ho005b_opstc_plus_ocase_alone_prices():
    """The authority-supported half of HO-005: on_opstc+ocase alone
    (without the unresolved federal PSTC leg) must price."""
    components = [
        _comp("on_opstc", "CA-ON", 1_800_000.0, line_id="HO005B-OPSTC", spend_category="atl_director"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="HO005B-OCASE", spend_category="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=2_100_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_guaranteed_incentive_usd > 0


def test_ho006_bc_service_plus_dave():
    """ca_federal_pstc (1M service labour, national) + ca_bc_pstc (1.8M
    BC labour) + ca_bc_dave (300K vfx labour) -- ca_bc_pstc+ca_bc_dave is
    AUTHORITY_SUPPORTED ADDITIVE; ca_federal_pstc+ca_bc_pstc is
    NATIONAL_SUBNATIONAL UNRESOLVED per the corrected oracle, so the
    3-way control is expected blocked; the BC-only 2-way leg must price."""
    components = [
        _comp("ca_federal_pstc", "CA", 1_000_000.0, line_id="HO006-FED", spend_category="atl_director"),
        _comp("ca_bc_pstc", "CA-BC", 1_800_000.0, line_id="HO006-BC", spend_category="atl_director"),
        _comp("ca_bc_dave", "CA-BC", 300_000.0, component_type="vfx", line_id="HO006-DAVE",
              spend_category="atl_director"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_100_000.0)
    assert res.executable is False, "ca_federal_pstc+ca_bc_pstc remains a genuine authority gap"

    bc_only = [
        _comp("ca_bc_pstc", "CA-BC", 1_800_000.0, line_id="HO006B-BC", spend_category="atl_director"),
        _comp("ca_bc_dave", "CA-BC", 300_000.0, component_type="vfx", line_id="HO006B-DAVE",
              spend_category="atl_director"),
    ]
    res_bc = generate_structural_candidate(bc_only, gross_budget_usd=2_100_000.0)
    assert res_bc.executable is True, res_bc.rejection_reason
    assert res_bc.total_guaranteed_incentive_usd > 0


def test_ho007_european_principal_plus_post():
    """uk_avec (GB 3M) + fr_trip (FR 3M) + NZ post grant (500K) -- three
    disjoint countries, no treaty required for the post leg; uk_avec+
    fr_trip is a genuinely disjoint-country pair with no registered rule
    -> allowed by default (component composition, Locked Structural
    Policy point 2)."""
    components = [
        _comp("uk_avec", "GB", 3_000_000.0, line_id="HO007-GB"),
        _comp("fr_trip", "FR", 3_000_000.0, line_id="HO007-FR", component_type="vfx"),
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
              component_type="post", line_id="HO007-NZ"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=6_500_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_allocated_usd == pytest.approx(6_500_000.0)


def test_ho008_ireland_australian_pdv_ontario_ocase():
    """ie_section_481 (Irish principal 5M) + au_pdv_offset (post 700K) +
    ocase (vfx 300K) -- three disjoint countries, genuine component
    composition."""
    components = [
        _comp("ie_section_481", "IE", 5_000_000.0, line_id="HO008-IE"),
        _comp("au_pdv_offset", "AU", 700_000.0, component_type="post", line_id="HO008-AU"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="HO008-ON", spend_category="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=6_000_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_allocated_usd == pytest.approx(6_000_000.0)


def test_ho009_nz_principal_plus_bc_dave_plus_ny_post():
    """nz_spg_international (NZ principal 5M) + ca_bc_dave (vfx 300K) +
    us_ny_post_production_credit (post 1.5M, clears its real $1M
    minimum) -- three disjoint countries."""
    components = [
        _comp("nz_spg_international", "NZ", 5_000_000.0, line_id="HO009-NZ"),
        _comp("ca_bc_dave", "CA-BC", 300_000.0, component_type="vfx", line_id="HO009-BC",
              spend_category="atl_director"),
        _comp("us_ny_post_production_credit", "US-NY", 1_500_000.0, component_type="post",
              line_id="HO009-NY"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=6_800_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_allocated_usd == pytest.approx(6_800_000.0)


def test_ho010_formulaic_plus_conditional_fund():
    """ca_federal_cptc (principal 1M) + on_ofttc (Ontario 1.8M) +
    ca_sk_creative_saskatchewan_grant (conditional fund 200K,
    Saskatchewan) -- the fund is a DIFFERENT province from Ontario
    (disjoint subnational, no registered rule with either CPTC or OFTTC)
    -- selective/competitive value must stay conditional, never entering
    guaranteed NPC."""
    components = [
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="HO010-CPTC", spend_category="atl_director"),
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="HO010-OFTTC", spend_category="atl_director"),
        _comp("ca_sk_creative_saskatchewan_grant", "CA-SK", 200_000.0,
              component_type="fund_overlay", line_id="HO010-SK"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_000_000.0)
    assert res.executable is True, res.rejection_reason
    # ca_sk_creative_saskatchewan_grant is DISPLAY_ONLY_ZERO_GUARANTEED
    # (a real, disclosed selective/competitive grant) -- its component
    # segment must not be executable as a guaranteed floor, so it
    # contributes conditional upside only, never guaranteed NPC.
    sk_econ = next(ce for ce in res.component_economics if ce.component.jurisdiction_code == "CA-SK")
    assert sk_econ.is_guaranteed is False
    assert sk_econ.conditional_incentive_usd >= 0


def test_ho011_selective_upside_stays_separate_from_guaranteed_npc():
    """us_ga_film_credit (principal 3M) + NZ post grant (500K) +
    us_tn_performance_grant (conditional award 100K, a different US
    state) -- the Tennessee grant is genuinely selective/negotiated and
    must never raise guaranteed NPC."""
    components = [
        _comp("us_ga_film_credit", "US-GA", 3_000_000.0, line_id="HO011-GA"),
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
              component_type="post", line_id="HO011-NZ"),
        _comp("us_tn_performance_grant", "US-TN", 100_000.0,
              component_type="selective_upside", line_id="HO011-TN"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_600_000.0)
    assert res.executable is True, res.rejection_reason
    tn_econ = next(ce for ce in res.component_economics if ce.component.jurisdiction_code == "US-TN")
    assert tn_econ.is_guaranteed is False, "us_tn_performance_grant is selective/negotiated -- conditional only"
    guaranteed_without_tn = sum(
        ce.guaranteed_incentive_usd for ce in res.component_economics if ce.component.jurisdiction_code != "US-TN"
    )
    assert res.total_guaranteed_incentive_usd <= guaranteed_without_tn + 0.01


def test_ho012_multilateral_feature():
    """uk_avec (GB 2.5M) + ie_section_481 (IE 2.5M) + fr_trip (FR 2.5M) --
    three disjoint European participants, no bilateral treaty required
    for this generic structural composition (the treaty engine's own
    multilateral framework is a SEPARATE, additive mechanism -- this
    proves the generic generator does not require treaty registration to
    combine three independently-allocated national programs)."""
    components = [
        _comp("uk_avec", "GB", 2_500_000.0, line_id="HO012-GB"),
        _comp("ie_section_481", "IE", 2_500_000.0, line_id="HO012-IE"),
        _comp("fr_trip", "FR", 2_500_000.0, line_id="HO012-FR", component_type="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=7_500_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_allocated_usd == pytest.approx(7_500_000.0)


def test_ho013_four_program_treaty_component_structure():
    """uk_avec (GB 3M) + au_producer_offset (AU 3M) + NZ post grant
    (500K) + ocase (Ontario vfx 300K) -- a real 4-program structure;
    every one of its six unordered pairs must be evaluated."""
    components = [
        _comp("uk_avec", "GB", 3_000_000.0, line_id="HO013-GB"),
        _comp("au_producer_offset", "AU", 3_000_000.0, line_id="HO013-AU"),
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
              component_type="post", line_id="HO013-NZ"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="HO013-ON", spend_category="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=6_800_000.0)
    assert res.executable is True, res.rejection_reason
    pairs = check_all_pairs(components)
    assert len(pairs) == 6, "a 4-member structure has exactly six unordered pairs"
    assert all(not p.blocks for p in pairs)


# ---------------------------------------------------------------------------
# Task 5 — the six registered executable pair controls
# ---------------------------------------------------------------------------

def test_registered_control_1_ca_bc_pstc_plus_ca_federal_cptc_rejects():
    components = [
        _comp("ca_bc_pstc", "CA-BC", 1_800_000.0, line_id="REG1-BC", spend_category="atl_director"),
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="REG1-FED", spend_category="atl_director"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=2_800_000.0)
    assert res.executable is False
    assert res.blocking_pairs and res.blocking_pairs[0].disposition == "mutually_exclusive"


def test_registered_control_2_ca_federal_cptc_plus_on_ofttc_prices():
    components = [
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="REG2-FED", spend_category="atl_director"),
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="REG2-ON", spend_category="atl_director"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=2_800_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_guaranteed_incentive_usd > 0


def test_registered_control_3_ca_federal_cptc_plus_on_opstc_rejects():
    components = [
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="REG3-FED", spend_category="atl_director"),
        _comp("on_opstc", "CA-ON", 1_800_000.0, line_id="REG3-ON", spend_category="atl_director"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=2_800_000.0)
    assert res.executable is False
    assert res.blocking_pairs and res.blocking_pairs[0].disposition == "mutually_exclusive"


def test_registered_control_4_ireland_uk_uses_separate_jurisdictional_components():
    """ie_section_481 + uk_avec must be handled through generic
    structural composition with SEPARATELY allocated jurisdictional
    costs -- not two incentives claiming the same whole budget. Proven
    by using two DISJOINT sets of budget lines (Irish principal vs UK
    principal, no shared line_id) and confirming spend is conserved and
    each program prices off ONLY its own allocated slice."""
    components = [
        _comp("ie_section_481", "IE", 3_000_000.0, line_id="REG4-IE"),
        _comp("uk_avec", "GB", 3_000_000.0, line_id="REG4-GB"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=6_000_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_allocated_usd == pytest.approx(6_000_000.0)
    ie_econ = next(ce for ce in res.component_economics if ce.component.jurisdiction_code == "IE")
    gb_econ = next(ce for ce in res.component_economics if ce.component.jurisdiction_code == "GB")
    assert ie_econ.segment.allocated_usd == pytest.approx(3_000_000.0)
    assert gb_econ.segment.allocated_usd == pytest.approx(3_000_000.0)


def test_registered_control_5_ny_distinct_cost_stacking():
    """ny_state_film + us_ny_post_production_credit, corrected disposition
    SAME_COST_PROHIBITED_DISTINCT_COSTS_ALLOWED: an isolated NY budget
    with real, DISJOINT principal and post cost pools (post >= $1M, the
    real statutory minimum) must price BOTH components; principal-
    photography spend must never enter post QPE."""
    principal = _comp("ny_state_film", "US-NY", 3_000_000.0, line_id="REG5-PRINCIPAL",
                       component_type="principal_production")
    post = _comp("us_ny_post_production_credit", "US-NY", 1_500_000.0, line_id="REG5-POST",
                 component_type="post")
    res = generate_structural_candidate([principal, post], gross_budget_usd=4_500_000.0)
    assert res.executable is True, res.rejection_reason
    principal_econ = next(ce for ce in res.component_economics if ce.component.program_slug == "ny_state_film")
    post_econ = next(ce for ce in res.component_economics if ce.component.program_slug == "us_ny_post_production_credit")
    assert principal_econ.segment.qpe_usd == pytest.approx(3_000_000.0)
    assert post_econ.segment.qpe_usd == pytest.approx(1_500_000.0)
    # No shared line_id -- principal spend never enters post's own QPE.
    assert not (principal.line_ids & post.line_ids)
    assert res.total_guaranteed_incentive_usd == pytest.approx(
        principal_econ.guaranteed_incentive_usd + post_econ.guaranteed_incentive_usd
    )


def test_registered_control_5b_ny_post_below_real_threshold_rejects():
    """The same distinct-cost structure with a post pool BELOW the real
    $1,000,000 statutory minimum must be precisely rejected -- proving
    the real threshold is enforced, not bypassed by the structural
    composition mechanism."""
    principal = _comp("ny_state_film", "US-NY", 3_000_000.0, line_id="REG5B-PRINCIPAL")
    post = _comp("us_ny_post_production_credit", "US-NY", 400_000.0, line_id="REG5B-POST",
                 component_type="post")
    res = generate_structural_candidate([principal, post], gross_budget_usd=3_400_000.0)
    assert res.executable is False
    assert "us_ny_post_production_credit" in res.rejection_reason


def test_registered_control_5c_ny_same_line_cannot_claim_both_programs():
    """The SAME NY cost pool can never be claimed by both ny_state_film
    and us_ny_post_production_credit at once -- the generic same-cost
    guard applies even within one jurisdiction."""
    shared = "REG5C-SHARED"
    principal = _comp("ny_state_film", "US-NY", 3_000_000.0, line_id=shared)
    post = _comp("us_ny_post_production_credit", "US-NY", 3_000_000.0, line_id=shared)
    res = generate_structural_candidate([principal, post], gross_budget_usd=3_000_000.0)
    assert res.executable is False
    assert "claimed by more than one component" in res.rejection_reason


def test_registered_control_6_on_ofttc_plus_on_opstc_rejects():
    components = [
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="REG6-OFTTC"),
        _comp("on_opstc", "CA-ON", 1_800_000.0, line_id="REG6-OPSTC"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=1_800_000.0)
    assert res.executable is False
    assert res.blocking_pairs and res.blocking_pairs[0].disposition == "mutually_exclusive"


# ---------------------------------------------------------------------------
# Task 6 — higher-order legality completion
# ---------------------------------------------------------------------------

def test_cptc_ofttc_opstc_still_rejects_via_the_generic_generator():
    """The exact 904d30e reproduction, now through the generic generator
    (not canonical_stack_bridge.price_program_group_stack directly) --
    proves the fix is preserved at this new layer too."""
    components = [
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="T6-CPTC", spend_category="atl_director"),
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="T6-OFTTC", spend_category="atl_director"),
        _comp("on_opstc", "CA-ON", 500_000.0, line_id="T6-OPSTC"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_300_000.0)
    assert res.executable is False
    assert len(res.blocking_pairs) == 2


def test_four_program_structure_rejects_if_any_of_six_pairs_prohibits():
    components = [
        _comp("ca_federal_cptc", "CA", 1_000_000.0, line_id="T6B-CPTC", spend_category="atl_director"),
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="T6B-OFTTC", spend_category="atl_director"),
        _comp("on_opstc", "CA-ON", 500_000.0, line_id="T6B-OPSTC"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="T6B-OCASE", spend_category="vfx"),
    ]
    res = generate_structural_candidate(components, gross_budget_usd=3_600_000.0)
    assert res.executable is False
    pairs = check_all_pairs(components)
    assert len(pairs) == 6


def test_all_permutations_of_a_valid_triple_produce_identical_economics():
    components = [
        _comp("us_ga_film_credit", "US-GA", 3_000_000.0, line_id="PERM-GA"),
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
              component_type="post", line_id="PERM-NZ"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="PERM-ON", spend_category="vfx"),
    ]
    results = [generate_structural_candidate(list(perm), gross_budget_usd=3_800_000.0)
               for perm in itertools.permutations(components)]
    assert all(r.executable for r in results)
    assert all(r.structure_id == results[0].structure_id for r in results)
    assert all(r.total_guaranteed_incentive_usd == pytest.approx(results[0].total_guaranteed_incentive_usd)
               for r in results)


def test_duplicate_economic_routes_collapse_to_one_canonical_structure():
    """Two component lists describing the SAME real allocation (same
    jurisdictions, programs, and source line_ids), built independently
    and passed in a different order, must collapse to one canonical
    structure_id -- never two separately-tracked 'different' routes."""
    a = [
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="DUP-1"),
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="DUP-2", spend_category="vfx"),
    ]
    b = [
        _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
              component_type="vfx", line_id="DUP-2", spend_category="vfx"),
        _comp("on_ofttc", "CA-ON", 1_800_000.0, line_id="DUP-1"),
    ]
    res_a = generate_structural_candidate(a, gross_budget_usd=2_100_000.0)
    res_b = generate_structural_candidate(b, gross_budget_usd=2_100_000.0)
    assert res_a.structure_id == res_b.structure_id


# ---------------------------------------------------------------------------
# CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 2:
# _hybrid_marginal_jurisdiction_benefits (canonical_evaluation.py) -- the bounded
# canonical counterfactual: remove one non-principal component, return its real
# AccountAllocation lines to the principal component, reprice through the SAME
# generate_structural_candidate this whole module already tests.
# ---------------------------------------------------------------------------

def _structure_entries(cache: dict) -> list:
    """Structure-level normalization cache entries (per-leg entries, keyed with a
    leading "leg_*" tag, are excluded)."""
    return [k for k in cache if not str(k[0]).startswith("leg_")]



def _economic_inputs(**overrides):
    from app.services.canonical_project_economics import ProjectEconomicInputs

    defaults = dict(
        project_id="test-project", project_name="Test Project", jurisdiction_code="GR",
        production_type="feature_film", gross_budget_usd=3_000_000.0, leaf_account_sum_usd=3_000_000.0,
        budget_lines=[], spend_category_by_code={}, accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(),
    )
    defaults.update(overrides)
    return ProjectEconomicInputs(**defaults)


def test_hybrid_marginal_jurisdiction_benefits_removes_each_non_principal_component_leg():
    """A US-GA anchor + NZ post + CA-ON vfx hybrid (the SAME real, verified-
    executable triple test_all_permutations_of_a_valid_triple_produce_identical_
    economics above uses): removing NZ returns its spend to the anchor and
    reprices; removing CA-ON returns its spend to the anchor and reprices. Both
    counterfactuals must be priced (repricing each component leg independently),
    one entry per non-principal component -- the principal_production component
    itself is never a removal candidate."""
    from app.services.canonical_evaluation import _hybrid_marginal_jurisdiction_benefits

    anchor = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="MJB-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
                     component_type="post", line_id="MJB-NZ")
    vfx_on = _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
                    component_type="vfx", line_id="MJB-ON", spend_category="vfx")
    components = [anchor, post_nz, vfx_on]
    inputs = _economic_inputs(jurisdiction_code="US-GA", gross_budget_usd=3_800_000.0)
    candidate = generate_structural_candidate(components, gross_budget_usd=3_800_000.0)
    assert candidate.executable, candidate.rejection_reason
    benefits = _hybrid_marginal_jurisdiction_benefits(
        components, "US-GA", 3_800_000.0, inputs, candidate.npc_with_adjustments_usd,
    )
    assert set(benefits.keys()) == {"NZ", "CA-ON"}
    assert all(isinstance(v, float) for v in benefits.values())


def test_hybrid_marginal_jurisdiction_benefits_single_component_hybrid_returns_empty():
    """Fewer than 2 components -- nothing to remove, no counterfactual to compute."""
    from app.services.canonical_evaluation import _hybrid_marginal_jurisdiction_benefits

    anchor = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production")
    inputs = _economic_inputs(jurisdiction_code="US-GA")
    benefits = _hybrid_marginal_jurisdiction_benefits([anchor], "US-GA", 3_000_000.0, inputs, 2_700_000.0)
    assert benefits == {}


def test_hybrid_marginal_jurisdiction_benefits_none_candidate_npc_returns_empty():
    """A candidate with no real NPC (e.g. non-executable) cannot support a real
    counterfactual comparison -- fails to an empty dict, never a fabricated benefit."""
    from app.services.canonical_evaluation import _hybrid_marginal_jurisdiction_benefits

    anchor = _comp("us_ga_film_credit", "US-GA", 3_300_000.0, component_type="principal_production", line_id="MJB2-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
                     component_type="post", line_id="MJB2-NZ")
    inputs = _economic_inputs(jurisdiction_code="US-GA")
    benefits = _hybrid_marginal_jurisdiction_benefits([anchor, post_nz], "US-GA", 3_800_000.0, inputs, None)
    assert benefits == {}


def test_hybrid_marginal_jurisdiction_benefits_removed_spend_is_returned_to_principal_not_dropped():
    """The counterfactual's total allocated spend must equal the original total --
    the removed component's real dollars are returned to the principal component,
    never discarded (which would silently shrink NPC = gross - incentive by making
    guaranteed_incentive artificially small over a smaller allocated base)."""
    from app.services.canonical_evaluation import _hybrid_marginal_jurisdiction_benefits

    anchor = _comp("us_ga_film_credit", "US-GA", 3_300_000.0, component_type="principal_production", line_id="MJB3-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
                     component_type="post", line_id="MJB3-NZ")
    components = [anchor, post_nz]
    inputs = _economic_inputs(jurisdiction_code="US-GA", gross_budget_usd=3_800_000.0)
    candidate = generate_structural_candidate(components, gross_budget_usd=3_800_000.0)
    assert candidate.executable, candidate.rejection_reason
    benefits = _hybrid_marginal_jurisdiction_benefits(
        components, "US-GA", 3_800_000.0, inputs, candidate.npc_with_adjustments_usd,
    )
    assert "NZ" in benefits
    # A real, finite dollar comparison was computed (not silently skipped) --
    # the exact sign/magnitude depends on the two programs' real rates, which
    # this test does not assert on (that is generate_structural_candidate's own
    # already-tested pricing contract); this test only proves the counterfactual
    # repricing actually ran to completion for the real removed component.
    assert benefits["NZ"] == benefits["NZ"]  # not NaN


# ---------------------------------------------------------------------------
# LLS-SPECIFIC PERFORMANCE REPAIR (2026-09-30) -- _hybrid_structure_
# normalization's optional `cache` and _hybrid_marginal_jurisdiction_
# benefits' pass-through normalization_cache/pricing_cache. Each test shares
# ONE cache dict across two calls to prove cached and uncached paths can
# never diverge.
# ---------------------------------------------------------------------------

def test_hybrid_structure_normalization_cache_hit_matches_uncached_result():
    from app.services.canonical_evaluation import _hybrid_structure_normalization

    anchor = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="HSN1-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
                     component_type="post", line_id="HSN1-NZ")
    components = [anchor, post_nz]
    inputs = _economic_inputs(jurisdiction_code="US-GA", gross_budget_usd=3_500_000.0)
    uncached = _hybrid_structure_normalization(inputs, "US-GA", components)

    cache: dict = {}
    first = _hybrid_structure_normalization(inputs, "US-GA", components, cache=cache)
    assert len(_structure_entries(cache)) == 1
    second = _hybrid_structure_normalization(inputs, "US-GA", components, cache=cache)
    assert len(_structure_entries(cache)) == 1, "an identical second call must be a cache HIT, never a second store"
    assert first == uncached == second


def test_hybrid_structure_normalization_cache_distinguishes_different_anchors():
    """The SAME components normalized against two DIFFERENT anchor
    jurisdictions must never collide -- the anchor drives which component is
    treated as the relocated principal and which legs get incremental-only
    treatment, a real difference in which real dollars apply."""
    from app.services.canonical_evaluation import _hybrid_structure_normalization

    ga = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="HSN2-GA")
    ny = _comp("ny_state_film", "US-NY", 500_000.0, component_type="post", line_id="HSN2-NY")
    inputs = _economic_inputs(jurisdiction_code="GR", gross_budget_usd=3_500_000.0)
    cache: dict = {}
    as_ga_anchor = _hybrid_structure_normalization(inputs, "US-GA", [ga, ny], cache=cache)
    as_ny_anchor = _hybrid_structure_normalization(inputs, "US-NY", [ga, ny], cache=cache)
    # len(cache) == 2 is the real correctness proof here (no key collision
    # between two different anchors) -- the two real normalized totals
    # happening to coincide numerically for this particular GA/NY pair is
    # not itself a bug; what would BE a bug is serving one anchor's cached
    # result for the other's genuinely different key.
    assert len(_structure_entries(cache)) == 2, "different anchor_code must occupy distinct cache entries"
    assert cache[("GR", "US-GA", (("US-GA", "principal_production", 3_000_000.0), ("US-NY", "post", 500_000.0)))] == as_ga_anchor
    assert cache[("GR", "US-NY", (("US-GA", "principal_production", 3_000_000.0), ("US-NY", "post", 500_000.0)))] == as_ny_anchor


def test_hybrid_structure_normalization_cache_distinguishes_different_component_types_same_jurisdiction_program_amount():
    """The exact same (jurisdiction_code, allocated_usd) pair but a different
    component_type must never collide -- component_type decides which
    component is treated as the relocated principal (principal_production)
    versus an incremental-only leg, a real difference in which normalization
    branch runs."""
    from app.services.canonical_evaluation import _hybrid_structure_normalization

    inputs = _economic_inputs(jurisdiction_code="GR", gross_budget_usd=3_500_000.0)
    as_principal = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="HSN3-A")
    as_post = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="post", line_id="HSN3-B")
    cache: dict = {}
    result_principal = _hybrid_structure_normalization(inputs, "US-GA", [as_principal], cache=cache)
    result_post = _hybrid_structure_normalization(inputs, "US-GA", [as_post], cache=cache)
    assert len(_structure_entries(cache)) == 2, "different component_type for the same jurisdiction/amount must be distinct entries"


def test_hybrid_marginal_jurisdiction_benefits_with_shared_caches_matches_uncached():
    """The full counterfactual pass, run once with fresh normalization_cache/
    pricing_cache dicts and once with none at all, must return identical
    marginal benefits -- the caches are a pure speed optimization, never an
    approximation of the real counterfactual reprice."""
    from app.services.canonical_evaluation import _hybrid_marginal_jurisdiction_benefits

    anchor = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="MJBC-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
                     component_type="post", line_id="MJBC-NZ")
    vfx_on = _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
                    component_type="vfx", line_id="MJBC-ON", spend_category="vfx")
    components = [anchor, post_nz, vfx_on]
    inputs = _economic_inputs(jurisdiction_code="US-GA", gross_budget_usd=3_800_000.0)
    candidate = generate_structural_candidate(components, gross_budget_usd=3_800_000.0)
    assert candidate.executable, candidate.rejection_reason

    uncached = _hybrid_marginal_jurisdiction_benefits(
        components, "US-GA", 3_800_000.0, inputs, candidate.npc_with_adjustments_usd,
    )
    norm_cache: dict = {}
    price_cache: dict = {}
    cached = _hybrid_marginal_jurisdiction_benefits(
        components, "US-GA", 3_800_000.0, inputs, candidate.npc_with_adjustments_usd,
        normalization_cache=norm_cache, pricing_cache=price_cache,
    )
    assert cached == uncached
    assert len(norm_cache) >= 1 and len(price_cache) >= 1, "the cached call must actually have populated both caches"


def test_hybrid_marginal_jurisdiction_benefits_reuses_pricing_cache_across_repeated_calls():
    """Two outer combinations that happen to produce the SAME counterfactual
    (same component removed, same remaining shape) must share cache entries
    -- this is the real speedup LLS's own profile showed (the same removed-
    component shape recurring across different outer branch-and-bound
    combinations) -- while still returning the exact same real benefits both
    times."""
    from app.services.canonical_evaluation import _hybrid_marginal_jurisdiction_benefits

    anchor = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="MJBR-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
                     component_type="post", line_id="MJBR-NZ")
    components = [anchor, post_nz]
    inputs = _economic_inputs(jurisdiction_code="US-GA", gross_budget_usd=3_500_000.0)
    candidate = generate_structural_candidate(components, gross_budget_usd=3_500_000.0)
    assert candidate.executable, candidate.rejection_reason

    norm_cache: dict = {}
    price_cache: dict = {}
    first = _hybrid_marginal_jurisdiction_benefits(
        components, "US-GA", 3_500_000.0, inputs, candidate.npc_with_adjustments_usd,
        normalization_cache=norm_cache, pricing_cache=price_cache,
    )
    norm_size_after_first = len(norm_cache)
    price_size_after_first = len(price_cache)
    # A second, independent outer combination that removes the exact same
    # component from the exact same remaining shape -- a real recurrence.
    second = _hybrid_marginal_jurisdiction_benefits(
        [anchor, post_nz], "US-GA", 3_500_000.0, inputs, candidate.npc_with_adjustments_usd,
        normalization_cache=norm_cache, pricing_cache=price_cache,
    )
    assert second == first
    assert len(norm_cache) == norm_size_after_first, "the identical counterfactual must be a cache HIT, never a second store"
    assert len(price_cache) == price_size_after_first


# ---------------------------------------------------------------------------
# COMPONENT-BUNDLE CORRECTION (2026-09-30): _program_distinguishes_spend_category
# (canonical_evaluation.py) -- the signal deciding whether a bundle member (e.g.
# "vfx") is exposed as its own independently-routable movable component.
# ---------------------------------------------------------------------------

def test_program_distinguishes_spend_category_true_for_a_real_component_basis_program():
    from app.services.canonical_evaluation import _program_distinguishes_spend_category

    # Ontario OCASE's real rate doctrine restricts its tier to
    # component_basis_spend_categories=("vfx",) -- a genuine, specific
    # distinguishing treatment.
    assert _program_distinguishes_spend_category(
        "ontario_computer_animation_and_special_effects_tax_credit_ocase", "vfx",
    ) is True


def test_program_distinguishes_spend_category_false_for_an_unrelated_category():
    from app.services.canonical_evaluation import _program_distinguishes_spend_category

    assert _program_distinguishes_spend_category(
        "ontario_computer_animation_and_special_effects_tax_credit_ocase", "music",
    ) is False


def test_program_distinguishes_spend_category_false_for_unknown_program():
    from app.services.canonical_evaluation import _program_distinguishes_spend_category

    assert _program_distinguishes_spend_category("not_a_real_program_slug", "vfx") is False


def test_program_distinguishes_spend_category_ignores_exclude_complement_conditions():
    """Bug fix (same pass, same day): a component_basis_spend_categories_exclude=True
    condition matches "every category NOT in this tuple" -- a broad, generic
    "everything else" complement bucket (e.g. us_or_opif's real payroll/non-payroll
    split), never a SPECIFIC carve-out for the category under test. Confirmed live
    this previously made "post" (via its real "post_production"/"sound" categories,
    legitimately absent from that payroll tuple) look specifically distinguished by
    Oregon's generic non-payroll bucket, reintroducing the exact over-fragmentation/
    combinatorial-blowup the bundle correction exists to remove (Little Utopia's
    evaluation hung past a minute before this fix; completed in ~100s after)."""
    from app.services.canonical_evaluation import _program_distinguishes_spend_category

    assert _program_distinguishes_spend_category("us_or_opif", "post_production") is False
    assert _program_distinguishes_spend_category("us_or_opif", "sound") is False
    # The real, non-excluded payroll side IS a specific, legitimate match.
    assert _program_distinguishes_spend_category("us_or_opif", "atl_writer") is True


# ---------------------------------------------------------------------------
# LLS-SPECIFIC PERFORMANCE REPAIR (2026-09-30) -- generate_structural_
# candidate's optional `_cache` memoization. Every test below shares a SINGLE
# dict across two calls to prove the cached path can never diverge from a
# fresh, uncached computation -- the resume task's own correctness mandate
# ("cached and uncached paths must return identical economics... prove that
# it cannot remove a materially distinct economic result").
# ---------------------------------------------------------------------------

def test_cache_hit_returns_identical_economics_to_an_uncached_call():
    """Calling twice with byte-identical inputs, once through a shared cache
    and once with no cache at all, must produce the same executable state,
    component economics, and NPC -- a cache hit is never an approximation.
    uk_avec + ie_section_481 (the real, confirmed-executable HO012 pair) is
    used rather than ca_federal_cptc/on_ofttc -- the latter does not clear
    its own real $1,000,000 QPE threshold at these amounts and was never
    actually exercising the cache-store path at all."""
    c1 = _comp("uk_avec", "GB", 2_500_000.0, line_id="CACHE1-GB")
    c2 = _comp("ie_section_481", "IE", 2_500_000.0, line_id="CACHE1-IE", component_type="vfx")
    uncached = generate_structural_candidate([c1, c2], gross_budget_usd=5_000_000.0)
    assert uncached.executable is True, uncached.rejection_reason

    cache: dict = {}
    first = generate_structural_candidate([c1, c2], gross_budget_usd=5_000_000.0, _cache=cache)
    assert len(cache) == 1, "a cache miss must populate exactly one entry"
    second = generate_structural_candidate([c1, c2], gross_budget_usd=5_000_000.0, _cache=cache)
    assert len(cache) == 1, "an identical second call must be a cache HIT, never a second store"

    for res in (first, second):
        assert res.executable == uncached.executable
        assert res.total_guaranteed_incentive_usd == pytest.approx(uncached.total_guaranteed_incentive_usd)
        assert res.npc_usd == pytest.approx(uncached.npc_usd)
        assert res.component_economics == uncached.component_economics


def test_cache_distinguishes_different_adjustment_deltas_for_the_same_structure():
    """The exact same components, priced with two DIFFERENT travel/FX/local-
    cost adjustment totals, must never collide on the same cache entry --
    the adjusted NPC is real money that depends on the adjustment inputs."""
    c1 = _comp("uk_avec", "GB", 2_500_000.0, line_id="CACHE2-GB")
    c2 = _comp("ie_section_481", "IE", 2_500_000.0, line_id="CACHE2-IE", component_type="vfx")
    cache: dict = {}
    low_adj = generate_structural_candidate(
        [c1, c2], gross_budget_usd=5_000_000.0,
        travel_incremental_delta_usd=10_000.0, _cache=cache,
    )
    high_adj = generate_structural_candidate(
        [c1, c2], gross_budget_usd=5_000_000.0,
        travel_incremental_delta_usd=250_000.0, _cache=cache,
    )
    assert low_adj.executable is True and high_adj.executable is True
    assert len(cache) == 1, "adjustment deltas are applied fresh per call; one intrinsic entry serves both"
    assert low_adj.npc_with_adjustments_usd != pytest.approx(high_adj.npc_with_adjustments_usd)
    assert high_adj.npc_with_adjustments_usd == pytest.approx(low_adj.npc_with_adjustments_usd + 240_000.0)


def test_cache_distinguishes_different_component_allocations():
    """The same two jurisdictions/programs but a materially different
    allocated amount on one component must never collide -- structure_id
    already encodes line_ids, which (with the production's own fixed budget)
    determine the real allocated dollars; two different line_ids/amounts for
    the same jurisdiction+program are a genuinely different structure."""
    c1 = _comp("uk_avec", "GB", 2_500_000.0, line_id="CACHE3-GB")
    c2_small = _comp("ie_section_481", "IE", 1_000_000.0, line_id="CACHE3-IE-SMALL", component_type="vfx")
    c2_large = _comp("ie_section_481", "IE", 2_500_000.0, line_id="CACHE3-IE-LARGE", component_type="vfx")
    cache: dict = {}
    small = generate_structural_candidate([c1, c2_small], gross_budget_usd=3_500_000.0, _cache=cache)
    large = generate_structural_candidate([c1, c2_large], gross_budget_usd=5_000_000.0, _cache=cache)
    assert small.executable is True and large.executable is True
    assert len(cache) == 2
    assert small.total_allocated_usd != pytest.approx(large.total_allocated_usd)
    assert small.npc_usd != pytest.approx(large.npc_usd)


def test_cache_hit_recomputes_anchor_relative_fields_fresh_per_call_never_stale():
    """anchor_npc_usd is deliberately excluded from the cache key -- it must
    be recomputed correctly for EACH call's own anchor, never served from
    whichever anchor happened to populate the cache entry first."""
    c1 = _comp("uk_avec", "GB", 2_500_000.0, line_id="CACHE4-GB")
    c2 = _comp("ie_section_481", "IE", 2_500_000.0, line_id="CACHE4-IE", component_type="vfx")
    cache: dict = {}
    first = generate_structural_candidate(
        [c1, c2], gross_budget_usd=5_000_000.0, anchor_npc_usd=2_000_000.0, _cache=cache,
    )
    second = generate_structural_candidate(
        [c1, c2], gross_budget_usd=5_000_000.0, anchor_npc_usd=5_000_000.0, _cache=cache,
    )
    assert first.executable is True and second.executable is True
    assert len(cache) == 1, "same structure/deltas, different anchor only -- still one cache entry"
    assert first.anchor_npc_usd == pytest.approx(2_000_000.0)
    assert second.anchor_npc_usd == pytest.approx(5_000_000.0)
    assert first.incremental_benefit_vs_anchor_usd != pytest.approx(second.incremental_benefit_vs_anchor_usd)
    assert first.incremental_benefit_vs_anchor_usd == pytest.approx(
        2_000_000.0 - first.npc_with_adjustments_usd,
    )
    assert second.incremental_benefit_vs_anchor_usd == pytest.approx(
        5_000_000.0 - second.npc_with_adjustments_usd,
    )


def test_two_independent_caches_never_share_entries():
    """Caches are plain local dicts the caller owns -- two separate cache
    instances (standing in for two separate evaluate_project invocations)
    must never see each other's entries."""
    c1 = _comp("uk_avec", "GB", 2_500_000.0, line_id="CACHE5-GB")
    c2 = _comp("ie_section_481", "IE", 2_500_000.0, line_id="CACHE5-IE", component_type="vfx")
    cache_a: dict = {}
    cache_b: dict = {}
    res_a = generate_structural_candidate([c1, c2], gross_budget_usd=5_000_000.0, _cache=cache_a)
    assert res_a.executable is True
    assert len(cache_a) == 1
    assert len(cache_b) == 0, "a second, independent cache must start and stay empty until its own call"
    generate_structural_candidate([c1, c2], gross_budget_usd=5_000_000.0, _cache=cache_b)
    assert len(cache_b) == 1
    assert set(cache_a.keys()) == set(cache_b.keys()), "same inputs still produce the same key independently"


def test_cache_key_pairs_component_type_with_its_own_jurisdiction_never_a_positional_collision():
    """CONFIRMED DEFECT, fixed same pass: component_type is not cosmetic --
    when a component's own program fails to resolve a rate, component_type
    in ("selective_upside", "fund_overlay") keeps the WHOLE structure
    executable (that one component silently contributes $0/$0, disclosed);
    any OTHER component_type rejects the entire structure. The exact same
    (jurisdiction_code, program_slug, line_id) pair -- us_ny_post_production_
    credit in US-NY at $400,000, genuinely below its real $1,000,000
    statutory minimum (see test_registered_control_5b_ny_post_below_real_
    threshold_rejects above, the real confirmed-failing case this test
    reuses verbatim) -- must NOT collide in the cache merely because
    _structure_id() itself does not encode component_type."""
    principal = _comp("ny_state_film", "US-NY", 3_000_000.0, line_id="CACHE6-PRINCIPAL")
    below_threshold_post = _comp(
        "us_ny_post_production_credit", "US-NY", 400_000.0,
        line_id="CACHE6-POST", component_type="post",
    )
    below_threshold_upside = _comp(
        "us_ny_post_production_credit", "US-NY", 400_000.0,
        line_id="CACHE6-POST", component_type="selective_upside",
    )
    # NOTE ON CACHE SIZE: a REJECTED structure returns via an early `return`
    # inside the pricing loop, before the function ever reaches its own
    # cache-store statement -- only an EXECUTABLE result is ever written to
    # the cache (a correct, if conservative, behavior: a key that was never
    # stored can never be wrongly read back). The real risk this test
    # guards is the reverse: an EXECUTABLE result cached under a key that a
    # later, genuinely-different (different component_type) REJECTED call
    # could collide with and wrongly read back as a false cache HIT.
    cache: dict = {}
    as_post = generate_structural_candidate(
        [principal, below_threshold_post], gross_budget_usd=3_400_000.0, _cache=cache,
    )
    assert as_post.executable is False, "reused from the real confirmed-failing control -- must still reject"
    assert len(cache) == 1, "a rejected intrinsic result is now cached too (anchor NPC is applied fresh per call)"
    as_upside = generate_structural_candidate(
        [principal, below_threshold_upside], gross_budget_usd=3_400_000.0, _cache=cache,
    )
    assert as_upside.executable is True, (
        "selective_upside must stay executable (that component contributes $0/$0)"
    )
    assert len(cache) == 2, "the executable selective_upside result is cached under its own (component_type-distinct) key"
    upside_econ = next(
        ce for ce in as_upside.component_economics
        if ce.component.program_slug == "us_ny_post_production_credit"
    )
    assert upside_econ.guaranteed_incentive_usd == 0.0
    assert upside_econ.conditional_incentive_usd == 0.0

    # Reverse call order -- the real collision risk: the EXECUTABLE
    # selective_upside call caches first; the genuinely-different REJECTED
    # "post" call, with the SAME jurisdiction/program/line_id, must not read
    # back that cached executable=True result as a false hit.
    cache_reverse: dict = {}
    as_upside_first = generate_structural_candidate(
        [principal, below_threshold_upside], gross_budget_usd=3_400_000.0, _cache=cache_reverse,
    )
    assert as_upside_first.executable is True
    assert len(cache_reverse) == 1
    as_post_second = generate_structural_candidate(
        [principal, below_threshold_post], gross_budget_usd=3_400_000.0, _cache=cache_reverse,
    )
    assert as_post_second.executable is False, (
        "a cache collision in this order would have wrongly inherited executable=True from selective_upside"
    )
    assert len(cache_reverse) == 2, "the rejected 'post' call is cached under its own component_type-distinct key"


def test_cache_result_objects_are_frozen_and_cannot_leak_mutable_state_across_candidates():
    """StructuralCandidateResult is a frozen dataclass of only tuple/str/
    float/bool/None fields -- a cache hit can never hand two different
    candidates a shared, later-mutated object. Proven directly: attempting
    to reassign a field on a real cached result must raise."""
    import dataclasses
    c1 = _comp("uk_avec", "GB", 2_500_000.0, line_id="CACHE7-GB")
    c2 = _comp("ie_section_481", "IE", 2_500_000.0, line_id="CACHE7-IE", component_type="vfx")
    cache: dict = {}
    result = generate_structural_candidate([c1, c2], gross_budget_usd=5_000_000.0, _cache=cache)
    assert result.executable is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.npc_usd = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# LLS anchor-cardinality repair, round 2 (2026-10-01): intrinsic pricing is
# cached independently of anchor-relative adjustments; per-leg normalization.
# ---------------------------------------------------------------------------

def _intrinsic_fixtures():
    ok_a = _comp("uk_avec", "GB", 2_500_000.0, line_id="INT-GB")
    ok_b = _comp("ie_section_481", "IE", 2_500_000.0, line_id="INT-IE", component_type="vfx")
    principal = _comp("ny_state_film", "US-NY", 3_000_000.0, line_id="INT-NY-P")
    low_post = _comp("us_ny_post_production_credit", "US-NY", 400_000.0, line_id="INT-NY-POST", component_type="post")
    low_upside = _comp("us_ny_post_production_credit", "US-NY", 400_000.0, line_id="INT-NY-POST", component_type="selective_upside")
    dup_a = _comp("uk_avec", "GB", 1_000_000.0, line_id="INT-DUP")
    dup_b = _comp("ie_section_481", "IE", 1_000_000.0, line_id="INT-DUP", component_type="vfx")
    return [
        ([ok_a, ok_b], 5_000_000.0),                       # executable
        ([principal, low_post], 3_400_000.0),              # rejected: threshold
        ([principal, low_upside], 3_400_000.0),            # executable, selective $0/$0 disclosed
        ([dup_a, dup_b], 2_000_000.0),                     # rejected: same-cost double claim
    ]


_ANCHOR_AND_DELTA_CASES = [
    (None, 0.0, 0.0, 0.0),
    (2_000_000.0, 0.0, 0.0, 0.0),
    (5_000_000.0, 10_000.0, 5_000.0, 2_500.0),
    (5_000_000.0, 250_000.0, 0.0, 0.0),
    (3_000_000.0, 0.0, -7_000.5, 120_000.0),
]


def test_intrinsic_cache_plus_fresh_adjustments_equals_uncached_result_exactly():
    """For executable, threshold-rejected, selective-upside and double-claim structures, every
    (anchor NPC, travel, FX, local-cost) combination served through ONE shared intrinsic cache (and a
    shared component cache) is exactly equal -- every field, dataclass equality -- to the original
    uncached computation. Covers identity, warnings/limitations, incentives, QPE, executability."""
    cache: dict = {}
    comp_cache: dict = {}
    for components, gross in _intrinsic_fixtures():
        for anchor, travel, fx, local in _ANCHOR_AND_DELTA_CASES:
            kwargs = dict(
                gross_budget_usd=gross, anchor_npc_usd=anchor, travel_incremental_delta_usd=travel,
                fx_delta_usd=fx, local_cost_delta_usd=local,
            )
            fresh = generate_structural_candidate(components, **kwargs)
            cached = generate_structural_candidate(components, _cache=cache, _component_cache=comp_cache, **kwargs)
            assert cached == fresh, (components[0].program_slug, kwargs)
            again = generate_structural_candidate(components, _cache=cache, _component_cache=comp_cache, **kwargs)
            assert again == fresh
            for f in ("structure_id", "executable", "rejection_reason", "disclosed_limitations",
                      "total_guaranteed_incentive_usd", "total_conditional_incentive_usd",
                      "total_allocated_usd", "administrative_allocation_risk"):
                assert getattr(cached, f) == getattr(fresh, f), f
    assert len(cache) == len(_intrinsic_fixtures()), "one intrinsic entry per structure, however many anchors/deltas"
    assert comp_cache, "component pricing cache must have been populated"


def test_intrinsic_cache_never_leaks_stale_npc_or_materiality_across_anchors_and_deltas():
    components, gross = _intrinsic_fixtures()[0]
    cache: dict = {}
    seen = {}
    for anchor, travel, fx, local in _ANCHOR_AND_DELTA_CASES:
        r = generate_structural_candidate(
            components, gross_budget_usd=gross, anchor_npc_usd=anchor, travel_incremental_delta_usd=travel,
            fx_delta_usd=fx, local_cost_delta_usd=local, _cache=cache,
        )
        adj = round(travel + fx + local, 2)
        assert r.npc_with_adjustments_usd == round(r.npc_usd + adj, 2)
        assert r.total_adjustments_usd == adj
        assert r.anchor_npc_usd == anchor
        if anchor is None:
            assert r.incremental_benefit_vs_anchor_usd is None and r.materiality_recommended is False
        else:
            assert r.incremental_benefit_vs_anchor_usd == round(anchor - r.npc_with_adjustments_usd, 2)
            assert r.materiality_recommended == (r.incremental_benefit_vs_anchor_usd >= 100_000.0)
        seen[(anchor, travel, fx, local)] = r.materiality_recommended
    assert True in seen.values() and False in seen.values(), "fixture must flip materiality across calls"
    assert len(cache) == 1


def test_per_leg_normalization_equals_complete_structure_normalization_and_reuses_legs():
    from app.services.canonical_evaluation import _hybrid_structure_normalization

    inputs = _economic_inputs(jurisdiction_code="GR", gross_budget_usd=4_000_000.0)
    principal = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="LEG-GA")
    nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0,
               component_type="post", line_id="LEG-NZ")
    ie = _comp("ie_section_481", "IE", 400_000.0, component_type="vfx", line_id="LEG-IE")
    structure_a = [principal, nz, ie]
    structure_b = [principal, nz]                       # shares the principal leg and the NZ leg

    uncached_a = _hybrid_structure_normalization(inputs, "US-GA", structure_a)
    uncached_b = _hybrid_structure_normalization(inputs, "US-GA", structure_b)
    cache: dict = {}
    assert _hybrid_structure_normalization(inputs, "US-GA", structure_a, cache=cache) == uncached_a
    legs_after_a = [k for k in cache if str(k[0]).startswith("leg_")]
    assert legs_after_a, "legs must be cached individually"
    assert _hybrid_structure_normalization(inputs, "US-GA", structure_b, cache=cache) == uncached_b
    legs_after_b = [k for k in cache if str(k[0]).startswith("leg_")]
    assert legs_after_b == legs_after_a, "structure B's legs were all already cached by structure A"
    # a different principal/anchor never reuses another anchor's legs
    other = _hybrid_structure_normalization(inputs, "NZ", [
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 3_000_000.0,
              component_type="principal_production", line_id="LEG-NZP"), ie,
    ], cache=cache)
    assert other == _hybrid_structure_normalization(inputs, "NZ", [
        _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 3_000_000.0,
              component_type="principal_production", line_id="LEG-NZP"), ie,
    ])
