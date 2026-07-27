"""
Optimizer-integration phase: the conditional (KNOWN BUT NON-PRICEABLE)
program layer and the structure compatibility engine.

These tests are invariant-based wherever the underlying data can grow —
counts are derived from the catalog itself rather than snapshotted — so
adding a program never forces a test edit, while real wiring defects
still fail.
"""
from __future__ import annotations

import pytest

from app.calculators.conditional_programs import (
    CONDITIONAL_PROGRAM_TYPES,
    build_conditional_program_index,
    conditional_nodes_for,
    get_conditional_program_index,
    node_to_dict,
)
from app.calculators.structure_compatibility import (
    CompatibilityVerdict,
    compatibility_to_dict,
    evaluate_structure_compatibility,
)


@pytest.fixture(scope="module")
def index():
    return get_conditional_program_index()


class TestConditionalProgramIndex:
    def test_index_matches_catalog_exactly(self, index):
        """Invariant: one node per catalog record whose program_type is a
        conditional (non-priceable) type — derived, not snapshotted."""
        from app.data import global_inventory as gi

        expected = [
            p for p in gi.ALL_PROGRAMS
            if p.program_type in CONDITIONAL_PROGRAM_TYPES
        ]
        assert len(index.nodes) == len(expected)
        assert len(index.nodes) > 0, "catalog must yield conditional programs"

    def test_production_support_never_included(self, index):
        """production_support was classified NO ACTIVE APPLICABLE PROGRAM
        (facilitation only, no monetary mechanism) — there is nothing
        conditional to pursue, so it must never appear."""
        assert all(n.program_type != "production_support" for n in index.nodes)

    def test_every_node_has_stable_identity_and_provenance(self, index):
        ids = [n.node_id for n in index.nodes]
        assert len(ids) == len(set(ids)), "node ids must be unique"
        for n in index.nodes:
            assert n.node_id.startswith("COND-")
            assert n.program_name and n.jurisdiction_name
            assert n.selection_basis  # every node states HOW its award is decided

    def test_subnational_codes_map_to_parent_country(self, index):
        for n in index.nodes:
            if n.scope == "subnational":
                assert "-" in n.jurisdiction_code
                assert n.parent_country == n.jurisdiction_code.split("-", 1)[0]

    def test_supranational_nodes_have_no_parent(self, index):
        for n in index.supranational:
            assert n.parent_country is None
            assert n.scope == "supranational"

    def test_index_is_deterministic(self):
        a = build_conditional_program_index()
        b = build_conditional_program_index()
        assert [n.node_id for n in a.nodes] == [n.node_id for n in b.nodes]

    def test_no_node_ever_carries_an_estimated_value(self, index):
        """documented_cap_usd may only ever be the catalog's own stated
        cap — never an expected value. Serialization must say so."""
        for n in index.nodes[:25]:
            d = node_to_dict(n)
            assert d["status"] == "conditional_unpriced"
            assert "not an expected value" in d["pricing_note"]


class TestConditionalAttachment:
    def test_mauritius_baseline_surfaces_none(self):
        """MU has no catalogued conditional programs — the baseline must
        surface zero rather than a fabricated avenue."""
        assert conditional_nodes_for(("MU",)) == []

    def test_participant_country_surfaces_its_own_programs(self):
        nodes = conditional_nodes_for(("MU", "IE"))
        assert nodes, "Ireland has catalogued conditional programs"
        assert all(
            n.parent_country == "IE" or n.scope == "supranational"
            for n in nodes
        )

    def test_subnational_participant_matches_country_programs(self):
        """A participant code like DE-BY must also surface Germany's
        national conditional programs via its country prefix."""
        nodes = conditional_nodes_for(("MU", "DE-BY"))
        assert any(n.scope == "national" and n.parent_country == "DE" for n in nodes)

    def test_supranational_attaches_only_on_proven_membership(self):
        """Eurimages attaches only where treaty_engine proves a
        participant's membership — never guessed."""
        from app.calculators import treaty_engine as te

        eurimages_for_ie = [
            n for n in conditional_nodes_for(("MU", "IE"))
            if "eurimages" in n.program_name.lower()
        ]
        if te.is_eurimages_member("IE"):
            assert eurimages_for_ie, "IE is a Eurimages member — fund must attach"
            assert "treaty_engine" in eurimages_for_ie[0].attachment_basis
        # A structure with no member participant must not attach it.
        assert not [
            n for n in conditional_nodes_for(("MU",))
            if "eurimages" in n.program_name.lower()
        ]

    def test_every_attached_node_states_why(self):
        for n in conditional_nodes_for(("MU", "IE", "DE")):
            assert n.attachment_basis, "attachment must always carry its reason"


class TestStructureCompatibility:
    def _evaluate(self, participants, slugs):
        return evaluate_structure_compatibility(
            structure_id="TEST",
            participants=participants,
            executable_program_slugs=slugs,
            conditional_nodes=conditional_nodes_for(participants),
            graph=None,
        )

    def test_development_fund_is_scope_mismatched(self):
        """A development fund finances development, not the production
        spend a structure prices — it can never offset production cost."""
        result = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        dev = [c for c in result.conditional if c.program_type == "development_fund"]
        assert dev, "Ireland has a development fund in the catalog"
        assert all(c.verdict == CompatibilityVerdict.SCOPE_MISMATCH for c in dev)

    def test_broadcaster_fund_is_gated_on_a_broadcaster(self):
        result = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        bc = [c for c in result.conditional if c.program_type == "broadcaster_fund"]
        assert bc
        for c in bc:
            assert c.verdict == CompatibilityVerdict.GATED
            assert any(g.kind == "broadcaster" for g in c.gates)

    def test_coproduction_fund_gate_reflects_real_treaty_registry(self):
        """MU has no treaty with IE — the co-production gate must report
        unsatisfied, sourced from treaty_engine rather than assumed."""
        result = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        cop = [c for c in result.conditional if c.program_type == "co_production_fund"]
        assert cop
        gates = [g for c in cop for g in c.gates if g.kind == "coproduction"]
        assert gates
        assert gates[0].satisfied is False
        assert "treaty_engine" in gates[0].basis

    def test_stackability_is_never_assumed(self):
        """Absence of STACKS_WITH evidence must surface as a gate, never
        as permission — and never as prohibition."""
        result = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        non_scope = [
            c for c in result.conditional
            if c.verdict != CompatibilityVerdict.SCOPE_MISMATCH
        ]
        assert non_scope
        for c in non_scope:
            assert any(g.kind == "stacking" for g in c.gates)
            assert c.verdict != CompatibilityVerdict.PROHIBITED_BY_EVIDENCE

    def test_cultural_test_gate_comes_from_a_real_condition(self):
        """Ireland's Section 481 carries a cultural_test_required
        RateCondition — it must surface as an executable gate."""
        result = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        cultural = [g for g in result.executable_gates if g.kind == "cultural_test"]
        assert cultural
        assert "cultural_test_required" in cultural[0].basis

    def test_no_conditional_program_ever_enters_npc(self):
        result = self._evaluate(("MU", "IE", "DE"), ("mu_edb_incentive",))
        assert all(c.enters_npc is False for c in result.conditional)
        assert "no conditional program enters Net Production Cost" in compatibility_to_dict(result)["note"]

    def test_pursuable_excludes_scope_mismatch(self):
        result = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        assert all(
            c.verdict != CompatibilityVerdict.SCOPE_MISMATCH
            for c in result.pursuable
        )

    def test_deterministic(self):
        a = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        b = self._evaluate(("MU", "IE"), ("mu_edb_incentive", "ie_section_481"))
        assert [c.conditional_node_id for c in a.conditional] == [
            c.conditional_node_id for c in b.conditional
        ]
        assert a.counts_by_verdict == b.counts_by_verdict


class TestRankingNeverContaminatedByConditional:
    def test_conditional_count_is_only_a_tie_break(self):
        """A structure with MORE conditional avenues must NEVER outrank a
        structure with a lower defensible NPC. Conditional depth may only
        break exact NPC ties."""
        from app.calculators.allocation_pricing import rank_allocated_structures

        class _P:
            def __init__(self, sid, npc):
                self.structure_id = sid
                self.label = sid
                self.is_fully_priced = True
                self.npc_with_adjustments_usd = npc
                self.npc_verified_usd = npc
                self.npc_conservative_usd = npc
                self.selected_incentive_usd = 0.0
                self.inkind_replacement_delta_usd = 0.0
                self.blockers = ()

        cheap_no_funding = _P("CHEAP", 1_000_000.0)
        pricey_rich_funding = _P("PRICEY", 2_000_000.0)
        ranked = rank_allocated_structures(
            [pricey_rich_funding, cheap_no_funding],
            {"CHEAP": 0, "PRICEY": 99},
        )
        assert ranked[0]["structure_id"] == "CHEAP", (
            "lowest defensible NPC must win regardless of conditional depth"
        )

    def test_tie_is_broken_by_conditional_depth(self):
        from app.calculators.allocation_pricing import rank_allocated_structures

        class _P:
            def __init__(self, sid):
                self.structure_id = sid
                self.label = sid
                self.is_fully_priced = True
                self.npc_with_adjustments_usd = 1_000_000.0
                self.npc_verified_usd = 1_000_000.0
                self.npc_conservative_usd = 1_000_000.0
                self.selected_incentive_usd = 0.0
                self.inkind_replacement_delta_usd = 0.0
                self.blockers = ()

        ranked = rank_allocated_structures(
            [_P("A_NO_FUNDING"), _P("B_WITH_FUNDING")],
            {"A_NO_FUNDING": 0, "B_WITH_FUNDING": 3},
        )
        assert ranked[0]["structure_id"] == "B_WITH_FUNDING"
        assert ranked[0]["conditional_pursuable_count"] == 3

    def test_omitting_counts_preserves_prior_behavior(self):
        from app.calculators.allocation_pricing import rank_allocated_structures

        class _P:
            def __init__(self, sid, npc):
                self.structure_id = sid
                self.label = sid
                self.is_fully_priced = True
                self.npc_with_adjustments_usd = npc
                self.npc_verified_usd = npc
                self.npc_conservative_usd = npc
                self.selected_incentive_usd = 0.0
                self.inkind_replacement_delta_usd = 0.0
                self.blockers = ()

        ranked = rank_allocated_structures([_P("B", 2.0), _P("A", 1.0)])
        assert [r["structure_id"] for r in ranked] == ["A", "B"]
        assert ranked[0]["conditional_pursuable_count"] == 0
