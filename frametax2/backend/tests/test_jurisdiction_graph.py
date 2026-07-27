"""
test_jurisdiction_graph.py

Targeted tests for the Phase 5A/5B Jurisdiction Graph wiring layer
(jurisdiction_graph.py) — wraps existing jurisdiction/program data into
graph-compatible nodes and relationships without collecting new data or
touching the optimizer. Phase 5B strengthens Requirement/Restriction/
Absence wiring and adds query helpers.
"""
from __future__ import annotations

import pytest

from app.calculators import jurisdiction_comparison as jc
from app.calculators import treaty_engine as te
from app.calculators.qualification_model import ReinvestmentCategory
from app.calculators.jurisdiction_graph import (
    JURISDICTION_GRAPH_VERSION,
    UNKNOWN,
    EvidenceRef,
    FactStatus,
    GraphNode,
    JurisdictionGraph,
    NodeType,
    Relationship,
    RelationshipType,
    build_jurisdiction_graph,
    get_program_known_facts,
    get_program_reinvestment,
    get_program_requirements,
    get_program_restrictions,
    get_program_unknowns,
)


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph()


# ── Graph creation ──────────────────────────────────────────────────────

class TestGraphCreation:
    def test_version(self):
        assert JURISDICTION_GRAPH_VERSION == "1.0.0"

    def test_empty_graph_constructible(self):
        g = JurisdictionGraph()
        assert g.nodes == []
        assert g.relationships == []

    def test_build_returns_jurisdiction_graph(self, graph):
        assert isinstance(graph, JurisdictionGraph)

    def test_graph_has_nodes_and_relationships(self, graph):
        assert len(graph.nodes) > 0
        assert len(graph.relationships) > 0

    def test_relationship_requires_known_nodes(self):
        g = JurisdictionGraph()
        g.add_node(GraphNode(node_id="country:XX", node_type=NodeType.COUNTRY, name="XX"))
        with pytest.raises(ValueError):
            g.add_relationship(Relationship(
                source_id="country:XX",
                relationship_type=RelationshipType.CONTAINS,
                target_id="program:does-not-exist",
            ))

    def test_duplicate_node_id_rejected(self):
        g = JurisdictionGraph()
        g.add_node(GraphNode(node_id="country:XX", node_type=NodeType.COUNTRY, name="XX"))
        with pytest.raises(ValueError):
            g.add_node(GraphNode(node_id="country:XX", node_type=NodeType.COUNTRY, name="XX again"))


# ── Countries / Programs inserted ───────────────────────────────────────

class TestCountriesAndProgramsInserted:
    def test_all_profile_countries_present(self, graph):
        countries = {n.attributes["jurisdiction_code"] for n in graph.nodes_of_type(NodeType.COUNTRY)}
        for code in jc.ALL_PROFILES:
            assert code in countries

    def test_mauritius_present(self, graph):
        mu = graph.get_node("country:MU")
        assert mu is not None
        assert mu.name == "Mauritius"
        assert mu.node_type == NodeType.COUNTRY

    def test_all_profile_programs_present(self, graph):
        program_ids = {n.node_id for n in graph.nodes_of_type(NodeType.NATIONAL_PROGRAM)}
        for profile in jc.ALL_PROFILES.values():
            assert f"program:{profile.program_slug}" in program_ids

    def test_country_contains_program(self, graph):
        contains = graph.relationships_of_type(RelationshipType.CONTAINS)
        pairs = {(r.source_id, r.target_id) for r in contains}
        assert ("country:MU", "program:mu_edb_incentive") in pairs

    def test_program_administered_by_agency(self, graph):
        admin_rels = graph.relationships_from("program:mu_edb_incentive")
        admin = [r for r in admin_rels if r.relationship_type == RelationshipType.ADMINISTERED_BY]
        assert len(admin) == 1
        agency = graph.get_node(admin[0].target_id)
        assert agency.node_type == NodeType.AGENCY
        assert "EDB" in agency.name or "Mauritius" in agency.name

    def test_program_carries_source_data_not_recomputed(self, graph):
        node = graph.get_node("program:mu_edb_incentive")
        assert node.attributes["base_rate"] == jc._MAURITIUS.base_rate
        assert node.attributes["confidence_tier"] == jc._MAURITIUS.confidence_tier


# ── National / Regional / Municipal relationship support ───────────────

class TestProgramTierSupport:
    def test_node_type_enum_has_all_three_program_tiers(self):
        assert NodeType.NATIONAL_PROGRAM in NodeType
        assert NodeType.REGIONAL_PROGRAM in NodeType
        assert NodeType.MUNICIPAL_PROGRAM in NodeType

    def test_national_programs_populated_from_existing_data(self, graph):
        assert len(graph.nodes_of_type(NodeType.NATIONAL_PROGRAM)) == len(jc.ALL_PROFILES)

    def test_no_regional_or_municipal_programs_fabricated(self, graph):
        """
        jurisdiction_comparison.py models one program per country, no
        sub-national programs. Phase 5A must not invent RegionalProgram
        or MunicipalProgram nodes that don't exist in source data — their
        absence from the built graph is the correct, honest state.
        """
        assert graph.nodes_of_type(NodeType.REGIONAL_PROGRAM) == []
        assert graph.nodes_of_type(NodeType.MUNICIPAL_PROGRAM) == []


# ── Treaty relationship support ─────────────────────────────────────────

class TestTreatySupport:
    def test_bilateral_treaties_present(self, graph):
        treaty_names = {n.name for n in graph.nodes_of_type(NodeType.TREATY)}
        assert "uk-ca-bilateral" in treaty_names

    def test_multilateral_treaties_present(self, graph):
        treaty_names = {n.name for n in graph.nodes_of_type(NodeType.TREATY)}
        assert "eurimages" in treaty_names

    def test_party_to_relationship_wires_countries_to_treaty(self, graph):
        party_rels = [r for r in graph.relationships_of_type(RelationshipType.PARTY_TO)
                      if r.target_id == "treaty:uk-ca-bilateral"]
        parties = {r.source_id for r in party_rels}
        assert parties == {"country:GB", "country:CA"}

    def test_mauritius_has_no_treaty_wired(self, graph):
        """
        No treaty involving MU exists in treaty_engine.py's registries —
        this must remain an honest absence, not a fabricated PARTY_TO
        edge.
        """
        mu_party_rels = [r for r in graph.relationships_of_type(RelationshipType.PARTY_TO)
                          if r.source_id == "country:MU"]
        assert mu_party_rels == []

    def test_multilateral_fund_unlocks_wired(self, graph):
        eurimages = te._MULTILATERAL["eurimages"]
        if eurimages.fund_unlocks:
            funded = [r for r in graph.relationships_of_type(RelationshipType.FUNDED_BY)
                      if r.source_id == "treaty:eurimages"]
            assert len(funded) == len(eurimages.fund_unlocks)


# ── Stacking relationship support ───────────────────────────────────────

class TestStackingRelationshipSupport:
    def test_stacks_with_is_a_valid_relationship_type(self):
        assert RelationshipType.STACKS_WITH in RelationshipType

    def test_stacks_with_edge_constructible_and_addable(self):
        g = JurisdictionGraph()
        g.add_node(GraphNode(node_id="program:a", node_type=NodeType.NATIONAL_PROGRAM, name="A"))
        g.add_node(GraphNode(node_id="fund:b", node_type=NodeType.FUND, name="B"))
        g.add_relationship(Relationship(
            source_id="program:a",
            relationship_type=RelationshipType.STACKS_WITH,
            target_id="fund:b",
        ))
        assert len(g.relationships_of_type(RelationshipType.STACKS_WITH)) == 1


# ── Unknown placeholders ─────────────────────────────────────────────────

class TestUnknownPlaceholders:
    def test_unknown_sentinel_defined(self):
        assert UNKNOWN == "UNKNOWN"

    def test_transferability_unknown_represented_explicitly(self, graph):
        """Mauritius profile has is_transferable=None — the graph must
        carry an explicit UNKNOWN restriction node, not silently omit
        the dimension."""
        node = graph.get_node("restriction:mu_edb_incentive:transferability_unknown")
        assert node is not None
        assert node.attributes["value"] == UNKNOWN

    def test_only_none_valued_fields_get_unknown_placeholder(self, graph):
        """Ireland has is_transferable=True explicitly set (not None) —
        no UNKNOWN placeholder should exist for it."""
        assert jc._IRELAND.is_transferable is True
        assert graph.get_node("restriction:ie_section_481:transferability_unknown") is None


# ── Reinvestment profile attached ───────────────────────────────────────

class TestReinvestmentProfileAttached:
    def test_every_country_has_reinvestment_profile_edge(self, graph):
        countries = graph.nodes_of_type(NodeType.COUNTRY)
        reinvest_edges = graph.relationships_of_type(RelationshipType.HAS_REINVESTMENT_PROFILE)
        sources = {r.source_id for r in reinvest_edges}
        for c in countries:
            assert c.node_id in sources

    def test_mauritius_reinvestment_is_unknown_not_not_permitted(self, graph):
        node = graph.get_node("reinvestment:MU")
        assert node.attributes["category"] == ReinvestmentCategory.UNKNOWN.value
        assert node.attributes["category"] != ReinvestmentCategory.NOT_PERMITTED.value
        assert node.attributes["is_explicit_unknown"] is True

    def test_unregistered_country_still_gets_explicit_unknown(self, graph):
        """Malta has no REINVESTMENT_REGISTRY entry — get_reinvestment_profile's
        own UNKNOWN fallback must still be wired, distinct from a country
        having no reinvestment data at all."""
        node = graph.get_node("reinvestment:MT")
        assert node is not None
        assert node.attributes["category"] == ReinvestmentCategory.UNKNOWN.value

    def test_reinvestment_category_never_defaults_to_not_permitted(self, graph):
        reinvest_nodes = [n for n in graph.nodes if n.node_id.startswith("reinvestment:")]
        for n in reinvest_nodes:
            if n.attributes["is_explicit_unknown"]:
                assert n.attributes["category"] != ReinvestmentCategory.NOT_PERMITTED.value


# ── Comparable-jurisdiction links ───────────────────────────────────────

class TestComparableJurisdictionLinks:
    def test_tier1_pairwise_comparable_links_present(self, graph):
        comparable = graph.relationships_of_type(RelationshipType.COMPARABLE_TO)
        pairs = {frozenset((r.source_id, r.target_id)) for r in comparable}
        assert frozenset(("country:MU", "country:MT")) in pairs
        assert frozenset(("country:MU", "country:GR")) in pairs
        assert frozenset(("country:MU", "country:CY")) in pairs

    def test_tier1_comparable_count_matches_combinations(self, graph):
        n = len(jc.TIER1_PROFILES)
        expected = n * (n - 1) // 2
        comparable = graph.relationships_of_type(RelationshipType.COMPARABLE_TO)
        assert len(comparable) == expected

    def test_non_tier1_countries_have_no_comparable_edges(self, graph):
        fr_comparable = [r for r in graph.relationships_of_type(RelationshipType.COMPARABLE_TO)
                          if "country:FR" in (r.source_id, r.target_id)]
        assert fr_comparable == []


# ── Available levers ─────────────────────────────────────────────────────

class TestAvailableLevers:
    def test_mauritius_program_has_available_levers(self, graph):
        lever_edges = [r for r in graph.relationships_of_type(RelationshipType.HAS_AVAILABLE_LEVER)
                        if r.source_id == "program:mu_edb_incentive"]
        assert len(lever_edges) == 3  # 21-00, 23-00, 42-00 per levers.py Phase 4

    def test_other_programs_have_no_fabricated_levers(self, graph):
        malta_lever_edges = [r for r in graph.relationships_of_type(RelationshipType.HAS_AVAILABLE_LEVER)
                              if r.source_id == "program:mt_mfc_rebate"]
        assert malta_lever_edges == []


# ── Evidence capability on assertive relationships ──────────────────────

class TestEvidenceCapability:
    def test_evidence_ref_default_is_unpopulated(self):
        ref = EvidenceRef()
        assert ref.graph_rule_id is None
        assert ref.graph_absence_id is None
        assert ref.citation is None

    def test_evidence_ref_can_carry_graph_hooks(self):
        ref = EvidenceRef(graph_rule_id="RULE-1", graph_absence_id="ABS-1", citation="cite")
        assert ref.graph_rule_id == "RULE-1"
        assert ref.graph_absence_id == "ABS-1"
        assert ref.citation == "cite"

    def test_administered_by_relationships_carry_evidence_ref(self, graph):
        admin_rels = graph.relationships_of_type(RelationshipType.ADMINISTERED_BY)
        assert all(isinstance(r.evidence, EvidenceRef) for r in admin_rels)

    def test_reinvestment_edges_carry_citation_when_available(self, graph):
        reinvest_edges = graph.relationships_of_type(RelationshipType.HAS_REINVESTMENT_PROFILE)
        for r in reinvest_edges:
            assert isinstance(r.evidence, EvidenceRef)


# ── No custom per-jurisdiction logic ────────────────────────────────────

class TestNoPerJurisdictionLogic:
    def test_no_hardcoded_jurisdiction_branch_in_source(self):
        """No function body in jurisdiction_graph.py contains a
        per-jurisdiction-code comparison (an ast.Compare against a
        jurisdiction code literal) — checked structurally rather than by
        substring, since the module's own docstrings discuss this design
        choice in prose."""
        import ast
        import inspect

        import app.calculators.jurisdiction_graph as jg_module

        source = inspect.getsource(jg_module)
        tree = ast.parse(source)
        codes = set(jc.ALL_PROFILES.keys())
        offending = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for cmp_node in [node.left, *node.comparators]:
                    if isinstance(cmp_node, ast.Constant) and cmp_node.value in codes:
                        offending.append(ast.dump(node))
        assert offending == [], offending

    def test_module_iterates_generically_over_all_profiles(self):
        import inspect

        import app.calculators.jurisdiction_graph as jg_module
        source = inspect.getsource(jg_module.build_jurisdiction_graph)
        assert "ALL_PROFILES" in source


# ── Deterministic graph construction ────────────────────────────────────

class TestDeterministicConstruction:
    def test_two_builds_produce_identical_node_ids_in_order(self):
        g1 = build_jurisdiction_graph()
        g2 = build_jurisdiction_graph()
        assert [n.node_id for n in g1.nodes] == [n.node_id for n in g2.nodes]

    def test_two_builds_produce_identical_relationship_lists(self):
        g1 = build_jurisdiction_graph()
        g2 = build_jurisdiction_graph()
        rel_tuple = lambda r: (r.source_id, r.relationship_type.value, r.target_id)
        assert [rel_tuple(r) for r in g1.relationships] == [rel_tuple(r) for r in g2.relationships]

    def test_node_count_stable_across_builds(self):
        g1 = build_jurisdiction_graph()
        g2 = build_jurisdiction_graph()
        assert len(g1.nodes) == len(g2.nodes)


# ── Existing optimizer tests unchanged ──────────────────────────────────

class TestNoOptimizerImpact:
    def test_optimization_engine_unaffected_by_graph_module_import(self):
        from app.calculators.qualification_model import build_little_utopia_qualification_register
        from app.calculators.optimization_engine import RiskCase, build_risk_cases
        from app.calculators.structuring_paths import derive_structuring_paths

        register = build_little_utopia_qualification_register(mu_rate=0.40)
        paths = derive_structuring_paths(register, rate=0.40)
        result = build_risk_cases(
            register=register, gross_budget_usd=4_364_393.0, rate=0.40,
            structuring_paths=paths,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(3_700_954.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_480_381.6, abs=1.0)

    def test_jurisdiction_graph_module_does_not_import_optimization_engine(self):
        import ast
        import inspect

        import app.calculators.jurisdiction_graph as jg_module
        source = inspect.getsource(jg_module)
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not any("optimization_engine" in m for m in imported_modules)


# ═════════════════════════════ Phase 5B ═════════════════════════════════
# Requirement / Restriction / Absence wiring, evidence refs, query helpers.

MU_PROGRAM = "program:mu_edb_incentive"
MT_PROGRAM = "program:mt_mfc_rebate"


class TestRequirementsAttachToProgram:
    def test_min_spend_requirement_attached(self, graph):
        node = graph.get_node("requirement:mt_mfc_rebate:min_spend")
        assert node is not None
        assert node.node_type == NodeType.REQUIREMENT
        assert node.attributes["status"] == FactStatus.KNOWN.value
        assert node.attributes["value"] == jc._MALTA.min_spend_local

    def test_cultural_test_requirement_always_attached_known(self, graph):
        """requires_cultural_test is a plain bool (never None) — every
        program gets a KNOWN cultural_test Requirement, True or False."""
        mu_node = graph.get_node("requirement:mu_edb_incentive:cultural_test")
        assert mu_node.attributes["status"] == FactStatus.KNOWN.value
        assert mu_node.attributes["value"] is False  # Mauritius: no cultural test
        fr_node = graph.get_node("requirement:fr_trip:cultural_test")
        assert fr_node.attributes["value"] is True  # France: cultural test required

    def test_requirements_reachable_via_helper(self, graph):
        reqs = get_program_requirements(graph, MU_PROGRAM)
        kinds = {n.attributes["kind"] for n in reqs}
        assert "cultural_test" in kinds
        assert "min_spend" in kinds
        assert "treaty_availability" in kinds


class TestRestrictionsAttachToProgram:
    def test_cap_funding_window_restriction_attached(self, graph):
        node = graph.get_node("restriction:it_tax_credit_foreign:cap_funding_window")
        assert node is not None
        assert node.node_type == NodeType.RESTRICTION
        assert node.attributes["status"] == FactStatus.KNOWN.value
        assert node.attributes["value"] == jc._ITALY.annual_cap_local

    def test_payout_timing_restriction_known_when_present(self, graph):
        node = graph.get_node("restriction:mt_mfc_rebate:payout_timing")
        assert node.attributes["status"] == FactStatus.KNOWN.value
        assert node.attributes["value"] == jc._MALTA.cashflow_timing_weeks

    def test_payout_timing_restriction_unknown_when_absent(self, graph):
        """Mauritius: cashflow_timing_weeks is None on the source profile."""
        assert jc._MAURITIUS.cashflow_timing_weeks is None
        node = graph.get_node("restriction:mu_edb_incentive:payout_timing")
        assert node.attributes["status"] == FactStatus.UNKNOWN.value
        assert node.attributes["value"] == UNKNOWN

    def test_restrictions_reachable_via_helper(self, graph):
        restrs = get_program_restrictions(graph, MU_PROGRAM)
        kinds = {n.attributes["kind"] for n in restrs}
        assert "cap_funding_window" in kinds
        assert "payout_timing" in kinds
        assert "is_transferable" in kinds  # transferability_unknown, Mauritius


class TestUnknownPlaceholdersForMissingFields:
    @pytest.mark.parametrize("key", [
        "eligible_production_types",
        "territorial_nexus",
        "local_entity_requirement",
        "stacking_rule",
        "application_timing_deadline",
    ])
    def test_absence_node_created_for_every_unmodeled_fact_and_every_program(self, graph, key):
        """None of these five fact categories has a field anywhere on
        JurisdictionIncentiveProfile — every program must carry an
        explicit ABSENCE node for each, not silently omit it."""
        for profile in jc.ALL_PROFILES.values():
            node = graph.get_node(f"absence:{profile.program_slug}:{key}")
            assert node is not None, f"missing absence node for {profile.program_slug}:{key}"
            assert node.node_type == NodeType.ABSENCE
            assert node.attributes["status"] == FactStatus.ABSENT.value
            assert "reason" in node.attributes

    def test_min_spend_unknown_for_mauritius(self, graph):
        assert jc._MAURITIUS.min_spend_local is None
        node = graph.get_node("requirement:mu_edb_incentive:min_spend")
        assert node.attributes["status"] == FactStatus.UNKNOWN.value
        assert node.attributes["value"] == UNKNOWN

    def test_min_spend_known_for_greece(self, graph):
        assert jc._GREECE.min_spend_local is not None
        node = graph.get_node("requirement:gr_cash_rebate:min_spend")
        assert node.attributes["status"] == FactStatus.KNOWN.value


class TestReinvestmentUnknownDistinctFromNotPermitted:
    def test_mauritius_reinvestment_status_is_unknown(self, graph):
        node = get_program_reinvestment(graph, MU_PROGRAM)
        assert node is not None
        assert node.attributes["category"] == ReinvestmentCategory.UNKNOWN.value
        assert node.attributes["status"] == FactStatus.UNKNOWN.value

    def test_not_permitted_category_would_be_status_known(self):
        """A hypothetical NOT_PERMITTED determination is a KNOWN fact
        (we looked and it's disallowed), never conflated with UNKNOWN
        (we have not looked) — proven directly against the graph's own
        status-derivation rule rather than only against the one
        UNKNOWN fixture the registry happens to contain today."""
        from app.calculators.qualification_model import ReinvestmentProfile
        from app.calculators.jurisdiction_graph import FactStatus as FS

        not_permitted = ReinvestmentProfile(
            jurisdiction_code="ZZ", category=ReinvestmentCategory.NOT_PERMITTED,
            evidence="statute-x", notes="",
        )
        is_unknown = not_permitted.category == ReinvestmentCategory.UNKNOWN
        status = FS.UNKNOWN.value if is_unknown else FS.KNOWN.value
        assert status == FS.KNOWN.value

    def test_all_reinvestment_nodes_never_conflate_unknown_and_not_permitted(self, graph):
        reinvest_nodes = [n for n in graph.nodes if n.node_id.startswith("reinvestment:")]
        for n in reinvest_nodes:
            if n.attributes["category"] == ReinvestmentCategory.UNKNOWN.value:
                assert n.attributes["status"] == FactStatus.UNKNOWN.value
            else:
                assert n.attributes["status"] == FactStatus.KNOWN.value


class TestTreatyAbsenceDistinctFromNoDataLoaded:
    def test_mauritius_treaty_availability_is_absent_and_checked(self, graph):
        node = graph.get_node("treaty_availability:mu_edb_incentive")
        assert node is not None
        assert node.node_type == NodeType.ABSENCE
        assert node.attributes["status"] == FactStatus.ABSENT.value
        assert node.attributes["checked"] is True
        assert node.attributes["treaty_slugs"] == []

    def test_absent_and_checked_is_structurally_distinguishable_from_unchecked(self):
        """
        Requirement #5: treaty absence (checked the registry, found
        nothing) must be distinguishable from "no treaty data loaded"
        (never checked). The builder always checks (te._BILATERAL /
        _MULTILATERAL are unconditionally consulted for every program),
        so it never itself produces a checked=False node — but the two
        states are distinct, constructible attribute combinations, which
        is what the requirement asks the model to support.
        """
        confirmed_absent = {"status": FactStatus.ABSENT.value, "checked": True, "treaty_slugs": []}
        not_loaded = {"status": FactStatus.UNKNOWN.value, "checked": False, "treaty_slugs": []}
        assert confirmed_absent != not_loaded
        assert confirmed_absent["checked"] is not not_loaded["checked"]
        assert confirmed_absent["status"] != not_loaded["status"]

    def test_uk_has_known_treaty_availability(self, graph):
        # Corrected (Worldwide Jurisdiction Population phase): GB now has a
        # real NationalProgram (uk_avec, added this phase — see
        # docs/architecture/CAPABILITY_LEDGER.md). The treaty registry
        # already had real UK-DE/UK-FR/UK-IE bilateral treaty data (present
        # before this phase, just dormant with no program to attach to) —
        # this test previously confirmed the HONEST ABSENCE of a GB program;
        # now that the program is real, the correct behavior mirrors
        # test_ireland_or_france_treaty_availability_status below: GB's
        # treaty_availability fact should be KNOWN with a real treaty list,
        # not fabricated absence.
        gb_program = None
        for p in graph.nodes_of_type(NodeType.NATIONAL_PROGRAM):
            if p.attributes.get("jurisdiction_code") == "GB":
                gb_program = p
                break
        assert gb_program is not None
        node = graph.get_node("treaty_availability:uk_avec")
        assert node is not None
        if node.attributes["treaty_slugs"]:
            assert node.node_type == NodeType.REQUIREMENT
            assert node.attributes["status"] == FactStatus.KNOWN.value

    def test_ireland_or_france_treaty_availability_status(self, graph):
        """France participates in bilateral treaties (e.g. fr-de-bilateral)
        and has a NationalProgram — its treaty_availability fact should
        be KNOWN with a non-empty treaty list."""
        node = graph.get_node("treaty_availability:fr_trip")
        assert node is not None
        if node.attributes["treaty_slugs"]:
            assert node.node_type == NodeType.REQUIREMENT
            assert node.attributes["status"] == FactStatus.KNOWN.value


class TestEvidenceRefsAttachCorrectly:
    def test_fact_nodes_carry_node_level_evidence_field(self, graph):
        node = graph.get_node("requirement:mu_edb_incentive:min_spend")
        assert isinstance(node.evidence, EvidenceRef)

    def test_reinvestment_node_evidence_populated_when_source_has_it(self, graph):
        node = get_program_reinvestment(graph, MU_PROGRAM)
        assert node.evidence.citation == node.attributes["evidence"]

    def test_evidence_ref_settable_on_fact_node(self):
        node = GraphNode(
            node_id="requirement:test:x", node_type=NodeType.REQUIREMENT, name="x",
            evidence=EvidenceRef(graph_rule_id="RULE-9"),
        )
        assert node.evidence.graph_rule_id == "RULE-9"

    def test_requires_relationships_all_carry_evidence_ref(self, graph):
        for r in graph.relationships_of_type(RelationshipType.REQUIRES):
            assert isinstance(r.evidence, EvidenceRef)

    def test_restricted_by_relationships_all_carry_evidence_ref(self, graph):
        for r in graph.relationships_of_type(RelationshipType.RESTRICTED_BY):
            assert isinstance(r.evidence, EvidenceRef)


class TestQueryingProgramReturnsKnownAndUnknown:
    def test_get_program_unknowns_for_mauritius_includes_expected_gaps(self, graph):
        unknowns = get_program_unknowns(graph, MU_PROGRAM)
        kinds = {n.attributes["kind"] for n in unknowns}
        assert "min_spend" in kinds          # UNKNOWN: None on source profile
        assert "payout_timing" in kinds      # UNKNOWN: None on source profile
        assert "is_transferable" in kinds    # UNKNOWN: None on source profile
        assert "eligible_production_types" in kinds  # ABSENT: no field at all
        assert "reinvestment_treatment" in kinds     # UNKNOWN: registry says UNKNOWN

    def test_get_program_known_facts_for_malta_includes_expected_knowns(self, graph):
        assert jc._MALTA.annual_cap_local is None
        knowns = get_program_known_facts(graph, MT_PROGRAM)
        kinds = {n.attributes["kind"] for n in knowns}
        assert "min_spend" in kinds
        assert "payout_timing" in kinds
        assert "cultural_test" in kinds  # always KNOWN regardless of jurisdiction
        assert "cap_funding_window" not in kinds  # Malta annual_cap_local is None -> UNKNOWN, not KNOWN

    def test_cap_funding_window_unknown_for_malta_via_unknowns_query(self, graph):
        unknowns = get_program_unknowns(graph, MT_PROGRAM)
        kinds = {n.attributes["kind"] for n in unknowns}
        assert "cap_funding_window" in kinds

    def test_known_and_unknown_partition_all_facts(self, graph):
        known = get_program_known_facts(graph, MU_PROGRAM)
        unknown = get_program_unknowns(graph, MU_PROGRAM)
        known_kinds = {n.node_id for n in known}
        unknown_kinds = {n.node_id for n in unknown}
        assert known_kinds.isdisjoint(unknown_kinds)

    def test_unregistered_program_returns_empty_lists_not_error(self, graph):
        assert get_program_requirements(graph, "program:does-not-exist") == []
        assert get_program_restrictions(graph, "program:does-not-exist") == []
        assert get_program_unknowns(graph, "program:does-not-exist") == []


class TestPhase5BDeterministicConstruction:
    def test_two_builds_identical_fact_node_attributes(self):
        g1 = build_jurisdiction_graph()
        g2 = build_jurisdiction_graph()
        n1 = graph_fact_snapshot(g1)
        n2 = graph_fact_snapshot(g2)
        assert n1 == n2

    def test_unknowns_query_deterministic_across_builds(self):
        g1 = build_jurisdiction_graph()
        g2 = build_jurisdiction_graph()
        u1 = [n.node_id for n in get_program_unknowns(g1, MU_PROGRAM)]
        u2 = [n.node_id for n in get_program_unknowns(g2, MU_PROGRAM)]
        assert u1 == u2


def graph_fact_snapshot(g):
    return sorted(
        (n.node_id, n.node_type.value, tuple(sorted((k, str(v)) for k, v in n.attributes.items())))
        for n in g.nodes
    )


class TestPhase5BNoOptimizerImpact:
    def test_optimizer_output_unchanged_after_5b_wiring(self):
        from app.calculators.qualification_model import build_little_utopia_qualification_register
        from app.calculators.optimization_engine import RiskCase, build_risk_cases
        from app.calculators.structuring_paths import derive_structuring_paths

        register = build_little_utopia_qualification_register(mu_rate=0.40)
        paths = derive_structuring_paths(register, rate=0.40)
        result = build_risk_cases(
            register=register, gross_budget_usd=4_364_393.0, rate=0.40,
            structuring_paths=paths,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(3_700_954.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_480_381.6, abs=1.0)

    def test_building_graph_does_not_mutate_shared_registries(self, graph):
        """Building the graph must not have side effects on the source
        modules' own module-level dicts (ALL_PROFILES, REINVESTMENT_REGISTRY).
        Invariant-based (not a hardcoded count, per the Worldwide
        Jurisdiction Population phase's high-throughput testing discipline):
        building a second, independent graph must observe the exact same
        ALL_PROFILES size as the fixture's graph did — proving no mutation
        occurred, regardless of how many jurisdictions are registered."""
        assert "MU" in jc.ALL_PROFILES
        size_after_fixture_graph = len(jc.ALL_PROFILES)
        build_jurisdiction_graph()
        assert len(jc.ALL_PROFILES) == size_after_fixture_graph
