"""
The SERVED contract of POST /projects/{id}/evaluation/begin.

A fresh evaluation and a reused one (EVALUATION_REUSED) must be indistinguishable to a
client except for ``status``: same engine version, fingerprint, discovery metadata, counts,
ranking and bounded first page. evaluate_project() already returns identical engine version,
fingerprint, counts, ranking and first page on both paths (they come from the same
_summarize_evaluation read-back); the ONE difference was the three ``discovery_*`` metadata
keys, which only the fresh path (that had just run discovery) attached.

Discovery is a pure, side-effect-free function of the project's economic inputs, so this
module derives the metadata the SAME way for both paths -- by running the same economic
discovery pass over the same inputs -- instead of trusting whichever path happened to have it
in hand. tests/test_served_contract_bounded.py pins that these values equal what a fresh
evaluation itself produces.

Deliberately not in canonical_evaluation.py: that module is a member of the fingerprint's
pricing-source digest, and this closeout must not invalidate persisted generations.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import derive_production_requirements
from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS
from app.services.canonical_project_economics import build_project_economic_inputs

DISCOVERY_KEYS = ("discovery_examined", "discovery_rejected", "discovery_capability_only")
_SERVED_STATUSES = ("EVALUATION_COMPLETE", "EVALUATION_REUSED")


async def discovery_metadata(session: AsyncSession, project_id) -> dict | None:
    """(examined, rejected, capability-only) counts of the economic discovery pass -- the SAME
    call, arguments and inputs evaluate_project() uses to generate candidates. None when the
    project cannot currently be evaluated (no inputs)."""
    econ = await build_project_economic_inputs(session, project_id, read_only=True)
    if not econ.ok:
        return None
    inputs = econ.inputs
    discovery = discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type=inputs.production_type,
        qpe_usd=inputs.gross_budget_usd,
        home_code=inputs.jurisdiction_code,
        evidenced_facts=(inputs.evidenced_program_facts | _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS),
        amount_facts=inputs.amount_facts,
        fx_context=inputs.fx_context,
    )
    return {
        "discovery_examined": len(discovery.examinations),
        "discovery_rejected": discovery.metrics.get("rejected_count", 0),
        "discovery_capability_only": discovery.metrics.get("capability_only_count", 0),
    }


async def apply_evaluation_contract(session: AsyncSession, project_id, result: dict) -> dict:
    """Give a fresh or reused evaluate_project() result the one served shape. Only ``status``
    may differ between the two; everything else, including discovery metadata, is derived
    identically."""
    if result.get("status") not in _SERVED_STATUSES:
        return result
    metadata = await discovery_metadata(session, project_id)
    if metadata is not None:
        result = {**result, **metadata}
    return result
