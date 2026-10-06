"""Builds docs/validation/JURISDICTION_LOCATION_CAPABILITY_CENSUS_CLAUDE.csv -- the fixed 114 x 10 location-capability census.

Read-only and offline (no evaluation, no database, no network): the cells come from the one canonical owner,
`jurisdiction_comparison.location_capability_cells`. For UNKNOWN cells the retained free-text notes (jurisdiction profiles and
global-inventory program records) are scanned for a keyword lead; a lead is only a pointer for a later, separately authorised
census -- it never turns a cell into SUPPORTED.

    python scripts/build_location_capability_census.py [out.csv]
"""
from __future__ import annotations

import csv
import dataclasses
import importlib
import json
import pkgutil
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calculators import jurisdiction_comparison as jc  # noqa: E402
from app.data.jurisdiction_location_capability import LOCATION_CENSUS_CATEGORIES  # noqa: E402

COLUMNS = [
    "jurisdiction_code", "jurisdiction_name", "category", "status", "repository_classification", "canonical_capability_token",
    "evidence_proposition", "source_title", "source_url_or_identifier", "publisher", "checked_or_effective_date",
    "evidence_tier", "runtime_consumed", "notes",
]
LEAD = {
    "island_tropical": r"island|archipelago|tropical|caribbean",
    "jungle_rainforest": r"rainforest|jungle|amazon",
    "desert_arid": r"desert|arid|sahara|gobi|outback|negev|empty quarter",
    "mountains_alpine": r"mountain|alpine|alps|rocky|andes|himalaya|tatr|pyrenees",
    "snow_arctic": r"snow|arctic|glacier|lapland|aurora",
    "urban_major_city": r"urban|metropolis|skyline|modern (?:city|architecture)|city locations",
    "small_town_suburban": r"small town|village",
    "rural_countryside": r"countryside|farmland|steppe|rural landscape",
    "forest_woodland": r"forest|woodland",
    "historic_old_world": r"historic|medieval|old town|old world|baroque|castle|colonial|old cit",
}


def _inventory_notes() -> dict[str, list[tuple[str, str]]]:
    import app.data as data

    out: dict[str, list[tuple[str, str]]] = {}
    seen: set[tuple[str, str]] = set()
    for m in pkgutil.iter_modules(data.__path__):
        if not m.name.startswith("global_inventory"):
            continue
        mod = importlib.import_module(f"app.data.{m.name}")
        for v in vars(mod).values():
            if isinstance(v, (list, tuple)):
                for e in v:
                    if dataclasses.is_dataclass(e) and hasattr(e, "jurisdiction_code") and hasattr(e, "source_url") and e.notes:
                        code = e.jurisdiction_code
                        if code == "AE":
                            code = "AE-DXB" if "dubai" in (e.source_url or "").lower() else "AE-AD"
                        if (code, e.notes) not in seen:
                            seen.add((code, e.notes))
                            out.setdefault(code, []).append((e.source_url or "", e.notes))
    return out


def build_rows() -> list[dict]:
    inv = _inventory_notes()
    rows: list[dict] = []
    for code in jc.location_census_jurisdictions():
        profile = jc.ALL_PROFILES.get(code)
        name = profile.jurisdiction_name if profile else "United States (national)"
        notes_pool = [("profile:" + (profile.authority_url_hint or "") if profile else "", profile.notes if profile else "")] + inv.get(code, [])
        for category, cell in jc.location_capability_cells(code).items():
            lead = ""
            if cell.status == "UNKNOWN":
                for src, text in notes_pool:
                    for sent in re.split(r"(?<=[.;])\s+", text or ""):
                        if re.search(LEAD[category], sent, re.I):
                            lead = f"LEAD_ONLY (not evidence; uncited / unverified free text, source hint {src or 'none'}): {sent.strip()[:200]}"
                            break
                    if lead:
                        break
            rows.append({
                "jurisdiction_code": code, "jurisdiction_name": name, "category": category, "status": cell.status,
                "repository_classification": "CANONICAL_DATA_MISSING" if cell.status == "UNKNOWN" else "EXISTS_BUT_DISCONNECTED",
                "canonical_capability_token": cell.token, "evidence_proposition": cell.proposition,
                "source_title": cell.source_title, "source_url_or_identifier": cell.source_url or cell.record_ref,
                "publisher": cell.publisher, "checked_or_effective_date": cell.checked_or_effective_date or "not retained",
                "evidence_tier": cell.evidence_tier,
                "runtime_consumed": {"SUPPORTED": "YES (capability provision)", "NOT_SUPPORTED": "YES (mismatch only for a hard requirement)",
                                     "UNKNOWN": "NEUTRAL (never a mismatch)"}[cell.status],
                "notes": (f"record_ref={cell.record_ref}" if cell.record_ref else "") + (lead if lead else ""),
            })
    return rows


def main(out: Path) -> dict:
    rows = build_rows()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    by_status = Counter(r["status"] for r in rows)
    residual = Counter(r["category"] for r in rows if r["status"] == "UNKNOWN")
    return {"rows": len(rows), "by_status": dict(by_status), "residual_unknown_by_category": dict(residual),
            "desert_supported": sorted(r["jurisdiction_code"] for r in rows if r["category"] == "desert_arid" and r["status"] == "SUPPORTED")}


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "docs/validation/JURISDICTION_LOCATION_CAPABILITY_CENSUS_CLAUDE.csv"
    print(json.dumps(main(target), indent=1))
