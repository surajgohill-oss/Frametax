"""
Backend-completion tranche, Objective 4 (pipeline validation) and
Objective 5 (data integrity): full-sweep invariant checks across every
conditional node and every jurisdiction examination in the REAL served
payload — not spot-checks of a few named programs (test_conditional_programs.py
already covers specific cases; this file sweeps ALL of them at once for
invariants that must hold universally).
"""
from __future__ import annotations


def _served():
    from app.demo.little_utopia_state import build_allocated_structures, get_state
    return build_allocated_structures(get_state())


class TestConditionalProgramsNeverEnterNPCAcrossEveryServedStructure:
    """Objective 4 (NPC exclusion) + Objective 5 (pricing/optimizer
    consistency): sweeps every one of the ~177 served structures, not a
    hand-picked example."""

    def test_every_conditional_entry_has_enters_npc_false(self):
        served = _served()
        checked = 0
        for s in served["structures"]:
            for c in s["conditional_compatibility"]["conditional"]:
                assert c["enters_npc"] is False, (s["structure_id"], c["conditional_node_id"])
                checked += 1
        assert checked > 0, "no conditional entries were found — the sweep would be vacuous"

    def test_no_structures_conditional_cap_ever_summed_into_its_own_npc(self):
        """A structure's total_incentive_floor_usd/npc_verified_usd must
        never equal (or trivially include) the sum of its OWN conditional
        programs' documented caps — the two are computed by entirely
        separate code paths (allocation_pricing.py vs conditional_programs.py)
        and must never be silently combined."""
        served = _served()
        for s in served["structures"]:
            conditional_cap_sum = sum(
                cp.get("documented_cap_usd") or 0.0 for cp in s["conditional_programs"]
            )
            if conditional_cap_sum <= 0:
                continue
            # NPC must not simply equal statutory-incentive + conditional-cap —
            # that would mean the conditional layer leaked into pricing.
            npc = s.get("npc_verified_usd")
            floor = s.get("total_incentive_floor_usd")
            if npc is None or floor is None:
                continue
            assert npc != round(s["gross_budget_usd"] - floor - conditional_cap_sum, 2), (
                s["structure_id"], "NPC appears to include the conditional cap sum"
            )


class TestConditionalNodeCatalogIntegrity:
    """Every one of the ~134 worldwide conditional nodes, checked at once."""

    def test_every_node_has_a_valid_program_type(self):
        from app.calculators.conditional_programs import (
            CONDITIONAL_PROGRAM_TYPES, get_conditional_program_index,
        )
        idx = get_conditional_program_index()
        assert len(idx.nodes) > 0
        for node in idx.nodes:
            assert node.program_type in CONDITIONAL_PROGRAM_TYPES, node.node_id

    def test_every_node_id_is_unique(self):
        from app.calculators.conditional_programs import get_conditional_program_index

        idx = get_conditional_program_index()
        ids = [n.node_id for n in idx.nodes]
        assert len(ids) == len(set(ids))

    def test_every_national_or_subnational_node_has_a_parent_country(self):
        from app.calculators.conditional_programs import get_conditional_program_index

        idx = get_conditional_program_index()
        for node in idx.nodes:
            if node.scope in ("national", "subnational"):
                assert node.parent_country, node.node_id
            if node.scope == "supranational":
                assert node.parent_country is None, node.node_id

    def test_documented_cap_is_never_a_fabricated_placeholder_zero(self):
        """A real absent cap must be None, never a silently-inserted 0.0
        (which would read as 'documented $0 cap' — a lie)."""
        from app.calculators.conditional_programs import get_conditional_program_index

        idx = get_conditional_program_index()
        for node in idx.nodes:
            if node.documented_cap_usd is not None:
                assert node.documented_cap_usd > 0, node.node_id


class TestCapabilityOnlyJurisdictionsAreRetainedNotDropped:
    """Objective 4 (capability-only routing): a jurisdiction that can
    physically host the production but has no priceable incentive must
    remain visible in discovery, never silently excluded — swept across
    every jurisdiction the real production's discovery examined."""

    def test_every_examined_jurisdiction_has_exactly_one_of_the_documented_classifications(self):
        served = _served()
        examined = served["discovery"]["examinations"]
        assert len(examined) > 0
        valid = {"incentive_ready", "capability_only", "rejected"}
        for e in examined:
            assert e["classification"] in valid, e["jurisdiction_code"]
            assert e["reason"], e["jurisdiction_code"]

    def test_capability_only_jurisdictions_are_not_also_marked_accepted(self):
        served = _served()
        for e in served["discovery"]["examinations"]:
            if e["classification"] == "capability_only":
                assert e["accepted"] is False, e["jurisdiction_code"]
                assert e["production_capable"] is True, e["jurisdiction_code"]

    def test_capability_only_count_matches_metrics(self):
        served = _served()
        examined = served["discovery"]["examinations"]
        metrics = served["discovery"]["metrics"]
        actual = sum(1 for e in examined if e["classification"] == "capability_only")
        assert actual == metrics["capability_only_count"]
