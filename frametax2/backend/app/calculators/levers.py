"""
levers.py

Phase 4 of the CineGlobe Production Intelligence Graph: the Lever
abstraction that generalizes StructuringPath (structuring_paths.py)
across every optimization category the architecture document defines —
structuring, treaty, stacking, reinvestment, normalization, timing.

Minimal safe approach: StructuringPath is NOT modified and
optimization_engine.py is NOT modified. build_risk_cases() continues to
consume StructuringPath objects exactly as before — Little Utopia's
Conservative/Base/Optimistic/Risk-Adjusted figures are unaffected by
this module's existence. Lever is a superset shape that StructuringPath
converts to and from; today only LeverType.STRUCTURING has real
producing logic (via structuring_path_to_lever /
derive_levers_from_structuring_paths). TREATY, STACKING, REINVESTMENT,
NORMALIZATION, and TIMING exist as valid, testable values with no
discovery logic yet — that is future work (Discovery Engine, per the
Production Intelligence Graph architecture), not this phase.

LeverStatus is intentionally the same lifecycle as StructuringPath's
PathStatus (PROPOSED -> APPROVED -> EXECUTED -> REALIZED) — reusing it
rather than defining a parallel enum keeps the two objects' lifecycles
identical by construction, not by convention.

No LLM calls. No optimizer behavior change.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators.qualification_model import AccountQualification, AuthorityBasis, QualificationConfidence
from app.calculators.structuring_paths import PathStatus, StructuringPath, derive_structuring_paths

LEVERS_VERSION = "1.0.0"

# Same threshold value as structuring_paths.is_recommended's default —
# kept self-contained (no cross-import) so this module carries no new
# dependency on optimization_engine.py, matching the minimal-safe-change
# instruction for this phase.
RECOMMEND_UPSIDE_TO_COST_RATIO = 3.0

# LeverStatus IS StructuringPath's PathStatus — not a parallel enum.
# A Lever converted from a StructuringPath and the path it came from
# always agree on lifecycle stage; there is no second source of truth
# to drift out of sync.
LeverStatus = PathStatus


class LeverType(str, enum.Enum):
    STRUCTURING = "structuring"
    TREATY = "treaty"
    STACKING = "stacking"
    REINVESTMENT = "reinvestment"
    NORMALIZATION = "normalization"
    TIMING = "timing"


@dataclass
class Lever:
    """
    The generalized optimization-opportunity object. Every dimension
    StructuringPath already carries is preserved; a few are added for
    categories StructuringPath was never meant to cover (jurisdiction,
    authority basis, graph evidence hooks — mirroring the same
    graph_rule_id / graph_absence_id pattern GreyAreaItem uses, so a
    Lever's provenance is checkable the same way a grey area's is).
    """
    lever_id: str
    lever_type: LeverType
    affected_accounts: tuple[str, ...]
    description: str
    mechanism: str
    current_value_usd: float
    achievable_value_usd: float
    implementation_cost_usd: float
    confidence: QualificationConfidence
    complexity: str  # "LOW" | "MEDIUM" | "HIGH"
    required_documents: tuple[str, ...]
    jurisdiction_code: str
    precedent: Optional[str] = None
    authority_basis: Optional[AuthorityBasis] = None
    graph_rule_id: Optional[str] = None
    graph_absence_id: Optional[str] = None
    status: LeverStatus = LeverStatus.PROPOSED
    evidence_bound: bool = False
    upside_incentive_usd: float = 0.0

    @property
    def upside_value_usd(self) -> float:
        """achievable - current, independent of rate — the raw QPE/NPC
        delta this lever represents, before any incentive-rate math."""
        return self.achievable_value_usd - self.current_value_usd


def is_lever_recommended(
    lever: Lever,
    upside_to_cost_ratio: float = RECOMMEND_UPSIDE_TO_COST_RATIO,
) -> bool:
    """
    Identical threshold rule to structuring_paths.is_recommended():
    recommended iff confidence >= MEDIUM and upside/cost >=
    upside_to_cost_ratio. A Lever below threshold remains visible
    (available, not recommended) — never hidden.
    """
    if lever.confidence not in (QualificationConfidence.MEDIUM, QualificationConfidence.HIGH):
        return False
    if lever.implementation_cost_usd <= 0:
        return lever.upside_incentive_usd > 0
    ratio = lever.upside_incentive_usd / lever.implementation_cost_usd
    return ratio >= upside_to_cost_ratio


# ── Conversions: StructuringPath <-> Lever ──────────────────────────────────

def structuring_path_to_lever(path: StructuringPath, jurisdiction_code: str = "MU") -> Lever:
    """
    StructuringPath -> Lever, lossless in both directions (see
    lever_to_structuring_path). StructuringPath carries no
    jurisdiction_code field today (the codebase is Little-Utopia/MU-
    scoped so far) — jurisdiction_code defaults to "MU" and is an
    explicit parameter so callers in other jurisdictions aren't silently
    mislabeled once this generalizes.
    """
    return Lever(
        lever_id=path.path_id,
        lever_type=LeverType.STRUCTURING,
        affected_accounts=(path.account_code,),
        description=path.description,
        mechanism=path.mechanism,
        current_value_usd=path.current_amount_usd,
        achievable_value_usd=path.structured_amount_usd,
        implementation_cost_usd=path.implementation_cost_usd,
        confidence=path.confidence,
        complexity=path.complexity,
        required_documents=path.required_documents,
        jurisdiction_code=jurisdiction_code,
        precedent=path.precedent,
        authority_basis=AuthorityBasis.STRUCTURING_DEPENDENT,
        status=path.status,
        evidence_bound=path.evidence_bound,
        upside_incentive_usd=path.upside_incentive_usd,
    )


def lever_to_structuring_path(lever: Lever) -> StructuringPath:
    """
    Lever -> StructuringPath. Only valid for LeverType.STRUCTURING with
    exactly one affected account — StructuringPath's shape (a single
    account_code field) cannot represent a multi-account or non-
    structuring Lever. Raises ValueError otherwise.
    """
    if lever.lever_type != LeverType.STRUCTURING:
        raise ValueError(
            f"Lever '{lever.lever_id}' is a {lever.lever_type.value} lever — "
            "only STRUCTURING levers convert to StructuringPath."
        )
    if len(lever.affected_accounts) != 1:
        raise ValueError(
            f"Lever '{lever.lever_id}' affects {len(lever.affected_accounts)} accounts — "
            "StructuringPath requires exactly one."
        )
    return StructuringPath(
        path_id=lever.lever_id,
        account_code=lever.affected_accounts[0],
        description=lever.description,
        mechanism=lever.mechanism,
        current_amount_usd=lever.current_value_usd,
        structured_amount_usd=lever.achievable_value_usd,
        implementation_cost_usd=lever.implementation_cost_usd,
        complexity=lever.complexity,
        confidence=lever.confidence,
        required_documents=lever.required_documents,
        precedent=lever.precedent,
        status=lever.status,
        evidence_bound=lever.evidence_bound,
        upside_incentive_usd=lever.upside_incentive_usd,
    )


def derive_levers_from_structuring_paths(
    paths: list[StructuringPath],
    jurisdiction_code: str = "MU",
) -> list[Lever]:
    """Convenience batch conversion — one Lever per StructuringPath."""
    return [structuring_path_to_lever(p, jurisdiction_code) for p in paths]


def derive_levers(
    register: list[AccountQualification],
    rate: float,
    jurisdiction_code: str = "MU",
) -> list[Lever]:
    """
    End-to-end convenience: register -> StructuringPath (existing,
    unchanged logic in structuring_paths.derive_structuring_paths) ->
    Lever. Produces today's only populated LeverType (STRUCTURING);
    TREATY/STACKING/REINVESTMENT/NORMALIZATION/TIMING levers have no
    discovery source yet and are not emitted by this function.
    """
    paths = derive_structuring_paths(register, rate=rate)
    return derive_levers_from_structuring_paths(paths, jurisdiction_code=jurisdiction_code)
