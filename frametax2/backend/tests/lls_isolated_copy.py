"""An ISOLATED COPY of the saved Lips Like Sugar inputs on the throw-away test database, for pricing questions about LLS under the CURRENT engine without reading or writing the real project:
the 46 budget lines and the saved project facts are copied from a JSON export taken read-only from the acceptance database (tests/data/lls_saved_inputs.json). Nothing here reaches the real
project; the copy lives inside ``isolated_session`` and is rolled back."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import select

from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.project import Project
from app.models.project_fact import ProjectFact
from tests.isolated_records import create_synthetic_project

DATA = Path(__file__).parent / "data" / "lls_saved_inputs.json"
_FIELDS = ("department", "atl_btl", "spend_category", "is_labor", "is_resident_labor", "is_fixed", "amount_raw", "amount_normalized", "currency_code", "amount_usd",
           "cash_amount_usd", "accounting_amount_usd", "compensation_type", "deferred_amount_usd", "equity_amount_usd", "in_kind_amount_usd",
           "is_qualifying_spend_candidate", "qualifying_amount_usd", "source_subaccounts")


def saved_inputs() -> dict:
    return json.loads(DATA.read_text())


async def create_lls_copy(session, *, facts: bool = True, overrides: dict | None = None) -> str:
    """Create the copy; ``overrides`` maps a budget line description to a dict of field overrides (a deliberate what-if, never a saved input)."""
    data = saved_inputs()
    lines = tuple((r["description"].split(" ", 1)[0], r["description"].split(" ", 1)[1], r["spend_category"] or "miscellaneous", r["atl_btl"], float(r["amount_usd"])) for r in data["lines"])
    pid = await create_synthetic_project(session, lines=lines, home_code="US-CA", title_suffix=" LLS-COPY")
    project = await session.get(Project, uuid.UUID(pid))
    project.format = data["project"].get("format") or project.format
    doc = (await session.execute(select(BudgetDocument).where(BudgetDocument.project_id == project.id))).scalar_one()
    created = (await session.execute(select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc.id))).scalars().all()
    by_desc: dict[str, list] = {}
    for row in created:
        by_desc.setdefault(row.description, []).append(row)
    for src in data["lines"]:
        target = by_desc[src["description"]].pop(0)
        for key in _FIELDS:
            if key in src and src[key] is not None:
                setattr(target, key, src[key])
        for key, value in ((overrides or {}).get(src["description"]) or {}).items():
            setattr(target, key, value)
    if facts:
        for key, value, source_type in data["facts"]:
            session.add(ProjectFact(id=uuid.uuid4(), project_id=project.id, fact_key=key, value=value, value_type="string", source_type=source_type, review_status="pending"))
    await session.flush()
    return pid
