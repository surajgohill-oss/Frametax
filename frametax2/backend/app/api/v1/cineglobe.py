"""
cineglobe.py

Phase 8A API surface for the current (Phase 4-8) CineGlobe engines.
Deliberately bypasses the legacy stack `optimization.py` still calls
(structuring_advisor / mediterranean_comparison / generate_structure_
scenarios / rank_production_structures) — every route here calls the
current opportunity_discovery / production_structure_composer /
production_recommendation_engine / legal_engine directly, or the
ui_presentation.py adapters over their output.

No business logic lives in this file. Every route:
  1. reads the single cached LittleUtopiaState (app.demo.little_utopia_state),
  2. optionally reshapes via dataclasses.asdict() / ui_presentation.py, and
  3. returns.

No route computes a number, applies a threshold, or makes a
qualification/legal determination — those all happened already, inside
the engines, before this file ever runs.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.calculators.optimization_engine import RiskCase
from app.calculators.production_constraint_engine import (
    ConstraintKind,
    ProductionConstraint,
    build_constraint_set,
    filter_candidates_by_constraints,
)
from app.calculators.production_recommendation_engine import RecommendationCategory
from app.calculators.production_scenario_engine import ProductionScenario, ScenarioKind, run_scenario
from app.calculators.qualification_model import is_authoritative_citation
from app.calculators.ui_presentation import (
    attribute_fact_to_display,
    case_dict_to_display,
    evidence_chain_to_display,
    group_recommendations_by_category,
)
from app.demo.little_utopia_state import (
    ANSWERABLE_FACTS,
    apply_fact_answers,
    current_fact_answers,
    get_state,
)

router = APIRouter(prefix="/cineglobe", tags=["cineglobe"])


# ── Production facts (Engine Integration Phase 1, Seam B) ───────────────────
# Question Engine answers become engine inputs: an answered fact feeds
# qualification derivation / structure composition and resolves the
# corresponding missing-input question. No route below computes anything —
# apply_fact_answers() invalidates the cached state and the engines
# recompute on the next get_state().

@router.get("/facts")
async def get_facts() -> dict[str, Any]:
    return {
        "answers": current_fact_answers(),
        "answerable": {
            key: {
                "type": spec["type"].__name__,
                "answers_question": spec["answers_question"],
                "description": spec["description"],
            }
            for key, spec in ANSWERABLE_FACTS.items()
        },
    }


class FactAnswers(BaseModel):
    answers: dict[str, Any]


@router.post("/facts")
async def post_facts(body: FactAnswers) -> dict[str, Any]:
    try:
        apply_fact_answers(body.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    s = get_state()
    conservative = next(
        (c for c in s.composition.candidates if c.is_fully_priced), None,
    )
    return {
        "answers": current_fact_answers(),
        "open_questions": len(s.package.missing_inputs),
        "conservative_qpe_usd": (
            conservative.cases[RiskCase.CONSERVATIVE].qpe_usd if conservative else None
        ),
        "candidate_ids": [c.candidate_id for c in s.composition.candidates],
    }


# ── Screen 1: Production ─────────────────────────────────────────────────────

@router.get("/production")
async def get_production() -> dict[str, Any]:
    s = get_state()
    rr = s.rate_resolution
    return {
        "production_id": s.production_id,
        "production_name": s.production_name,
        "jurisdiction_code": s.jurisdiction_code,
        "gross_budget_usd": s.gross_budget_usd,
        "rate": s.rate,
        # Permanent rate-authority rules: the rate's full statutory
        # provenance, condition evaluations, guaranteed floor, and any
        # budget-vs-database conflict (reported, never absorbed).
        "rate_resolution": (
            {
                "modeled_rate": rr.modeled_rate,
                "floor_rate": rr.floor_rate,
                "is_band_ceiling": rr.is_band_ceiling,
                "tier_id": rr.tier_id,
                "basis": rr.basis,
                "conditions": [asdict(c) for c in rr.conditions_evaluated],
                "unverified_claims": [asdict(u) for u in rr.unverified_claims],
                "conflicts": [asdict(c) for c in rr.conflicts],
            }
            if rr is not None else None
        ),
        "rate_warnings": list(s.rate_warnings),
        # Real-budget reconciliation: the source PDF's own stated Grand
        # Total (the controlling gross budget) vs. the sum of its 44
        # parsed leaf accounts, and the accepted source-document rounding
        # variance between them — never hidden, never balanced away.
        "budget_reconciliation": {
            "authoritative_gross_usd": s.budget_authoritative_gross_usd,
            "leaf_account_sum_usd": s.budget_leaf_account_sum_usd,
            "variance_usd": s.budget_reconciliation_variance_usd,
            "note": s.budget_reconciliation_note,
        },
        "as_of_date": "2026-07-10",
    }


# ── Screen 2: Package Intelligence (Budget / Script / Questions) ────────────

@router.get("/package")
async def get_package() -> dict[str, Any]:
    s = get_state()
    pkg = s.package
    return {
        "production_id": pkg.production_id,
        "confidence": pkg.confidence.value,
        "is_ready_for_downstream_engines": pkg.is_ready_for_downstream_engines,
        "register": [
            {
                "account_code": a.account_code,
                "description": a.description,
                "amount_usd": a.amount_usd,
                "state": a.state.value,
                "confidence": a.confidence.value,
                "authority_basis": a.authority_basis.value,
                "reason": a.reason,
                # Part 4 A-F: why a line is grey (null unless state is grey).
                # The UI's Grey-Area panel renders this as the "why".
                "grey_reason": a.grey_reason.value if a.grey_reason else None,
                "financial_impact_usd": a.financial_impact_usd,
                "structuring_mechanism": a.structuring_mechanism,
                "resolving_evidence": a.resolving_evidence,
                "incentive_upside_usd": a.incentive_upside_usd,
            }
            for a in s.register
        ],
        "budget": {
            "known": pkg.budget.known,
            "filename": pkg.budget.filename,
            "currency_code": pkg.budget.currency_code,
            "total_budget_usd": pkg.budget.total_budget_usd,
            "line_item_count": pkg.budget.line_item_count,
            "atl_total_usd": pkg.budget.atl_total_usd,
            "btl_total_usd": pkg.budget.btl_total_usd,
            "post_total_usd": pkg.budget.post_total_usd,
            "other_total_usd": pkg.budget.other_total_usd,
            "labor_usd": pkg.budget.labor_usd,
            "non_labor_usd": pkg.budget.non_labor_usd,
            "totals_by_spend_category_usd": pkg.budget.totals_by_spend_category_usd,
            "opportunity_hints": [asdict(h) for h in pkg.budget.opportunity_hints],
        },
        "script": {
            "known": pkg.script.known,
            "filename": pkg.script.filename,
            "page_count": pkg.script.page_count,
            "word_count": pkg.script.word_count,
            "locations_mentioned": list(pkg.script.locations_mentioned),
            "character_names": list(pkg.script.character_names),
            "attributes": {k: attribute_fact_to_display(v) for k, v in pkg.script.attributes.items()},
        },
        "package_people_count": len(pkg.package.all_people),
        "package_entities_count": len(pkg.package.all_entities),
        "location_count": len(pkg.location.locations),
        "missing_inputs": [
            {
                "identifier": m.identifier,
                "question": m.question,
                "why_it_matters": m.why_it_matters,
                "downstream_engines": [e.value for e in m.downstream_engines],
                "optimizer_value": m.optimizer_value.value,
                "blocking": m.blocking,
                "discovery_hooks": [asdict(h) for h in m.discovery_hooks],
            }
            for m in pkg.missing_inputs
        ],
    }


# ── Screen 3: Recommendations (Financial / Structural / Creative / Legal) ──

@router.get("/recommendations")
async def get_recommendations() -> dict[str, Any]:
    s = get_state()
    recs = s.recommendations.recommendations
    grouped = group_recommendations_by_category(recs)
    legal_gated = [r for r in recs if r.requires_counsel_approval]

    def _rec_dict(r) -> dict[str, Any]:
        d = asdict(r)
        d["category"] = r.category.value
        d["confidence"] = r.confidence.value
        d["status"] = r.status.value
        return d

    return {
        "total": len(recs),
        "by_category": {
            "financial": [_rec_dict(r) for r in grouped[RecommendationCategory.FINANCIAL.value]],
            "structural": [_rec_dict(r) for r in grouped[RecommendationCategory.STRUCTURAL.value]],
            "creative": [_rec_dict(r) for r in grouped[RecommendationCategory.CREATIVE.value]],
            "required_input": [_rec_dict(r) for r in grouped[RecommendationCategory.REQUIRED_INPUT.value]],
        },
        "legal": [_rec_dict(r) for r in legal_gated],
    }


# ── Screen 4: Scenarios (Structures / Risk cases / Optimizer outputs) ──────

@router.get("/structures")
async def get_structures() -> dict[str, Any]:
    """
    NOTE on risk_adjusted_npc_usd: the scenario ranker's ORDER is still
    computed on risk-adjusted NPC (global_scenario_ranker.py, untouched —
    that ranking math is not in scope here). But the PRIMARY figure this
    endpoint surfaces per candidate is conservative_npc_usd — the NPC
    implied by the verified/conservative QPE only. Risk-adjusted NPC
    blends in optimistic upside that has not been established as verified
    QPE, so it is kept as a secondary field (risk_adjusted_npc_usd, still
    present, just not primary) until the underlying grey areas/structuring
    paths are actually resolved.
    """
    s = get_state()
    ranked_structures_by_id = {st.structure_id: st for st in s.scenario_ranking.structures}

    def _candidate_dict(c) -> dict[str, Any]:
        return {
            "candidate_id": c.candidate_id,
            "label": c.label,
            "participating_jurisdictions": list(c.participating_jurisdictions),
            "priceable_pct": c.priceable_pct,
            "unknown_pct": c.unknown_pct,
            "is_fully_priced": c.is_fully_priced,
            "cases": case_dict_to_display(c.cases),
            "informational_upside_usd": c.informational_upside_usd,
            "constraints": [asdict(x) for x in c.constraints],
            "included_opportunity_ids": list(c.included_opportunity_ids),
        }

    def _conservative_npc(structure_id: str) -> float | None:
        st = ranked_structures_by_id.get(structure_id)
        if st is None or not st.cases:
            return None
        return st.cases[RiskCase.CONSERVATIVE].net_production_cost_usd

    return {
        "candidates": [_candidate_dict(c) for c in s.composition.candidates],
        "pruned": s.composition.pruned,
        "ranking": [
            {
                "rank": r.rank,
                "structure_id": r.structure_id,
                "label": r.label,
                "is_priceable": r.is_priceable,
                "conservative_npc_usd": _conservative_npc(r.structure_id),
                "secondary_analysis": {
                    "risk_adjusted_npc_usd": r.risk_adjusted_npc_usd,
                    "note": "Blends optimistic upside (unresolved grey areas / structuring "
                            "paths) into NPC. Informational only until those items are "
                            "actually resolved — conservative_npc_usd is the primary figure.",
                },
            }
            for r in s.scenario_ranking.ranks
        ],
    }


class ScenarioRequest(BaseModel):
    kind: str
    target_jurisdiction: str | None = None


@router.post("/scenarios")
async def post_scenario(body: ScenarioRequest) -> dict[str, Any]:
    s = get_state()
    try:
        kind = ScenarioKind(body.kind)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown scenario kind '{body.kind}'.")

    scenario = ProductionScenario(
        scenario_id=f"API-{kind.value}", kind=kind,
        description=f"{kind.value} (via API)", target_jurisdiction=body.target_jurisdiction,
    )
    result = run_scenario(
        scenario, s.collection, graph=s.graph, register=s.register,
        gross_budget_usd=s.gross_budget_usd, rate=s.rate, grey_areas=s.grey_areas_baseline,
    )
    return {
        "scenario_id": scenario.scenario_id,
        "kind": kind.value,
        "notes": result.notes,
        "baseline_candidate_id": result.baseline_candidate_id,
        "scenario_candidate_id": result.scenario_candidate_id,
        "baseline_risk_adjusted_npc_usd": result.baseline_risk_adjusted_npc_usd,
        "scenario_risk_adjusted_npc_usd": result.scenario_risk_adjusted_npc_usd,
        "delta_usd": result.delta_usd,
        "relevant_structuring_opportunities": [
            {"opportunity_id": o.opportunity_id, "description": o.description, "subtype": o.subtype}
            for o in result.relevant_structuring_opportunities
        ],
    }


@router.get("/constraints/check")
async def check_constraints() -> dict[str, Any]:
    """Demonstrates production_constraint_engine against the real
    composed candidates — jurisdiction_required is the only kind
    checkable without a producer-supplied budget ceiling, so that's what
    this read-only demo route exercises."""
    s = get_state()
    constraints = build_constraint_set([
        ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value=s.jurisdiction_code),
    ])
    compatible, results = filter_candidates_by_constraints(s.composition.candidates, constraints)
    return {
        "compatible_candidate_ids": [c.candidate_id for c in compatible],
        "results": [
            {
                "candidate_id": r.candidate_id,
                "compatible": r.compatible,
                "violated_constraint_ids": list(r.violated_constraint_ids),
                "unverifiable_constraint_ids": list(r.unverifiable_constraint_ids),
            }
            for r in results
        ],
    }


# ── Screen 5: Evidence (Authority / Grey Areas / Evidence Trace) ───────────

@router.get("/legal")
async def get_legal() -> dict[str, Any]:
    s = get_state()

    def _grey_area_dict(g) -> dict[str, Any]:
        return {
            "item_id": g.item_id,
            "account_codes": list(g.account_codes),
            "amount_usd": g.amount_usd,
            "jurisdiction_code": g.jurisdiction_code,
            "authority_to_ask": g.authority_to_ask,
            "resolving_evidence": g.resolving_evidence,
            "status": g.status.value,
            "ruling_citation": g.ruling_citation,
            # Provenance flag: False when the resolution's citation is
            # mock/demo research output (never statutory evidence).
            "citation_is_authoritative": is_authoritative_citation(g.ruling_citation),
            "off_budget": g.off_budget,
            "graph_rule_id": g.graph_rule_id,
        }

    evidence_trace: list[dict[str, Any]] = []
    authority_scores: dict[str, Any] = {}
    if s.legal_commit is not None and s.legal_commit.score is not None:
        chain = s.legal_engine.evidence_graph.trace_rule(s.legal_commit.committed_id)
        evidence_trace = evidence_chain_to_display(chain)
        authority_scores[s.legal_commit.committed_id] = {
            "composite": s.legal_commit.score.composite,
            "confidence": s.legal_commit.score.confidence.value,
            "breakdown": asdict(s.legal_commit.score.breakdown),
        }

    return {
        # RESEARCH VIEW ONLY: everything below reflects the Legal
        # Engine's mock-connector research cycle. It never feeds the
        # primary production register/QPE served by /package and
        # /structures — those are computed from the raw statutory
        # register exclusively.
        "is_research_view": True,
        "grey_areas_current": [_grey_area_dict(g) for g in s.legal_rerun.grey_areas_used],
        "questions_detected": len(s.legal_cycle.questions),
        "questions_auto_executed": list(s.legal_cycle.executed_task_ids),
        "questions_awaiting_verification": list(s.legal_cycle.awaiting_verification),
        "committed_rule_id": s.legal_commit.committed_id if s.legal_commit else None,
        "authority_scores": authority_scores,
        "evidence_trace": evidence_trace,
        "connector_source_label": "MockConnector (no live retrieval — see legal_authority_acquisition.py)",
        "conservative_npc_before_usd": (
            s.legal_rerun_before.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
        ),
        "conservative_npc_after_usd": (
            s.legal_rerun.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
        ),
    }
