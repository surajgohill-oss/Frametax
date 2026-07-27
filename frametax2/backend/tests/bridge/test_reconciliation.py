from __future__ import annotations

import pytest

from app.bridge.reconciliation import reconcile, record_disposition, suggest_disposition
from app.bridge.schema import (
    AgreementKind,
    Disposition,
    Finding,
    FindingClassification,
    OverallDisposition,
    OperationType,
    ProviderID,
    ReconciledCluster,
    ReviewResponse,
    Severity,
)


def _finding(fid, **overrides):
    kwargs = dict(finding_id=fid, classification=FindingClassification.QUALIFICATION_GAP,
                  severity=Severity.MEDIUM, rationale="test", confidence=0.5)
    kwargs.update(overrides)
    return Finding(**kwargs)


def _response(review_id, provider, findings):
    return ReviewResponse(
        review_id=review_id, package_id="pkg_x", provider=provider, model="test-model",
        operation=OperationType.QUALIFICATION_AUDIT, overall_disposition=OverallDisposition.ISSUES_FOUND,
        executive_summary="test", findings=findings,
    )


class TestClustering:
    def test_two_providers_same_target_same_classification_is_factual_agreement(self):
        f1 = _finding("f1", jurisdiction_or_program="CY", affected_rule_or_budget_line="cultural_test")
        f2 = _finding("f2", jurisdiction_or_program="CY", affected_rule_or_budget_line="cultural_test")
        clusters = reconcile("pkg_x", [
            _response("r1", ProviderID.ANTHROPIC, [f1]),
            _response("r2", ProviderID.OPENAI, [f2]),
        ])
        assert len(clusters) == 1
        assert clusters[0].agreement_kind == AgreementKind.FACTUAL_AGREEMENT

    def test_two_providers_different_targets_are_separate_clusters(self):
        f1 = _finding("f1", jurisdiction_or_program="CY")
        f2 = _finding("f2", jurisdiction_or_program="GB")
        clusters = reconcile("pkg_x", [
            _response("r1", ProviderID.ANTHROPIC, [f1]),
            _response("r2", ProviderID.OPENAI, [f2]),
        ])
        assert len(clusters) == 2

    def test_two_findings_same_provider_same_target_is_duplicate(self):
        f1 = _finding("f1", jurisdiction_or_program="CY")
        f2 = _finding("f2", jurisdiction_or_program="CY")
        clusters = reconcile("pkg_x", [_response("r1", ProviderID.ANTHROPIC, [f1, f2])])
        assert clusters[0].agreement_kind == AgreementKind.DUPLICATED_FINDING

    def test_disagreeing_classifications_are_interpretive_disagreement(self):
        f1 = _finding("f1", jurisdiction_or_program="CY", classification=FindingClassification.CONFIRMED)
        f2 = _finding("f2", jurisdiction_or_program="CY", classification=FindingClassification.DISAGREEMENT)
        clusters = reconcile("pkg_x", [
            _response("r1", ProviderID.ANTHROPIC, [f1]),
            _response("r2", ProviderID.OPENAI, [f2]),
        ])
        assert clusters[0].agreement_kind == AgreementKind.INTERPRETIVE_DISAGREEMENT

    def test_finding_with_no_target_still_gets_its_own_cluster_never_dropped(self):
        f1 = _finding("f1")  # no jurisdiction, no rule line
        clusters = reconcile("pkg_x", [_response("r1", ProviderID.ANTHROPIC, [f1])])
        assert len(clusters) == 1
        assert clusters[0].member_finding_ids == ["anthropic:f1"]

    def test_calculation_disagreement_on_conflicting_observed_results(self):
        f1 = _finding("f1", jurisdiction_or_program="CY", affected_rule_or_budget_line="qpe",
                       classification=FindingClassification.CALCULATION_ERROR,
                       expected_result="100", observed_result="80")
        f2 = _finding("f2", jurisdiction_or_program="CY", affected_rule_or_budget_line="qpe",
                       classification=FindingClassification.CALCULATION_ERROR,
                       expected_result="100", observed_result="90")
        clusters = reconcile("pkg_x", [
            _response("r1", ProviderID.ANTHROPIC, [f1]),
            _response("r2", ProviderID.OPENAI, [f2]),
        ])
        assert clusters[0].agreement_kind == AgreementKind.CALCULATION_DISAGREEMENT


class TestNoAutomaticRuleMutation:
    """The central safety property of the whole reconciliation layer."""

    def test_record_disposition_requires_real_actor(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.FACTUAL_AGREEMENT, member_finding_ids=[])
        with pytest.raises(ValueError, match="real dispositioned_by actor"):
            record_disposition(cluster, Disposition.REJECTED, dispositioned_by="")

    def test_record_disposition_rejects_none_actor_implicitly_via_type(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.FACTUAL_AGREEMENT, member_finding_ids=[])
        with pytest.raises(ValueError):
            record_disposition(cluster, Disposition.REJECTED, dispositioned_by="   ")

    def test_accepted_for_implementation_requires_task_id(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.FACTUAL_AGREEMENT, member_finding_ids=[])
        with pytest.raises(ValueError, match="requires implementation_task_id"):
            record_disposition(cluster, Disposition.ACCEPTED_FOR_IMPLEMENTATION, dispositioned_by="tester")

    def test_accepted_for_implementation_succeeds_with_task_id_and_real_actor(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.FACTUAL_AGREEMENT, member_finding_ids=[])
        result = record_disposition(
            cluster, Disposition.ACCEPTED_FOR_IMPLEMENTATION,
            dispositioned_by="claude-session-abc", implementation_task_id="task-123",
        )
        assert result.disposition == Disposition.ACCEPTED_FOR_IMPLEMENTATION
        assert result.implementation_task_id == "task-123"
        assert result.dispositioned_by == "claude-session-abc"

    def test_reconcile_itself_never_sets_a_disposition(self):
        f1 = _finding("f1", jurisdiction_or_program="CY")
        clusters = reconcile("pkg_x", [_response("r1", ProviderID.ANTHROPIC, [f1])])
        assert clusters[0].disposition is None

    def test_suggest_disposition_is_pure_never_persists_anything(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.DUPLICATED_FINDING, member_finding_ids=[])
        suggestion = suggest_disposition(cluster, [])
        assert cluster.disposition is None  # the input cluster itself is untouched
        assert suggestion == Disposition.DUPLICATE


class TestSuggestDisposition:
    def test_duplicate_suggests_duplicate(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.DUPLICATED_FINDING, member_finding_ids=[])
        assert suggest_disposition(cluster, []) == Disposition.DUPLICATE

    def test_missing_evidence_suggests_needs_primary_source(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.MISSING_EVIDENCE, member_finding_ids=[])
        assert suggest_disposition(cluster, []) == Disposition.NEEDS_PRIMARY_SOURCE

    def test_interpretive_disagreement_suggests_model_disagreement(self):
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.INTERPRETIVE_DISAGREEMENT, member_finding_ids=[])
        assert suggest_disposition(cluster, []) == Disposition.MODEL_DISAGREEMENT

    def test_factual_agreement_never_auto_suggests_confirmed_defect(self):
        """Even clean agreement across providers still requires a human
        to look at evidence before CONFIRMED_DEFECT — never auto-suggested."""
        cluster = ReconciledCluster(cluster_id="c1", package_id="p1",
                                     agreement_kind=AgreementKind.FACTUAL_AGREEMENT, member_finding_ids=[])
        assert suggest_disposition(cluster, []) != Disposition.CONFIRMED_DEFECT
        assert suggest_disposition(cluster, []) != Disposition.ACCEPTED_FOR_IMPLEMENTATION
