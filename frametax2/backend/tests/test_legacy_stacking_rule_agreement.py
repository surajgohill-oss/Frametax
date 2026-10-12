"""The legacy database stacking-rule seed agrees with the code registry (NA-CODEX-08). DB-free: the migration module is loaded and its rows are compared
with app.optimization.stacking_rules, the registry every canonical pricing path reads."""
from __future__ import annotations

import importlib.util
import pathlib

from app.optimization import stacking_rules

_PATH = pathlib.Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0082_correct_ontario_opstc_stacking_rules.py"


def _migration():
    spec = importlib.util.spec_from_file_location("mig0082", _PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_corrected_legacy_rows_have_the_registry_rule_types_and_ids_are_stable():
    mod = _migration()
    assert (mod.revision, mod.down_revision) == ("0082", "0081")
    reg = stacking_rules._SLUG_PAIR_RULES
    assert reg[frozenset({"ca_federal_cptc", "on_opstc"})]["rule_type"] == "spend_reduction"
    assert reg[frozenset({"ca_federal_pstc", "on_opstc"})]["rule_type"] == "spend_reduction"
    assert reg[frozenset({"on_ofttc", "on_opstc"})]["rule_type"] == "mutually_exclusive"
    assert reg[frozenset({"ca_federal_pstc", "ca_federal_cptc"})]["rule_type"] == "mutually_exclusive"
    old = importlib.util.spec_from_file_location("mig0022", _PATH.with_name("0022_stacking_rules_expansion.py"))
    m22 = importlib.util.module_from_spec(old); old.loader.exec_module(m22)
    assert mod.CPTC_OPSTC_ID == m22._RULE_IDS["cptc_opstc_exclusive"], "the correction updates the seeded row in place"


def test_the_migration_text_states_the_registry_basis():
    mod = _migration()
    for text in (mod.CPTC_OPSTC_TEXT, mod.PSTC_OPSTC_TEXT):
        assert "s.1.01" in text
    assert "LABOUR portion" in mod.PSTC_OPSTC_TEXT and "60%" in mod.CPTC_OPSTC_TEXT
