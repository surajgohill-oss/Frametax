"""PRODUCTION TYPE ELECTION (2026-10-13): the one canonical write/read of the producer's stated production type.

``Project.format`` is the stored fact; ``canonical_project_economics._FORMAT_TO_PRODUCTION_TYPE`` maps it to the production_type vocabulary the statutory RateRules are scoped by, so a stated type
changes WHICH programs can price (e.g. most US state programs are scoped to feature films), and it is part of the evaluation fingerprint. This module only validates, writes and describes it: it does
not evaluate (the caller runs the shared single-flight evaluation, like every other producer-input save).

Unknown is not a type: a project with no stated format is priced as a feature film because the engine needs a type, and the served view says so instead of presenting the default as the producer's answer."""
from __future__ import annotations

from app.services.canonical_project_economics import _FORMAT_TO_PRODUCTION_TYPE

#: (stored format, label) in display order. The stored values are exactly the keys the engine maps; nothing else is accepted.
PRODUCTION_FORMAT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("feature", "Feature film"),
    ("series", "TV series"),
    ("documentary", "Documentary"),
    ("animation", "Animation"),
)
DEFAULT_PRODUCTION_TYPE = "feature_film"


def validate_format(value) -> str | None:
    """None clears the stated type (Unknown). Anything not in the engine's own mapping is refused: no free-form type can reach eligibility."""
    if value is None:
        return None
    if not isinstance(value, str) or value.strip().lower() not in _FORMAT_TO_PRODUCTION_TYPE:
        raise ValueError(f"production type must be one of {', '.join(k for k, _ in PRODUCTION_FORMAT_OPTIONS)} or null (not stated)")
    return value.strip().lower()


def production_type_view(stored_format: str | None) -> dict:
    stated = (stored_format or "").strip().lower() in _FORMAT_TO_PRODUCTION_TYPE
    effective = _FORMAT_TO_PRODUCTION_TYPE.get((stored_format or "").strip().lower(), DEFAULT_PRODUCTION_TYPE)
    return {
        "state": "STATED" if stated else "NOT_STATED",
        "format": (stored_format or "").strip().lower() if stated else None,
        "effective_production_type": effective,
        "options": [{"format": f, "label": label, "production_type": _FORMAT_TO_PRODUCTION_TYPE[f]} for f, label in PRODUCTION_FORMAT_OPTIONS],
        "note": (
            f"Priced as {effective.replace('_', ' ')}: programs are matched to this type, so a different type changes which programs are eligible."
            if stated else
            "No production type is stated, so the engine prices it as a feature film (the engine needs a type); state the type to have eligibility matched to it."
        ),
    }


async def write_production_type(session, project, value) -> dict:
    """Validate and persist the stated type on the project (null clears it). Returns the served view. Does not evaluate and does not commit."""
    project.format = validate_format(value)
    await session.flush()
    return production_type_view(project.format)
