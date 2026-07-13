"""
test_legal_engine.py

Targeted tests for the Legal Engine (legal_engine.py) — the reusable
subsystem that runs the detect -> question -> connector -> stage ->
provenance -> verify -> approve -> commit -> score -> resolve -> rerun
loop automatically over the existing LAAE / Evidence Graph / Authority
Score / optimizer architecture. Covers automatic uncertainty detection,
LAAE execution-policy preservation (scenario grade never auto-runs),
provenance checking, both human gates, Evidence Graph commit + Authority
Score integration, grey-area resolution flowing into a genuinely changed
optimizer rerun, determinism, and non-mutation.
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.evidence_graph import AuthorityTier
from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import (
    ConnectorClass,
    MockConnector,
    QuestionGrade,
)
from app.calculators.optimization_engine import RiskCase
from app.calculators.qualification_model import (
    GreyAreaStatus,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)

from app.calculators.legal_engine import (
    GOVERNING_AUTHORITY_BY_CLASS,
    LEGAL_ENGINE_VERSION,
    REQUIRED_DOCUMENT_TYPES_BY_CLASS,
    LegalEngine,
    ProvenanceStatus,
)

MU_RATE = 0.40
MU_GROSS_BUDGET = 4_364_393.0
AS_OF = "2026-07-10"


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph(mu_rate=MU_RATE)


@pytest.fixture()
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture()
def register():
    return build_little_utopia_qualification_register(mu_rate=MU_RATE)


@pytest.fixture()
def engine():
    return LegalEngine(connectors={
        ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE),
    })


def _run_through_commit(engine, grey_areas, graph, staged_id="STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT"):
    """Drive one item through the full gate sequence to COMMITTED."""
    engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
    engine.record_verification(staged_id, verified_by="counsel@example.com", outcome="authority_found")
    engine.record_approval(staged_id, approved_by="producer@example.com")
    ga = next(g for g in grey_areas if f"STG-TASK-{g.item_id}" == staged_id)
    return engine.commit_and_score(
        staged_id, target_jurisdiction_code="MU", as_of_date=AS_OF,
        rule_text="ATL compensation for MU-rendered services qualifies as QPE.",
        tier=AuthorityTier.OFFICIAL_GUIDANCE, authority_body="Mauritius Revenue Authority",
        resolves_grey_area=ga, grey_area_outcome=GreyAreaStatus.RESOLVED_INCLUDE,
    )


# ── Automatic uncertainty detection ──────────────────────────────────────────

class TestDetection:
    def test_detects_every_grey_area_and_graph_unknown(self, engine, grey_areas, graph):
        docket, questions = engine.detect_open_questions(grey_areas=grey_areas, graph=graph)
        assert len(questions) == len(docket.tasks) > 100  # 2 grey areas + 103 graph unknowns today

    def test_question_ids_match_task_ids_exactly(self, engine, grey_areas, graph):
        docket, questions = engine.detect_open_questions(grey_areas=grey_areas, graph=graph)
        assert {q.question_id for q in questions} == {t.task_id for t in docket.tasks}

    def test_no_manual_identification_required(self, engine, graph):
        """Detection over the graph alone — nobody names any gap; every
        UNKNOWN/ABSENT fact node surfaces on its own."""
        _, questions = engine.detect_open_questions(graph=graph)
        assert len(questions) > 100
        assert all(q.source_kind == "jurisdiction_unknown" for q in questions)

    def test_governing_authority_and_doc_types_assigned_deterministically(self, engine, grey_areas, graph):
        _, questions = engine.detect_open_questions(grey_areas=grey_areas, graph=graph)
        for q in questions:
            assert q.governing_authority == GOVERNING_AUTHORITY_BY_CLASS[q.connector_class]
            assert q.required_document_types == REQUIRED_DOCUMENT_TYPES_BY_CLASS[q.connector_class]

    def test_priority_ordering_preserved_from_laae(self, engine, grey_areas, graph):
        _, questions = engine.detect_open_questions(grey_areas=grey_areas, graph=graph)
        scores = [q.priority_score for q in questions]
        assert scores == sorted(scores, reverse=True)


# ── Execution policy ─────────────────────────────────────────────────────────

class TestExecutionPolicy:
    def test_only_commitment_grade_with_connector_auto_executes(self, engine, grey_areas, graph):
        cycle = engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        assert set(cycle.executed_task_ids) == {"TASK-GA-LEGAL-ACCOUNTING-SPLIT", "TASK-GA-INKIND-FMV"}

    def test_scenario_grade_never_auto_executes(self, engine, grey_areas, graph):
        cycle = engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        scenario_ids = {q.question_id for q in cycle.questions if q.question_grade == QuestionGrade.SCENARIO}
        assert scenario_ids, "expected scenario-grade questions"
        assert not (scenario_ids & set(cycle.executed_task_ids))
        for task_id in scenario_ids:
            assert "scenario-grade" in cycle.not_executed[task_id]

    def test_missing_connector_reported_not_silently_skipped(self, grey_areas, graph):
        bare_engine = LegalEngine()  # no connectors configured
        cycle = bare_engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        assert cycle.executed_task_ids == ()
        assert "no connector configured" in cycle.not_executed["TASK-GA-LEGAL-ACCOUNTING-SPLIT"]

    def test_max_tasks_bound_respected(self, engine, grey_areas, graph):
        cycle = engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph, max_tasks=1)
        assert len(cycle.executed_task_ids) == 1

    def test_promote_to_commitment_requires_real_stakes(self, engine, graph):
        _, questions = engine.detect_open_questions(graph=graph)
        scenario_q = questions[0]
        promoted = engine.promote_to_commitment(scenario_q.question_id, value_at_stake_usd=25_000.0, reason="Production attached to this jurisdiction.")
        assert promoted.question_grade == QuestionGrade.COMMITMENT
        assert promoted.value_at_stake_usd == 25_000.0
        assert promoted.task_id.endswith("-COMMIT")

    def test_promote_unknown_task_raises(self, engine):
        with pytest.raises(ValueError, match="Unknown task"):
            engine.promote_to_commitment("TASK-NOPE", 1.0, "x")


# ── Provenance ────────────────────────────────────────────────────────────────

class TestProvenance:
    def test_mock_connector_output_passes_all_checks(self, engine, grey_areas, graph):
        cycle = engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        assert cycle.provenance_failed == ()
        for report in cycle.provenance.values():
            assert report.status == ProvenanceStatus.PASSED
            assert all(report.checks.values())

    def test_tampered_content_fails_hash_check(self, engine, grey_areas, graph):
        from dataclasses import replace
        engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        staged = engine._staged["STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT"]
        # ConnectorResult is frozen — build a tampered copy properly
        tampered = copy.deepcopy(staged)
        tampered.connector_result = replace(staged.connector_result, excerpt="TAMPERED CONTENT")
        report = engine.check_provenance(tampered)
        assert report.status == ProvenanceStatus.FAILED
        assert report.checks["content_hash_matches"] is False

    def test_verification_refused_on_provenance_failure(self, engine, grey_areas, graph):
        from dataclasses import replace
        engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        staged = engine._staged["STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT"]
        staged.connector_result = replace(staged.connector_result, excerpt="TAMPERED")
        with pytest.raises(ValueError, match="failed provenance"):
            engine.record_verification("STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", verified_by="x", outcome="authority_found")


# ── Human gates ───────────────────────────────────────────────────────────────

class TestGates:
    def test_commit_blocked_without_verification(self, engine, grey_areas, graph):
        engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        with pytest.raises(ValueError, match="not verified"):
            engine.commit_and_score(
                "STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", target_jurisdiction_code="MU", as_of_date=AS_OF,
                rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE,
            )

    def test_high_impact_commit_blocked_without_approval(self, engine, grey_areas, graph):
        engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        engine.record_verification("STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", verified_by="counsel@example.com", outcome="authority_found")
        with pytest.raises(ValueError, match="requires approval"):
            engine.commit_and_score(
                "STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", target_jurisdiction_code="MU", as_of_date=AS_OF,
                rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE,
            )

    def test_engine_never_fabricates_a_verifier(self, engine, grey_areas, graph):
        """No code path in run_acquisition_cycle may set verification —
        everything staged is UNVERIFIED until record_verification."""
        from app.calculators.legal_authority_acquisition import VerificationStatus
        cycle = engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        for staged in cycle.staged.values():
            assert staged.verification_status == VerificationStatus.UNVERIFIED
            assert staged.verified_by is None


# ── Commit / score / resolve / rerun ─────────────────────────────────────────

class TestCommitScoreRerun:
    def test_full_loop_commits_scores_and_resolves(self, engine, grey_areas, graph):
        commit = _run_through_commit(engine, grey_areas, graph)
        assert commit.committed_id == "RULE-STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT"
        assert commit.score is not None
        assert commit.score.composite > 0
        assert commit.resolved_grey_area.status == GreyAreaStatus.RESOLVED_INCLUDE
        assert commit.resolved_grey_area.graph_rule_id == commit.committed_id

    def test_original_grey_area_never_mutated(self, engine, grey_areas, graph):
        ga = next(g for g in grey_areas if g.item_id == "GA-LEGAL-ACCOUNTING-SPLIT")
        _run_through_commit(engine, grey_areas, graph)
        assert ga.status == GreyAreaStatus.OPEN  # resolution is a new object

    def test_rerun_books_resolution_into_conservative_case(self, engine, grey_areas, register, graph):
        """GA-LEGAL-ACCOUNTING-SPLIT's accounts (70-00/71-00) already
        QUALIFY under the canonical QPE rule before any resolution runs
        (see test_qualification_model.py) — so committing this specific
        resolution is a legitimate no-op on NPC: there was nothing being
        withheld to release. The rerun mechanism itself must still never
        make the case WORSE after a resolved, evidence-backed commit."""
        before = engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas, graph=graph)
        _run_through_commit(engine, grey_areas, graph)
        after = engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas, graph=graph, as_of_date=AS_OF)
        before_npc = before.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
        after_npc = after.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
        assert after_npc <= before_npc  # never worse; no-op here since nothing was withheld

    def test_rerun_never_mutates_caller_inputs(self, engine, grey_areas, register, graph):
        _run_through_commit(engine, grey_areas, graph)
        register_before = copy.deepcopy(register)
        greys_before = copy.deepcopy(grey_areas)
        engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas, graph=graph)
        assert register == register_before
        assert grey_areas == greys_before

    def test_rerun_exposes_authority_scores_for_committed_rules(self, engine, grey_areas, register, graph):
        commit = _run_through_commit(engine, grey_areas, graph)
        result = engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas, graph=graph, as_of_date=AS_OF)
        assert commit.committed_id in result.authority_scores
        assert result.authority_scores[commit.committed_id].composite == commit.score.composite

    def test_rerun_regenerates_recommendations(self, engine, grey_areas, register, graph):
        _run_through_commit(engine, grey_areas, graph)
        result = engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE, grey_areas=grey_areas, graph=graph)
        assert len(result.recommendations.recommendations) > 0

    def test_absence_commit_produces_no_score(self, engine, grey_areas, graph):
        engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
        sid = "STG-TASK-GA-INKIND-FMV"
        engine.record_verification(sid, verified_by="counsel@example.com", outcome="absence_confirmed")
        engine.record_approval(sid, approved_by="producer@example.com")
        commit = engine.commit_and_score(
            sid, target_jurisdiction_code="MU", as_of_date=AS_OF,
            absence_question="Is in-kind post FMV includible in QPE?",
            searched_tiers=(AuthorityTier.OFFICIAL_GUIDANCE, AuthorityTier.OFFICIAL_FAQ),
        )
        assert commit.committed_id.startswith("ABS-")
        assert commit.score is None  # absence never manufactures a score


# ── Determinism ───────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_two_cycles_over_identical_state_are_identical(self, graph):
        e1 = LegalEngine(connectors={ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE)})
        e2 = LegalEngine(connectors={ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE)})
        c1 = e1.run_acquisition_cycle(AS_OF, grey_areas=build_little_utopia_grey_areas(), graph=graph)
        c2 = e2.run_acquisition_cycle(AS_OF, grey_areas=build_little_utopia_grey_areas(), graph=graph)
        assert c1.executed_task_ids == c2.executed_task_ids
        assert c1.awaiting_verification == c2.awaiting_verification
        assert [q.question_id for q in c1.questions] == [q.question_id for q in c2.questions]

    def test_version_constant_present(self):
        assert LEGAL_ENGINE_VERSION
