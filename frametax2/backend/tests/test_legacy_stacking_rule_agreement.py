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


def test_the_manitoba_federal_rows_agree_with_the_registry():
    spec = importlib.util.spec_from_file_location("mig0083", _PATH.with_name("0083_manitoba_federal_stacking_rules.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert (mod.revision, mod.down_revision) == ("0083", "0082")
    reg = stacking_rules._SLUG_PAIR_RULES
    for _id, a, b, _text in mod.ROWS:
        assert reg[frozenset({a, b})]["rule_type"] == "spend_reduction"
    assert len({r[0] for r in mod.ROWS}) == 2


def test_the_bc_quebec_and_ocase_federal_rows_agree_with_the_registry_and_state_their_primary_basis():
    spec = importlib.util.spec_from_file_location("mig0084", _PATH.with_name("0084_federal_pstc_provincial_stacking_rules.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert (mod.revision, mod.down_revision) == ("0084", "0083")
    reg = stacking_rules._SLUG_PAIR_RULES
    assert len(mod.ROWS) == 4 and len({_rule for _rule in map(mod._rule_id, [r[0] for r in mod.ROWS])}) == 4
    for _key, a, b, text in mod.ROWS:
        assert reg[frozenset({a, b})]["rule_type"] == "spend_reduction", (a, b)
        assert text.strip(), "a seeded rule states its basis"
    assert "s.79(1)" in reg[frozenset({"ca_federal_pstc", "ca_bc_pstc"})]["condition_text"]
    assert "note 7" in reg[frozenset({"ca_federal_pstc", "ca_qc_pstc"})]["condition_text"]


def test_the_newfoundland_federal_rows_agree_with_the_registry_and_cite_the_regulation():
    spec = importlib.util.spec_from_file_location("mig0085", _PATH.with_name("0085_nl_federal_stacking_rules.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert (mod.revision, mod.down_revision) == ("0085", "0084")
    reg = stacking_rules._SLUG_PAIR_RULES
    assert len(mod.ROWS) == 2 and len({mod._rule_id(r[0]) for r in mod.ROWS}) == 2
    for _key, a, b, text in mod.ROWS:
        assert reg[frozenset({a, b})]["rule_type"] == "spend_reduction", (a, b)
        assert "Regulation 31/23" in text and "Regulation 31/23" in reg[frozenset({a, b})]["condition_text"]
        assert "s.2(m)" in reg[frozenset({a, b})]["condition_text"]


def test_the_na_unruled_pair_rows_agree_with_the_registry():
    spec = importlib.util.spec_from_file_location("mig0086", _PATH.with_name("0086_na_unruled_provincial_stacking_rules.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert (mod.revision, mod.down_revision) == ("0086", "0085")
    reg = stacking_rules._SLUG_PAIR_RULES
    assert tuple(int(x) for x in stacking_rules.STACKING_RULES_VERSION.split(".")) >= (1, 10, 0)      # 1.10.0 added these rows; later versions only add rules
    assert len(mod.ROWS) == 10 and len({mod._rule_id(r[0]) for r in mod.ROWS}) == 10
    for _key, a, b, rule_type, text in mod.ROWS:
        assert text.strip()
        if _key in ("dave+cptc", "ofttc+pstc"):
            continue                                  # seeded as `conditional` by 0086, ruled `spend_reduction` by 0089 from primary text (checked below)
        assert reg[frozenset({a, b})]["rule_type"] == rule_type, (a, b)
    assert {r[3] for r in mod.ROWS if r[0] in ("dave+cptc", "ofttc+pstc")} == {"conditional"}


def test_the_na_conditional_pairs_are_ruled_by_0089_and_the_registry_agrees():
    spec = importlib.util.spec_from_file_location("mig0089", _PATH.with_name("0089_na_conditional_pairs_ruled_and_cmpa_retired.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert (mod.revision, mod.down_revision) == ("0089", "0088")
    reg = stacking_rules._SLUG_PAIR_RULES
    assert reg[frozenset({"ca_bc_dave", "ca_federal_cptc"})]["rule_type"] == mod._RULED["dave+cptc"][0] == "spend_reduction"
    assert reg[frozenset({"on_ofttc", "ca_federal_pstc"})]["rule_type"] == mod._RULED["ofttc+pstc"][0] == "spend_reduction"
    assert reg[frozenset({"ca_bc_film_tv_tax_credit", "ca_federal_pstc"})]["rule_type"] == mod._INSERT[2] == "spend_reduction"
    assert not [k for k in reg if "ca_cmpa_foreign" in k]
    assert {v[0] for v in mod._OLD.values()} == {"conditional"}


def test_the_qprdp_spelling_is_retired_in_the_registry_and_the_legacy_rows_are_deleted_by_0087():
    spec = importlib.util.spec_from_file_location("mig0087", _PATH.with_name("0087_retire_qprdp_stacking_spelling.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert (mod.revision, mod.down_revision) == ("0087", "0086")
    assert not [k for k in stacking_rules._SLUG_PAIR_RULES if "ca_qc_qprdp" in k]
    assert not [t for t in stacking_rules._NAME_SLUG_RULES if t[2] == "ca_qc_qprdp"]
