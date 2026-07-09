"""
structuring_paths.py

StructuringPath model: the object form of a STRUCTURING_OPPORTUNITY
account from qualification_model.py — a currently non-qualifying account
that no rule bars, blocked only by production structure (routing,
employer-of-record, vendor location).

A path has a lifecycle (PROPOSED -> APPROVED -> EXECUTED -> REALIZED) and
economics (structured value, implementation cost, confidence) that
optimization_engine.py consumes to decide which case (Base/Conservative)
a path's upside belongs in.

No LLM calls. Implementation-cost figures are clearly labeled
representative estimates, not sourced from any authority — they exist so
the 3x recommendation threshold has something concrete to test against.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators.qualification_model import (
    AccountQualification,
    QualificationConfidence,
    QualificationState,
)

STRUCTURING_PATHS_VERSION = "1.0.0"

# Representative implementation-cost estimate for routing an imported
# crew member's pay through an MU employer-of-record / production SPV
# (payroll setup, immigration/work-permit administration, arm's-length
# invoicing documentation). NOT sourced from any quote or authority —
# a labeled placeholder pending real vendor pricing.
REPRESENTATIVE_ROUTING_SETUP_COST_USD = 8_000.0


class PathStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    EXECUTED = "executed"
    REALIZED = "realized"


@dataclass
class StructuringPath:
    path_id: str
    account_code: str
    description: str
    mechanism: str
    current_amount_usd: float          # what qualifies today under this structure (0 while unstructured)
    structured_amount_usd: float       # what qualifies once the mechanism is executed
    implementation_cost_usd: float
    complexity: str                    # "LOW" | "MEDIUM" | "HIGH"
    confidence: QualificationConfidence
    required_documents: tuple[str, ...]
    precedent: Optional[str] = None
    status: PathStatus = PathStatus.PROPOSED
    evidence_bound: bool = False
    upside_incentive_usd: float = 0.0  # (structured_amount - current_amount) * rate, set at derive time


def derive_structuring_paths(
    register: list[AccountQualification],
    rate: float,
) -> list[StructuringPath]:
    """
    Build a StructuringPath for every STRUCTURING_OPPORTUNITY account in
    the register. One path per account — Little Utopia currently produces
    three (21-00 DP, 23-00 Sound, 42-00 Stunts), all sharing the same
    MU employer-of-record / SPV routing mechanism and precedent.
    """
    paths: list[StructuringPath] = []
    for a in register:
        if a.state != QualificationState.STRUCTURING_OPPORTUNITY:
            continue
        upside_usd = round(a.amount_usd * rate, 2)
        paths.append(StructuringPath(
            path_id=f"SP-{a.account_code}",
            account_code=a.account_code,
            description=a.description,
            mechanism=a.structuring_mechanism or "Route through MU employer-of-record or production SPV.",
            current_amount_usd=0.0,
            structured_amount_usd=a.amount_usd,
            implementation_cost_usd=REPRESENTATIVE_ROUTING_SETUP_COST_USD,
            complexity="MEDIUM",
            confidence=a.confidence,
            required_documents=(
                "MU employer-of-record or SPV routing agreement",
                "Arm's-length invoicing documentation",
            ),
            precedent="33-00 Frogsquad SPV routing (executed precedent on this production)",
            upside_incentive_usd=upside_usd,
        ))
    return paths


def is_recommended(
    path: StructuringPath,
    upside_to_cost_ratio: float = 3.0,
) -> bool:
    """
    A path is recommended when its net upside clears the implementation
    cost by at least `upside_to_cost_ratio` AND confidence is at least
    MEDIUM. Below threshold, the path remains visible (available, not
    recommended) — never hidden.
    """
    if path.confidence not in (QualificationConfidence.MEDIUM, QualificationConfidence.HIGH):
        return False
    if path.implementation_cost_usd <= 0:
        return path.upside_incentive_usd > 0
    ratio = path.upside_incentive_usd / path.implementation_cost_usd
    return ratio >= upside_to_cost_ratio
