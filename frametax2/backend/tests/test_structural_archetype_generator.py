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
