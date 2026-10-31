"""Read-only provenance for the isolated four-anchor copies: per-project content hashes, source versus copy.

    python scripts/isolated_copy_manifest.py generate   # writes docs/validation/ISOLATED_COPY_MANIFEST_20261029.json
    python scripts/isolated_copy_manifest.py verify     # recomputes every registered database against the manifest; exit 1 on any difference

Every connection is opened ``default_transaction_read_only=on``; nothing is evaluated or written. The hash method is one documented function (`_digest`):
sha256 over the sorted JSON of selected, id-free columns (jurisdiction / talent ids differ between schema generations, so they are never hashed)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.evaluation_authorization import FOUR_ANCHORS, MANIFEST_PATH  # noqa: E402

DSN = "host=localhost user=frametax password=frametax connect_timeout=5 dbname={}"
OPT = "-c default_transaction_read_only=on -c statement_timeout=100000"
SOURCE = "frametax2_claude_optimizer_acceptance_20260919"
COPIES = (("frametax2_four_closeout_20261029", "evaluation_copy", "isolated copy of the four anchors (facts, people, budget, requirements, newest retained generation) made from the read-only source"),
          ("frametax2_four_closeout_base_20261029", "evaluation_copy_base", "template clone of the closeout copy, used only for the engine 1.130.0 A/B"))
TABLES = {
    "facts": "select fact_key, value::text, value_type, source_type, review_status from project_facts where project_id = %s",
    "people": "select role, is_confirmed, notes from project_people where project_id = %s",
    "budget_lines": ("select l.description, l.atl_btl, l.spend_category, l.amount_raw::text, l.amount_usd::text from budget_line_items l "
                     "join budget_documents d on d.id = l.budget_document_id where d.project_id = %s"),
    "location_requirements": "select category_key, location_key, description from project_location_requirements where project_id = %s",
    "documents": "select filename, file_type, total_budget_raw::text from budget_documents where project_id = %s",
}


def _digest(rows) -> list:
    blob = json.dumps(sorted([["∅" if v is None else str(v) for v in r] for r in rows]), separators=(",", ":"))
    return [len(rows), hashlib.sha256(blob.encode()).hexdigest()[:16]]


def snapshot(database: str) -> dict:
    conn = psycopg.connect(DSN.format(database), options=OPT)
    try:
        assert conn.execute("show default_transaction_read_only").fetchone()[0] == "on"
        out = {}
        for pid in FOUR_ANCHORS:
            title = conn.execute("select title from projects where id = %s", (pid,)).fetchone()
            if title is None:
                continue
            out[pid] = {"title": title[0], **{name: _digest(conn.execute(sql, (pid,)).fetchall()) for name, sql in TABLES.items()}}
        present = conn.execute("select count(*) from projects").fetchone()[0]
        return {"projects": out, "project_count": present}
    finally:
        conn.close()


def generate() -> dict:
    source = snapshot(SOURCE)
    databases = [{"database": SOURCE, "role": "read_only_source", "evaluation_allowed": False, "project_count": source["project_count"],
                  "note": "the acceptance database; holds other real productions; never evaluated or written by the closeout", "projects": source["projects"]}]
    for name, role, note in COPIES:
        snap = snapshot(name)
        differs = {pid: [k for k in TABLES if snap["projects"][pid][k] != source["projects"][pid][k]] for pid in FOUR_ANCHORS}
        databases.append({"database": name, "role": role, "evaluation_allowed": True, "source_database": SOURCE, "project_count": snap["project_count"], "note": note,
                          "differs_from_source": {p: d for p, d in differs.items() if d}, "projects": snap["projects"]})
    manifest = {"manifest": "ISOLATED_COPY_MANIFEST_20261029", "anchors": {pid: {"code": c, "title": t} for pid, (c, t) in FOUR_ANCHORS.items()},
                "hash_method": "sha256 of sorted JSON rows over the id-free columns in scripts/isolated_copy_manifest.py TABLES (first 16 hex)", "databases": databases}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def verify() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    bad = 0
    for entry in manifest["databases"]:
        snap = snapshot(entry["database"])
        diffs = [(pid, k) for pid, p in entry["projects"].items() for k in TABLES if snap["projects"].get(pid, {}).get(k) != p[k]]
        titles = [pid for pid, p in entry["projects"].items() if snap["projects"].get(pid, {}).get("title") != p["title"]]
        print(f"{entry['database']}: role={entry['role']} projects={snap['project_count']} (manifest {entry['project_count']}) differing={diffs} title_mismatch={titles}")
        bad += len(diffs) + len(titles) + (snap["project_count"] != entry["project_count"])
    return 1 if bad else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "generate":
        m = generate()
        for d in m["databases"]:
            print(d["database"], d["role"], "differs_from_source=", d.get("differs_from_source"))
    else:
        sys.exit(verify())
