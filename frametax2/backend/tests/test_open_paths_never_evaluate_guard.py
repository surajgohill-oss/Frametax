"""Recurrence guard (NA-RECONCILIATION-15): only these functions may call evaluate_project().

Opening Library, Overview, Workspace or Globe reads retained results and never evaluates (repair 9d29ecb6; behavioural controls: test_retained_results_open_controls,
test_durable_project_visibility_controls). This test is the structural complement: a new evaluate_project() call site on any other function fails here, so a read route cannot start
evaluating by accident. get_project_state is allowed only because it skips the call for a STALE project (`retained_only`); that guard is asserted below."""
from __future__ import annotations

import ast
import pathlib

APP = pathlib.Path(__file__).resolve().parents[1] / "app"

ALLOWED = {
    ("services/bounded_regeneration.py", "_go"),            # explicit operator script (regenerate_project_bounded.py)
    ("api/v1/evaluation.py", "begin_project_evaluation"),    # explicit POST /evaluation/begin
    ("api/v1/cineglobe.py", "post_project_locations"),       # explicit user save
    ("api/v1/cineglobe.py", "post_project_content_gates"),   # explicit user save
    ("api/v1/cineglobe.py", "get_project_state"),            # guarded: skipped when the generation is STALE
}


def _call_sites() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path in APP.rglob("*.py"):
        if path.name == "secrets.py":
            continue
        try:
            tree = ast.parse(path.read_text())
        except (OSError, SyntaxError):
            continue

        def walk(node, fn=None):
            for child in ast.iter_child_nodes(node):
                cur = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
                if isinstance(child, ast.Call) and (getattr(child.func, "id", None) or getattr(child.func, "attr", None)) in {"evaluate_project", "begin_evaluation"}:
                    found.add((path.relative_to(APP).as_posix(), cur or "<module>"))
                walk(child, cur)

        walk(tree)
    return found


def test_only_the_explicit_actions_and_the_guarded_state_route_call_evaluate_project():
    sites = _call_sites()
    assert sites <= ALLOWED, f"a read path now evaluates: {sorted(sites - ALLOWED)}"


def test_the_state_route_skips_evaluation_for_a_stale_generation():
    source = (APP / "api/v1/cineglobe.py").read_text()
    guard = source.index('retained_only = _fresh == "STALE"')
    call = source.index("await evaluate_project(db, project_id)", guard)
    assert "if not retained_only:" in source[guard:call], "the evaluate_project call must stay behind the STALE guard"
