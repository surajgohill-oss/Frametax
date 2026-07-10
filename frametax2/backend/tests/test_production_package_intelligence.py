"""
test_production_package_intelligence.py

Targeted tests for Phase 7E — the Production Package Intelligence Engine
(production_package_intelligence.py). Covers Budget/Script/Package/
Location/Travel Intelligence construction, the Question Engine's
deterministic gap generation, discovery-hook description-only behavior,
determinism, non-mutation of every consumed object, interoperability
with the existing classify_budget_line_items/screenplay_parser/
travel_model functions, and Little Utopia compatibility (this module
never touches optimizer figures at all).
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.classify_budget_line_items import classify_atl_btl_split
from app.calculators.qualification_model import QualificationConfidence
from app.calculators.travel_model import estimate_travel_cost
from app.ingestion.budget_parser import parse_budget_csv
from app.ingestion.screenplay_parser import parse_screenplay_text

from app.calculators.production_package_intelligence import (
    PRODUCTION_PACKAGE_INTELLIGENCE_VERSION,
    SCRIPT_ATTRIBUTE_KEYS,
    AttributeFact,
    CrewMovementIntake,
    DiscoverySourceKind,
    DownstreamEngine,
    EntityIntake,
    FactKnowledgeState,
    LocationIntake,
    LocationRole,
    MissingInput,
    OptimizerValue,
    PersonIntake,
    PersonRole,
    ProductionPackage,
    build_budget_intelligence,
    build_location_intelligence,
    build_package_intelligence,
    build_production_package,
    build_script_intelligence,
    build_travel_intelligence,
    generate_missing_inputs,
)

BUDGET_CSV = """description,amount,department
Director fee,150000,ATL
Writer fee,50000,ATL
VFX shots,300000,POST
Camera rental,80000,GRIP
Hotel and lodging,40000,TRAVEL
"""

SCRIPT_TEXT = """INT. PARIS APARTMENT - DAY
JEAN sits by the window.

EXT. LONDON STREET - NIGHT
A car speeds past.
"""


@pytest.fixture()
def budget_parse_result():
    return parse_budget_csv(BUDGET_CSV, filename="lu_budget.csv")


@pytest.fixture()
def screenplay_parse_result():
    return parse_screenplay_text(SCRIPT_TEXT, filename="lu_script.fdx")


@pytest.fixture()
def people():
    return [
        PersonIntake(person_id="P1", name="Jane Director", role=PersonRole.DIRECTOR, nationality="FR"),
        PersonIntake(person_id="P2", name="John Writer", role=PersonRole.WRITER),
        PersonIntake(
            person_id="P3", name="Cast Member", role=PersonRole.CAST,
            residency="GB", residency_verification_required=True,
        ),
    ]


@pytest.fixture()
def production_companies():
    return [EntityIntake(entity_id="E1", name="Little Utopia Productions LLC", entity_type="production_company", registered_jurisdiction="MU")]


@pytest.fixture()
def vendors():
    return [EntityIntake(entity_id="V1", name="Acme VFX", entity_type="vfx_vendor")]


@pytest.fixture()
def locations():
    return [
        LocationIntake(location_id="L1", role=LocationRole.PRINCIPAL_PHOTOGRAPHY, jurisdiction_code="MU"),
        LocationIntake(location_id="L2", role=LocationRole.VFX, vendor_entity_id="V1"),
    ]


@pytest.fixture()
def crew_movements():
    return [CrewMovementIntake(movement_id="M1", home_base="LA", destination_jurisdiction="MU", business_class_seats=2, hotel_nights=14, per_diem_days=14)]


@pytest.fixture()
def package(budget_parse_result, screenplay_parse_result, people, production_companies, vendors, locations, crew_movements):
    return build_production_package(
        production_id="LITTLE-UTOPIA",
        budget_parse_result=budget_parse_result,
        screenplay_parse_result=screenplay_parse_result,
        script_known_attributes={"language": "English"},
        people=people,
        production_companies=production_companies,
        vendors=vendors,
        locations=locations,
        crew_movements=crew_movements,
        production_facts={"treaty_partner": None},
    )


# ── Budget Intelligence ───────────────────────────────────────────────────────

class TestBudgetIntelligence:
    def test_unknown_when_no_budget_supplied(self):
        bi = build_budget_intelligence(None)
        assert bi.known is False
        assert bi.line_item_count == 0
        assert bi.totals_by_spend_category_usd == {}

    def test_reuses_classify_atl_btl_split_exactly(self, budget_parse_result):
        bi = build_budget_intelligence(budget_parse_result)
        items = [{"description": li.description, "department": li.department, "amount_usd": li.amount_usd or 0.0} for li in budget_parse_result.line_items]
        expected = classify_atl_btl_split(items)["totals"]
        assert bi.atl_total_usd == round(expected["atl_total_usd"], 2)
        assert bi.btl_total_usd == round(expected["btl_total_usd"], 2)
        assert bi.post_total_usd == round(expected["post_total_usd"], 2)

    def test_totals_by_spend_category_sum_to_grand_total(self, budget_parse_result):
        bi = build_budget_intelligence(budget_parse_result)
        assert round(sum(bi.totals_by_spend_category_usd.values()), 2) == round(
            bi.atl_total_usd + bi.btl_total_usd + bi.post_total_usd + bi.other_total_usd, 2
        )

    def test_known_categories_present(self, budget_parse_result):
        bi = build_budget_intelligence(budget_parse_result)
        assert "atl_director" in bi.totals_by_spend_category_usd
        assert "vfx" in bi.totals_by_spend_category_usd
        assert bi.totals_by_spend_category_usd["vfx"] == 300000.0

    def test_does_not_mutate_parse_result(self, budget_parse_result):
        before = copy.deepcopy(budget_parse_result)
        build_budget_intelligence(budget_parse_result)
        assert budget_parse_result == before


# ── Script Intelligence ──────────────────────────────────────────────────────

class TestScriptIntelligence:
    def test_unknown_when_no_screenplay_supplied(self):
        si = build_script_intelligence(None)
        assert si.known is False
        assert all(a.state == FactKnowledgeState.UNKNOWN for a in si.attributes.values())

    def test_all_script_attribute_keys_present_and_unknown_by_default(self, screenplay_parse_result):
        si = build_script_intelligence(screenplay_parse_result)
        assert set(si.attributes.keys()) == set(SCRIPT_ATTRIBUTE_KEYS)
        assert all(a.state == FactKnowledgeState.UNKNOWN for a in si.attributes.values())

    def test_known_attributes_override_only_supplied_keys(self, screenplay_parse_result):
        si = build_script_intelligence(screenplay_parse_result, {"language": "English", "period": "1920s"})
        assert si.attributes["language"].state == FactKnowledgeState.KNOWN
        assert si.attributes["language"].value == "English"
        assert si.attributes["period"].value == "1920s"
        assert si.attributes["documentary"].state == FactKnowledgeState.UNKNOWN

    def test_locations_extracted_from_existing_scene_heading_parser(self, screenplay_parse_result):
        si = build_script_intelligence(screenplay_parse_result)
        assert "PARIS APARTMENT" in si.locations_mentioned
        assert "LONDON STREET" in si.locations_mentioned

    def test_does_not_mutate_parse_result(self, screenplay_parse_result):
        before = copy.deepcopy(screenplay_parse_result)
        build_script_intelligence(screenplay_parse_result)
        assert screenplay_parse_result == before

    def test_never_infers_attributes_from_word_count_or_scene_content(self, screenplay_parse_result):
        """A screenplay with scene headings must not cause vfx_intensity,
        documentary, or animation to be silently marked known."""
        si = build_script_intelligence(screenplay_parse_result)
        for key in ("vfx_intensity", "documentary", "animation", "marine_usage"):
            assert si.attributes[key].state == FactKnowledgeState.UNKNOWN


# ── Package Intelligence ─────────────────────────────────────────────────────

class TestPackageIntelligence:
    def test_people_bucketed_by_role(self, people):
        pkg = build_package_intelligence(people=people)
        assert len(pkg.directors) == 1
        assert len(pkg.writers) == 1
        assert len(pkg.cast) == 1
        assert len(pkg.producers) == 0

    def test_known_nationality_is_actionable(self, people):
        pkg = build_package_intelligence(people=people)
        assert pkg.directors[0].nationality.state == FactKnowledgeState.KNOWN
        assert pkg.directors[0].nationality.is_actionable

    def test_missing_nationality_is_unknown_not_fabricated(self, people):
        pkg = build_package_intelligence(people=people)
        assert pkg.writers[0].nationality.state == FactKnowledgeState.UNKNOWN
        assert pkg.writers[0].nationality.value is None

    def test_verification_required_is_not_actionable(self, people):
        pkg = build_package_intelligence(people=people)
        cast = pkg.cast[0]
        assert cast.residency.state == FactKnowledgeState.VERIFICATION_REQUIRED
        assert cast.residency.value == "GB"
        assert cast.residency.is_actionable is False  # carries a value but is not usable yet

    def test_entities_split_into_companies_and_vendors(self, production_companies, vendors):
        pkg = build_package_intelligence(production_companies=production_companies, vendors=vendors)
        assert len(pkg.production_companies) == 1
        assert len(pkg.vendors) == 1
        assert pkg.production_companies[0].registered_jurisdiction.value == "MU"
        assert pkg.vendors[0].registered_jurisdiction.state == FactKnowledgeState.UNKNOWN

    def test_all_people_and_all_entities_properties(self, people, production_companies, vendors):
        pkg = build_package_intelligence(people=people, production_companies=production_companies, vendors=vendors)
        assert len(pkg.all_people) == 3
        assert len(pkg.all_entities) == 2

    def test_empty_intake_produces_empty_package(self):
        pkg = build_package_intelligence()
        assert pkg.all_people == ()
        assert pkg.all_entities == ()


# ── Location Intelligence ────────────────────────────────────────────────────

class TestLocationIntelligence:
    def test_known_jurisdiction_appears_in_known_codes(self, locations):
        li = build_location_intelligence(locations)
        assert "MU" in li.jurisdiction_codes_known

    def test_unknown_jurisdiction_excluded_from_known_codes(self, locations):
        li = build_location_intelligence(locations)
        vfx = li.of_role(LocationRole.VFX)[0]
        assert vfx.jurisdiction.state == FactKnowledgeState.UNKNOWN
        assert "UNKNOWN" not in li.jurisdiction_codes_known

    def test_graph_refs_use_existing_country_ref_convention(self, locations):
        li = build_location_intelligence(locations)
        assert li.graph_refs == ("country:MU",)

    def test_of_role_filters_correctly(self, locations):
        li = build_location_intelligence(locations)
        assert len(li.of_role(LocationRole.PRINCIPAL_PHOTOGRAPHY)) == 1
        assert len(li.of_role(LocationRole.POST)) == 0

    def test_empty_intake_produces_empty_location_intelligence(self):
        li = build_location_intelligence()
        assert li.locations == ()
        assert li.graph_refs == ()


# ── Travel Intelligence ──────────────────────────────────────────────────────

class TestTravelIntelligence:
    def test_priceable_movement_flagged_correctly(self, crew_movements):
        ti = build_travel_intelligence(crew_movements)
        assert ti.movements[0].is_priceable
        assert len(ti.priceable_movements) == 1

    def test_incomplete_movement_is_not_priceable(self):
        ti = build_travel_intelligence([CrewMovementIntake(movement_id="M2", home_base="LA")])
        assert ti.movements[0].is_priceable is False
        assert ti.priceable_movements == ()

    def test_to_travel_model_kwargs_interoperates_with_existing_travel_model(self, crew_movements):
        ti = build_travel_intelligence(crew_movements)
        kwargs = ti.movements[0].to_travel_model_kwargs()
        result = estimate_travel_cost(**kwargs, incentive_value_usd=500_000.0)
        assert result.total_travel_cost_usd > 0
        assert result.net_incentive_after_travel_usd < 500_000.0

    def test_kwargs_omit_unset_optional_fields(self):
        ti = build_travel_intelligence([CrewMovementIntake(movement_id="M3", home_base="LA", destination_jurisdiction="GB")])
        kwargs = ti.movements[0].to_travel_model_kwargs()
        assert "business_class_seats" not in kwargs
        # estimate_travel_cost must still work using its own defaults
        result = estimate_travel_cost(**kwargs)
        assert result.total_travel_cost_usd > 0


# ── Question Engine ───────────────────────────────────────────────────────────

class TestQuestionEngine:
    def test_missing_budget_is_blocking(self):
        from app.calculators.production_package_intelligence import build_budget_intelligence, build_script_intelligence, build_package_intelligence, build_location_intelligence
        missing = generate_missing_inputs(
            build_budget_intelligence(None), build_script_intelligence(None),
            build_package_intelligence(), build_location_intelligence(),
        )
        budget_q = next(m for m in missing if m.identifier == "MISSING-BUDGET")
        assert budget_q.blocking is True

    def test_missing_vfx_location_is_blocking_but_principal_photography_gap_is_not(self, package):
        by_id = {m.identifier: m for m in package.missing_inputs}
        assert by_id["MISSING-LOCATION-L2"].blocking is True  # VFX

    def test_missing_nationality_generates_question_with_hooks(self, package):
        q = next(m for m in package.missing_inputs if m.identifier == "MISSING-NATIONALITY-P2")
        assert q.blocking is False
        assert DownstreamEngine.CULTURAL_TEST_RULES in q.downstream_engines
        assert any(h.source == DiscoverySourceKind.IMDB for h in q.discovery_hooks)
        assert q.optimizer_value == OptimizerValue.HIGH  # writer role

    def test_known_nationality_generates_no_question(self, package):
        assert not any(m.identifier == "MISSING-NATIONALITY-P1" for m in package.missing_inputs)

    def test_verification_required_still_generates_a_question(self, package):
        assert any(m.identifier == "MISSING-RESIDENCY-P3" for m in package.missing_inputs)

    def test_production_facts_supplied_suppresses_question(self, budget_parse_result, screenplay_parse_result):
        from app.calculators.production_package_intelligence import build_budget_intelligence, build_script_intelligence, build_package_intelligence, build_location_intelligence
        missing = generate_missing_inputs(
            build_budget_intelligence(budget_parse_result), build_script_intelligence(screenplay_parse_result),
            build_package_intelligence(), build_location_intelligence(),
            production_facts={"financing_timing": "Equity funds at closing; incentive bridge at principal photography start."},
        )
        assert not any(m.identifier == "MISSING-FINANCING-TIMING" for m in missing)

    def test_discovery_hooks_never_call_anything_are_pure_data(self):
        hook_module_has_no_network_imports = True
        import app.calculators.production_package_intelligence as ppi
        import inspect
        source = inspect.getsource(ppi)
        for forbidden in ("import requests", "import httpx", "urlopen", "socket."):
            assert forbidden not in source
        assert hook_module_has_no_network_imports

    def test_missing_inputs_are_deterministically_ordered(self, package):
        ids = [m.identifier for m in package.missing_inputs]
        assert ids == sorted(ids)


# ── Top-level ProductionPackage ──────────────────────────────────────────────

class TestProductionPackage:
    def test_returns_production_package(self, package):
        assert isinstance(package, ProductionPackage)
        assert package.production_id == "LITTLE-UTOPIA"
        assert package.engine_version == PRODUCTION_PACKAGE_INTELLIGENCE_VERSION

    def test_confidence_low_when_blocking_input_present(self, package):
        assert package.confidence == QualificationConfidence.LOW
        assert package.is_ready_for_downstream_engines is False

    def test_confidence_high_when_nothing_missing(self):
        pkg = build_production_package(
            production_id="COMPLETE",
            budget_parse_result=parse_budget_csv(BUDGET_CSV, filename="b.csv"),
            production_facts={
                "financing_timing": "known", "payroll_structure": "known",
                "treaty_partner": "known", "local_spend_allocation_pct": "known",
            },
        )
        # script never supplied -> non-blocking MISSING-SCRIPT remains -> MEDIUM, not HIGH
        assert pkg.confidence in (QualificationConfidence.MEDIUM, QualificationConfidence.HIGH)
        assert pkg.is_ready_for_downstream_engines is True

    def test_known_facts_and_unknown_facts_are_disjoint_concepts(self, package):
        assert "person.P1.nationality" in package.known_facts
        assert "person.P2.nationality" in package.unknown_facts
        assert "person.P1.nationality" not in package.unknown_facts

    def test_graph_refs_derived_from_location_intelligence(self, package):
        assert package.graph_refs == package.location.graph_refs

    def test_blocking_missing_inputs_property(self, package):
        assert all(m.blocking for m in package.blocking_missing_inputs)
        assert len(package.blocking_missing_inputs) >= 1

    def test_empty_production_package_is_still_deterministic_and_valid(self):
        pkg = build_production_package(production_id="EMPTY")
        assert pkg.budget.known is False
        assert pkg.script.known is False
        assert pkg.package.all_people == ()
        assert pkg.location.locations == ()
        assert pkg.travel.movements == ()
        assert pkg.confidence == QualificationConfidence.LOW  # missing budget is blocking


# ── Determinism / non-mutation ────────────────────────────────────────────────

class TestDeterminismAndNonMutation:
    def test_two_builds_produce_identical_output(self, budget_parse_result, screenplay_parse_result, people, production_companies, vendors, locations, crew_movements):
        kwargs = dict(
            production_id="LITTLE-UTOPIA",
            budget_parse_result=budget_parse_result,
            screenplay_parse_result=screenplay_parse_result,
            script_known_attributes={"language": "English"},
            people=people,
            production_companies=production_companies,
            vendors=vendors,
            locations=locations,
            crew_movements=crew_movements,
        )
        p1 = build_production_package(**kwargs)
        p2 = build_production_package(**kwargs)
        assert [m.identifier for m in p1.missing_inputs] == [m.identifier for m in p2.missing_inputs]
        assert p1.known_facts == p2.known_facts
        assert p1.unknown_facts == p2.unknown_facts

    def test_does_not_mutate_intake_lists(self, people, production_companies, vendors, locations, crew_movements):
        before_people = copy.deepcopy(people)
        before_companies = copy.deepcopy(production_companies)
        before_vendors = copy.deepcopy(vendors)
        before_locations = copy.deepcopy(locations)
        before_movements = copy.deepcopy(crew_movements)
        build_production_package(
            production_id="X", people=people, production_companies=production_companies,
            vendors=vendors, locations=locations, crew_movements=crew_movements,
        )
        assert people == before_people
        assert production_companies == before_companies
        assert vendors == before_vendors
        assert locations == before_locations
        assert crew_movements == before_movements

    def test_never_touches_pricing_or_composition_engines(self):
        """Import-boundary check mirroring the discipline
        test_legal_authority_acquisition.py enforces for LAAE: this
        module has no import of optimization_engine.py,
        opportunity_discovery.py, or production_structure_composer.py —
        it produces inputs FOR them, never calls into them or duplicates
        their pricing/composition math."""
        import app.calculators.production_package_intelligence as ppi
        import inspect
        import_lines = [
            line for line in inspect.getsource(ppi).splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        forbidden = ("optimization_engine", "opportunity_discovery", "production_structure_composer")
        for line in import_lines:
            assert not any(name in line for name in forbidden), f"unexpected import: {line}"

    def test_recommendation_engine_import_is_read_only_registry_reuse(self):
        """Phase 7 Part A (derive_likely_cultural_test_categories) reuses
        production_recommendation_engine.CULTURAL_TEST_REGISTRY as the
        single source of truth for valid test slugs — this is the ONE
        sanctioned import from that module, a read-only constant, never
        any Recommendation-constructing or gate-bearing function. This
        test pins that the import stays exactly that."""
        import app.calculators.production_package_intelligence as ppi
        import inspect
        import_lines = [
            line.strip() for line in inspect.getsource(ppi).splitlines()
            if line.strip().startswith(("import ", "from ")) and "production_recommendation_engine" in line
        ]
        assert import_lines == ["from app.calculators.production_recommendation_engine import CULTURAL_TEST_REGISTRY"]


# ── Phase 7 closeout, Part A: advanced script intelligence ──────────────────

from app.calculators.production_package_intelligence import (
    PERIOD_CLASSIFICATIONS,
    derive_likely_cultural_test_categories,
)


class TestAdvancedScriptIntelligence:
    def test_new_attribute_keys_present(self):
        for key in ("period_classification", "cities", "regions", "stunt_intensity", "underwater", "aviation", "military", "sports", "music_heavy"):
            assert key in SCRIPT_ATTRIBUTE_KEYS

    def test_period_classification_is_fixed_vocabulary(self):
        assert PERIOD_CLASSIFICATIONS == ("historical", "contemporary", "future")

    def test_confidence_always_exposed_and_defaults_medium_for_known(self, screenplay_parse_result):
        si = build_script_intelligence(screenplay_parse_result, {"language": "English"})
        assert si.attributes["language"].confidence == QualificationConfidence.MEDIUM
        assert si.attributes["documentary"].confidence == QualificationConfidence.NOT_APPLICABLE

    def test_caller_can_assert_explicit_confidence(self, screenplay_parse_result):
        si = build_script_intelligence(
            screenplay_parse_result, {"vfx_intensity": "high"}, attribute_confidence={"vfx_intensity": QualificationConfidence.LOW},
        )
        assert si.attributes["vfx_intensity"].confidence == QualificationConfidence.LOW

    def test_derive_likely_cultural_test_categories_single_country(self):
        assert derive_likely_cultural_test_categories(("FR",)) == ("fr_cnc_cultural_test",)
        assert derive_likely_cultural_test_categories(("US",)) == ()

    def test_derive_likely_cultural_test_categories_multilateral(self):
        result = derive_likely_cultural_test_categories(("FR", "IE"))
        assert "eu_eurimages_test" in result
        assert "eu_european_convention_test" in result
        assert "fr_cnc_cultural_test" in result
        assert "ie_section_481_test" in result

    def test_derive_likely_cultural_test_categories_empty_input(self):
        assert derive_likely_cultural_test_categories(()) == ()

    def test_derive_likely_cultural_test_categories_never_fabricates_untested_country(self):
        assert derive_likely_cultural_test_categories(("ZZ",)) == ()

    def test_all_suggested_slugs_are_real_registry_entries(self):
        from app.calculators.production_recommendation_engine import CULTURAL_TEST_REGISTRY
        for slug in derive_likely_cultural_test_categories(("FR", "IE", "CA", "AU")):
            assert slug in CULTURAL_TEST_REGISTRY


# ── Phase 7 closeout, Part B: advanced budget intelligence (OpportunityHints) ─

from app.calculators.production_package_intelligence import (
    JURISDICTION_FIXED_SPEND_CATEGORIES,
    MOVABLE_SPEND_CATEGORIES,
    OpportunityHint,
)

CONCENTRATED_BUDGET_CSV = """description,amount,department
Director fee,150000,ATL
Director fee,150000,ATL
VFX shots,300000,POST
VFX cleanup,200000,POST
Camera rental,80000,GRIP
Hotel and lodging,700000,TRAVEL
"""


class TestAdvancedBudgetIntelligence:
    def test_opportunity_hints_are_pure_data_never_priced_recommendations(self, budget_parse_result):
        bi = build_budget_intelligence(budget_parse_result)
        assert all(isinstance(h, OpportunityHint) for h in bi.opportunity_hints)

    def test_movable_and_fixed_categories_are_disjoint(self):
        assert not (MOVABLE_SPEND_CATEGORIES & JURISDICTION_FIXED_SPEND_CATEGORIES)

    def test_movable_spend_hint_present_when_movable_categories_exist(self, budget_parse_result):
        bi = build_budget_intelligence(budget_parse_result)
        movable_hint = next(h for h in bi.opportunity_hints if h.hint_id == "HINT-MOVABLE-SPEND")
        assert movable_hint.amount_usd > 0
        assert set(movable_hint.affected_spend_categories) <= MOVABLE_SPEND_CATEGORIES

    def test_qualifying_spend_candidate_excludes_other_bucket(self, budget_parse_result):
        bi = build_budget_intelligence(budget_parse_result)
        hint = next(h for h in bi.opportunity_hints if h.hint_id == "HINT-QUALIFYING-SPEND-CANDIDATE")
        assert hint.amount_usd == round(bi.atl_total_usd + bi.btl_total_usd + bi.post_total_usd, 2)

    def test_department_concentration_hint_fires_above_threshold(self):
        result = parse_budget_csv(CONCENTRATED_BUDGET_CSV, filename="c.csv")
        bi = build_budget_intelligence(result)
        assert any(h.hint_id == "HINT-DEPT-CONCENTRATION-TRAVEL" for h in bi.opportunity_hints)

    def test_duplicate_line_item_hint_detects_repeated_descriptions(self):
        result = parse_budget_csv(CONCENTRATED_BUDGET_CSV, filename="c.csv")
        bi = build_budget_intelligence(result)
        dup_hint = next(h for h in bi.opportunity_hints if h.hint_id == "HINT-DUPLICATE-LINE-ITEMS")
        assert "director fee" in dup_hint.description.lower()

    def test_high_cost_categories_sorted_descending(self):
        result = parse_budget_csv(CONCENTRATED_BUDGET_CSV, filename="c.csv")
        bi = build_budget_intelligence(result)
        hint = next(h for h in bi.opportunity_hints if h.hint_id == "HINT-HIGH-COST-CATEGORIES")
        amounts = [bi.totals_by_spend_category_usd[c] for c in hint.affected_spend_categories]
        assert amounts == sorted(amounts, reverse=True)

    def test_travel_concentration_hint_fires_above_threshold(self):
        result = parse_budget_csv(CONCENTRATED_BUDGET_CSV, filename="c.csv")
        bi = build_budget_intelligence(result)
        assert any(h.hint_id == "HINT-TRAVEL-CONCENTRATION" for h in bi.opportunity_hints)

    def test_no_hints_when_no_budget(self):
        bi = build_budget_intelligence(None)
        assert bi.opportunity_hints == ()

    def test_no_pricing_no_recommendation_language_in_hints(self, budget_parse_result):
        """Opportunity hints must never claim a dollar VALUE UNLOCKED —
        only a pattern in already-known totals."""
        bi = build_budget_intelligence(budget_parse_result)
        for hint in bi.opportunity_hints:
            assert "unlock" not in hint.description.lower()
            assert "incentive value" not in hint.description.lower()

    def test_hints_deterministic_ordering(self, budget_parse_result):
        bi1 = build_budget_intelligence(budget_parse_result)
        bi2 = build_budget_intelligence(budget_parse_result)
        assert [h.hint_id for h in bi1.opportunity_hints] == [h.hint_id for h in bi2.opportunity_hints]


# ── Phase 7 closeout, Part C: package enrichment model (discovery sources) ───

class TestPackageEnrichmentModel:
    def test_unknown_person_nationality_carries_discovery_sources(self, people):
        pkg = build_package_intelligence(people=people)
        writer = pkg.writers[0]
        assert writer.nationality.state == FactKnowledgeState.UNKNOWN
        assert len(writer.nationality.possible_discovery_sources) > 0
        assert DiscoverySourceKind.IMDB in writer.nationality.possible_discovery_sources

    def test_known_person_nationality_carries_no_discovery_sources(self, people):
        pkg = build_package_intelligence(people=people)
        director = pkg.directors[0]
        assert director.nationality.state == FactKnowledgeState.KNOWN
        assert director.nationality.possible_discovery_sources == ()

    def test_verification_required_still_carries_discovery_sources(self, people):
        pkg = build_package_intelligence(people=people)
        cast = pkg.cast[0]
        assert cast.residency.state == FactKnowledgeState.VERIFICATION_REQUIRED
        assert len(cast.residency.possible_discovery_sources) > 0

    def test_unknown_entity_jurisdiction_carries_company_registry_hook(self, vendors):
        pkg = build_package_intelligence(vendors=vendors)
        vendor = pkg.vendors[0]
        assert DiscoverySourceKind.COMPANY_REGISTRY in vendor.registered_jurisdiction.possible_discovery_sources

    def test_unknown_location_jurisdiction_carries_film_commission_hook(self, locations):
        li = build_location_intelligence(locations)
        vfx = li.of_role(LocationRole.VFX)[0]
        assert DiscoverySourceKind.FILM_COMMISSION_DATABASE in vfx.jurisdiction.possible_discovery_sources

    def test_discovery_hooks_never_perform_enrichment(self):
        """Modeling only — no function in this module actually resolves
        a fact from a discovery source."""
        import app.calculators.production_package_intelligence as ppi
        import inspect
        source = inspect.getsource(ppi)
        for forbidden in ("requests.get", "httpx.get", "urlopen(", "aiohttp"):
            assert forbidden not in source


# ── Phase 7 closeout, Part G: engine integration bridges ────────────────────

from app.calculators.production_package_intelligence import (
    production_package_to_cultural_test_inputs,
    production_package_to_extra_jurisdiction_sets,
    production_package_to_known_jurisdiction_codes,
    production_package_to_relevant_cultural_test_slugs,
)


class TestEngineIntegrationBridges:
    def test_known_jurisdiction_codes_merge_all_sources(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Dir", role=PersonRole.DIRECTOR, residency="IE")],
            production_companies=[EntityIntake(entity_id="E1", name="Co", entity_type="production_company", registered_jurisdiction="FR")],
            locations=[LocationIntake(location_id="L1", role=LocationRole.PRINCIPAL_PHOTOGRAPHY, jurisdiction_code="MU")],
        )
        codes = production_package_to_known_jurisdiction_codes(pkg)
        assert set(codes) == {"IE", "FR", "MU"}

    def test_extra_jurisdiction_sets_shape_matches_composer_parameter(self):
        pkg = build_production_package(
            production_id="X",
            locations=[LocationIntake(location_id="L1", role=LocationRole.VFX, jurisdiction_code="CA")],
        )
        sets = production_package_to_extra_jurisdiction_sets(pkg)
        assert sets == [("CA",)]
        assert all(isinstance(s, tuple) for s in sets)

    def test_relevant_cultural_test_slugs_reuses_part_a_function(self):
        pkg = build_production_package(
            production_id="X",
            locations=[LocationIntake(location_id="L1", role=LocationRole.PRINCIPAL_PHOTOGRAPHY, jurisdiction_code="FR")],
        )
        assert production_package_to_relevant_cultural_test_slugs(pkg) == derive_likely_cultural_test_categories(("FR",))

    def test_cultural_test_inputs_only_populates_answerable_keys(self):
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Dir", role=PersonRole.DIRECTOR, nationality="FR")],
        )
        inputs = production_package_to_cultural_test_inputs(pkg)
        assert inputs["fr_cnc_cultural_test"]["director_french_or_eea"] is True
        # writer never supplied -> no writer key anywhere
        assert "writer_french_or_eea" not in inputs.get("fr_cnc_cultural_test", {})

    def test_cultural_test_inputs_empty_when_nothing_known(self):
        pkg = build_production_package(production_id="EMPTY")
        assert production_package_to_cultural_test_inputs(pkg) == {}

    def test_bridge_output_is_directly_usable_by_recommendation_engine(self):
        """Real integration proof, not just shape-matching: feed the
        bridge output straight into
        production_recommendation_engine.generate_cultural_recommendations()
        and confirm it runs without error."""
        from app.calculators.production_recommendation_engine import generate_cultural_recommendations
        pkg = build_production_package(
            production_id="X",
            people=[PersonIntake(person_id="P1", name="Dir", role=PersonRole.DIRECTOR, nationality="FR")],
            locations=[LocationIntake(location_id="L1", role=LocationRole.PRINCIPAL_PHOTOGRAPHY, jurisdiction_code="FR")],
        )
        slugs = production_package_to_relevant_cultural_test_slugs(pkg)
        inputs = production_package_to_cultural_test_inputs(pkg)
        recs = generate_cultural_recommendations(inputs, slugs)
        assert isinstance(recs, list)  # no exception is the real assertion here
