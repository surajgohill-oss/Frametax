"""Builds docs/validation/JURISDICTION_LOCATION_CAPABILITY_CENSUS_CLAUDE.csv (+ .summary.json) -- the frozen 114 x 10 census.

Read-only and offline (no evaluation, no database, no network): every cell comes from the one canonical owner,
`jurisdiction_comparison.location_capability_cells`, whose data (app/data/jurisdiction_location_capability.py) was derived by
backend/scripts/location_census_derivation from the structured official/authoritative datasets named in its SOURCES records.

    python scripts/build_location_capability_census.py [out.csv]
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calculators import jurisdiction_comparison as jc  # noqa: E402
from app.data.jurisdiction_location_capability import (  # noqa: E402
    GENERIC_UNRESOLVED_ATTEMPT, LOCATION_CENSUS_CATEGORIES, MISSING_PROPOSITION,
)

COLUMNS = [
    "jurisdiction_code", "jurisdiction_name", "category", "terminal_status", "component_capabilities", "canonical_capability_tokens",
    "evidence_proposition", "source_title", "source_url_or_identifier", "publisher", "source_version_or_checked_date", "evidence_tier",
    "derivation_method", "sources_attempted_if_unresolved", "runtime_consumed", "notes",
]
RUNTIME = {
    "SUPPORTED": "YES: capability provision (satisfies a hard requirement; soft match disclosed)",
    "NOT_SUPPORTED": "YES: affirmative denial (Not Suitable only for a hard requirement; soft mismatch disclosed, never an exclusion)",
    "UNRESOLVED_NEUTRAL": "NEUTRAL: hard requirement -> Conditional (<TOKEN>_NOT_ASSESSABLE); soft -> disclosed, never a mismatch",
}


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for code in jc.location_census_jurisdictions():
        profile = jc.ALL_PROFILES.get(code)
        name = profile.jurisdiction_name if profile else "United States (national)"
        for category, cell in jc.location_capability_cells(code).items():
            unresolved = cell.status == "UNRESOLVED_NEUTRAL"
            comps = ";".join(f"{tok.removesuffix('_environments').removesuffix('_climate')}={st}" for tok, st in cell.components) \
                if len(cell.components) > 1 else f"{category}={cell.status}"
            tokens = ";".join(dict.fromkeys([cell.token, *(t for t, _ in cell.components)]))
            rows.append({
                "jurisdiction_code": code, "jurisdiction_name": name, "category": category, "terminal_status": cell.terminal_status,
                "component_capabilities": comps, "canonical_capability_tokens": tokens,
                "evidence_proposition": cell.proposition, "source_title": cell.source_title, "source_url_or_identifier": cell.source_url,
                "publisher": cell.publisher, "source_version_or_checked_date": cell.source_version, "evidence_tier": cell.evidence_tier,
                "derivation_method": cell.derivation_method,
                "sources_attempted_if_unresolved": (" | ".join([*cell.sources_attempted, GENERIC_UNRESOLVED_ATTEMPT]) + " || missing proposition: "
                                                    + MISSING_PROPOSITION) if unresolved else "",
                "runtime_consumed": RUNTIME[cell.status],
                "notes": f"source_ids={','.join(cell.source_ids)}" if cell.source_ids else "",
            })
    return rows


def summarize(rows: list[dict]) -> dict:
    by_status = Counter(r["terminal_status"] for r in rows)
    unresolved = [r for r in rows if r["terminal_status"] == "AUTHORITY_UNRESOLVED_NEUTRAL"]
    per_j: dict[str, list[str]] = defaultdict(list)
    for r in unresolved:
        per_j[r["jurisdiction_code"]].append(r["category"])
    return {
        "rows": len(rows), "terminal_status": dict(by_status),
        "terminal_status_by_category": {c: dict(Counter(r["terminal_status"] for r in rows if r["category"] == c)) for c in LOCATION_CENSUS_CATEGORIES},
        "evidence_tier": dict(Counter(r["evidence_tier"] or "(unresolved)" for r in rows)),
        "desert_supported": sorted(r["jurisdiction_code"] for r in rows if r["category"] == "desert_arid" and r["terminal_status"] == "AUTHORITY_VERIFIED_SUPPORTED"),
        "desert_not_supported": sorted(r["jurisdiction_code"] for r in rows if r["category"] == "desert_arid" and r["terminal_status"] == "AUTHORITY_VERIFIED_NOT_SUPPORTED"),
        "desert_unresolved": sorted(r["jurisdiction_code"] for r in rows if r["category"] == "desert_arid" and r["terminal_status"] == "AUTHORITY_UNRESOLVED_NEUTRAL"),
        "unresolved_by_category": dict(Counter(r["category"] for r in unresolved)),
        "unresolved_by_jurisdiction": {k: sorted(v) for k, v in sorted(per_j.items())},
        "generic_unknown_cells": 0,
    }


def main(out: Path) -> dict:
    rows = build_rows()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    summary = summarize(rows)
    out.with_suffix(".summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    return summary


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "docs/validation/JURISDICTION_LOCATION_CAPABILITY_CENSUS_CLAUDE.csv"
    s = main(target)
    print(json.dumps({k: s[k] for k in ("rows", "terminal_status", "evidence_tier", "unresolved_by_category")}, indent=1))
