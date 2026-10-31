"""Who may be evaluated, and where: the four-anchor allow-list and the registered isolated copies.

Operator evaluations (``bounded_regeneration.regenerate_project`` with ``require_isolated_database=True``) and, when
``CINEGLOBE_EVALUATION_ALLOWLIST=four-anchor-copies`` is set, the producer-input Save worker (``evaluation_worker``) must pass
``assert_authorized_evaluation`` before any evaluation starts:

* the project is one of the four anchors (The Little Utopia, Lips Like Sugar, F#K Valentine's Day, Bad Hombres), by canonical UUID;
* the connected database is registered in ``docs/validation/ISOLATED_COPY_MANIFEST_20261029.json`` as an evaluation copy (a registered read-only
  source or an unregistered database is refused), so every evaluated copy traces to a named source with per-project content hashes;
* the database holds exactly the four anchors (no further real production is present to be evaluated or touched) and each anchor's stored title equals
  the manifest title for its UUID (a UUID is the identity; a display name is only checked, never trusted to select a project).

``scripts/isolated_copy_manifest.py verify`` additionally recomputes the per-project content hashes against the manifest. Not a fingerprint-hashed module."""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from sqlalchemy import text

ENV_FLAG = "CINEGLOBE_EVALUATION_ALLOWLIST"
ENV_VALUE = "four-anchor-copies"
MANIFEST_PATH = Path(__file__).resolve().parents[3] / "docs" / "validation" / "ISOLATED_COPY_MANIFEST_20261029.json"

#: canonical UUID -> (short code, title). The UUID is the identity.
FOUR_ANCHORS = {
    "fa5cade5-0669-4816-bfe6-72146f8d3bae": ("LU", "The Little Utopia"),
    "ab10b319-978e-44d3-9331-af2a5f2cccc2": ("LLS", "Lips Like Sugar"),
    "6c6f1c13-2d49-4bbc-bafb-2a12efa93112": ("FVD", "F#K Valentine's Day"),
    "4355ae88-a636-4c18-af60-ad73b2646124": ("BH", "Bad Hombres"),
}


class EvaluationNotAuthorized(RuntimeError):
    """The project or the database is outside the four-anchor allow-list or the registered isolated copies."""


def load_manifest(path: Path | None = None) -> dict:
    return json.loads((path or MANIFEST_PATH).read_text())


def restriction_enabled() -> bool:
    return os.environ.get(ENV_FLAG, "") == ENV_VALUE


def check_static(project_id, database: str, manifest: dict | None = None) -> None:
    """The checks that need no database access: the UUID is an anchor and the database is a registered evaluation copy."""
    pid = str(project_id).lower()
    if pid not in FOUR_ANCHORS:
        raise EvaluationNotAuthorized(f"project {pid} is not one of the four authorized anchors {sorted(FOUR_ANCHORS)}")
    manifest = manifest or load_manifest()
    entry = next((d for d in manifest["databases"] if d["database"] == database), None)
    if entry is None:
        raise EvaluationNotAuthorized(f"database {database!r} is not registered in the isolated-copy manifest")
    if not entry.get("evaluation_allowed"):
        raise EvaluationNotAuthorized(f"database {database!r} is registered as {entry.get('role')!r}, which is not evaluable")
    if pid not in entry["projects"]:
        raise EvaluationNotAuthorized(f"project {pid} is not registered for database {database!r}")


async def assert_authorized_evaluation(session_or_conn, project_id, manifest: dict | None = None) -> str:
    """Returns the database name when the evaluation is authorized; raises EvaluationNotAuthorized otherwise. Read-only."""
    database = (await session_or_conn.execute(text("select current_database()"))).scalar()
    manifest = manifest or load_manifest()
    check_static(project_id, database, manifest)
    rows = (await session_or_conn.execute(text("select id::text, title from projects"))).all()
    present = {r[0].lower(): r[1] for r in rows}
    extra = sorted(set(present) - set(FOUR_ANCHORS))
    if extra:
        raise EvaluationNotAuthorized(f"database {database!r} holds {len(extra)} project(s) outside the four anchors (first: {extra[0]}); it is not an isolated four-anchor copy")
    for pid, (_, title) in FOUR_ANCHORS.items():
        if pid in present and present[pid] != title:
            raise EvaluationNotAuthorized(f"project {pid} is titled {present[pid]!r} in {database!r}, the manifest says {title!r}")
    if str(project_id).lower() not in present:
        raise EvaluationNotAuthorized(f"project {project_id} is not present in {database!r}")
    return database


def parse_project_id(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
