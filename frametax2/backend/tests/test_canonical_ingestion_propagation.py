"""
Canonical Ingestion/Analysis Propagation closeout.

Confirms the generic version-aware backfill mechanism this task audited
and repaired: budget routing previously had NO version marker at all
(unlike screenplay routing's PARSER_VERSION) so a real budget-parser fix
could never mark an already-routed project's BudgetDocument stale.
Fixed generically (BUDGET_PARSER_VERSION + material_routing._route_budget
version-aware guard, mirroring screenplay routing's own convention) --
see tests/test_material_routing.py for the direct routing-level tests.
This file covers the location-taxonomy generic fix (a real ontology gap,
proven from real screenplay evidence, not a per-project patch) and the
cross-cutting "no project-specific code" guard for every file this task
touched.
"""
from __future__ import annotations

import ast
import inspect

from app.calculators.production_requirements import abstract_location


def _code_only(src: str) -> str:
    """Strip docstrings/comments so a project name in explanatory prose
    (this codebase's own established convention -- e.g. 'no Little
    Utopia' explaining what a function does NOT special-case) doesn't
    false-positive a project-specific-code guard. Checks actual executable
    string literals only, via the real AST -- not a text/regex heuristic."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)):
                node.body[0].value = ast.Constant(value="")
    # unparse strips comments inherently (they're not part of the AST)
    return ast.unparse(tree)


# ── A. Location taxonomy: a real, generic gap -- proven, not guessed ───────

def test_marine_open_water_keywords_are_generic_not_a_per_project_patch():
    """The 'marine_open_water' TAXONOMY category itself uses the words
    'marine' and 'open water' -- but neither was recognized as an input
    keyword before this fix, a real gap independent of any one project
    (confirmed from a real screenplay's own evidence text using exactly
    this vocabulary). Proven against arbitrary text, never a Little
    Utopia-specific string."""
    assert "marine_open_water" in abstract_location("A marine biology research vessel.")
    assert "marine_open_water" in abstract_location("An open water swimming scene.")
    assert "marine_open_water" in abstract_location("Two men adrift on a small boat.")
    # Still resolves the pre-existing keywords unchanged (no regression).
    assert "marine_open_water" in abstract_location("The endless sea stretches to the horizon.")


def test_location_ontology_gap_fix_lives_in_the_shared_module_not_a_demo_file():
    """Section 16: no 'Little Utopia' conditional anywhere in the fix --
    the new keywords are plain dict entries in the SAME shared
    _LOCATION_ONTOLOGY every project's abstract_location() call already
    reads, never a per-project branch."""
    import app.calculators.production_requirements as mod

    src = _code_only(inspect.getsource(mod))
    assert "Little Utopia" not in src
    assert "little_utopia" not in src.lower()


def test_unrelated_location_text_still_resolves_to_nothing_fabricated():
    """A location string matching no real keyword still returns an empty
    set -- the new keywords didn't loosen the classifier into guessing."""
    assert abstract_location("A quiet suburban kitchen.") == frozenset({"suburban"})
    assert abstract_location("xyzzy plugh") == frozenset()


# ── J. No project-specific code in any file this task touched ──────────────

def test_no_project_specific_branching_in_touched_propagation_files():
    import app.ingestion.budget_parser as budget_parser_mod
    import app.services.material_routing as routing_mod

    for mod in (budget_parser_mod, routing_mod):
        src = _code_only(inspect.getsource(mod))
        for banned in (
            "ab10b319-978e-44d3-9331-af2a5f2cccc2",  # Lips Like Sugar
            "4355ae88-a636-4c18-af60-ad73b2646124",  # Bad Hombres
            "fa5cade5-0669-4816-bfe6-72146f8d3bae",  # Little Utopia
            "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",  # FVD
            "Lips Like Sugar", "Bad Hombres", "Little Utopia",
            'project.title ==',
        ):
            assert banned not in src, f"{mod.__name__} must not branch on {banned!r}"
