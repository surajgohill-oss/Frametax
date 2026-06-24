"""
Tests for Phase D systems: D1-D6.

D1: cultural_qualification_model
D2: cultural_test_rules
D3: qualification_path_engine
D4: structure_graph_model
D5: financing_interaction_model
D6: recommendation_engine
"""
import pytest

# ---------------------------------------------------------------------------
# D1: Cultural Qualification Model
# ---------------------------------------------------------------------------

from app.data.cultural_qualification_model import (
    get_requirements as get_nationality_requirements,
    get_required_roles,
    has_cultural_test,
    NationalityRequirement,
)


def test_d1_get_requirements_uk_avec():
    reqs = get_nationality_requirements("uk_avec")
    assert len(reqs) > 0
    roles = {r.role for r in reqs}
    assert "director" in roles or "writer" in roles or "producer" in roles


def test_d1_required_roles_filtering():
    reqs = get_required_roles("uk_avec")
    # All returned entries must have status == "required"
    assert all(r.status == "required" for r in reqs)


def test_d1_has_cultural_test_known_programs():
    assert has_cultural_test("uk_avec") is True
    assert has_cultural_test("ie_section_481") is True


def test_d1_has_cultural_test_unknown_program():
    assert has_cultural_test("nonexistent_program_xyz") is False


def test_d1_requirement_fields():
    reqs = get_nationality_requirements("uk_avec")
    for r in reqs:
        assert isinstance(r, NationalityRequirement)
        assert r.program_slug == "uk_avec"
        assert r.status in ("required", "optional", "weighted", "unknown")
        assert r.role is not None and len(r.role) > 0


def test_d1_eurimages_requirements():
    reqs = get_nationality_requirements("eu_eurimages")
    assert len(reqs) > 0


def test_d1_ca_federal_requirements():
    reqs = get_nationality_requirements("ca_federal_cptc")
    assert len(reqs) > 0


# ---------------------------------------------------------------------------
# D2: Cultural Test Rules
# ---------------------------------------------------------------------------

from app.calculators.cultural_test_rules import (
    score_fr_cnc_cultural_test,
    score_ie_section_481_test,
    score_eu_eurimages_test,
    score_ibermedia_test,
    score_ca_content_test,
    score_au_content_test,
    score_eu_european_convention_test,
)


def _make_profile(**kwargs):
    return dict(kwargs)


def test_d2_cnc_strong_french_production():
    profile = _make_profile(
        french_language_or_subject=True,
        director_french_or_eea=True,
        writer_french_or_eea=True,
        producer_french=True,
        french_spend_pct=0.55,
        cast_french=True,
        crew_french=True,
    )
    result = score_fr_cnc_cultural_test(profile)
    assert result.total_score >= result.minimum_required
    assert result.passes_overall is True


def test_d2_cnc_empty_production_fails():
    result = score_fr_cnc_cultural_test({})
    assert result.total_score == 0
    assert result.passes_overall is False


def test_d2_section_481_strong_irish():
    profile = _make_profile(
        irish_or_eea_company=True,
        irish_qe_above_125k=True,
        irish_qe_pct=0.75,
        qualifying_production_type=True,
        within_individual_cap=True,
    )
    result = score_ie_section_481_test(profile)
    assert result.passes_overall is True


def test_d2_section_481_empty_fails():
    result = score_ie_section_481_test({})
    assert result.passes_overall is False


def test_d2_eurimages_strong_european():
    profile = _make_profile(
        coproducer_country_count=3,
        all_coproducers_member_states=True,
        no_single_country_over_80pct=True,
        each_coproducer_min_10pct=True,
        majority_producer_from_applicant_country=True,
    )
    result = score_eu_eurimages_test(profile)
    assert result.passes_overall is True


def test_d2_eurimages_empty_fails():
    result = score_eu_eurimages_test({})
    assert result.passes_overall is False


def test_d2_ibermedia_strong():
    profile = _make_profile(
        ibermedia_country_count=3,
        all_coproducers_ibermedia_members=True,
        no_single_country_over_80pct=True,
        each_coproducer_min_10pct=True,
    )
    result = score_ibermedia_test(profile)
    assert result.passes_overall is True


def test_d2_ca_content_strong_canadian():
    profile = _make_profile(
        director_canadian=True,
        writer_canadian=True,
        lead_performer_canadian=True,
        second_lead_canadian=True,
        dop_canadian=True,
        art_director_canadian=True,
        composer_canadian=True,
        editor_canadian=True,
    )
    result = score_ca_content_test(profile)
    assert result.passes_overall is True


def test_d2_ca_content_empty_fails():
    result = score_ca_content_test({})
    assert result.passes_overall is False


def test_d2_au_content_strong():
    profile = _make_profile(
        australian_script_or_rights=True,
        director_australian=True,
        producer_australian=True,
        lead_actor_australian=True,
        supporting_cast_australian_pct=0.75,
        australian_music=True,
        post_production_in_australia=True,
    )
    result = score_au_content_test(profile)
    assert result.passes_overall is True


def test_d2_eu_convention_strong():
    profile = _make_profile(
        signatory_country_count=3,
        majority_coproducer_min_50pct=True,
        each_coproducer_min_10pct=True,
        director_or_writer_from_signatory_state=True,
        no_single_country_over_80pct=True,
    )
    result = score_eu_european_convention_test(profile)
    assert result.passes_overall is True


def test_d2_all_score_functions_return_result_object():
    empty = {}
    from app.calculators.evaluate_qualification_tests import QualificationTestResult
    for fn in [
        score_fr_cnc_cultural_test,
        score_ie_section_481_test,
        score_eu_eurimages_test,
        score_ibermedia_test,
        score_ca_content_test,
        score_au_content_test,
        score_eu_european_convention_test,
    ]:
        result = fn(empty)
        assert isinstance(result, QualificationTestResult), f"{fn.__name__} wrong return type"
        assert hasattr(result, "total_score"), f"{fn.__name__} missing total_score"
        assert hasattr(result, "passes_overall"), f"{fn.__name__} missing passes_overall"
        assert hasattr(result, "minimum_required"), f"{fn.__name__} missing minimum_required"


# ---------------------------------------------------------------------------
# D3: Qualification Path Engine
# ---------------------------------------------------------------------------

from app.optimization.qualification_path_engine import (
    analyse_qualification,
    get_lowest_friction_path,
    get_test_slug_for_program,
    summarise_deficits,
    QualificationAnalysis,
    QualificationDeficit,
    QualificationPath,
)


def test_d3_bfi_passing_profile():
    profile = {
        "uk_setting": True,
        "lead_characters_british": True,
        "british_subject_matter": True,
        "english_language_variant": True,
        "british_cultural_contribution": True,
        "director_british": True,
        "writer_british": True,
        "producer_british": True,
        "composer_british": True,
        "lead_actor_british": True,
        "second_lead_british": True,
        "british_cast_days_pct": 0.80,
        "british_crew_days_pct": 0.80,
        "uk_shoot_pct": 0.80,
        "uk_vfx": True,
    }
    analysis = analyse_qualification("uk_avec", profile)
    assert isinstance(analysis, QualificationAnalysis)
    assert analysis.is_currently_qualifying is True


def test_d3_bfi_empty_profile_fails():
    analysis = analyse_qualification("uk_avec", {})
    assert analysis.is_currently_qualifying is False
    # Empty profile = all unknowns; deficits may be empty but score should be 0
    assert analysis.current_score == 0 or len(analysis.unknown_factors) > 0


def test_d3_deficits_have_required_fields():
    analysis = analyse_qualification("uk_avec", {})
    for d in analysis.deficits:
        assert isinstance(d, QualificationDeficit)
        assert d.criterion_code is not None
        assert d.description is not None
        assert isinstance(d.friction_score, (int, float))
        assert d.friction_score >= 0


def test_d3_paths_exist_for_bfi():
    analysis = analyse_qualification("uk_avec", {})
    assert len(analysis.paths) > 0
    for p in analysis.paths:
        assert isinstance(p, QualificationPath)
        assert p.path_id is not None
        assert p.description is not None
        assert len(p.actions) > 0
        assert isinstance(p.friction_score, (int, float))


def test_d3_lowest_friction_path():
    path = get_lowest_friction_path("uk_avec", {})
    if path is not None:
        assert isinstance(path, QualificationPath)


def test_d3_summarise_deficits_returns_strings():
    analysis = analyse_qualification("uk_avec", {})
    deficits = summarise_deficits(analysis)
    assert isinstance(deficits, list)
    for d in deficits:
        assert isinstance(d, str)
        assert len(d) > 0


def test_d3_get_test_slug_for_program():
    slug = get_test_slug_for_program("uk_avec")
    assert slug is not None
    assert "bfi" in slug or "uk" in slug


def test_d3_canadian_content_passing():
    profile = {
        "director_ca": True,
        "writer_ca": True,
        "lead_performer_ca": True,
        "supporting_performer_ca": True,
        "dop_ca": True,
        "art_director_ca": True,
        "music_director_ca": True,
        "editor_ca": True,
    }
    analysis = analyse_qualification("ca_federal_cptc", profile)
    assert analysis.is_currently_qualifying is True


def test_d3_analysis_has_score_info_for_points_test():
    profile = {}
    analysis = analyse_qualification("uk_avec", profile)
    # For point-based tests, current_score and required_score should be present
    assert analysis.current_score is not None or analysis.is_currently_qualifying is False


def test_d3_unknown_program_returns_unknown_analysis():
    analysis = analyse_qualification("nonexistent_slug_xyz", {})
    assert isinstance(analysis, QualificationAnalysis)
    assert analysis.is_currently_qualifying is False


# ---------------------------------------------------------------------------
# D4: Structure Graph Model
# ---------------------------------------------------------------------------

from app.data.structure_graph_model import (
    get_edges_from,
    get_edges_to,
    get_edges_by_type,
    get_incompatibilities,
    get_requirements as get_graph_requirements,
    get_unlocked_by,
    STRUCTURE_GRAPH_EDGES,
    GraphEdge,
)


def test_d4_edges_list_not_empty():
    assert len(STRUCTURE_GRAPH_EDGES) > 0


def test_d4_edges_have_required_fields():
    for e in STRUCTURE_GRAPH_EDGES:
        assert isinstance(e, GraphEdge)
        assert e.source_type is not None
        assert e.source_slug is not None
        assert e.edge_type in (
            "unlocks", "requires", "improves", "reduces", "incompatible_with",
            "enables", "complements", "alternative_to", "blocks",
            "majority_only", "minority_only",
        )
        assert e.target_type is not None
        assert e.target_slug is not None


def test_d4_get_edges_from_returns_matching():
    edges = get_edges_from("uk_avec")
    for e in edges:
        assert e.source_slug == "uk_avec"


def test_d4_get_edges_to_returns_matching():
    # eu_eurimages is a common target
    edges = get_edges_to("eu_eurimages")
    for e in edges:
        assert e.target_slug == "eu_eurimages"


def test_d4_get_edges_by_type_unlocks():
    edges = get_edges_by_type("unlocks")
    assert len(edges) > 0
    for e in edges:
        assert e.edge_type == "unlocks"


def test_d4_get_incompatibilities():
    # incompatible_with edges should exist
    incompat_edges = get_edges_by_type("incompatible_with")
    if len(incompat_edges) > 0:
        slug = incompat_edges[0].source_slug
        incompat = get_incompatibilities(slug)
        assert isinstance(incompat, list)


def test_d4_get_requirements_returns_target_slugs():
    req_edges = get_edges_by_type("requires")
    if len(req_edges) > 0:
        slug = req_edges[0].source_slug
        reqs = get_graph_requirements(slug)
        assert isinstance(reqs, list)
        for e in reqs:
            assert e.edge_type == "requires"


def test_d4_at_least_30_edges():
    assert len(STRUCTURE_GRAPH_EDGES) >= 30


# ---------------------------------------------------------------------------
# D5: Financing Interaction Model
# ---------------------------------------------------------------------------

from app.optimization.financing_interaction_model import (
    get_govt_assistance_impact,
    get_stacking_ceiling,
    get_all_govt_assistance_for_slug,
    get_recoupment_interactions,
    compute_effective_qualifying_basis,
    list_all_govt_assistance_slugs,
    ALL_FINANCING_INTERACTIONS,
    FinancingInteraction,
)


def test_d5_all_interactions_not_empty():
    assert len(ALL_FINANCING_INTERACTIONS) > 0


def test_d5_interactions_have_required_fields():
    for ia in ALL_FINANCING_INTERACTIONS:
        assert isinstance(ia, FinancingInteraction)
        assert ia.slug_a is not None
        assert ia.slug_b is not None
        assert ia.interaction_type is not None


def test_d5_get_govt_assistance_impact_exists():
    slugs = list_all_govt_assistance_slugs()
    if len(slugs) >= 2:
        # Try to find a matching pair
        for ia in ALL_FINANCING_INTERACTIONS:
            if ia.interaction_type == "govt_assistance":
                result = get_govt_assistance_impact(ia.slug_a, ia.slug_b)
                assert result is not None
                break


def test_d5_get_stacking_ceiling():
    # Check ceiling interactions exist
    ceiling_ias = [ia for ia in ALL_FINANCING_INTERACTIONS if ia.interaction_type == "stacking_ceiling"]
    if ceiling_ias:
        ia = ceiling_ias[0]
        ceiling = get_stacking_ceiling(ia.slug_a, ia.slug_b)
        assert ceiling is not None
        assert isinstance(ceiling, float)
        assert 0.0 < ceiling <= 1.0


def test_d5_compute_effective_qualifying_basis_no_grants():
    # Without grants, basis should be equal to total spend
    basis = compute_effective_qualifying_basis("uk_avec", 1_000_000, {})
    assert basis == pytest.approx(1_000_000, rel=0.01)


def test_d5_compute_effective_qualifying_basis_with_govt_grant():
    # With a govt grant that causes reduction, basis should be <= total spend
    basis = compute_effective_qualifying_basis("ie_section_481", 1_000_000, {"ie_govt_grant": 100_000})
    assert basis <= 1_000_000


def test_d5_list_all_govt_assistance_slugs_returns_list():
    slugs = list_all_govt_assistance_slugs()
    assert isinstance(slugs, list)


def test_d5_get_all_govt_assistance_for_slug():
    slugs = list_all_govt_assistance_slugs()
    if slugs:
        target = slugs[0]
        interactions = get_all_govt_assistance_for_slug(target)
        assert isinstance(interactions, list)


def test_d5_recoupment_interactions():
    recoup = [ia for ia in ALL_FINANCING_INTERACTIONS if ia.interaction_type == "recoupment"]
    if recoup:
        ia = recoup[0]
        interactions = get_recoupment_interactions(ia.slug_a)
        assert isinstance(interactions, list)


# ---------------------------------------------------------------------------
# D6: Recommendation Engine
# ---------------------------------------------------------------------------

from app.optimization.recommendation_engine import (
    evaluate_program_qualification,
    evaluate_structure,
    explain_structure,
    ProgramQualificationStatus,
    StructureQualificationReport,
    StructureRecommendation,
    ENGINE_VERSION,
)


def test_d6_engine_version_set():
    assert ENGINE_VERSION is not None
    assert len(ENGINE_VERSION) > 0


def test_d6_evaluate_program_qualification_returns_status():
    profile = {}
    status = evaluate_program_qualification("uk_avec", "UK Cultural Test (BFI)", profile)
    assert isinstance(status, ProgramQualificationStatus)
    assert status.program_slug == "uk_avec"
    assert status.program_name == "UK Cultural Test (BFI)"
    assert isinstance(status.is_qualifying, bool)


def test_d6_evaluate_program_fails_on_empty_profile():
    status = evaluate_program_qualification("uk_avec", "BFI", {})
    assert status.is_qualifying is False
    assert len(status.disqualifying_reasons) > 0 or not status.is_qualifying


def test_d6_evaluate_program_passes_on_full_bfi_profile():
    profile = {
        "uk_setting": True,
        "lead_characters_british": True,
        "british_subject_matter": True,
        "english_language_variant": True,
        "british_cultural_contribution": True,
        "director_british": True,
        "writer_british": True,
        "producer_british": True,
        "composer_british": True,
        "lead_actor_british": True,
        "second_lead_british": True,
        "british_cast_days_pct": 0.80,
        "british_crew_days_pct": 0.80,
        "uk_shoot_pct": 0.80,
        "uk_vfx": True,
    }
    status = evaluate_program_qualification("uk_avec", "BFI", profile)
    assert status.is_qualifying is True
    assert len(status.qualifying_reasons) > 0


def test_d6_evaluate_structure_returns_report():
    programs = [("uk_avec", "BFI Cultural Test"), ("ie_section_481", "Section 481")]
    profile = {}
    report = evaluate_structure(programs, profile)
    assert isinstance(report, StructureQualificationReport)
    assert len(report.program_statuses) == 2
    assert report.engine_version == ENGINE_VERSION


def test_d6_evaluate_structure_all_failing_empty_profile():
    programs = [("uk_avec", "BFI")]
    report = evaluate_structure(programs, {})
    assert report.overall_qualifying is False
    assert "uk_avec" in report.failing_programs


def test_d6_evaluate_structure_recommendations_generated():
    programs = [("uk_avec", "BFI")]
    report = evaluate_structure(programs, {})
    assert isinstance(report.recommendations, list)
    # At least some recommendations should be generated for a failing program
    assert len(report.recommendations) > 0


def test_d6_recommendations_have_required_fields():
    programs = [("uk_avec", "BFI")]
    report = evaluate_structure(programs, {})
    for rec in report.recommendations:
        assert isinstance(rec, StructureRecommendation)
        assert rec.recommendation_id is not None
        assert isinstance(rec.priority, int)
        assert rec.recommendation_type in (
            "add_crew", "move_spend", "add_coproducer", "increase_spend",
            "use_treaty", "restructure", "move_post", "change_entity",
        )
        assert rec.target_program_slug is not None
        assert isinstance(rec.actions, list)
        assert isinstance(rec.friction_score, (int, float))


def test_d6_explain_structure_returns_dict():
    programs = [("uk_avec", "BFI")]
    report = evaluate_structure(programs, {})
    explanation = explain_structure(report)
    assert isinstance(explanation, dict)
    assert "overall_qualifying" in explanation
    assert "program_details" in explanation
    assert "recommendations" in explanation
    assert "financing_notes" in explanation
    assert "incompatibilities" in explanation


def test_d6_incompatibilities_are_strings():
    programs = [("uk_avec", "BFI"), ("ie_section_481", "Section 481")]
    report = evaluate_structure(programs, {})
    for w in report.incompatibilities:
        assert isinstance(w, str)


def test_d6_financing_notes_are_strings():
    programs = [("uk_avec", "BFI"), ("ie_section_481", "Section 481")]
    report = evaluate_structure(programs, {})
    for note in report.financing_notes:
        assert isinstance(note, str)


def test_d6_evaluate_structure_mixed_qualifying():
    # BFI passes; Section 481 explicitly fails (no Irish entity, spend below minimum)
    profile = {
        "uk_setting": True,
        "lead_characters_british": True,
        "british_subject_matter": True,
        "english_language_variant": True,
        "british_cultural_contribution": True,
        "director_british": True,
        "writer_british": True,
        "producer_british": True,
        "composer_british": True,
        "lead_actor_british": True,
        "second_lead_british": True,
        "british_cast_days_pct": 0.80,
        "british_crew_days_pct": 0.80,
        "uk_shoot_pct": 0.80,
        "uk_vfx": True,
        # Explicit Section 481 failures
        "has_irish_entity": False,
        "irish_qualifying_spend_usd": 0,
        "production_type": "feature",
    }
    programs = [("uk_avec", "BFI"), ("ie_section_481", "Section 481")]
    report = evaluate_structure(programs, profile)
    assert "uk_avec" in report.qualifying_programs
    assert "ie_section_481" in report.failing_programs
    assert report.overall_qualifying is False
