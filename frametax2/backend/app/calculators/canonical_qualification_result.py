"""
canonical_qualification_result.py

Canonical Co-production Qualification Reconnection — Task 4. The ONE
structured qualification-result contract used by every qualification
consumer this phase reconnects (role/nationality gates now, treaty/
cultural scoring later if reconnected in a future phase). Never
collapsed into a single boolean or a single string status — every state
Codex's audit found necessary is a distinct value, and every dimension a
regime's rule data can name is a distinct optional field, present only
when real data exists for it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CANONICAL_QUALIFICATION_RESULT_VERSION = "1.0.0"

# ── Qualification state vocabulary (Task 4) — never collapsed ───────────
QUAL_QUALIFIES = "QUALIFIES"
QUAL_HARD_FAIL = "HARD_FAIL"
QUAL_CURABLE_GAP = "CURABLE_GAP"
QUAL_USER_FACT_REQUIRED = "USER_FACT_REQUIRED"
QUAL_SCRIPT_FACT_REQUIRED = "SCRIPT_FACT_REQUIRED"
QUAL_RULE_DATA_INCOMPLETE = "RULE_DATA_INCOMPLETE"
QUAL_NOT_APPLICABLE = "NOT_APPLICABLE"

ALL_QUALIFICATION_STATES = frozenset({
    QUAL_QUALIFIES, QUAL_HARD_FAIL, QUAL_CURABLE_GAP, QUAL_USER_FACT_REQUIRED,
    QUAL_SCRIPT_FACT_REQUIRED, QUAL_RULE_DATA_INCOMPLETE, QUAL_NOT_APPLICABLE,
})


@dataclass(frozen=True)
class RoleGateFinding:
    """One role-level gate check, preserved individually — never
    flattened into a single pass/fail for the whole regime."""
    role: str
    required_jurisdiction: str | None
    status: str  # "satisfied" | "failed" | "indeterminate" (cultural_qualification_model.GateStatus)
    known_codes: tuple[str, ...]
    notes: str


@dataclass
class CanonicalQualificationResult:
    """Task 4 — the one canonical qualification result contract.
    Preserves every dimension Codex's audit named, populated only where
    real data/facts actually support it; every unpopulated field stays
    None/empty rather than being guessed."""
    regime_id: str                      # program_slug or treaty_slug
    jurisdiction_code: str | None
    state: str                          # one of ALL_QUALIFICATION_STATES

    # Qualification route / identity
    qualification_route: str | None = None   # e.g. "role_nationality_gate", "bilateral_treaty", "eurimages"

    # Role-level findings (Task 5) — one per role this regime's data names
    role_findings: tuple[RoleGateFinding, ...] = ()

    # Point-bearing / threshold state (Task 7) — only when real point data exists
    current_points: float | None = None
    required_points: float | None = None

    # Contribution / ownership (Task 8) — only when real facts exist
    contribution_requirements: tuple[str, ...] = ()
    ownership_control_requirements: tuple[str, ...] = ()

    # Resolution bookkeeping
    resolved_facts: tuple[str, ...] = ()
    missing_facts: tuple[str, ...] = ()
    failed_requirements: tuple[str, ...] = ()
    curable_requirements: tuple[str, ...] = ()
    available_levers: tuple[str, ...] = ()

    # Provenance (Task 4)
    authority_basis: str | None = None
    confidence_state: str = "LOW"       # LOW | MEDIUM | HIGH — mirrors QualificationConfidence
    reasoning_trace: tuple[str, ...] = field(default_factory=tuple)


def qualification_result_to_dict(r: CanonicalQualificationResult) -> dict:
    return {
        "regime_id": r.regime_id,
        "jurisdiction_code": r.jurisdiction_code,
        "state": r.state,
        "qualification_route": r.qualification_route,
        "role_findings": [
            {
                "role": f.role, "required_jurisdiction": f.required_jurisdiction,
                "status": f.status, "known_codes": list(f.known_codes), "notes": f.notes,
            }
            for f in r.role_findings
        ],
        "current_points": r.current_points,
        "required_points": r.required_points,
        "contribution_requirements": list(r.contribution_requirements),
        "ownership_control_requirements": list(r.ownership_control_requirements),
        "resolved_facts": list(r.resolved_facts),
        "missing_facts": list(r.missing_facts),
        "failed_requirements": list(r.failed_requirements),
        "curable_requirements": list(r.curable_requirements),
        "available_levers": list(r.available_levers),
        "authority_basis": r.authority_basis,
        "confidence_state": r.confidence_state,
        "reasoning_trace": list(r.reasoning_trace),
    }
