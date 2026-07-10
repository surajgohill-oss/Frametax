"""
production_constraint_engine.py

Phase 7 closeout, Part E: the Production Constraint Engine.

A producer arrives with decisions already made — "the director is fixed",
"we must shoot in Georgia", "the budget ceiling is $40M" — that no
existing engine models as an input. Opportunity Discovery and the
Production Structure Composer both explore the full space of legally
supportable structures; nothing today lets a caller say "don't bother
proposing structures that violate this fixed decision."

This module:

- performs no optimization and alters no optimizer math. It is a pure
  filter/annotation layer over ProductionStructureCandidate objects
  production_structure_composer.py already built — every candidate it
  is given is returned exactly as-is (never mutated, never re-priced),
  just partitioned into compatible / incompatible with an explicit
  reason per incompatible candidate.
- never invents a violation. A constraint whose kind this module has no
  deterministic check for a given candidate's information is treated as
  UNVERIFIABLE, not as satisfied and not as violated — the same
  "unknown is never silently collapsed" discipline the rest of this
  codebase enforces.
- becomes an optimizer input only in the sense of narrowing which
  already-composed candidates a caller carries forward — it does not
  reach into optimization_engine.py or production_structure_composer.py
  at all.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from app.calculators.optimization_engine import RiskCase
from app.calculators.production_structure_composer import ProductionStructureCandidate

PRODUCTION_CONSTRAINT_ENGINE_VERSION = "1.0.0"


class ConstraintKind(str, enum.Enum):
    DIRECTOR_FIXED = "director_fixed"
    WRITER_FIXED = "writer_fixed"
    LEAD_FIXED = "lead_fixed"
    LOCATION_FIXED = "location_fixed"
    SCHEDULE_FIXED = "schedule_fixed"
    BUDGET_CEILING = "budget_ceiling"
    TRAVEL_CEILING = "travel_ceiling"
    REQUIRED_VENDOR = "required_vendor"
    REQUIRED_DISTRIBUTOR = "required_distributor"
    REQUIRED_PRODUCTION_COMPANY = "required_production_company"
    JURISDICTION_REQUIRED = "jurisdiction_required"
    COMPLETION_DEADLINE = "completion_deadline"
    UNION_REQUIRED = "union_required"
    LOCAL_HIRE_REQUIRED = "local_hire_required"


# Constraint kinds this engine can actually check against a
# ProductionStructureCandidate's existing fields today. Everything else
# is a real, storable constraint (the optimizer/producer still needs to
# know about it) but this module honestly reports UNVERIFIABLE rather
# than inventing a check it can't perform — e.g. LOCAL_HIRE_REQUIRED
# needs payroll-routing detail no candidate object carries.
_CHECKABLE_AGAINST_CANDIDATE: frozenset[ConstraintKind] = frozenset({
    ConstraintKind.JURISDICTION_REQUIRED,
    ConstraintKind.BUDGET_CEILING,
})


@dataclass(frozen=True)
class ProductionConstraint:
    constraint_id: str
    kind: ConstraintKind
    value: str
    hard: bool = True  # hard = must not be violated; soft = a stated preference
    notes: str = ""


@dataclass
class ProductionConstraintSet:
    constraints: tuple[ProductionConstraint, ...]

    def of_kind(self, kind: ConstraintKind) -> tuple[ProductionConstraint, ...]:
        return tuple(c for c in self.constraints if c.kind == kind)


def build_constraint_set(constraints: Optional[list[ProductionConstraint]] = None) -> ProductionConstraintSet:
    return ProductionConstraintSet(
        constraints=tuple(sorted(constraints or [], key=lambda c: c.constraint_id)),
    )


@dataclass(frozen=True)
class ConstraintCheckResult:
    candidate_id: str
    compatible: bool
    violated_constraint_ids: tuple[str, ...]
    unverifiable_constraint_ids: tuple[str, ...]
    reasons: dict[str, str]


def _check_jurisdiction_required(constraint: ProductionConstraint, candidate: ProductionStructureCandidate) -> Optional[bool]:
    """True (satisfied) / False (violated). Never None here — this kind
    is always checkable from participating_jurisdictions."""
    return constraint.value.upper() in candidate.participating_jurisdictions


def _check_budget_ceiling(constraint: ProductionConstraint, candidate: ProductionStructureCandidate) -> Optional[bool]:
    """None (unverifiable) when the candidate isn't fully priced — an
    unpriced candidate's cost is unknown, not zero and not infinite."""
    if not candidate.is_fully_priced or candidate.cases is None:
        return None
    try:
        ceiling = float(constraint.value)
    except (TypeError, ValueError):
        return None
    npc = candidate.npc(RiskCase.RISK_ADJUSTED)
    return npc is not None and npc <= ceiling


_CHECKERS = {
    ConstraintKind.JURISDICTION_REQUIRED: _check_jurisdiction_required,
    ConstraintKind.BUDGET_CEILING: _check_budget_ceiling,
}


def check_candidate_against_constraints(
    candidate: ProductionStructureCandidate,
    constraint_set: ProductionConstraintSet,
) -> ConstraintCheckResult:
    violated: list[str] = []
    unverifiable: list[str] = []
    reasons: dict[str, str] = {}

    for constraint in sorted(constraint_set.constraints, key=lambda c: c.constraint_id):
        if constraint.kind not in _CHECKABLE_AGAINST_CANDIDATE:
            unverifiable.append(constraint.constraint_id)
            reasons[constraint.constraint_id] = (
                f"{constraint.kind.value} cannot be checked against a ProductionStructureCandidate "
                "with the information this engine has today."
            )
            continue
        checker = _CHECKERS[constraint.kind]
        outcome = checker(constraint, candidate)
        if outcome is None:
            unverifiable.append(constraint.constraint_id)
            reasons[constraint.constraint_id] = f"{constraint.kind.value} could not be evaluated for '{candidate.candidate_id}' (insufficient pricing/data)."
        elif outcome is False and constraint.hard:
            violated.append(constraint.constraint_id)
            reasons[constraint.constraint_id] = f"Violates hard constraint {constraint.kind.value}='{constraint.value}'."
        elif outcome is False:
            reasons[constraint.constraint_id] = f"Does not satisfy soft constraint {constraint.kind.value}='{constraint.value}' (non-blocking)."

    return ConstraintCheckResult(
        candidate_id=candidate.candidate_id,
        compatible=not violated,
        violated_constraint_ids=tuple(sorted(violated)),
        unverifiable_constraint_ids=tuple(sorted(unverifiable)),
        reasons=reasons,
    )


def filter_candidates_by_constraints(
    candidates: list[ProductionStructureCandidate],
    constraint_set: ProductionConstraintSet,
) -> tuple[list[ProductionStructureCandidate], list[ConstraintCheckResult]]:
    """
    Returns (compatible_candidates, all_check_results) — candidates are
    returned in their original order, unmutated, unpruned in the
    composer's own sense (this is a caller-side filter, not a
    replacement for eliminate_duplicates/prune_dominated). Every
    candidate gets a ConstraintCheckResult, even a compatible one, so a
    caller can see unverifiable constraints even when nothing was
    violated.
    """
    results = [check_candidate_against_constraints(c, constraint_set) for c in candidates]
    compatible = [c for c, r in zip(candidates, results) if r.compatible]
    return compatible, results
