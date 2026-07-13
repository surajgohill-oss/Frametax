"""
test_legal_authority_acquisition.py

Targeted tests for Phase 6A-6E of the Legal Authority Acquisition Engine
(legal_authority_acquisition.py). Covers docket generation, staging
lifecycle, connector policy boundaries, verification/approval gates,
Evidence Graph commit behavior, absence-as-first-class-outcome, and
freshness/supersession review-queue hooks.
"""
from __future__ import annotations

import pytest

from app.calculators.evidence_graph import AuthorityTier, EvidenceGraph
from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.optimization_engine import build_risk_cases
from app.calculators.qualification_model import (
    GreyAreaStatus,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)
from app.calculators.structuring_paths import derive_structuring_paths

from app.calculators.legal_authority_acquisition import (
    LAAE_VERSION,
    AcquisitionDocket,
    AcquisitionPriority,
    AcquisitionStatus,
    ApprovalClass,
    ConnectorClass,
    FreshnessClass,
    MockConnector,
    QuestionGrade,
    VerificationStatus,
    approve_staged_authority,
    build_docket,
    classify_approval,
    classify_freshness,
    commit_staged_authority,
    compute_priority_score,
    content_hash_of,
    detect_stale_authority,
    flag_supersession_for_review,
    priority_band,
    reject_staged_authority,
    run_connector,
    tasks_from_grey_areas,
    tasks_from_jurisdiction_graph_unknowns,
    verify_staged_authority,
)

MU_RATE = 0.40


@pytest.fixture(scope="module")
def grey_areas():
    return build_little_utopia_grey_areas()


@pytest.fixture(scope="module")
def graph():
    return build_jurisdiction_graph(mu_rate=MU_RATE)


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert LAAE_VERSION == "1.0.0"

    def test_eleven_lifecycle_states(self):
        assert len(AcquisitionStatus) == 11
        names = {s.value for s in AcquisitionStatus}
        assert names == {
            "identified", "queued", "connector_selected", "retrieved", "staged",
            "parsed", "verified", "approved", "committed", "rejected", "superseded",
        }

    def test_six_connector_classes(self):
        assert len(ConnectorClass) == 6


# ── Docket creation from grey areas ─────────────────────────────────────────

class TestDocketFromGreyAreas:
    def test_open_grey_areas_produce_tasks(self, grey_areas):
        tasks = tasks_from_grey_areas(grey_areas)
        assert len(tasks) == 2
        ids = {t.source_ref for t in tasks}
        assert ids == {"GA-LEGAL-ACCOUNTING-SPLIT", "GA-INKIND-FMV"}

    def test_tasks_are_commitment_grade(self, grey_areas):
        tasks = tasks_from_grey_areas(grey_areas)
        assert all(t.question_grade == QuestionGrade.COMMITMENT for t in tasks)

    def test_task_carries_existing_amount_not_invented(self, grey_areas):
        tasks = tasks_from_grey_areas(grey_areas)
        by_ref = {t.source_ref: t for t in tasks}
        assert by_ref["GA-LEGAL-ACCOUNTING-SPLIT"].value_at_stake_usd == 113_000.0

    def test_resolved_grey_area_excluded_from_docket(self):
        areas = build_little_utopia_grey_areas()
        areas[0].status = GreyAreaStatus.RESOLVED_INCLUDE
        tasks = tasks_from_grey_areas(areas)
        assert len(tasks) == 1
        assert tasks[0].source_ref == "GA-INKIND-FMV"


# ── Docket creation from jurisdiction graph unknowns ────────────────────────

class TestDocketFromJurisdictionUnknowns:
    def test_produces_tasks(self, graph):
        tasks = tasks_from_jurisdiction_graph_unknowns(graph)
        assert len(tasks) > 0

    def test_tasks_are_scenario_grade(self, graph):
        tasks = tasks_from_jurisdiction_graph_unknowns(graph)
        assert all(t.question_grade == QuestionGrade.SCENARIO for t in tasks)

    def test_no_invented_value_at_stake(self, graph):
        tasks = tasks_from_jurisdiction_graph_unknowns(graph)
        assert all(t.value_at_stake_usd is None for t in tasks)

    def test_mauritius_absence_nodes_produce_absent_confidence_gap(self, graph):
        tasks = tasks_from_jurisdiction_graph_unknowns(graph)
        mu_tasks = [t for t in tasks if t.jurisdiction_code == "MU"]
        assert any(t.confidence_gap == 1.0 for t in mu_tasks)

    def test_reinvestment_unknown_creates_task_not_not_permitted(self, graph):
        """Mauritius's reinvestment profile is UNKNOWN (absence of
        authority), not NOT_PERMITTED — a task must exist for it, and its
        question must reference reinvestment treatment, not a permitted/
        not-permitted determination."""
        tasks = tasks_from_jurisdiction_graph_unknowns(graph)
        reinvestment_tasks = [t for t in tasks if "reinvestment" in t.question.lower()]
        assert any(t.jurisdiction_code == "MU" for t in reinvestment_tasks)
        for t in reinvestment_tasks:
            assert "not_permitted" not in t.question.lower()
            assert "permitted" not in t.question.lower()


# ── Prioritization formula ──────────────────────────────────────────────────

class TestPrioritizationFormula:
    def test_formula_is_value_times_gap_over_effort(self):
        score = compute_priority_score(value_at_stake_usd=100_000.0, confidence_gap=0.5, acquisition_effort=2.0)
        assert score == pytest.approx(25_000.0)

    def test_none_value_treated_as_zero_not_invented(self):
        score = compute_priority_score(value_at_stake_usd=None, confidence_gap=1.0, acquisition_effort=1.0)
        assert score == 0.0

    def test_deterministic_repeated_calls(self, grey_areas):
        first = [t.priority_score for t in tasks_from_grey_areas(grey_areas)]
        second = [t.priority_score for t in tasks_from_grey_areas(grey_areas)]
        assert first == second

    def test_docket_sort_is_deterministic_across_runs(self, grey_areas, graph):
        d1 = build_docket("D-1", grey_areas=grey_areas, graph=graph)
        d2 = build_docket("D-2", grey_areas=grey_areas, graph=graph)
        ids1 = [t.task_id for t in d1.sorted_by_priority()]
        ids2 = [t.task_id for t in d2.sorted_by_priority()]
        assert ids1 == ids2

    def test_priority_band_thresholds(self):
        assert priority_band(60_000.0) == AcquisitionPriority.CRITICAL
        assert priority_band(15_000.0) == AcquisitionPriority.HIGH
        assert priority_band(5_000.0) == AcquisitionPriority.MEDIUM
        assert priority_band(0.0) == AcquisitionPriority.LOW

    def test_grey_area_tasks_outrank_scenario_unknowns_in_docket(self, grey_areas, graph):
        """A real, valued grey area (nonzero value_at_stake) must sort
        above a value-less scenario unknown."""
        docket = build_docket("D-MIXED", grey_areas=grey_areas, graph=graph)
        ranked = docket.sorted_by_priority()
        top = ranked[0]
        assert top.source_kind == "grey_area"


# ── Execution policy: scenario vs. commitment grade ─────────────────────────

class TestExecutionPolicy:
    def test_scenario_task_does_not_auto_execute(self, graph):
        tasks = tasks_from_jurisdiction_graph_unknowns(graph)
        task = tasks[0]
        connector = MockConnector()
        with pytest.raises(ValueError, match="scenario-grade"):
            run_connector(task, connector, as_of_date="2026-01-01")

    def test_commitment_task_can_queue_connector_work(self, grey_areas):
        task = tasks_from_grey_areas(grey_areas)[0]
        connector = MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE)
        staged = run_connector(task, connector, as_of_date="2026-01-01")
        assert staged.status == AcquisitionStatus.STAGED
        assert task.status == AcquisitionStatus.STAGED

    def test_run_connector_rejects_already_staged_task(self, grey_areas):
        task = tasks_from_grey_areas(grey_areas)[0]
        connector = MockConnector()
        run_connector(task, connector, as_of_date="2026-01-01")
        with pytest.raises(ValueError, match="cannot run a connector"):
            run_connector(task, connector, as_of_date="2026-01-01")


# ── Mock connector ───────────────────────────────────────────────────────────

class TestMockConnector:
    def test_produces_staged_authority(self, grey_areas):
        task = tasks_from_grey_areas(grey_areas)[0]
        connector = MockConnector()
        staged = run_connector(task, connector, as_of_date="2026-01-01")
        assert staged.connector_result.task_id == task.task_id
        assert staged.connector_result.retrieved_date == "2026-01-01"

    def test_deterministic_content_hash(self, grey_areas):
        task = tasks_from_grey_areas(grey_areas)[0]
        s1 = run_connector(task, MockConnector(), as_of_date="2026-01-01")
        task2 = tasks_from_grey_areas(grey_areas)[0]
        s2 = run_connector(task2, MockConnector(), as_of_date="2026-01-01")
        assert s1.connector_result.content_hash == s2.connector_result.content_hash

    def test_content_hash_helper_deterministic(self):
        assert content_hash_of("abc") == content_hash_of("abc")
        assert content_hash_of("abc") != content_hash_of("abd")


# ── Staging / verification / approval / commit ──────────────────────────────

class TestStagingLifecycle:
    def _staged(self, grey_areas, item_ref="GA-LEGAL-ACCOUNTING-SPLIT"):
        task = next(t for t in tasks_from_grey_areas(grey_areas) if t.source_ref == item_ref)
        return run_connector(task, MockConnector(), as_of_date="2026-01-01")

    def test_unverified_cannot_commit(self, grey_areas):
        staged = self._staged(grey_areas)
        graph = EvidenceGraph()
        with pytest.raises(ValueError, match="not verified"):
            commit_staged_authority(staged, graph, rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE)

    def test_verified_can_commit_rule(self, grey_areas):
        staged = self._staged(grey_areas)
        verify_staged_authority(staged, verified_by="reviewer@cineglobe", outcome="authority_found")
        if staged.approval_class == ApprovalClass.REQUIRES_APPROVAL:
            approve_staged_authority(staged, approved_by="counsel@cineglobe")
        graph = EvidenceGraph()
        decision = commit_staged_authority(
            staged, graph,
            rule_text="ATL writer/director/producer fees qualify as QPE under EDB guidance §4.2.",
            tier=AuthorityTier.OFFICIAL_GUIDANCE,
        )
        assert decision.decision == "commit_rule"
        assert staged.status == AcquisitionStatus.COMMITTED
        rule = graph.get_rule(decision.committed_rule_id)
        assert graph.rule_is_fully_chained(rule.rule_id)

    def test_absence_finding_is_first_class_outcome(self, grey_areas):
        staged = self._staged(grey_areas, "GA-INKIND-FMV")
        verify_staged_authority(staged, verified_by="reviewer@cineglobe", outcome="absence_confirmed")
        if staged.approval_class == ApprovalClass.REQUIRES_APPROVAL:
            approve_staged_authority(staged, approved_by="counsel@cineglobe")
        graph = EvidenceGraph()
        decision = commit_staged_authority(
            staged, graph,
            absence_question="Does in-kind post FMV qualify as QPE?",
            searched_tiers=(AuthorityTier.PRIMARY_LEGISLATION, AuthorityTier.OFFICIAL_GUIDANCE),
        )
        assert decision.decision == "commit_absence"
        absence = graph.get_absence_of_authority(decision.committed_absence_id)
        assert absence.jurisdiction_code == "MU"

    def test_high_impact_requires_approval_before_commit(self, grey_areas):
        staged = self._staged(grey_areas, "GA-LEGAL-ACCOUNTING-SPLIT")  # 113,000 >= 50,000 threshold
        assert staged.approval_class == ApprovalClass.REQUIRES_APPROVAL
        verify_staged_authority(staged, verified_by="reviewer@cineglobe", outcome="authority_found")
        graph = EvidenceGraph()
        with pytest.raises(ValueError, match="requires approval"):
            commit_staged_authority(staged, graph, rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE)
        approve_staged_authority(staged, approved_by="counsel@cineglobe")
        decision = commit_staged_authority(staged, graph, rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE)
        assert decision.decision == "commit_rule"

    def test_low_impact_auto_eligible_no_approval_needed(self):
        # Build a low-value grey-area-shaped task directly to exercise the
        # auto-eligible path without depending on Little Utopia amounts.
        from app.calculators.legal_authority_acquisition import AcquisitionTask
        task = AcquisitionTask(
            task_id="TASK-LOW", jurisdiction_code="MU", question="q",
            question_grade=QuestionGrade.COMMITMENT, source_kind="grey_area",
            source_ref="GA-LOW", value_at_stake_usd=500.0,
            confidence_gap=1.0, acquisition_effort=2.0,
        )
        staged = run_connector(task, MockConnector(), as_of_date="2026-01-01")
        assert staged.approval_class == ApprovalClass.AUTO_ELIGIBLE
        verify_staged_authority(staged, verified_by="reviewer@cineglobe", outcome="authority_found")
        graph = EvidenceGraph()
        decision = commit_staged_authority(staged, graph, rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE)
        assert decision.decision == "commit_rule"

    def test_rejected_authority_cannot_commit(self, grey_areas):
        staged = self._staged(grey_areas)
        reject_staged_authority(staged, rejected_by="reviewer@cineglobe", notes="source not authoritative")
        assert staged.verification_status == VerificationStatus.REJECTED
        graph = EvidenceGraph()
        with pytest.raises(ValueError, match="not verified"):
            commit_staged_authority(staged, graph, rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE)

    def test_classify_approval_threshold(self):
        from app.calculators.legal_authority_acquisition import AcquisitionTask
        low = AcquisitionTask(
            task_id="T1", jurisdiction_code="MU", question="q", question_grade=QuestionGrade.COMMITMENT,
            source_kind="grey_area", source_ref="r", value_at_stake_usd=49_999.0,
            confidence_gap=1.0, acquisition_effort=1.0,
        )
        high = AcquisitionTask(
            task_id="T2", jurisdiction_code="MU", question="q", question_grade=QuestionGrade.COMMITMENT,
            source_kind="grey_area", source_ref="r", value_at_stake_usd=50_000.0,
            confidence_gap=1.0, acquisition_effort=1.0,
        )
        assert classify_approval(low) == ApprovalClass.AUTO_ELIGIBLE
        assert classify_approval(high) == ApprovalClass.REQUIRES_APPROVAL


# ── Freshness / supersession ────────────────────────────────────────────────

class TestFreshnessAndSupersession:
    def test_fresh_within_aging_window(self):
        assert classify_freshness("2026-01-01", "2026-03-01") == FreshnessClass.FRESH

    def test_aging_between_windows(self):
        assert classify_freshness("2025-01-01", "2026-01-01") == FreshnessClass.AGING

    def test_stale_beyond_window(self):
        assert classify_freshness("2020-01-01", "2026-01-01") == FreshnessClass.STALE

    def test_unknown_when_no_retrieved_date(self):
        assert classify_freshness(None, "2026-01-01") == FreshnessClass.UNKNOWN

    def test_detect_stale_authority_produces_review_entries(self):
        held = [
            ("RULE-1", "MU", "2020-01-01"),
            ("RULE-2", "MU", "2026-01-01"),
        ]
        entries = detect_stale_authority(held, as_of_date="2026-06-01")
        assert len(entries) == 1
        assert entries[0].subject_id == "RULE-1"
        assert entries[0].reason == "stale_authority"

    def test_supersession_creates_review_needed_entry(self):
        from app.calculators.evidence_graph import DocumentVersion
        new_version = DocumentVersion(
            version_id="DOCV-2", document_id="DOC-1", version_label="v2",
            retrieved_date="2026-06-01",
        )
        entry = flag_supersession_for_review("DOCV-1", new_version, jurisdiction_code="MU")
        assert entry.reason == "superseded_source"
        assert entry.subject_id == "DOCV-1"
        assert "DOCV-2" in entry.notes


# ── Architectural boundaries ─────────────────────────────────────────────────

class TestArchitecturalBoundaries:
    def test_module_does_not_import_optimization_engine(self):
        import ast
        import inspect
        import app.calculators.legal_authority_acquisition as laae_module

        tree = ast.parse(inspect.getsource(laae_module))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any("optimization_engine" in m for m in imported)

    def test_optimization_engine_does_not_import_laae(self):
        import ast
        import inspect
        import app.calculators.optimization_engine as opt_module

        tree = ast.parse(inspect.getsource(opt_module))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any("legal_authority_acquisition" in m for m in imported)

    def test_no_optimizer_output_changes(self):
        register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
        paths = derive_structuring_paths(register, rate=MU_RATE)
        result = build_risk_cases(
            register=register, gross_budget_usd=4_364_393.0, rate=MU_RATE,
            structuring_paths=paths,
        )
        from app.calculators.optimization_engine import RiskCase
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(3_700_954.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_480_381.6, abs=1.0)

    def test_no_jurisdiction_graph_mutation(self, graph):
        node_count_before = len(graph.nodes)
        rel_count_before = len(graph.relationships)
        tasks_from_jurisdiction_graph_unknowns(graph)
        assert len(graph.nodes) == node_count_before
        assert len(graph.relationships) == rel_count_before

    def test_commit_only_writes_to_evidence_graph_param(self, grey_areas):
        task = next(t for t in tasks_from_grey_areas(grey_areas) if t.source_ref == "GA-LEGAL-ACCOUNTING-SPLIT")
        staged = run_connector(task, MockConnector(), as_of_date="2026-01-01")
        verify_staged_authority(staged, verified_by="r", outcome="authority_found")
        approve_staged_authority(staged, approved_by="c")
        graph1 = EvidenceGraph()
        graph2 = EvidenceGraph()
        commit_staged_authority(staged, graph1, rule_text="x", tier=AuthorityTier.OFFICIAL_GUIDANCE)
        assert len(graph1._rules) == 1
        assert len(graph2._rules) == 0
