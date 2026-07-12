"""
test_ui_presentation.py

Targeted tests for the Phase 8 bridge presentation adapters
(ui_presentation.py). Every function here must be pure reshaping — these
tests assert: JSON-serializability of every output, zero re-ranking/
re-classification (order and values preserved from the source engine),
and that no adapter mutates its input.
"""
from __future__ import annotations

import copy
import json

import pytest

from app.calculators.evidence_graph import AuthorityTier
from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import ConnectorClass, MockConnector
from app.calculators.legal_engine import LegalEngine
from app.calculators.opportunity_discovery import discover_all_opportunities
from app.calculators.optimization_engine import RiskCase
from app.calculators.production_package_intelligence import (
    PersonIntake,
    PersonRole,
    build_production_package,
)
from app.calculators.production_recommendation_engine import (
    RecommendationCategory,
    generate_production_recommendations,
)
from app.calculators.production_structure_composer import compose_production_structures
from app.calculators.qualification_model import (
    GreyAreaStatus,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)

from app.calculators.ui_presentation import (
    AUTHORITY_TIER_LABELS,
    UI_PRESENTATION_VERSION,
    attribute_fact_to_display,
    case_dict_to_display,
    evidence_chain_to_display,
    group_recommendations_by_category,
)

MU_RATE = 0.40
MU_GROSS_BUDGET = 4_364_393.0


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph(mu_rate=MU_RATE)


@pytest.fixture(scope="module")
def collection(graph):
    return discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)


@pytest.fixture()
def register():
    return build_little_utopia_qualification_register(mu_rate=MU_RATE)


@pytest.fixture()
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture()
def composition_result(collection, graph, register, grey_areas):
    return compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )


class TestCaseDictToDisplay:
    def test_priced_candidate_produces_four_riskcase_keys(self, composition_result):
        baseline = next(c for c in composition_result.candidates if c.candidate_id == "PSC-MU")
        display = case_dict_to_display(baseline.cases)
        assert set(display.keys()) == {"conservative", "base", "optimistic", "risk_adjusted"}

    def test_values_match_source_exactly(self, composition_result):
        baseline = next(c for c in composition_result.candidates if c.candidate_id == "PSC-MU")
        display = case_dict_to_display(baseline.cases)
        for case in RiskCase:
            assert display[case.value]["net_production_cost_usd"] == baseline.cases[case].net_production_cost_usd

    def test_none_input_returns_empty_dict_never_fabricated(self):
        assert case_dict_to_display(None) == {}

    def test_unpriced_candidate_returns_empty_dict(self, composition_result):
        unpriced = next((c for c in composition_result.candidates if c.cases is None), None)
        if unpriced is None:
            pytest.skip("no unpriced candidate in this composition result")
        assert case_dict_to_display(unpriced.cases) == {}

    def test_output_is_json_serializable(self, composition_result):
        baseline = next(c for c in composition_result.candidates if c.candidate_id == "PSC-MU")
        json.dumps(case_dict_to_display(baseline.cases))  # must not raise

    def test_does_not_mutate_source(self, composition_result):
        baseline = next(c for c in composition_result.candidates if c.candidate_id == "PSC-MU")
        before = copy.deepcopy(baseline.cases)
        case_dict_to_display(baseline.cases)
        assert baseline.cases == before


class TestAttributeFactToDisplay:
    def test_known_fact_flattened_correctly(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Dir", role=PersonRole.DIRECTOR, nationality="FR")],
        )
        display = attribute_fact_to_display(pkg.package.directors[0].nationality)
        assert display["value"] == "FR"
        assert display["is_known"] is True
        assert display["needs_verification"] is False

    def test_unknown_fact_flattened_correctly(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Writer", role=PersonRole.WRITER)],
        )
        display = attribute_fact_to_display(pkg.package.writers[0].nationality)
        assert display["value"] is None
        assert display["is_known"] is False
        assert display["discovery_sources"], "expected non-empty discovery sources for an unknown fact"

    def test_verification_required_flattened_correctly(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(
                person_id="P1", name="Cast", role=PersonRole.CAST,
                residency="GB", residency_verification_required=True,
            )],
        )
        display = attribute_fact_to_display(pkg.package.cast[0].residency)
        assert display["needs_verification"] is True
        assert display["is_actionable"] is False
        assert display["value"] == "GB"  # carries a value even though not actionable

    def test_discovery_sources_are_plain_strings(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Writer", role=PersonRole.WRITER)],
        )
        display = attribute_fact_to_display(pkg.package.writers[0].nationality)
        assert all(isinstance(s, str) for s in display["discovery_sources"])

    def test_output_is_json_serializable(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Dir", role=PersonRole.DIRECTOR, nationality="FR")],
        )
        json.dumps(attribute_fact_to_display(pkg.package.directors[0].nationality))


class TestEvidenceChainToDisplay:
    @pytest.fixture()
    def committed_chain(self, grey_areas, graph):
        engine = LegalEngine(connectors={ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE)})
        engine.run_acquisition_cycle("2026-07-10", grey_areas=grey_areas, graph=graph)
        engine.record_verification("STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", verified_by="c@example.com", outcome="authority_found")
        engine.record_approval("STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", approved_by="p@example.com")
        ga = next(g for g in grey_areas if g.item_id == "GA-LEGAL-ACCOUNTING-SPLIT")
        commit = engine.commit_and_score(
            "STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", target_jurisdiction_code="MU", as_of_date="2026-07-10",
            rule_text="Test rule text.", tier=AuthorityTier.OFFICIAL_GUIDANCE,
            authority_body="Mauritius Revenue Authority",
            resolves_grey_area=ga, grey_area_outcome=GreyAreaStatus.RESOLVED_INCLUDE,
        )
        return engine.evidence_graph.trace_rule(commit.committed_id)

    def test_preserves_link_order(self, committed_chain):
        display = evidence_chain_to_display(committed_chain)
        assert len(display) == len(committed_chain)
        assert [d["evidence_id"] for d in display] == [c["evidence"].evidence_id for c in committed_chain]

    def test_flattens_nested_dataclass_fields(self, committed_chain):
        display = evidence_chain_to_display(committed_chain)
        link = display[0]
        assert link["authority_tier"] == "OFFICIAL_GUIDANCE"
        assert link["authority_body"] == "Mauritius Revenue Authority"
        assert isinstance(link["superseded"], bool)

    def test_output_is_json_serializable(self, committed_chain):
        json.dumps(evidence_chain_to_display(committed_chain))

    def test_never_resorts(self, committed_chain):
        display1 = evidence_chain_to_display(committed_chain)
        display2 = evidence_chain_to_display(committed_chain)
        assert display1 == display2


class TestGroupRecommendationsByCategory:
    @pytest.fixture()
    def recommendations(self, collection, composition_result, register):
        return generate_production_recommendations(
            collection, composition_result=composition_result, register=register,
            rate=MU_RATE, jurisdiction_code="MU",
        ).recommendations

    def test_every_category_key_present_even_if_empty(self, recommendations):
        grouped = group_recommendations_by_category(recommendations)
        assert set(grouped.keys()) == {c.value for c in RecommendationCategory}

    def test_total_count_preserved(self, recommendations):
        grouped = group_recommendations_by_category(recommendations)
        assert sum(len(v) for v in grouped.values()) == len(recommendations)

    def test_within_group_order_matches_source_order(self, recommendations):
        grouped = group_recommendations_by_category(recommendations)
        financial_ids_in_source = [r.recommendation_id for r in recommendations if r.category == RecommendationCategory.FINANCIAL]
        financial_ids_in_group = [r.recommendation_id for r in grouped["financial"]]
        assert financial_ids_in_group == financial_ids_in_source

    def test_no_recommendation_reclassified(self, recommendations):
        grouped = group_recommendations_by_category(recommendations)
        for category_value, recs in grouped.items():
            assert all(r.category.value == category_value for r in recs)

    def test_empty_input(self):
        grouped = group_recommendations_by_category([])
        assert all(v == [] for v in grouped.values())


class TestAuthorityTierLabels:
    def test_covers_every_tier(self):
        assert set(AUTHORITY_TIER_LABELS.keys()) == set(AuthorityTier)

    def test_labels_are_human_readable(self):
        assert AUTHORITY_TIER_LABELS[AuthorityTier.OFFICIAL_GUIDANCE] == "Official Guidance"
        assert AUTHORITY_TIER_LABELS[AuthorityTier.PRIMARY_LEGISLATION] == "Primary Legislation"


def test_version_constant_present():
    assert UI_PRESENTATION_VERSION
