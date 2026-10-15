"""Persistence and served view of the explicit production locations (NA-RECONCILIATION-23).

One ProjectFact row (`shoot_locations`, JSON, USER_OVERRIDE) holds the project's explicit locations - retained schedule locations and locations the producer selected for a scenario - each with its
jurisdiction, optional city / county / days and per-attribute provenance. The pure resolver (`app.calculators.locality`) reduces them to numeric `locality:*` facts that flow through the existing
amount-fact path and therefore the evaluation fingerprint. Saving never evaluates. A location with no jurisdiction cannot be stored (locality is never inferred from the jurisdiction alone), and
free-text `ProjectLocationRequirement.production_location` values are listed as UNRESOLVED text, never parsed into a place.
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators import locality as loc
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.project_fact import ProjectFact

FACT_KEY = "shoot_locations"
MAX_LOCATIONS = 100


def entries_from_rows(rows) -> list[loc.LocationEntry]:
    for row in rows:
        if getattr(row, "fact_key", None) == FACT_KEY and row.value:
            try:
                data = json.loads(row.value)
            except (TypeError, ValueError):
                return []
            out = []
            for raw in data if isinstance(data, list) else []:
                try:
                    out.append(loc.validate_entry(raw))
                except ValueError:
                    continue                                   # a corrupted stored entry is dropped, never repaired
            return out
    return []


async def write_shoot_locations(session: AsyncSession, project_id, locations: list[dict]) -> dict:
    """Replace the project's explicit locations (an empty list clears them). ValueError with the reason on any invalid entry; nothing is written then."""
    if len(locations) > MAX_LOCATIONS:
        raise ValueError(f"at most {MAX_LOCATIONS} locations")
    entries = [loc.validate_entry(raw) for raw in locations]
    ids = [e.id for e in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("location ids must be unique")
    payload = [{"id": e.id, "label": e.label, "jurisdiction_code": e.jurisdiction_code, "role": e.role, "city": e.city, "county": e.county, "days": e.days,
                "attributes": dict(e.attributes), "evidence": {k: dict(v) for k, v in e.evidence.items()}} for e in sorted(entries, key=lambda x: x.id)]
    value = json.dumps(payload, sort_keys=True) if payload else None
    row = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == FACT_KEY))).scalar_one_or_none()
    if row is not None:
        row.value, row.value_type = value, "json"
        row.source_type = ProjectFactSourceType.USER_OVERRIDE.value
        row.review_status = ReviewStatus.APPROVED.value
    elif value is not None:
        session.add(ProjectFact(id=uuid.uuid4(), project_id=project_id, fact_key=FACT_KEY, value=value, value_type="json",
                                source_type=ProjectFactSourceType.USER_OVERRIDE.value, review_status=ReviewStatus.APPROVED.value))
    await session.flush()
    return {"locations": len(entries)}


async def locations_view(session: AsyncSession, project_id) -> dict:
    """Read-only: the locations with their resolved classifications, provenance and exactly what is still unresolved; never evaluates."""
    from app.models.project_location_requirement import ProjectLocationRequirement
    rows = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == FACT_KEY))).scalars().all()
    entries = entries_from_rows(rows)
    text = (await session.execute(select(ProjectLocationRequirement.production_location).where(
        ProjectLocationRequirement.project_id == project_id, ProjectLocationRequirement.production_location.is_not(None)))).scalars().all()
    return {
        "locations": loc.describe(entries),
        "unresolved_text_locations": sorted({t for t in text if t and t.strip()}),
        "datasets": [{k: v for k, v in loc.MO_COUNTY_DATASET.items()}],
        "open_classifications": dict(loc.OPEN_CLASSIFICATIONS),
        "note": ("Locality is established only from explicit locations. A free-text production location is not parsed into a place. A classification the repository holds no dataset for stays Unknown unless the "
                 "producer asserts it per location with its source; the exact source still required is named."),
    }
