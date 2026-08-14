"""
optimizer_handoff.py

Script Analyzer SA-1, Part J — the adapter, and nothing more.

Maps a generic `CanonicalProductionState` into the `ProductionOptimizerInput`
contract the existing optimizer consumes. This module deliberately contains
NO economics: it does not price, allocate, rank, or evaluate an incentive. It
translates and it refuses.

"Refuses" is the important half. If the state is not READY_FOR_OPTIMIZER the
adapter returns the blockers rather than a degraded input — a partially-known
production must never be silently priced as though it were fully specified.

Explicitly untouched by this phase: production discovery, structure
composition, allocation, production normalization, incentive evaluation,
NPC and ranking. Those algorithms are reused exactly as they are.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from app.services.canonical_production_state import (
    READY_FOR_OPTIMIZER,
    CanonicalProductionState,
)

CONTRACT_NAME = "ProductionOptimizerInput"
CONTRACT_VERSION = "sa1-1.0.0"


@dataclass
class ProductionOptimizerInput:
    """The canonical contract handed to the existing optimizer."""

    contract_name: str
    contract_version: str

    project_id: str
    state_version: str
    input_fingerprint: str
    as_of: str

    script_version_id: str | None
    screenplay_id: str | None
    budget_document_ids: list[str]

    gross_production_cost_usd: float | None
    budget_lines: list[dict] = field(default_factory=list)

    scripted_locations: list[dict] = field(default_factory=list)
    production_requirements: list[dict] = field(default_factory=list)
    assumptions: list[dict] = field(default_factory=list)

    shoot_days: int | None = None
    base_jurisdiction: str | None = None

    unknowns: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    provisional: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class HandoffResult:
    accepted: bool
    reason: str
    optimizer_input: ProductionOptimizerInput | None = None
    blockers: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "blockers": list(self.blockers),
            "optimizer_input": self.optimizer_input.as_dict() if self.optimizer_input else None,
        }


def _assumption(state: CanonicalProductionState, key: str):
    for a in state.assumptions:
        if a.get("key") == key and a.get("value") is not None:
            return a.get("value")
    return None


def build_optimizer_input(state: CanonicalProductionState) -> HandoffResult:
    """Translate a canonical state into the optimizer contract, or refuse."""
    if state.readiness != READY_FOR_OPTIMIZER:
        return HandoffResult(
            accepted=False,
            reason=(
                "CanonicalProductionState is not READY_FOR_OPTIMIZER. Required "
                "inputs are missing and are deliberately not defaulted — a "
                "partially-known production is not priced as though complete."
            ),
            blockers=list(state.blockers) or ["Incomplete inputs."],
        )

    shoot_days_raw = _assumption(state, "intended_shoot_days")
    try:
        shoot_days = int(shoot_days_raw) if shoot_days_raw is not None else None
    except (TypeError, ValueError):
        shoot_days = None

    oi = ProductionOptimizerInput(
        contract_name=CONTRACT_NAME,
        contract_version=CONTRACT_VERSION,
        project_id=state.project_id,
        state_version=state.state_version,
        input_fingerprint=state.input_fingerprint,
        as_of=state.as_of,
        script_version_id=state.script_document_version_id,
        screenplay_id=state.screenplay_id,
        budget_document_ids=list(state.budget_document_ids),
        gross_production_cost_usd=state.gross_budget_usd,
        budget_lines=list(state.budget_lines),
        scripted_locations=list(state.scripted_locations),
        production_requirements=list(state.production_requirements),
        assumptions=list(state.assumptions),
        shoot_days=shoot_days,
        base_jurisdiction=_assumption(state, "base_jurisdiction"),
        unknowns=list(state.unknowns),
        blockers=list(state.blockers),
        # Any remaining unknown keeps the run PROVISIONAL. The canonical rule
        # is that provisional output is never labelled actual.
        provisional=bool(state.unknowns or state.blockers),
    )
    return HandoffResult(
        accepted=True,
        reason="Canonical state satisfies the minimum optimizer input contract.",
        optimizer_input=oi,
    )
