"""NA-RECONCILIATION-25: the PROPOSED real-anchor acceptance manifest stays current and honest. Static analysis only: no database is opened, nothing is evaluated, none of the 42 controls is run."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "validation"
STEM = "REAL_ANCHOR_ACCEPTANCE_MANIFEST_PROPOSED_20261015"


def _generated():
    import sys
    sys.path.insert(0, str(ROOT / "backend" / "scripts"))
    import real_anchor_manifest as m
    return m.build(), m


def test_the_committed_manifest_equals_the_regenerated_one():
    built, m = _generated()
    assert json.loads((DOCS / f"{STEM}.json").read_text()) == json.loads(json.dumps(built)), "regenerate with: python backend/scripts/real_anchor_manifest.py"
    assert (DOCS / f"{STEM}.md").read_text() == m.render_md(built)


def test_the_manifest_covers_exactly_the_42_reconciled_controls_with_unchanged_ids():
    built, _ = _generated()
    reconciliation = (DOCS / "INHERITED_FAILURE_RECONCILIATION_20261015.md").read_text().split("## OPEN")[1]
    expected = re.findall(r"\| (tests/test_[a-z_0-9]+\.py::[^ ]+) \|", reconciliation)
    assert len(expected) == 42 and [c["node_id"] for c in built["controls"]] == sorted(expected, key=lambda n: [c["node_id"] for c in built["controls"]].index(n))
    assert set(c["node_id"] for c in built["controls"]) == set(expected)
    assert built["status"].startswith("PROPOSED - NOT EXECUTED")


def test_no_control_is_registered_or_deselected_and_every_one_is_classified():
    from tests.real_production_registry import is_real_production_test
    built, _ = _generated()
    assert not [c["node_id"] for c in built["controls"] if is_real_production_test(c["node_id"])], "the 42 are OPEN: registering one would hide it"
    for c in built["controls"]:
        assert c["category"] in ("A_READ_ONLY_RETAINED", "B_EVALUATE_IDEMPOTENT", "C_EVALUATE_AND_COMMIT", "D_MUTATE_FACTS")
        assert c["anchors"], f"{c['node_id']} names no anchor"
        assert (ROOT / "backend" / c["node_id"].split("::")[0]).exists()
