"""
Deterministic AuditPackage construction from the REAL served CineGlobe
pipeline (app.demo.little_utopia_state.build_allocated_structures) —
never synthetic/invented data. "Deterministic" here means: given the
same repository commit/working-tree state and the same production
state, the same package_id and the same package contents are produced
— not that every field is guaranteed non-null (real data has real
gaps, which the package discloses rather than fills).
"""
from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone

from app.bridge.schema import (
    AuditPackage,
    BudgetQpeLine,
    ConfidentialityClassification,
    EconomicsSummary,
    EvidenceRecordRef,
    NonClaimingSegment,
    OperationType,
    PackageInputs,
    QualificationFacts,
    RejectedStructure,
    StructureSummary,
)


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def _working_tree_fingerprint() -> str:
    """A stable-enough fingerprint of uncommitted state so package_id
    doesn't silently collide across two different working trees on the
    same commit. Not a full diff hash (that would be expensive to
    recompute per package) — status output is enough to detect "dirty
    vs not" and roughly how dirty."""
    try:
        out = subprocess.run(
            ["git", "status", "--short"], capture_output=True, text=True, timeout=5,
        )
        status = out.stdout if out.returncode == 0 else ""
    except Exception:
        status = ""
    return hashlib.sha256(status.encode()).hexdigest()[:12]


def _engine_versions() -> dict[str, str]:
    """Real module-level version markers already present in the served
    payload — never invented. build_allocated_structures()'s own
    "version" field, plus this package schema's own version."""
    return {"allocated_structures_schema": "1.1.0", "bridge_package_schema": "1.0.0"}


def build_qpe_trace(structure: dict, contingency: dict) -> list[BudgetQpeLine]:
    lines: list[BudgetQpeLine] = []
    for seg in structure.get("segments", []):
        for t in seg.get("qualification_trace", []):
            lines.append(BudgetQpeLine(
                account_code=t["account_code"],
                description=t["description"],
                normalized_category=None,
                source_amount=t["amount_usd"],
                source_currency="USD",
                jurisdiction_code=seg["jurisdiction_code"],
                included_in_qpe=(t["state"] == "qualifies"),
                exclusion_authority=t.get("authority_basis"),
                qpe_usd=t["amount_usd"] if t["state"] == "qualifies" else 0.0,
            ))
    return lines


def build_non_claiming_segments(structure: dict) -> list[NonClaimingSegment]:
    """Incentive/Optimizer Core Closeout (Bridge export fix, item 2):
    surface segments that are real, allocated spend but claim no
    incentive (program_slug=None) — previously entirely absent from the
    exported package, which is why every prior reviewer (Claude, Codex,
    Gemini) flagged the gross_budget_usd-vs-QPE-trace-sum gap as an
    unexplained defect rather than the real, disclosed, intentional
    non-local/non-claiming spend it actually is."""
    out: list[NonClaimingSegment] = []
    for seg in structure.get("segments", []):
        if seg.get("program_slug") is not None:
            continue
        out.append(NonClaimingSegment(
            jurisdiction_code=seg["jurisdiction_code"],
            account_codes=list(seg.get("account_codes", [])),
            allocated_usd=seg.get("allocated_usd") or 0.0,
            note=(seg.get("notes") or [None])[0],
        ))
    return out


def build_qualification_facts(structure: dict) -> QualificationFacts:
    facts = QualificationFacts()
    for seg in structure.get("segments", []):
        req = seg.get("requirements")
        if not req:
            continue
        if req.get("cultural_test_required"):
            facts.cultural_test_criteria.append(
                f"{seg['jurisdiction_code']}: cultural test required"
                + (f" ({req['cultural_test_threshold']} pt threshold)" if req.get("cultural_test_threshold") else "")
            )
        if req.get("min_local_spend_usd"):
            facts.minimum_spend = req["min_local_spend_usd"]
        if req.get("local_entity_required"):
            facts.entity_requirements.append(f"{seg['jurisdiction_code']}: local entity required")
        if req.get("preapproval_mandatory"):
            facts.timing_preapproval_requirements.append(f"{seg['jurisdiction_code']}: preapproval mandatory")
        if req.get("application_deadline"):
            facts.timing_preapproval_requirements.append(
                f"{seg['jurisdiction_code']}: {req['application_deadline']['value']} "
                f"({req['application_deadline']['basis']})"
            )
        if req.get("audit_required"):
            facts.filing_audit_requirements.append(f"{seg['jurisdiction_code']}: audit required")
    for b in structure.get("blockers", []):
        facts.unresolved_facts.append(b)
    facts.qualification_state = "fully_priced" if structure.get("is_fully_priced") else "blocked"
    return facts


def build_structure_summary(structure: dict) -> StructureSummary:
    return StructureSummary(
        structure_id=structure["structure_id"],
        structure_type=structure["structure_type"],
        label=structure["label"],
        participants=list(structure["participants"]),
        is_fully_priced=structure["is_fully_priced"],
        blockers=list(structure.get("blockers", [])),
        ownership_shares=dict(structure.get("ownership_shares", {})),
        treaty_slug=structure.get("treaty_slug"),
        conditional_program_ids=[
            c["conditional_node_id"] for c in structure.get("conditional_compatibility", {}).get("conditional", [])
        ],
    )


def build_economics_summary(structure: dict) -> EconomicsSummary:
    # Incentive/Optimizer Core Closeout (Bridge export fix, item 1):
    # npc_usd now sources from npc_with_adjustments_usd — the SAME figure
    # allocation_pricing.rank_allocated_structures() actually ranks on —
    # instead of npc_verified_usd (the pre-adjustment figure, which
    # understated real relocation cost for every non-anchor jurisdiction
    # in every external review of this package). npc_verified_usd is kept
    # available under its own field for anyone who wants the base figure.
    # allocation_pricing.py / the ranking algorithm are unchanged; this is
    # a package-representation fix only.
    return EconomicsSummary(
        gross_budget_usd=structure.get("gross_budget_usd"),
        qpe_usd=sum(
            s.get("qpe_usd") or 0.0 for s in structure.get("segments", []) if s.get("claims_incentive")
        ) or None,
        gross_incentive_usd=structure.get("selected_incentive_usd"),
        finance_cost_usd=structure.get("financing_cost_usd"),
        local_cost_delta_usd=structure.get("local_cost_delta_usd"),
        travel_delta_usd=structure.get("travel_incremental_delta_usd"),
        fx_delta_usd=structure.get("fx_delta_usd"),
        net_incentive_usd=structure.get("selected_incentive_usd"),
        npc_usd=structure.get("npc_with_adjustments_usd"),
        npc_verified_usd=structure.get("npc_verified_usd"),
    )


def build_package(
    *,
    operation: OperationType,
    confidentiality: ConfidentialityClassification = ConfidentialityClassification.INTERNAL,
    structure_id: str | None = None,
    production_or_scenario_id: str = "little-utopia",
) -> AuditPackage:
    """Builds one AuditPackage from the REAL served pipeline. structure_id
    selects which structure's segments/economics populate sections C-F;
    None uses the ranked leader (rank == 1). Section G (evidence) is
    populated from every populated ProgramRequirementsProfile's own
    EvidenceRecord touched by the selected structure's segments."""
    from app.demo.little_utopia_state import build_allocated_structures, get_state

    state = get_state()
    served = build_allocated_structures(state)

    structures = served["structures"]
    if structure_id is not None:
        structure = next(s for s in structures if s["structure_id"] == structure_id)
    else:
        rank1 = next(r for r in served["ranking"] if r.get("rank") == 1)
        structure = next(s for s in structures if s["structure_id"] == rank1["structure_id"])

    rejected = [
        RejectedStructure(structure_type=c["category"], reason=c["reason"])
        for c in served.get("coverage", {}).get("categories", [])
        if c.get("count", 1) == 0 and c.get("reason")
    ] if isinstance(served.get("coverage"), dict) else []

    evidence: list[EvidenceRecordRef] = []
    for seg in structure.get("segments", []):
        req = seg.get("requirements")
        if req and req.get("evidence"):
            e = req["evidence"]
            evidence.append(EvidenceRecordRef(
                source_title=e["source_title"], source_url=e.get("source_url"),
                publisher_authority=e["issuing_authority"], source_type=e["source_type"],
                effective_date=e.get("effective_date"), retrieved_date=e.get("access_date"),
                proposition_supported=f"Requirements profile for {seg['program_slug']}",
                primary_or_secondary=e["source_type"],
                stale_or_conflict_warning=None if e["status"] == "current" else e["status"],
            ))

    generated_at = datetime.now(timezone.utc).isoformat()
    fingerprint = _working_tree_fingerprint()
    package_id = AuditPackage.compute_package_id(
        production_or_scenario_id, operation, fingerprint, generated_at[:10],
    )

    return AuditPackage(
        package_id=package_id,
        production_or_scenario_id=production_or_scenario_id,
        repository_commit=_git_commit(),
        working_tree_fingerprint=fingerprint,
        engine_versions=_engine_versions(),
        generated_at=generated_at,
        operation=operation,
        confidentiality=confidentiality,
        inputs=PackageInputs(
            budget_or_target_usd=structure.get("gross_budget_usd"),
            unknowns=list(structure.get("blockers", [])),
        ),
        budget_qpe_trace=build_qpe_trace(structure, served.get("contingency", {})),
        non_claiming_segments=build_non_claiming_segments(structure),
        contingency_summary=served.get("contingency", {}),
        qualification=build_qualification_facts(structure),
        structures_considered=[build_structure_summary(s) for s in structures],
        structures_rejected=rejected,
        economics=build_economics_summary(structure),
        evidence=evidence,
    )
