"""
test_jurisdiction_graph.py

Targeted tests for the Phase 5A Jurisdiction Graph wiring layer
(jurisdiction_graph.py) — wraps existing jurisdiction/program data into
graph-compatible nodes and relationships without collecting new data or
touching the optimizer.
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
    GraphNode,
    JurisdictionGraph,
    NodeType,
    Relationship,
    RelationshipType,
    build_jurisdiction_graph,
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
        assert cons.qpe_usd == pytest.approx(1_979_913.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(791_965.0, abs=1.0)

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
