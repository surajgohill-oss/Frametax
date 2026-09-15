"""Read-only four-project runtime capture for the Codex optimizer audit."""
from __future__ import annotations

import asyncio
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures


PROJECTS = {
    "The Little Utopia": "fa5cade5-0669-4816-bfe6-72146f8d3bae",
    "F#K Valentine's Day": "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    "Bad Hombres": "4355ae88-a636-4c18-af60-ad73b2646124",
    "Lips Like Sugar": "ab10b319-978e-44d3-9331-af2a5f2cccc2",
}


async def main() -> None:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        for name, project_id in PROJECTS.items():
            evaluation = await evaluate_project(session, project_id)
            # The audit is read-only. Reused evaluations have no writes; a
            # future fresh evaluation is explicitly rolled back before exit.
            await session.flush()
            view = await build_production_and_structures(session, project_id)
            structures = view.get("structures", {})
            allocated = structures.get("allocated_structures", {})
            entries = allocated.get("structures", [])
            ranking = allocated.get("ranking", [])
            baseline = next((e for e in entries if e.get("is_baseline")), None)
            winner = next((e for e in ranking if e.get("rank") == 1), None)
            summary = {
                "project": name,
                "project_id": project_id,
                "evaluation_status": evaluation.get("status"),
                "engine_version": evaluation.get("engine_version"),
                "fingerprint": entries[0].get("input_fingerprint") if entries else None,
                "candidate_count": len(entries),
                "priced_count": sum(bool(e.get("is_fully_priced")) for e in entries),
                "rejected_count": sum(not bool(e.get("is_fully_priced")) for e in entries),
                "structure_types": sorted({str(e.get("structure_type")) for e in entries}),
                "treaty_count": sum(e.get("structure_type") == "treaty_coproduction" for e in entries),
                "component_count": sum(e.get("structure_type") == "component_relocation" for e in entries),
                "stack_count": sum(e.get("structure_type") == "multi_program" for e in entries),
                "winner": winner,
                "baseline": baseline,
                "leading_conditional_structure": allocated.get("leading_conditional_structure"),
            }
            print(json.dumps(summary, sort_keys=True, default=str))
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(main())
