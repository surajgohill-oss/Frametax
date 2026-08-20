"""
Final Global Discovery phase, Task 91: first-class contingency treatment.
"""
from __future__ import annotations

import pytest

from app.calculators.contingency_treatment import (
    ContingencyAllocation,
    ContingencyDeployment,
    ContingencyState,
    add_deployment,
    expand_contingency_lines,
)
from app.calculators.qualification_derivation import BudgetLine


def _alloc(original=100_000.0, deployments=()):
    return ContingencyAllocation(
        source_account_code="9999",
        source_description="Test contingency",
        original_amount_usd=original,
        deployments=deployments,
    )


def _deploy(amount=10_000.0, category="post_production", note="test"):
    return ContingencyDeployment(
        destination_account_code="9999-D",
        destination_description="destination",
        destination_spend_category=category,
        amount_usd=amount,
        note=note,
        deployed_by="tester",
        deployed_at="2026-07-24T00:00:00Z",
    )


class TestContingencyAllocationModel:
    def test_undeployed_state_when_no_deployments(self):
        a = _alloc()
        assert a.state == ContingencyState.UNDEPLOYED
        assert a.deployed_amount_usd == 0.0
        assert a.undeployed_amount_usd == 100_000.0

    def test_partially_deployed_state(self):
        a = _alloc(deployments=(_deploy(30_000.0),))
        assert a.state == ContingencyState.PARTIALLY_DEPLOYED
        assert a.deployed_amount_usd == 30_000.0
        assert a.undeployed_amount_usd == 70_000.0

    def test_fully_deployed_state(self):
        a = _alloc(deployments=(_deploy(100_000.0),))
        assert a.state == ContingencyState.FULLY_DEPLOYED
        assert a.undeployed_amount_usd == 0.0

    def test_multiple_deployments_sum_correctly(self):
        a = _alloc(deployments=(_deploy(30_000.0), _deploy(20_000.0, category="vfx")))
        assert a.deployed_amount_usd == 50_000.0
        assert a.undeployed_amount_usd == 50_000.0
        assert a.state == ContingencyState.PARTIALLY_DEPLOYED


class TestAddDeployment:
    def test_add_deployment_returns_new_immutable_allocation(self):
        a = _alloc()
        b = add_deployment(a, _deploy(10_000.0))
        assert a.deployments == ()  # original untouched
        assert b.deployments == (b.deployments[0],)
        assert b.deployed_amount_usd == 10_000.0

    def test_rejects_negative_or_zero_amount(self):
        a = _alloc()
        with pytest.raises(ValueError):
            add_deployment(a, _deploy(0.0))
        with pytest.raises(ValueError):
            add_deployment(a, _deploy(-5.0))

    def test_rejects_overdeployment_beyond_undeployed_balance(self):
        a = _alloc(original=100_000.0, deployments=(_deploy(90_000.0),))
        with pytest.raises(ValueError, match="only \\$10,000.00"):
            add_deployment(a, _deploy(10_000.01))

    def test_allows_deploying_exactly_the_remaining_balance(self):
        a = _alloc(original=100_000.0, deployments=(_deploy(90_000.0),))
        b = add_deployment(a, _deploy(10_000.0))
        assert b.state == ContingencyState.FULLY_DEPLOYED


class TestExpandContingencyLines:
    def test_no_allocations_dict_is_a_pure_passthrough(self):
        lines = [BudgetLine("9999", "Contingency", 100_000.0, spend_category="contingency")]
        assert expand_contingency_lines(lines, None) == lines
        assert expand_contingency_lines(lines, {}) == lines

    def test_line_without_matching_allocation_passes_through_unchanged(self):
        lines = [BudgetLine("9999", "Contingency", 100_000.0, spend_category="contingency")]
        other_alloc = {"OTHER": _alloc()}
        assert expand_contingency_lines(lines, other_alloc) == lines

    def test_non_contingency_line_is_never_touched_even_if_code_matches(self):
        """A line whose account_code happens to match an allocation key but
        whose spend_category is NOT 'contingency' must never be split —
        the category label is the gate, not just the code."""
        lines = [BudgetLine("9999", "Some other spend", 5_000.0, spend_category="post_production")]
        allocations = {"9999": _alloc()}
        assert expand_contingency_lines(lines, allocations) == lines

    def test_fully_undeployed_line_expands_to_one_unchanged_amount_line(self):
        lines = [BudgetLine("9999", "Contingency", 100_000.0, spend_category="contingency")]
        allocations = {"9999": _alloc(original=100_000.0)}
        out = expand_contingency_lines(lines, allocations)
        assert len(out) == 1
        assert out[0].amount_usd == 100_000.0
        assert out[0].spend_category == "contingency"
        assert out[0].account_code == "9999"

    def test_partial_deployment_splits_into_remainder_plus_deployment_lines(self):
        lines = [BudgetLine("9999", "Contingency", 100_000.0, spend_category="contingency")]
        allocations = {"9999": _alloc(original=100_000.0, deployments=(_deploy(30_000.0, category="vfx"),))}
        out = expand_contingency_lines(lines, allocations)
        assert len(out) == 2
        by_cat = {l.spend_category: l for l in out}
        assert by_cat["contingency"].amount_usd == 70_000.0
        assert by_cat["vfx"].amount_usd == 30_000.0
        # Both derived lines keep the SAME account_code as the source —
        # critical: production_allocation.py's duplicate-account-code
        # guard must never see two DIFFERENT account codes for one
        # contingency line (allocation happens before this expansion).
        assert all(l.account_code == "9999" for l in out)

    def test_full_deployment_produces_no_undeployed_remainder_line(self):
        lines = [BudgetLine("9999", "Contingency", 100_000.0, spend_category="contingency")]
        allocations = {"9999": _alloc(original=100_000.0, deployments=(_deploy(100_000.0),))}
        out = expand_contingency_lines(lines, allocations)
        assert len(out) == 1
        assert out[0].spend_category == "post_production"
        assert out[0].amount_usd == 100_000.0

    def test_total_dollars_conserved_across_expansion(self):
        lines = [BudgetLine("9999", "Contingency", 301_131.0, spend_category="contingency")]
        allocations = {
            "9999": _alloc(
                original=301_131.0,
                deployments=(_deploy(50_000.0, category="vfx"), _deploy(25_000.0, category="post_production")),
            )
        }
        out = expand_contingency_lines(lines, allocations)
        assert round(sum(l.amount_usd for l in out), 2) == 301_131.0


class TestLadderIntegration:
    """The ladder's own new step (qualification_derivation.py step 5.5)."""

    def test_program_with_no_contingency_rule_excludes_by_structural_definition(self):
        from app.calculators.qualification_derivation import (
            ProductionFacts, derive_qualification_register,
        )
        from app.data.program_spend_rules import QualificationDoctrine

        lines = [BudgetLine("9999", "Contingency", 100_000.0, spend_category="contingency")]
        facts = ProductionFacts(jurisdiction_code="ZZ", accounts_outside_jurisdiction=frozenset())
        reg = derive_qualification_register(
            lines, program_slug="__no_such_program__", facts=facts, rate=0.25,
            rules={}, doctrine=QualificationDoctrine.OPEN_DEFAULT_INCLUDE,
        )
        assert len(reg) == 1
        assert reg[0].state.value == "excluded"
        assert reg[0].authority_basis.value == "structural_definition"

    def test_deployed_portion_is_governed_by_destination_category_doctrine(self):
        """A deployed line is tagged with the destination category and
        reaches the ladder as an ordinary line in that category — under
        OPEN_DEFAULT_INCLUDE with no specific rule for that category
        either, it is INCLUDED (the destination's own doctrine, not the
        contingency default)."""
        from app.calculators.qualification_derivation import (
            ProductionFacts, derive_qualification_register,
        )
        from app.data.program_spend_rules import QualificationDoctrine

        lines = [BudgetLine("9999", "Contingency (deployed)", 30_000.0, spend_category="vfx")]
        facts = ProductionFacts(jurisdiction_code="ZZ", accounts_outside_jurisdiction=frozenset())
        reg = derive_qualification_register(
            lines, program_slug="__no_such_program__", facts=facts, rate=0.25,
            rules={}, doctrine=QualificationDoctrine.OPEN_DEFAULT_INCLUDE,
        )
        assert reg[0].state.value == "qualifies"


class TestMauritiusBaselineUnaffectedByMechanismAvailability:
    """Objective 4 / the project's own standing constraint: Mauritius's
    baseline must not change merely because the ACTUAL/incurred
    contingency-deployment mechanism (Task 91, contingency_treatment.py)
    NOW EXISTS — only an explicit deployment may change it, and even
    then only for the deployed dollars (the undeployed remainder keeps
    MU's own verified unconditional-eligibility rule).

    Consolidated Backend Correction, Part 19-20 (CBA-009): this is a
    DIFFERENT, later correction than Task 91 above — it closes Codex's
    confirmed defect that the full undeployed reserve was projected as
    100%-qualifying unconditionally. build_little_utopia_real_register's
    default `facts=None` now means the PROJECTED expected-utilization
    fact is genuinely unset, so the $301,131.00 contingency line
    correctly becomes a disclosed GREY_AREA_REQUIRES_AUTHORITY line
    (full amount still visible as potential upside) rather than a false
    QUALIFIES. The Task 91 property this class exists to prove — that
    the deployment MECHANISM's mere existence doesn't change the
    baseline — is unaffected and still verified below via explicit
    facts that pin expected utilization to 100% (the historical,
    pre-correction assumption), which reproduces the OLD qualifies
    behavior exactly."""

    def test_mu_contingency_is_disclosed_grey_when_utilization_unset(self):
        from app.calculators.qualification_model import build_little_utopia_real_register

        reg = build_little_utopia_real_register(mu_rate=0.40, contingency_allocations={})
        c = next(a for a in reg if a.account_code == "8300")
        assert c.state.value == "grey_area_requires_authority"
        assert c.amount_usd == 301_131.0
        # Full amount disclosed as potential upside, never silently priced in.
        assert c.incentive_upside_usd == pytest.approx(301_131.0 * 0.40, abs=0.01)

    def test_mu_contingency_qualifies_when_utilization_explicitly_100pct(self):
        """The Task 91 property this class exists to prove — the
        deployment-tracking mechanism's mere presence doesn't change the
        baseline — reproduced under the new correction via an explicit
        producer election of 100% expected utilization."""
        from app.calculators.qualification_derivation import ProductionFacts
        from app.calculators.qualification_model import build_little_utopia_real_register
        from app.data.little_utopia_real_budget import (
            LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
            LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
        )

        facts = ProductionFacts(
            jurisdiction_code="MU",
            accounts_outside_jurisdiction=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
            offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
            contingency_expected_utilization_pct=100.0,
        )
        reg = build_little_utopia_real_register(mu_rate=0.40, facts=facts, contingency_allocations={})
        c = next(a for a in reg if a.account_code == "8300")
        assert c.state.value == "qualifies"
        assert c.amount_usd == 301_131.0

        reg_none = build_little_utopia_real_register(mu_rate=0.40, facts=facts, contingency_allocations=None)
        c_none = next(a for a in reg_none if a.account_code == "8300")
        assert c_none.state.value == "qualifies"
        assert c_none.amount_usd == 301_131.0


class TestLiveStateMutators:
    """app.demo.little_utopia_state's deploy_contingency/reset/current —
    the producer-facing mutation surface, module-level-dict pattern
    matching apply_fact_answers exactly."""

    def teardown_method(self):
        from app.demo.little_utopia_state import reset_contingency_allocations
        reset_contingency_allocations()

    def test_no_op_by_default_mu_baseline_is_disclosed_grey(self):
        """Consolidated Backend Correction, Part 19-20 (CBA-009): the live
        demo state has no `contingency_expected_utilization_pct` fact
        answer by default, so the $301,131.00 reserve is now correctly a
        disclosed GREY_AREA_REQUIRES_AUTHORITY line — not a silent
        100%-unconditional QUALIFIES (the exact defect Codex's audit
        confirmed). See test_mu_contingency_qualifies_when_utilization_
        explicitly_100pct above for reachability of the old value."""
        from app.demo.little_utopia_state import get_state

        state = get_state()
        c = next(a for a in state.register if a.account_code == "8300")
        assert c.state.value == "grey_area_requires_authority"
        assert c.amount_usd == 301_131.0

    def test_fact_answer_sets_utilization_and_restores_qualifies(self):
        """The producer-facing facts API (apply_fact_answers/
        reset_fact_answers) is the EXISTING, generic user-control surface
        for this new fact — same pattern as every other production fact
        this module already exposes (post_work_in_jurisdiction,
        payroll_routing_localized, treaty_partner_code)."""
        from app.demo.little_utopia_state import (
            apply_fact_answers, get_state, reset_fact_answers,
        )

        try:
            apply_fact_answers({"contingency_expected_utilization_pct": 100.0})
            state = get_state()
            c = next(a for a in state.register if a.account_code == "8300")
            assert c.state.value == "qualifies"
            assert c.amount_usd == 301_131.0
        finally:
            reset_fact_answers()

    def test_deploy_then_reset_round_trips_to_original_state(self):
        from app.demo.little_utopia_state import (
            current_contingency_state, deploy_contingency, get_state,
            reset_contingency_allocations,
        )

        deploy_contingency(
            source_account_code="8300",
            destination_account_code="8300-D1",
            destination_description="Extra VFX pass",
            destination_spend_category="vfx",
            amount_usd=50_000.0,
            note="test",
            deployed_by="tester",
        )
        assert "8300" in current_contingency_state()
        state = get_state()
        lines = [a for a in state.register if a.account_code == "8300"]
        assert len(lines) == 2
        assert round(sum(l.amount_usd for l in lines), 2) == 301_131.0

        reset_contingency_allocations()
        assert current_contingency_state() == {}
        state2 = get_state()
        lines2 = [a for a in state2.register if a.account_code == "8300"]
        assert len(lines2) == 1
        assert lines2[0].amount_usd == 301_131.0

    def test_deploy_rejects_unknown_source_account(self):
        from app.demo.little_utopia_state import deploy_contingency

        with pytest.raises(ValueError):
            deploy_contingency(
                source_account_code="0001",  # a real account, but not a contingency-category one
                destination_account_code="X",
                destination_description="x",
                destination_spend_category="vfx",
                amount_usd=1.0,
                note="x",
            )

    def test_deploy_rejects_overdeployment(self):
        from app.demo.little_utopia_state import deploy_contingency

        deploy_contingency(
            source_account_code="8300", destination_account_code="D1",
            destination_description="d", destination_spend_category="vfx",
            amount_usd=300_000.0, note="x",
        )
        with pytest.raises(ValueError):
            deploy_contingency(
                source_account_code="8300", destination_account_code="D2",
                destination_description="d2", destination_spend_category="vfx",
                amount_usd=2_000.0, note="x",
            )

    def test_audit_trail_preserves_every_deployment_with_actor_and_timestamp(self):
        from app.demo.little_utopia_state import current_contingency_state, deploy_contingency

        deploy_contingency(
            source_account_code="8300", destination_account_code="D1",
            destination_description="d1", destination_spend_category="vfx",
            amount_usd=10_000.0, note="first", deployed_by="alice",
        )
        deploy_contingency(
            source_account_code="8300", destination_account_code="D2",
            destination_description="d2", destination_spend_category="post_production",
            amount_usd=5_000.0, note="second", deployed_by="bob",
        )
        alloc = current_contingency_state()["8300"]
        assert len(alloc.deployments) == 2
        assert alloc.deployments[0].deployed_by == "alice"
        assert alloc.deployments[0].note == "first"
        assert alloc.deployments[0].deployed_at  # non-empty timestamp
        assert alloc.deployments[1].deployed_by == "bob"
        assert alloc.original_amount_usd == 301_131.0
        assert alloc.deployed_amount_usd == 15_000.0
        assert alloc.undeployed_amount_usd == 286_131.0


class TestServedPayloadIntegration:
    """The full served /structures payload (build_allocated_structures) —
    the same function the live API route calls. Runtime evidence, not
    just unit-level."""

    def teardown_method(self):
        from app.demo.little_utopia_state import reset_contingency_allocations
        reset_contingency_allocations()

    def test_contingency_key_present_and_empty_by_default(self):
        from app.demo.little_utopia_state import build_allocated_structures, get_state

        served = build_allocated_structures(get_state())
        assert served["contingency"] == {}

    def test_contingency_key_reflects_live_deployment(self):
        from app.demo.little_utopia_state import (
            build_allocated_structures, deploy_contingency, get_state,
        )

        deploy_contingency(
            source_account_code="8300", destination_account_code="D1",
            destination_description="Extra VFX", destination_spend_category="vfx",
            amount_usd=40_000.0, note="served-payload test", deployed_by="tester",
        )
        served = build_allocated_structures(get_state())
        c = served["contingency"]["8300"]
        assert c["original_amount_usd"] == 301_131.0
        assert c["deployed_amount_usd"] == 40_000.0
        assert c["undeployed_amount_usd"] == 261_131.0
        assert c["state"] == "partially_deployed"
        assert len(c["deployments"]) == 1
        assert c["deployments"][0]["destination_spend_category"] == "vfx"

    def test_every_structures_segment_reflects_the_deployment_too(self):
        """The deployment must propagate through EVERY structure's own
        segment pricing (production_allocation happens once per
        structure, contingency expansion happens inside each one's own
        price_segment call) — not just the top-level audit-trail key."""
        from app.demo.little_utopia_state import (
            build_allocated_structures, deploy_contingency, get_state,
        )

        deploy_contingency(
            source_account_code="8300", destination_account_code="D1",
            destination_description="Extra VFX", destination_spend_category="vfx",
            amount_usd=40_000.0, note="test", deployed_by="tester",
        )
        served = build_allocated_structures(get_state())
        mu_structure = next(s for s in served["structures"] if s["structure_id"] == "ALLOC-BASELINE-MU")
        mu_seg = next(sg for sg in mu_structure["segments"] if sg["jurisdiction_code"] == "MU")
        trace_8300 = [t for t in mu_seg["qualification_trace"] if t["account_code"] == "8300"]
        assert len(trace_8300) == 2  # undeployed remainder + deployed-to-vfx
        assert round(sum(t["amount_usd"] for t in trace_8300), 2) == 301_131.0
