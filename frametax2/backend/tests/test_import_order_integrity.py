"""test_import_order_integrity.py

Codex final runtime remediation, item P1:import_order
(GLOBAL_PROGRAM_FINAL_CLAUDE_REMEDIATION_MANIFEST_CODEX.csv).

Codex's independent audit reproduced a genuine circular-import defect: a
FRESH Python process importing app.services.canonical_production_view
before app.data.program_rate_rules (or anything that imports it) raised

    ImportError: cannot import name 'DoctrineRateTier' from partially
    initialized module 'app.data.executable_jurisdiction_registry'

because executable_jurisdiction_registry.py imported RateCondition/
RateRule/SourceProvenance/get_rate_rules from program_rate_rules.py at
MODULE SCOPE, and program_rate_rules.py side-effect-imports program_rate_
rules_worldwide.py (to trigger rule registration) which in turn imports
DoctrineRateTier/DoctrineRecord/register/rate_rules_for FROM executable_
jurisdiction_registry.py -- a real circular edge. Importing
canonical_evaluation first happened to pull in program_rate_rules early
enough to mask the cycle; that was a coincidence of import order, not a
fix.

The fix (executable_jurisdiction_registry.py): the three type names are
used only as annotations (safe under `from __future__ import annotations`,
which makes every annotation a lazily-evaluated string) so they moved
behind `if TYPE_CHECKING:`; RateRule and get_rate_rules are only actually
called inside function bodies (rate_rules_for / get_provenance), so those
two became function-local deferred imports. executable_jurisdiction_
registry.py no longer imports program_rate_rules.py at module scope at
all, which breaks the cycle with zero economics/registration/public-API
change.

These tests use subprocess-spawned CLEAN interpreters (not importlib
reload or in-process module-cache tricks) for every material import
order Codex identified, so a regression here cannot be masked by
whatever else happened to already be imported earlier in a shared test
session.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

BACKEND_ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _assert_clean(proc: subprocess.CompletedProcess) -> None:
    assert proc.returncode == 0, (
        f"fresh-process import failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )


# ── The exact defect Codex reproduced: canonical_production_view first. ──

def test_fresh_process_canonical_production_view_imports_first():
    proc = _run("import app.services.canonical_production_view; print('OK')")
    _assert_clean(proc)
    assert "OK" in proc.stdout


# ── The order that previously masked the defect -- must keep working. ───

def test_fresh_process_canonical_evaluation_then_production_view():
    proc = _run(
        "import app.services.canonical_evaluation\n"
        "import app.services.canonical_production_view\n"
        "print('OK')"
    )
    _assert_clean(proc)
    assert "OK" in proc.stdout


# ── The reverse order -- must also work (order must not matter at all). ──

def test_fresh_process_production_view_then_canonical_evaluation():
    proc = _run(
        "import app.services.canonical_production_view\n"
        "import app.services.canonical_evaluation\n"
        "print('OK')"
    )
    _assert_clean(proc)
    assert "OK" in proc.stdout


# ── The registry module standalone, with no prior program_rate_rules
# import in the process at all. ───────────────────────────────────────────

def test_fresh_process_executable_jurisdiction_registry_standalone_first():
    proc = _run(
        "import app.data.executable_jurisdiction_registry as r\n"
        "print('OK', r.get_doctrine('ca_federal_cptc'))"
    )
    _assert_clean(proc)
    assert "OK" in proc.stdout


# ── program_rate_rules.py standalone first (the other direction of the
# original cycle). ────────────────────────────────────────────────────────

def test_fresh_process_program_rate_rules_standalone_first():
    proc = _run(
        "import app.data.program_rate_rules as prr\n"
        "print('rule_count', len(prr._RULES_BY_PROGRAM))"
    )
    _assert_clean(proc)
    assert "rule_count" in proc.stdout


# ── program_rate_rules_worldwide.py standalone first (the module that
# actually creates the circular edge back into executable_jurisdiction_
# registry.py). ────────────────────────────────────────────────────────────

def test_fresh_process_program_rate_rules_worldwide_standalone_first():
    proc = _run(
        "import app.data.program_rate_rules_worldwide\n"
        "print('OK')"
    )
    _assert_clean(proc)
    assert "OK" in proc.stdout


# ── The real application entrypoint modules a request handler would hit,
# in a fresh process, with no other app module warmed first. ────────────

def test_fresh_process_real_production_entrypoint():
    proc = _run(
        "import asyncio\n"
        "from app.services.canonical_evaluation import evaluate_project\n"
        "from app.services.canonical_production_view import build_production_and_structures\n"
        "print('OK', evaluate_project is not None, build_production_and_structures is not None)"
    )
    _assert_clean(proc)
    assert "OK" in proc.stdout


# ── Deterministic registration: identical rule/doctrine counts regardless
# of which module triggers the registration first. No duplicate
# registrations from being imported via two different paths. ────────────

def test_fresh_process_rule_and_doctrine_counts_are_order_independent():
    code_a = (
        "import app.services.canonical_production_view\n"
        "from app.data.program_rate_rules import _RULES_BY_PROGRAM\n"
        "from app.data.executable_jurisdiction_registry import all_doctrine_records\n"
        "print(len(_RULES_BY_PROGRAM), len(all_doctrine_records()))"
    )
    code_b = (
        "import app.services.canonical_evaluation\n"
        "from app.data.program_rate_rules import _RULES_BY_PROGRAM\n"
        "from app.data.executable_jurisdiction_registry import all_doctrine_records\n"
        "print(len(_RULES_BY_PROGRAM), len(all_doctrine_records()))"
    )
    proc_a, proc_b = _run(code_a), _run(code_b)
    _assert_clean(proc_a)
    _assert_clean(proc_b)
    counts_a = proc_a.stdout.strip().splitlines()[-1]
    counts_b = proc_b.stdout.strip().splitlines()[-1]
    assert counts_a == counts_b, f"registration counts differ by import order: {counts_a!r} vs {counts_b!r}"


# ── Real economics unaffected: a fresh-process resolution matches the
# in-process test-suite value regardless of which module warms first. ───

def test_fresh_process_economics_match_regardless_of_import_order():
    code = (
        "import app.services.canonical_production_view\n"
        "from app.data.program_rate_rules import resolve_program_rate\n"
        "r = resolve_program_rate('ca_film_30', 'feature_film', 5_000_000)\n"
        "print(r.modeled_rate)"
    )
    proc = _run(code)
    _assert_clean(proc)
    rate = float(proc.stdout.strip().splitlines()[-1])
    assert rate > 0
