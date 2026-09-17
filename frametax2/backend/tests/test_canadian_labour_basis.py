"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION, labour-basis pass.

Hand-calculated controls for app/calculators/canadian_labour_basis.py.
Every expected number below is computed by hand in the test itself
(never asserted against the module's own output as its own oracle) and
traces directly to the three primary sources fetched and quoted this
workstream: CAVCO CPTC application guidelines [CPTC-GUIDE], CRA Guide
T1131 [T1131], CAVCO PSTC application guidelines [PSTC-GUIDE].
"""
from dataclasses import dataclass

from app.calculators.canadian_labour_basis import (
    FIELD_ASSISTANCE_USD,
    FIELD_CANADIAN_STATUS,
    FIELD_LOOK_THROUGH_WAGES_USD,
    FIELD_PAYEE_TYPE,
    FIELD_PAYMENT_STATUS,
    FIELD_PSC_PROFIT_ELEMENT_ELIGIBLE,
    FIELD_SERVICE_LOCATION,
    LINE_FACT_PREFIX,
    derive_canadian_labour_basis,
    to_amount_facts,
)


@dataclass(frozen=True)
class _Line:
    line_id: str
    amount_usd: float
    spend_category: str
    is_memo: bool = False


@dataclass(frozen=True)
class _Fact:
    fact_key: str
    value: str


def _lf(line_id: str, field: str, value) -> _Fact:
    return _Fact(fact_key=f"{LINE_FACT_PREFIX}{line_id}:{field}", value=str(value))


# 1. Qualifying Canadian resident director, paid in full.
def test_qualifying_canadian_director_paid():
    lines = [_Line("L1", 500_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", "role", "director"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    # Employee/individual, paid in full, no look-through cap, no assistance.
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 500_000.0
    assert r.evidenced_eligible_labour_usd["ca_federal_pstc"] == 0.0  # nonresident/service_location not evidenced -> PSTC gate
    assert r.qualified_labour_usd["ca_federal_cptc"] == 500_000.0
    assert not r.missing_fact_line_ids


# 2. Nonresident director -- excluded for PSTC, NOT auto-excluded for CPTC
#    (residency gate not confirmed for CPTC's own labour-expenditure text).
def test_nonresident_director():
    lines = [_Line("L1", 500_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "nonresident"),
        _lf("L1", FIELD_SERVICE_LOCATION, "outside_canada"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_pstc"] == 0.0
    reasons = [d.reason for d in r.line_dispositions if d.program_slug == "ca_federal_pstc"]
    assert any("resident in Canada" in r_ for r_ in reasons)
    # CPTC: no confirmed residency gate in the fetched text -- not excluded on this basis alone.
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 500_000.0


# 3. Deferred director fee -- excluded per [CPTC-GUIDE] contingent-liability rule.
def test_deferred_director_fee_excluded():
    lines = [_Line("L1", 200_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", FIELD_PAYMENT_STATUS, "deferred"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 0.0
    assert r.potentially_eligible_usd["ca_federal_cptc"] == 200_000.0  # was IN the pool, excluded by the payment-status rule specifically
    assert any("deferred" in d.reason for d in r.line_dispositions)


# 4. Contingent/backend fee -- excluded per [T1131] "amounts determined
#    with reference to profits or revenues" exclusion.
def test_contingent_backend_fee_excluded():
    lines = [_Line("L1", 150_000.0, "atl_producer")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", FIELD_PAYMENT_STATUS, "contingent"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 0.0


# 5/6/7. Canadian writer / performer / producer -- same treatment as director (no role-specific gate found).
def test_canadian_writer_performer_producer_all_qualify_when_evidenced():
    lines = [
        _Line("W1", 100_000.0, "atl_writer"),
        _Line("C1", 100_000.0, "atl_cast"),
        _Line("P1", 100_000.0, "atl_producer"),
    ]
    facts = [
        _lf("W1", FIELD_CANADIAN_STATUS, "resident_citizen"), _lf("W1", FIELD_PAYMENT_STATUS, "paid"),
        _lf("C1", FIELD_CANADIAN_STATUS, "resident_citizen"), _lf("C1", FIELD_PAYMENT_STATUS, "paid"),
        _lf("P1", FIELD_CANADIAN_STATUS, "resident_citizen"), _lf("P1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 300_000.0


# 8a. Eligible loan-out with evidenced look-through wages (only the employee wage counts).
def test_loan_out_look_through_eligible():
    lines = [_Line("L1", 300_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_PAYEE_TYPE, "loan_out_corp"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
        _lf("L1", FIELD_LOOK_THROUGH_WAGES_USD, 120_000.0),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 120_000.0  # NEVER the full $300k invoice
    assert any("look-through cap applied" in d.reason for d in r.line_dispositions)


# 8b. Ineligible loan-out: no look-through wage evidenced and no PSC-profit-element fact -> fails closed to $0.
def test_loan_out_missing_look_through_fails_closed():
    lines = [_Line("L1", 300_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_PAYEE_TYPE, "loan_out_corp"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 0.0
    assert any("cannot be derived and fails closed to $0" in d.reason for d in r.line_dispositions)


# 8c. Foreign corporation payee -- excluded outright per [T1131] lines 605/606.
def test_foreign_corp_payee_excluded():
    lines = [_Line("L1", 250_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_PAYEE_TYPE, "foreign_corp"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 0.0
    assert any("non-taxable Canadian corporations and foreign corporations" in d.reason for d in r.line_dispositions)


# 8d. Majority-owned personal service corp with the evidenced profit-element fact -- full amount, no look-through cap.
def test_psc_profit_element_eligible_full_amount():
    lines = [_Line("L1", 400_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_PAYEE_TYPE, "personal_service_corp"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
        _lf("L1", FIELD_PSC_PROFIT_ELEMENT_ELIGIBLE, "true"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 400_000.0


# 9. Assistance reduction.
def test_assistance_reduces_eligible_labour():
    lines = [_Line("L1", 500_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
        _lf("L1", FIELD_ASSISTANCE_USD, 50_000.0),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 450_000.0


# 10. CPTC 60% cap: hand-calculated -- $2,000,000 evidenced eligible labour
#     against a $3,000,000 gross budget with $0 assistance -> net production
#     cost = $3,000,000 -> cap = 0.60 * 3,000,000 = $1,800,000, which is
#     LESS than the evidenced $2,000,000, so qualified labour is capped.
def test_cptc_60_percent_cap_binds():
    lines = [_Line("L1", 2_000_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 2_000_000.0
    assert r.statutory_cap_usd["ca_federal_cptc"] == 1_800_000.0
    assert r.qualified_labour_usd["ca_federal_cptc"] == 1_800_000.0  # min(2,000,000; 1,800,000)


def test_cptc_60_percent_cap_does_not_bind_when_labour_is_lower():
    lines = [_Line("L1", 1_000_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    # cap = 1,800,000 > evidenced 1,000,000 -> qualified = evidenced, uncapped.
    assert r.qualified_labour_usd["ca_federal_cptc"] == 1_000_000.0


# 11. PSTC distinct treatment: same evidenced facts, but PSTC has NO
#     confirmed cap in the fetched text -- qualified labour is the full
#     evidenced amount, never capped the way CPTC is.
def test_pstc_distinct_no_cap():
    lines = [_Line("L1", 2_000_000.0, "atl_director")]
    facts = [
        _lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"),
        _lf("L1", FIELD_SERVICE_LOCATION, "in_canada"),
        _lf("L1", FIELD_PAYMENT_STATUS, "paid"),
    ]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    assert r.statutory_cap_usd["ca_federal_pstc"] is None
    assert r.evidenced_eligible_labour_usd["ca_federal_pstc"] == 2_000_000.0
    assert r.qualified_labour_usd["ca_federal_pstc"] == 2_000_000.0  # uncapped, unlike CPTC's 1,800,000 for the same facts


# 12. CPTC/PSTC mutual exclusion is enforced at the stacking-rule layer
#     (frametax2/backend/tests/test_stacking_engine.py and the registry
#     entry added this pass), not by this derivation module -- this
#     module only derives each program's OWN qualified-labour figure
#     independently; it is not this module's job to decide which one a
#     production may claim.
def test_mutual_exclusion_is_a_stacking_concern_not_a_derivation_concern():
    from app.calculators.canonical_stack_bridge import load_named_pair_rule
    rule = load_named_pair_rule("ca_federal_cptc", "ca_federal_pstc")
    assert rule is not None and rule["rule_type"] == "mutually_exclusive"


# 13. Missing facts fail closed -- no line_fact rows at all for an
#     eligible-category line.
def test_missing_facts_fail_closed():
    lines = [_Line("L1", 500_000.0, "atl_director")]
    r = derive_canadian_labour_basis(lines, [], gross_budget_usd=3_000_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 0.0
    assert r.qualified_labour_usd["ca_federal_cptc"] is None
    assert "L1" in r.missing_fact_line_ids
    assert to_amount_facts(r) == {}  # never emits a fabricated 0.0 amount fact


def test_to_amount_facts_only_emits_confirmed_positive_values():
    lines = [_Line("L1", 500_000.0, "atl_director")]
    facts = [_lf("L1", FIELD_CANADIAN_STATUS, "resident_citizen"), _lf("L1", FIELD_PAYMENT_STATUS, "paid")]
    r = derive_canadian_labour_basis(lines, facts, gross_budget_usd=3_000_000.0)
    out = to_amount_facts(r)
    assert out.get("ca_federal_cptc_qualified_labour_usd") == 500_000.0
    assert "ca_federal_pstc_qualified_labour_usd" not in out  # PSTC evidenced=0 here (no service_location) -> not emitted
