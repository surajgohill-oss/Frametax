"""CRA RC4164 (T1131 guide): line-level assistance reduces the PRODUCTION COST that sets the 60% cap (lines 421-430), not the labour line (618).
PSTC keeps the per-line reduction. Hand computation: labour 1,000,000, gross 1,000,000, stated assistance 300,000 ->
CPTC: labour 1,000,000 unreduced, cap 60% x (1,000,000 - 300,000) = 420,000, qualified 420,000 (the old per-line deduction gave min(700,000, 600,000) = 600,000)."""
from types import SimpleNamespace as R

import pytest

from app.calculators.canadian_labour_basis import derive_canadian_labour_basis


def _result(assistance):
    line = R(line_id="L1", amount_usd=1_000_000.0, spend_category="btl_crew_labor", is_memo=False)
    facts = [R(fact_key=f"line_fact:L1:{k}", value=v) for k, v in
             (("role", "other"), ("canadian_status", "resident_citizen"), ("service_location", "in_canada"), ("payee_type", "employee"),
              ("payment_status", "paid"), ("assistance_usd", str(assistance)))]
    return derive_canadian_labour_basis([line], facts, gross_budget_usd=1_000_000.0)


def test_cptc_assistance_acts_on_net_production_cost_and_not_on_the_labour_line():
    r = _result(300_000.0)
    assert r.evidenced_eligible_labour_usd["ca_federal_cptc"] == 1_000_000.0
    assert r.net_production_cost_usd == 700_000.0 and r.statutory_cap_usd["ca_federal_cptc"] == pytest.approx(420_000.0)
    assert r.qualified_labour_usd["ca_federal_cptc"] == pytest.approx(420_000.0)
    assert r.qualified_labour_usd["ca_federal_pstc"] == pytest.approx(700_000.0)      # PSTC keeps the per-line reduction


def test_without_assistance_the_cap_is_sixty_percent_of_production_cost():
    r = _result(0.0)
    assert r.qualified_labour_usd["ca_federal_cptc"] == pytest.approx(600_000.0) and r.qualified_labour_usd["ca_federal_pstc"] == pytest.approx(1_000_000.0)
