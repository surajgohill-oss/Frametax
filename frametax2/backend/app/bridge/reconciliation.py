"""
Reconciliation layer (spec section 11). Compares findings across
multiple ReviewResponse objects (one or more providers, one package) and
groups them into ReconciledCluster records with an AgreementKind. NOTHING
in this module ever mutates a rule, a requirements profile, qualification
state, QPE, optimizer ranking, or production data — it only produces
clusters that a human dispositions via record_disposition(), and only
ACCEPTED_FOR_IMPLEMENTATION dispositions create an implementation task
reference (never code, never data).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.bridge.schema import (
    AgreementKind,
    Disposition,
    Finding,
    ReconciledCluster,
    ReviewResponse,
    new_id,
)


@dataclass(frozen=True)
class _AttributedFinding:
    provider: str
    finding: Finding


def _same_target(a: Finding, b: Finding) -> bool:
    """Two findings are "about the same thing" if they name the same
    jurisdiction/program AND the same affected rule/budget line — pure
    string match on the providers' own field values, never inferred."""
    return (
        (a.jurisdiction_or_program or "") == (b.jurisdiction_or_program or "")
        and (a.affected_rule_or_budget_line or "") == (b.affected_rule_or_budget_line or "")
        and bool(a.jurisdiction_or_program or a.affected_rule_or_budget_line)
    )


def _agreement_kind(members: list[_AttributedFinding]) -> AgreementKind:
    classifications = {m.finding.classification for m in members}
    providers = {m.provider for m in members}

    if len(providers) == 1:
        return AgreementKind.DUPLICATED_FINDING if len(members) > 1 else AgreementKind.FACTUAL_AGREEMENT

    if len(classifications) == 1:
        cls = next(iter(classifications))
        if cls.value in ("calculation_error", "qpe_classification_error", "stacking_error"):
            observed = {m.finding.observed_result for m in members}
            expected = {m.finding.expected_result for m in members}
            if len(observed) > 1 or len(expected) > 1:
                return AgreementKind.CALCULATION_DISAGREEMENT
        return AgreementKind.FACTUAL_AGREEMENT

    if any(c.value == "insufficient_evidence" for c in classifications):
        return AgreementKind.MISSING_EVIDENCE

    return AgreementKind.INTERPRETIVE_DISAGREEMENT


def reconcile(package_id: str, responses: list[ReviewResponse]) -> list[ReconciledCluster]:
    """Groups findings across all given ReviewResponses (already
    schema-validated) into clusters by (jurisdiction_or_program,
    affected_rule_or_budget_line). A finding with neither field set gets
    its own singleton cluster — never silently dropped."""
    attributed: list[_AttributedFinding] = [
        _AttributedFinding(provider=r.provider.value, finding=f)
        for r in responses for f in r.findings
    ]

    clusters: list[list[_AttributedFinding]] = []
    for item in attributed:
        placed = False
        for cluster in clusters:
            if _same_target(cluster[0].finding, item.finding):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])

    out: list[ReconciledCluster] = []
    for cluster in clusters:
        target = cluster[0].finding.jurisdiction_or_program or cluster[0].finding.affected_rule_or_budget_line
        out.append(ReconciledCluster(
            cluster_id=new_id("cluster", package_id, target or "", str(len(out))),
            package_id=package_id,
            jurisdiction_or_program=cluster[0].finding.jurisdiction_or_program,
            member_finding_ids=[f"{m.provider}:{m.finding.finding_id}" for m in cluster],
            agreement_kind=_agreement_kind(cluster),
        ))
    return out


def suggest_disposition(cluster: ReconciledCluster, responses: list[ReviewResponse]) -> Disposition:
    """A SUGGESTION only — reconcile()/this function never write a
    disposition themselves; record_disposition() is the only function
    that persists one, and it always requires an explicit human actor."""
    if cluster.agreement_kind == AgreementKind.DUPLICATED_FINDING:
        return Disposition.DUPLICATE
    if cluster.agreement_kind == AgreementKind.MISSING_EVIDENCE:
        return Disposition.NEEDS_PRIMARY_SOURCE
    if cluster.agreement_kind == AgreementKind.INTERPRETIVE_DISAGREEMENT:
        return Disposition.MODEL_DISAGREEMENT
    if cluster.agreement_kind == AgreementKind.CALCULATION_DISAGREEMENT:
        return Disposition.MODEL_DISAGREEMENT
    # FACTUAL_AGREEMENT and FACTUAL_CONFLICT both still require a human
    # to actually look at the evidence before this can become
    # CONFIRMED_DEFECT or ACCEPTED_FOR_IMPLEMENTATION — never auto-suggested.
    return Disposition.NEEDS_PRIMARY_SOURCE


def record_disposition(
    cluster: ReconciledCluster,
    disposition: Disposition,
    *,
    dispositioned_by: str,
    note: str | None = None,
    implementation_task_id: str | None = None,
) -> ReconciledCluster:
    """The ONLY function in this module that produces a dispositioned
    cluster. Requires a real actor identity (never defaults to "system"
    or "auto") — this is the human-gate the whole reconciliation layer
    exists to enforce."""
    if not dispositioned_by or not dispositioned_by.strip():
        raise ValueError("record_disposition requires a real dispositioned_by actor — never blank/auto.")
    if disposition == Disposition.ACCEPTED_FOR_IMPLEMENTATION and not implementation_task_id:
        raise ValueError(
            "ACCEPTED_FOR_IMPLEMENTATION requires implementation_task_id — "
            "an accepted finding must always produce an explicit implementation task, "
            "never a direct data/rule mutation."
        )
    from datetime import datetime, timezone
    return cluster.model_copy(update={
        "disposition": disposition,
        "disposition_note": note,
        "dispositioned_by": dispositioned_by,
        "dispositioned_at": datetime.now(timezone.utc).isoformat(),
        "implementation_task_id": implementation_task_id,
    })
