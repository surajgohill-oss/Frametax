"""Regenerate the NA fact inventory artifacts (docs/validation/NA_FACT_INVENTORY_20261014.{json,csv}). Read-only: walks the canonical registries, opens no database and evaluates nothing."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = Path(__file__).resolve().parents[2] / "docs" / "validation"
STEM = "NA_FACT_INVENTORY_20261014"


def render() -> tuple[str, str]:
    from app.services.na_fact_inventory import build_inventory
    inv = build_inventory()
    data = json.dumps({"facts": inv, "count": len(inv)}, indent=1, sort_keys=True) + "\n"
    import io
    buf = io.StringIO()
    cols = list(inv[0].keys())
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in inv:
        w.writerow([json.dumps(r[c]) if isinstance(r[c], (list, dict)) else r[c] for c in cols])
    return data, buf.getvalue()


if __name__ == "__main__":
    j, c = render()
    (OUT / f"{STEM}.json").write_text(j)
    (OUT / f"{STEM}.csv").write_text(c)
    print(f"wrote {OUT / (STEM + '.json')}")
