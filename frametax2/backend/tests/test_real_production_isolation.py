"""The real-production isolation registry stays honest: every listed test exists and really reaches a real production, the deselection helper matches by file and function, and authorization is read from the
same variable that lifts the conftest write guard."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.isolated_records import REAL_ANCHOR_PROJECT_IDS
from tests.real_production_registry import REAL_PRODUCTION_TESTS, authorization_given, is_real_production_test

_TESTS = Path(__file__).resolve().parent
_ANCHOR_PREFIXES = tuple(pid[:8] for pid in REAL_ANCHOR_PROJECT_IDS)
#: helpers/fixtures through which a test reaches a real production without naming its id (the formulaic file's fixture mutates FVD's stored facts)
_REAL_FIXTURES = {"clean_facts"}


def _functions(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    consts = {t.id: n.value.value for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
              and any(p in n.value.value for p in _ANCHOR_PREFIXES) for t in n.targets if isinstance(t, ast.Name)}
    funcs = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[n.name] = n
    return tree, consts, funcs, path.read_text(encoding="utf-8")


def test_every_listed_test_exists_and_reaches_a_real_production():
    problems = []
    for fname, names in REAL_PRODUCTION_TESTS.items():
        path = _TESTS / fname
        assert path.exists(), f"{fname} no longer exists"
        _, consts, funcs, src = _functions(path)
        for name in names:
            fn = funcs.get(name)
            if fn is None:
                problems.append(f"{fname}::{name} no longer exists")
                continue
            seg = ast.get_source_segment(src, fn) or ""
            argnames = {a.arg for a in fn.args.args}
            decorators = "".join(ast.unparse(d) for d in fn.decorator_list)
            parametrized_over_anchor = any(p in decorators for p in _ANCHOR_PREFIXES) or any(c in decorators for c in consts)
            reaches = any(c in seg for c in consts) or parametrized_over_anchor or bool(argnames & _REAL_FIXTURES) or any(p in seg for p in _ANCHOR_PREFIXES) \
                or any(n in seg for n in ("known_baseline", "production_names", "all_projects")) or fn.name.startswith("test_every_production")
            if not reaches:
                problems.append(f"{fname}::{name} does not reach a real production (remove it from the registry)")
    assert not problems, problems


def test_the_helper_matches_node_ids_by_file_and_function_including_parametrised_cases():
    assert is_real_production_test("tests/test_canonical_authority_substrate.py::test_georgia_prices_with_real_numbers_in_fvd")
    assert is_real_production_test("tests/test_canonical_served_wiring_repair.py::test_stale_engine_rows_never_leak_into_served_output[6c6f1c13-2d49-4bbc-bafb-2a12efa93112]")
    assert not is_real_production_test("tests/test_na_synthetic_pipeline_controls.py::test_texas_award_facts_gate_the_ceiling_and_the_awarded_rate_prices_not_the_ceiling")
    assert not is_real_production_test("tests/test_other_file.py::test_georgia_prices_with_real_numbers_in_fvd")


def test_authorization_is_read_from_the_variable_that_lifts_the_write_guard(monkeypatch):
    monkeypatch.delenv("CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS", raising=False)
    assert authorization_given() is False
    monkeypatch.setenv("CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS", "6c6f1c13-2d49-4bbc-bafb-2a12efa93112")
    assert authorization_given() is True


def test_the_default_run_deselected_the_listed_tests(request):
    """This run itself: when no authorization is given, none of the listed tests is in the session."""
    if authorization_given():
        pytest.skip("authorized run: the listed tests are collected on purpose")
    collected = {i.nodeid for i in request.session.items}
    assert not [n for n in collected if is_real_production_test(n)], "a listed real-production test was collected without authorization"
