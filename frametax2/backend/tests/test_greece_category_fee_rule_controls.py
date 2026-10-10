"""Greece category / fee rules (PROJECT_OPEN_ITEM_RECOVERY G-04, G-08, G-09, G-10, G-11; register Q37, Q39-Q41).

SYNTHETIC ONLY -- invented amounts, no database, no real project, no persisted generation. Every expectation is a closed-form
sum derived here from the dated primary text (KYA 607434, Gazette B' 87/14.01.2026, Annex B.3(i)-(ii), Art. 5(1), Annex B.2(viii),
Annex I Table A), never from an engine or AG output:

  * insurance premiums and guarantee costs count up to 5% of the TOTAL eligible cost;
  * the director, the screenwriter and the two leading actors count up to 30% of the TOTAL eligible cost (the producer is not in
    the group), where the total includes the capped group itself, so Q = other + min(ins, 0.05 Q) + min(fees, 0.30 Q);
  * eligible expense never exceeds 80% of the total production cost of the work (the worldwide budget total).
Excess of a KNOWN member category (insurance, bond, writer, director) is legally disallowed: excluded, kept in the cap trace.
Only excess that depends on an unresolved membership (the cast account, which also holds supporting cast) is conditional, and
a music account whose composer/services/licence split is unknown is reported as unresolved membership with an exactness
envelope. Contingency needs evidenced Action A and eligible deployed-category prerequisites; the producer's election is not
evidence, and deployed reserve is limited to 10% of the non-ATL eligible base once (KYA 607434 Annex B.2(viii), Annex II)."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import price_segment
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.data.cultural_point_tables import CULTURAL_POINT_TABLES
from app.data.program_requirements import get_program_requirements
from app.data.program_spend_rules import get_program_rules
from app.data.program_rate_rules import QPE_SHARE_CAP_RULES, get_qpe_cap, _GR_CITATION

BTL, INS, BOND, WRITER, DIRECTOR, CAST, PRODUCER = (
    "btl_crew_labor", "insurance", "completion_bond", "atl_writer", "atl_director", "atl_cast", "atl_producer")


def _gr(lines, gross, contingency_pct=None, evidenced=None):
    allocs = [
        AccountAllocation(
            account_code=code, description=desc, amount_usd=amt, component="production", jurisdiction_code="GR",
            assignment_kind=AssignmentKind.FIXED, rationale="greece control", governing_decision="greece-control",
            line_id=f"L{code}", spend_category=cat)
        for code, desc, amt, cat in lines
    ]
    return price_segment(
        jurisdiction_code="GR", program_slug="gr_cash_rebate", allocations=allocs,
        spend_category_by_code={code: cat for code, _d, _a, cat in lines}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=gross, contingency_expected_utilization_pct=contingency_pct,
        evidenced_requirement_facts=frozenset(evidenced or ()))


# other 1,000,000; insurance 20,000 + bond 10,000; writer 100,000 + director 100,000 + cast 900,000 (fee group 1,100,000)
BASE = [("3100", "CAMERA", 1_000_000.0, BTL), ("7200", "INSURANCE", 20_000.0, INS), ("7905", "BOND", 10_000.0, BOND),
        ("1100", "SCRIPT", 100_000.0, WRITER), ("1300", "DIRECTOR", 100_000.0, DIRECTOR), ("1400", "CAST", 900_000.0, CAST)]


def test_the_principal_fee_group_is_capped_at_thirty_percent_of_the_total_that_includes_it():
    seg = _gr(BASE, gross=3_000_000.0)
    q = (1_000_000.0 + 30_000.0) / (1 - 0.30)                 # closed form of Q = 1,030,000 + 0.30 Q
    assert seg.executable and seg.qpe_usd == pytest.approx(q, abs=0.02)
    allowed_fees = 0.30 * q
    assert seg.unresolved_usd == pytest.approx(1_100_000.0 - allowed_fees, abs=0.02)   # conditional, not excluded
    assert seg.excluded_usd == 0.0 and seg.qpe_cap_applied_usd == 0.0
    assert seg.qpe_share_cap_applied_usd == pytest.approx(1_100_000.0 - allowed_fees, abs=0.02)
    assert seg.incentive_floor_usd == pytest.approx(0.40 * q, abs=0.02)
    (group,) = seg.qpe_share_cap_groups
    assert group["group_id"] == "principal_fees" and group["cap_pct"] == 0.30 and group["raw_usd"] == 1_100_000.0


def test_the_producer_fee_is_outside_the_current_thirty_percent_group():
    seg = _gr(BASE + [("1200", "PRODUCERS", 500_000.0, PRODUCER)], gross=4_000_000.0)
    q = (1_000_000.0 + 500_000.0 + 30_000.0) / (1 - 0.30)    # producer counts as ordinary eligible cost
    assert seg.qpe_usd == pytest.approx(q, abs=0.02)


def test_known_insurance_and_guarantee_excess_is_excluded_not_conditional():
    lines = [("3100", "CAMERA", 1_000_000.0, BTL), ("7200", "INSURANCE", 300_000.0, INS), ("7905", "BOND", 200_000.0, BOND)]
    seg = _gr(lines, gross=2_000_000.0)
    q = 1_000_000.0 / (1 - 0.05)                               # Q = 1,000,000 + 0.05 Q
    assert seg.qpe_usd == pytest.approx(q, abs=0.02)
    assert seg.excluded_usd == pytest.approx(500_000.0 - 0.05 * q, abs=0.02)   # disallowed by the 5% cap, whatever the payees
    assert seg.unresolved_usd == 0.0                           # no payee fact can waive the cap: nothing is upside
    (group,) = seg.qpe_share_cap_groups
    assert group["group_id"] == "insurance_and_guarantees" and group["raw_usd"] == 500_000.0   # source dollars kept in the trace
    assert group["definite_excess_usd"] == pytest.approx(500_000.0 - 0.05 * q, abs=0.02) and group["conditional_excess_usd"] == 0.0
    assert not [p for p in seg.presumed_facts if p["condition_id"] == "gr-principal-fee-membership"]


def test_known_writer_and_director_excess_is_excluded_and_only_the_cast_account_excess_is_conditional():
    lines = [("3100", "CAMERA", 1_000_000.0, BTL), ("1100", "SCRIPT", 600_000.0, WRITER), ("1300", "DIRECTOR", 600_000.0, DIRECTOR)]
    seg = _gr(lines, gross=3_000_000.0)
    q = 1_000_000.0 / (1 - 0.30)                               # known members alone already exceed 30%
    assert seg.qpe_usd == pytest.approx(q, abs=0.02)
    assert seg.excluded_usd == pytest.approx(1_200_000.0 - 0.30 * q, abs=0.02) and seg.unresolved_usd == 0.0
    cast = _gr(lines + [("1400", "CAST", 100_000.0, CAST)], gross=3_000_000.0)
    (group,) = cast.qpe_share_cap_groups
    q_upper = (1_000_000.0 + 100_000.0) / 0.70                 # cast entirely outside the group: the smallest possible excess
    q_proxy = 1_000_000.0 / 0.70                               # cast entirely inside the group: the served lower envelope
    assert group["definite_excess_usd"] == pytest.approx(1_200_000.0 - 0.30 * q_upper, abs=0.02)   # certain under any split
    assert group["excess_usd"] == pytest.approx(1_300_000.0 - 0.30 * q_proxy, abs=0.02)
    assert group["conditional_excess_usd"] == pytest.approx(group["excess_usd"] - group["definite_excess_usd"], abs=0.02)
    assert cast.excluded_usd == pytest.approx(group["definite_excess_usd"], abs=0.02)
    assert cast.unresolved_usd == pytest.approx(group["conditional_excess_usd"], abs=0.02)   # may exceed the cast account itself
    assert cast.qpe_usd == pytest.approx(q_proxy, abs=0.05)


def test_music_stays_outside_the_group_but_its_unresolved_membership_and_envelope_are_disclosed():
    base = _gr(BASE, gross=3_200_000.0)
    seg = _gr(BASE + [("6000", "MUSIC", 200_000.0, "music")], gross=3_200_000.0)
    assert seg.qpe_usd == pytest.approx((1_030_000.0 + 200_000.0) / 0.70, abs=0.02)   # music planned as ordinary cost
    (m,) = [p for p in seg.presumed_facts if p["condition_id"] == "gr-principal-fee-membership"]
    assert m["exact"] is False
    assert {(u["category"], u["treatment"]) for u in m["unresolved_members"]} == {
        ("atl_cast", "inside_group_proxy"), ("music", "outside_group_planning_value")}
    env = m["total_eligible_envelope_usd"]
    assert env["lower"] <= env["served"] <= env["upper"] and env["upper"] - env["lower"] > 0
    # a music account too small to move the eligible total is not reported as an open membership
    assert not [p for p in _gr([("3100", "CAMERA", 1_000_000.0, BTL), ("6000", "MUSIC", 5_000.0, "music")],
                               gross=2_000_000.0).presumed_facts if p["condition_id"] == "gr-principal-fee-membership"]
    assert base.qpe_usd > 0


def test_a_cap_that_does_not_bind_changes_nothing():
    lines = [("3100", "CAMERA", 1_000_000.0, BTL), ("7200", "INSURANCE", 20_000.0, INS),
             ("1300", "DIRECTOR", 50_000.0, DIRECTOR), ("1100", "SCRIPT", 30_000.0, WRITER)]
    seg = _gr(lines, gross=2_000_000.0)
    assert seg.qpe_usd == pytest.approx(1_100_000.0) and seg.qpe_share_cap_applied_usd == 0.0
    assert seg.qpe_share_cap_groups == () and seg.unresolved_usd == 0.0


def test_the_eighty_percent_limit_still_applies_when_no_share_cap_binds():
    seg = _gr([("3100", "CAMERA", 900_000.0, BTL)], gross=1_000_000.0)
    assert seg.qpe_usd == pytest.approx(800_000.0) and seg.qpe_cap_applied_usd == pytest.approx(100_000.0)
    assert seg.qpe_share_cap_applied_usd == 0.0
    # the denominator is the worldwide total INCLUDING financing: a finance line inside the 1,000,000 gross does not shrink it
    with_finance = _gr([("3100", "CAMERA", 700_000.0, BTL), ("7901", "FINANCE FEE", 100_000.0, "finance_costs")], gross=1_000_000.0)
    assert with_finance.qpe_usd == pytest.approx(700_000.0)   # financing is not eligible, but the cap base stays the 1,000,000 total


def test_share_caps_and_the_eighty_percent_limit_are_resolved_together():
    gross = 1_500_000.0                                        # 80% limit = 1,200,000
    seg = _gr(BASE, gross=gross)
    limit = 0.80 * gross
    assert seg.qpe_usd == pytest.approx(limit, abs=0.02)       # the final eligible total sits on the limit
    assert seg.qpe_share_cap_groups[0]["total_eligible_basis_usd"] == pytest.approx(limit, abs=0.02)
    assert seg.qpe_share_cap_groups[0]["allowed_usd"] == pytest.approx(0.30 * limit, abs=0.02)   # fee group = 30% of the limit
    assert seg.qpe_share_cap_applied_usd == pytest.approx(1_100_000.0 - 0.30 * limit, abs=0.02)
    assert seg.qpe_cap_applied_usd > 0                         # the rest of the reduction is the 80% limit itself


ACTION_A, DEPLOYED_OK = "gr_action_a_applicant_evidenced", "gr_contingency_category_eligible_evidenced"
NOT_ACTION_A, DEPLOYED_BAD = "gr_action_a_not_applicant_evidenced", "gr_contingency_category_ineligible_evidenced"
CONT = [("3100", "CAMERA", 1_000_000.0, BTL), ("7902", "CONTINGENCY", 500_000.0, "contingency")]


def _cont(pct, evidenced):
    return _gr(CONT, gross=2_000_000.0, contingency_pct=pct, evidenced=evidenced)


def test_a_contingency_election_is_not_evidence_that_the_reserve_qualifies():
    for evidence in (set(), {ACTION_A}, {DEPLOYED_OK}):       # either prerequisite missing = conditional
        seg = _cont(100.0, evidence)
        assert seg.qpe_usd == pytest.approx(1_000_000.0) and seg.unresolved_usd == pytest.approx(500_000.0)
        assert seg.excluded_usd == 0.0


def test_known_ineligible_contingency_prerequisites_fail_the_reserve_and_contradictory_evidence_stays_conditional():
    for evidence in ({NOT_ACTION_A, DEPLOYED_OK}, {ACTION_A, DEPLOYED_BAD}):
        seg = _cont(100.0, evidence)
        assert seg.qpe_usd == pytest.approx(1_000_000.0) and seg.excluded_usd == pytest.approx(500_000.0)
        assert seg.unresolved_usd == 0.0                       # known failure is excluded even with no election
    assert _cont(None, {NOT_ACTION_A, DEPLOYED_OK}).excluded_usd == pytest.approx(500_000.0)
    contradictory = _cont(100.0, {ACTION_A, NOT_ACTION_A, DEPLOYED_OK})
    assert contradictory.unresolved_usd == pytest.approx(500_000.0) and contradictory.excluded_usd == 0.0


def test_evidenced_contingency_is_limited_to_ten_percent_of_the_non_atl_base_once_at_each_deployment_level():
    ok = {ACTION_A, DEPLOYED_OK}
    full = _cont(100.0, ok)                                    # 500,000 deployed, bound 10% x 1,000,000 = 100,000
    assert full.qpe_usd == pytest.approx(1_100_000.0) and full.excluded_usd == pytest.approx(400_000.0)
    assert full.contingency_allowance_applied_usd == pytest.approx(400_000.0) and full.unresolved_usd == 0.0
    half = _cont(50.0, ok)                                     # 250,000 deployed: undeployed 250,000 + over-bound 150,000
    assert half.qpe_usd == pytest.approx(1_100_000.0) and half.excluded_usd == pytest.approx(400_000.0)
    assert half.contingency_allowance_applied_usd == pytest.approx(150_000.0)
    none = _cont(0.0, ok)
    assert none.qpe_usd == pytest.approx(1_000_000.0) and none.excluded_usd == pytest.approx(500_000.0)
    assert none.contingency_allowance_applied_usd == 0.0
    unset = _cont(None, ok)                                    # prerequisites evidenced, deployment still a project fact
    assert unset.qpe_usd == pytest.approx(1_000_000.0) and unset.unresolved_usd == pytest.approx(500_000.0)
    small = _gr([CONT[0], ("7902", "CONTINGENCY", 50_000.0, "contingency")], gross=2_000_000.0, contingency_pct=100.0, evidenced=ok)
    assert small.qpe_usd == pytest.approx(1_050_000.0) and small.contingency_allowance_applied_usd == 0.0   # inside the bound
    assert full.qpe_usd + full.excluded_usd == pytest.approx(1_500_000.0)   # gross reserve unchanged: every dollar accounted


def test_the_unevidenced_greek_incurrence_presumption_is_disclosed_without_changing_the_rate():
    seg = _gr(BASE, gross=3_000_000.0)
    assert {p["condition_id"] for p in seg.presumed_facts} == {
        "gr-local-incurrence-schedule", "gr-application-date-and-regime", "gr-principal-fee-membership"}
    assert seg.rate_floor == pytest.approx(0.40) and seg.rate_ceiling == pytest.approx(0.40) and not seg.ceiling_requires_confirmation


def test_programs_without_share_rules_are_untouched():
    alloc = AccountAllocation(
        account_code="3100", description="CAMERA", amount_usd=1_000_000.0, component="production", jurisdiction_code="US-NM",
        assignment_kind=AssignmentKind.FIXED, rationale="control", governing_decision="control", line_id="L1", spend_category=BTL)
    seg = price_segment(jurisdiction_code="US-NM", program_slug="us_nm_film_credit", allocations=[alloc],
                        spend_category_by_code={"3100": BTL}, offshore_payroll_accounts=frozenset(), gross_budget_usd=1_400_000.0)
    assert seg.qpe_share_cap_applied_usd == 0.0 and seg.qpe_share_cap_groups == ()


def test_the_retained_records_carry_the_dated_primary_figures():
    rules = {r.group_id: r for r in QPE_SHARE_CAP_RULES["gr_cash_rebate"]}
    assert rules["insurance_and_guarantees"].cap_pct == 0.05 and rules["principal_fees"].cap_pct == 0.30
    pf = rules["principal_fees"]
    assert pf.categories == frozenset({"atl_writer", "atl_director"})       # Annex II 1.1, 1.2; the producer (1.3) is outside
    assert pf.proxy_categories == frozenset({"atl_cast"}) and pf.outside_unresolved_categories == frozenset({"music"})
    assert "1.5" in pf.unresolved_note and "6.8" in pf.unresolved_note and "B.2(vii)" in pf.unresolved_note
    assert "14.01.2026" in rules["principal_fees"].quote and "Annex B.3(ii)" in rules["principal_fees"].quote
    contingency = get_program_rules("gr_cash_rebate")["contingency"]
    assert contingency.qualifies is True and "B.2(viii)" in contingency.notes and "Action A" in contingency.notes
    cap = get_qpe_cap("gr_cash_rebate")
    assert cap.cap_pct == 0.80 and cap.cap_base == "total_worldwide_budget" and "ELIGIBLE total" in cap.description


def test_the_cultural_threshold_follows_the_primary_current_text_and_the_citation_no_longer_denies_the_test():
    table = CULTURAL_POINT_TABLES["gr_cash_rebate"]
    profile = get_program_requirements("gr_cash_rebate")
    assert (table.total_points, table.threshold) == (50, 23)
    assert profile.cultural_test_required and (profile.cultural_test_points, profile.cultural_test_threshold) == (50, 23)
    assert "23 of 50" in table.source_note and "KYA 607434" in table.source_note
    assert "no cultural test" not in _GR_CITATION
