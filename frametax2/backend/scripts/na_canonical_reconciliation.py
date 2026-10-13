"""Write the NA canonical reconciliation matrix (NA-RECONCILIATION-11) from the live registries. Read-only: no database, no evaluation, no network.

    env -u DATABASE_URL .venv/bin/python scripts/na_canonical_reconciliation.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services import na_canonical_reconciliation as na  # noqa: E402

OUT = ROOT.parent / "docs" / "validation"
STEM = "NA_CANONICAL_RECONCILIATION_20261013"


def main() -> None:
    matrix = na.build_matrix()
    summary = na.summary(matrix)
    with open(OUT / f"{STEM}.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=na.columns())
        writer.writeheader()
        writer.writerows(matrix)
    with open(OUT / f"{STEM}.json", "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "columns": na.columns(), "rows": matrix}, fh, indent=1, sort_keys=False)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
