"""Company Globe portfolio payload (2026-10-08): ONE aggregate read for every active project.

Company Globe used to fetch each project's full served state (~34 MB, 8-30 s apiece, one request per project). This
module is the smallest extension to the existing canonical served owner (canonical_production_view): it reads that
owner once per project/generation, keeps a compact structure snapshot keyed by (engine_version, input fingerprint) on the
project row, and serves every active project's leading structure in a single response. It never evaluates (no
evaluate_project, no FX refresh) and never re-derives a structure: the leader is the served view's own
canonical_selected_structure_id / leading_conditional_structure, and a producer's "Set as Leading" choice wins.

Leading precedence: explicit user selection -> canonical selected (rank 1) -> canonical leading-conditional ->
baseline jurisdiction only when no valid evaluated structure exists.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services.leading_selection import reconcile_selection, selection_status

SNAPSHOT_SCHEMA = 2

# Fields the Globe surfaces read: identity, topology (principal / participants / component and co-production legs) and
# the hover economics already computed by the served view. Nothing here is recomputed.
_STRUCTURE_FIELDS = (
    "structure_id", "label", "structure_type", "classification", "primary_jurisdiction", "anchor_jurisdiction",
    "participants", "treaty_slug", "is_baseline", "is_fully_priced", "economic_identity", "scenario_category",
    "production_fit_status", "npc_with_adjustments_usd", "npc_conservative_usd", "selected_incentive_usd",
    "confirmed_incentive_floor_usd", "maximum_supported_incentive_usd", "confirmed_npc_usd", "potential_npc_usd",
    "potential_upside_usd", "ceiling_status", "economics_certainty",
)


def compact_structure(entry: dict) -> dict:
    out = {k: entry.get(k) for k in _STRUCTURE_FIELDS}
    out["component_allocations"] = [
        {"component": c.get("component"), "jurisdiction_code": c.get("jurisdiction_code"), "allocated_usd": c.get("allocated_usd")}
        for c in (entry.get("component_allocations") or [])
    ]
    out["coproduction_partners"] = [
        {"jurisdiction_code": p.get("jurisdiction_code") or p.get("code")}
        for p in (entry.get("coproduction_partners") or [])
    ]
    return out


def _selectable_structures(allocated: dict) -> list[dict]:
    """Every structure a producer can pick as leading: the served ranked page PLUS the optimizer candidate pool the
    Workspace Optimizer cards are drawn from (e.g. a three-jurisdiction hybrid is only in the latter). First occurrence
    wins, so the ranked page's entry is the one kept."""
    seen: dict[str, dict] = {}
    for pool in ("structures", "optimizer_candidates", "optimizer_opportunities_requiring_facts"):
        for entry in allocated.get(pool) or []:
            sid = entry.get("structure_id")
            if sid and sid not in seen:
                seen[sid] = compact_structure(entry)
    return list(seen.values())


def build_snapshot(view: dict, *, engine_version: str, fingerprint: str) -> dict:
    allocated = view["structures"]["allocated_structures"]
    production = view["production"]
    baseline = next((s for s in allocated["structures"] if s.get("is_baseline") or s.get("structure_type") == "single_country"), None)
    conditional = allocated.get("leading_conditional_structure") or {}
    return {
        "schema": SNAPSHOT_SCHEMA,
        "engine_version": engine_version,
        "fingerprint": fingerprint,
        "canonical_structure_id": allocated.get("canonical_selected_structure_id"),
        "conditional_structure_id": conditional.get("structure_id"),
        "baseline_jurisdiction": production.get("jurisdiction_code"),
        "home_code": (baseline or {}).get("primary_jurisdiction")
            or (allocated.get("jurisdiction_accounting") or {}).get("home_jurisdiction"),
        "gross_budget_usd": production.get("gross_budget_usd"),
        "structures": _selectable_structures(allocated),
    }


def snapshot_is_current(snapshot: dict | None, *, engine_version: str, fingerprint: str) -> bool:
    return bool(
        snapshot and snapshot.get("schema") == SNAPSHOT_SCHEMA
        and snapshot.get("engine_version") == engine_version and snapshot.get("fingerprint") == fingerprint
    )


def resolve_leader(snapshot: dict, *, user_structure_id: str | None, user_selected: bool) -> tuple[dict | None, str]:
    """(structure, source). Pure: the precedence contract."""
    by_id = {s["structure_id"]: s for s in snapshot.get("structures", [])}
    if user_selected and user_structure_id and user_structure_id in by_id:
        return by_id[user_structure_id], "user"
    for key, source in (("canonical_structure_id", "canonical"), ("conditional_structure_id", "canonical_conditional")):
        sid = snapshot.get(key)
        if sid and sid in by_id:
            return by_id[sid], source
    return None, "baseline"


async def served_fingerprints(session: AsyncSession, project_ids) -> dict[uuid.UUID, str]:
    """project_id -> current input fingerprint, for projects whose CURRENT-engine generation exists at that project's
    freshly recomputed fingerprint -- the served predicate every current-evaluation reader uses. Presence is read from
    the one-row-per-generation summary (unique on project/fingerprint/engine, tiny) instead of scanning the
    structure-result table, which holds hundreds of thousands of rows per production (that scan alone cost 14-18 s)."""
    from app.models.production import EvaluationGenerationSummary
    from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint

    rows = (await session.execute(
        select(EvaluationGenerationSummary.project_id, EvaluationGenerationSummary.input_fingerprint)
        .where(
            EvaluationGenerationSummary.project_id.in_(list(project_ids)),
            EvaluationGenerationSummary.engine_version == ENGINE_VERSION,
        )
    )).all()
    persisted: dict[uuid.UUID, set[str]] = {}
    for pid, fp in rows:
        persisted.setdefault(pid, set()).add(fp)
    served: dict[uuid.UUID, str] = {}
    for pid, fps in persisted.items():
        fingerprint = await current_generation_fingerprint(session, pid)
        if fingerprint is not None and fingerprint in fps:
            served[pid] = fingerprint
    return served


async def build_portfolio_globe(session: AsyncSession, organization_id) -> dict[str, Any]:
    from app.api.v1.projects import _is_producer_visible
    from app.services.canonical_evaluation import ENGINE_VERSION
    from app.services.canonical_production_view import build_production_and_structures

    projects = [
        p for p in (await session.execute(
            select(Project).where(Project.organization_id == organization_id).order_by(Project.title)
        )).scalars().all() if _is_producer_visible(p.title)
    ]
    served = await served_fingerprints(session, [p.id for p in projects])
    rows: list[dict] = []
    rebuilt = 0
    for project in projects:
        fingerprint = served.get(project.id)
        lifecycle = (project.lifecycle or "EVALUATION").upper()
        if fingerprint is None or lifecycle == "ARCHIVED":
            continue  # Submitted (no served generation) and Archived are not active
        snapshot = project.portfolio_globe_snapshot
        if not snapshot_is_current(snapshot, engine_version=ENGINE_VERSION, fingerprint=fingerprint):
            view = await build_production_and_structures(session, project.id)
            if view.get("status") != "OK":
                continue
            snapshot = build_snapshot(view, engine_version=ENGINE_VERSION, fingerprint=fingerprint)
            project.portfolio_globe_snapshot = snapshot
            await session.commit()
            rebuilt += 1
        await reconcile_selection(session, project, engine_version=ENGINE_VERSION, fingerprint=fingerprint)
        status = await selection_status(session, project)
        structure, source = resolve_leader(
            snapshot,
            user_structure_id=str(project.leading_structure_id) if project.leading_structure_id else None,
            user_selected=status["user_selected"] and not status["unavailable"],
        )
        rows.append({
            "project_id": str(project.id),
            "title": project.title,
            "lifecycle": lifecycle,
            "is_served_production": True,
            "gross_budget_usd": snapshot.get("gross_budget_usd") if project.total_budget_usd is None else float(project.total_budget_usd),
            "baseline_jurisdiction": snapshot.get("baseline_jurisdiction"),
            "home_code": snapshot.get("home_code"),
            "leading_structure_id": str(project.leading_structure_id) if project.leading_structure_id else None,
            "leading": {
                "source": source,
                "user_selected": source == "user",
                # the choice is unavailable when it no longer exists after a regeneration, or is not in this generation
                "unavailable": status["user_selected"] and source != "user",
                "structure": structure,
            },
        })
    return {
        "projects": rows,
        "excluded_not_active": len(projects) - len(rows),
        "snapshots_rebuilt": rebuilt,
    }
