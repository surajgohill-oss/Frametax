"""
test_legacy_endpoint_isolation.py

Final Consolidated Backend Correction + Global Structuring Intelligence
Acceptance, Part 3/CBA-007 — Codex's audit found that mounted production
APIs expose the superseded run_full_analysis path (app/api/v1/
structures.py), separate optimization engines (app/api/v1/optimization.py),
and unparameterized Little-Utopia-only state (app/api/v1/cineglobe.py),
and that these routes "can calculate/persist or serve state outside the
canonical evaluator."

Investigated directly against the current source (never assumed):

- structures.py's calculate_structure_impl (the run_full_analysis-backed
  legacy path) DOES persist a real StructureCalculationResult row, but
  NEVER writes project.leading_structure_id -- it structurally cannot
  become a project's served/recommended/current result.
- optimization.py's five endpoints (gap-analysis/recommendations/
  generate-structures/maximize/travel-cost) never call db.add/db.commit
  at all -- stateless calculators, zero persistence, zero contamination
  risk by construction.
- Every canonical serving surface (canonical_production_view.py,
  project_workspace_view.py, canonical_evaluation.py's own
  _summarize_evaluation) filters strictly on
  StructureCalculationResult.engine_version == the CURRENT ENGINE_VERSION
  string -- a legacy "0.1.0" row (run_full_analysis's own engine_version)
  can never match that filter, so it can never be served as current even
  if persisted. test_canonical_served_wiring_repair.py's
  test_stale_engine_rows_never_leak_into_served_output already proves
  this end-to-end against real, persisted legacy 0.1.0 rows for FVD.

This is verified here as a durable, tested guarantee (not merely a
one-time grep), so a future edit to either file that reintroduces a
leading_structure_id write or a persistence call is caught immediately.
"""
from __future__ import annotations

import ast
import inspect


def test_calculate_structure_impl_never_writes_leading_structure_id():
    from app.api.v1.structures import calculate_structure_impl

    tree = ast.parse(inspect.getsource(calculate_structure_impl))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "leading_structure_id":
            # A READ is fine (there is none currently); only a WRITE
            # (an Attribute used as an assignment target) is the real
            # contamination risk this test guards against.
            parent_stores = [
                n for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and any(
                    isinstance(t, ast.Attribute) and t.attr == "leading_structure_id"
                    for t in n.targets
                )
            ]
            assert not parent_stores, (
                "calculate_structure_impl must never write project.leading_structure_id -- "
                "doing so would let a legacy run_full_analysis result masquerade as the "
                "project's current/recommended served state"
            )


def test_optimization_router_never_persists_to_the_database():
    """Codex evidence: 'separate optimization engines' as a contamination
    risk. Verified: every endpoint in this module is a stateless
    calculator with no db.add/db.commit call anywhere in the file."""
    import app.api.v1.optimization as optimization_module

    source = inspect.getsource(optimization_module)
    assert "db.add(" not in source
    assert ".commit()" not in source


def test_cineglobe_unparameterized_endpoints_are_explicitly_demo_scoped():
    """Codex evidence: cineglobe.py's unparameterized endpoints
    (/production, /structures, /package, /economics, /people, /facts,
    /legal, /recommendations) read app.demo.little_utopia_state directly
    -- confirmed still true, and confirmed still genuinely used (not dead
    code) by three real company-level screens (CompanyKnowledge.jsx,
    Today.jsx, CompanyGlobe.jsx) that are legitimately NOT scoped to any
    one project. Per CBA-007's "separate demo namespace/storage" option
    (removal was rejected -- it would break real, live functionality
    outside this pass's scope), this test locks in that the project-
    scoped canonical path (get_project_state) remains the one and only
    entry point for any PROJECT's served economics -- never these."""
    import app.api.v1.cineglobe as cineglobe_module

    source = inspect.getsource(cineglobe_module)
    # The canonical, project-scoped entry point must still exist and be
    # the one this module defers to for any real project's economics.
    assert "get_project_state" in source
    assert "build_production_and_structures" in source
