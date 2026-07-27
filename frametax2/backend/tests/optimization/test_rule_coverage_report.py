from __future__ import annotations

"""Phase 5 — machine-readable rule-coverage report."""

from app.optimization.rule_coverage_report import build_rule_coverage_report


class TestReportIntegrity:
    def test_deterministic(self):
        assert build_rule_coverage_report() == build_rule_coverage_report()

    def test_every_executable_jurisdiction_prices(self):
        r = build_rule_coverage_report()
        assert r["summary"]["executable_jurisdictions"] == 110
        assert r["pricing_rules"]["executable_jurisdictions_all_price"] is True

    def test_minimum_spend_is_the_sole_machine_enforced_gate(self):
        r = build_rule_coverage_report()
        assert r["qualification_rules"]["machine_enforced_fields"] == ["minimum_spend"]

    def test_incomplete_count_is_consistent(self):
        r = build_rule_coverage_report()
        s = r["summary"]
        assert (
            s["primary_programs_with_requirements_profile"]
            + s["primary_programs_without_requirements_profile"]
            == s["executable_jurisdictions"]
        )
        assert (
            len(r["incomplete"]["jurisdictions_without_requirements_profile"])
            == r["incomplete"]["jurisdictions_without_requirements_profile_count"]
        )

    def test_assumptions_and_roadmap_are_present(self):
        r = build_rule_coverage_report()
        assert r["hard_coded_assumptions"]
        assert all("location" in a for a in r["hard_coded_assumptions"])
        assert r["roadmap"]
