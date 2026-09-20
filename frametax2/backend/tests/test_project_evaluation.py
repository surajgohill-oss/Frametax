"""
project_evaluation.py -- RETIRED_UNREACHABLE legacy orchestrator: retirement guards.

`app/services/project_evaluation.py::begin_evaluation` / `_summarize` (the run_full_analysis-backed
"Begin Evaluation" orchestrator) were removed. They were unreachable from production -- the served
evaluation is canonical_evaluation.evaluate_project -- and their read-back loaded every row of a
project (all engine versions and generations) into memory, which an evaluation generation of 500,000+
rows makes prohibited (PROJECT_RULES.md, LONG-RUNNING PROCESS DISCIPLINE, rule 10).

These tests keep that closed:

  * the removed names stay removed and the module says RETIRED_UNREACHABLE;
  * the module is not part of the canonical fingerprint digest (its retirement invalidates nothing);
  * NO production module may import, reference or call anything from it except the one helper still used
    canonically, `_derive_home_jurisdiction` (imported by canonical_project_economics.py) -- proven by an
    AST scan of every module under app/, by the eager-import closure of app.main (the module is not even
    loaded by the running application) and by the OpenAPI route table (no route is served from it);
  * the preserved helper still derives a base jurisdiction from a budget filename.

Synthetic only: the helper test builds its own disposable Organization/Project/BudgetDocument and deletes
them; nothing here touches, evaluates or needs a generation of a real production.
"""
from __future__ import annotations

import ast
import pathlib
import uuid

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.budget import BudgetDocument
from app.models.jurisdiction import Jurisdiction
from app.models.organization import Organization
from app.models.project import Project

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
LEGACY_MODULE = "app.services.project_evaluation"
LEGACY_FILE = APP / "services" / "project_evaluation.py"
RETIRED_NAMES = ("begin_evaluation", "_summarize")
#: the ONLY production importer of the legacy module, and the ONLY name it may take from it
ALLOWED_IMPORTS = {"app/services/canonical_project_economics.py": {"_derive_home_jurisdiction"}}


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def project(db: AsyncSession):
    org = Organization(name="Evaluation Test Org", slug=f"evaluation-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.flush()
    org_id = org.id
    p = Project(id=uuid.uuid4(), organization_id=org_id, title=f"Evaluation Test Project {uuid.uuid4().hex[:8]}")
    db.add(p)
    await db.commit()
    await db.refresh(p)
    project_id = p.id
    try:
        yield p
    finally:
        await db.rollback()
        await db.execute(sa_delete(Project).where(Project.id == project_id))
        await db.execute(sa_delete(Organization).where(Organization.id == org_id))
        await db.commit()


# ── lineage: retired, and not part of the fingerprint ────────────────────────────────────

def test_retired_entrypoints_stay_removed_and_the_module_says_so():
    from app.services import project_evaluation as mod

    for name in RETIRED_NAMES:
        assert not hasattr(mod, name), f"{name} was retired (unbounded read path) and must not come back"
    assert "RETIRED_UNREACHABLE" in (mod.__doc__ or "")
    # the helper that IS still canonically used is preserved
    assert callable(mod._derive_home_jurisdiction)


def test_legacy_module_is_not_part_of_the_canonical_fingerprint_digest():
    """Editing/retiring it can therefore never invalidate a persisted generation."""
    import importlib

    from app.services import canonical_runtime_attribution as cra

    assert LEGACY_MODULE not in cra._SEMANTIC_PRICING_MODULES
    digest_files = {pathlib.Path(importlib.import_module(m).__file__).resolve() for m in cra._SEMANTIC_PRICING_MODULES}
    assert LEGACY_FILE.resolve() not in digest_files


# ── reachability: imports, call graph, OpenAPI ───────────────────────────────────────────

def _app_sources():
    for path in sorted(APP.rglob("*.py")):
        if path == LEGACY_FILE:
            continue
        yield path, path.read_text(encoding="utf-8")


def test_no_production_module_imports_references_or_calls_the_retired_entrypoints():
    violations, scanned = [], 0
    for path, source in _app_sources():
        rel = path.relative_to(BACKEND).as_posix()
        scanned += 1
        for node in ast.walk(ast.parse(source, filename=rel)):
            if isinstance(node, ast.ImportFrom):
                imported = {alias.name for alias in node.names}
                if node.module == LEGACY_MODULE:
                    if not imported <= ALLOWED_IMPORTS.get(rel, set()):
                        violations.append(f"{rel}:{node.lineno} imports {sorted(imported)} from the legacy module")
                elif node.module == "app.services" and "project_evaluation" in imported:
                    violations.append(f"{rel}:{node.lineno} imports the legacy module object")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == LEGACY_MODULE or alias.name.startswith(LEGACY_MODULE + "."):
                        violations.append(f"{rel}:{node.lineno} imports the legacy module")
            elif isinstance(node, ast.Name) and node.id in RETIRED_NAMES[:1]:
                violations.append(f"{rel}:{node.lineno} references {node.id}")
            elif isinstance(node, ast.Attribute) and node.attr in RETIRED_NAMES[:1]:
                violations.append(f"{rel}:{node.lineno} references .{node.attr}")
            elif isinstance(node, ast.Constant) and node.value in (LEGACY_MODULE, "app/services/project_evaluation.py"):
                violations.append(f"{rel}:{node.lineno} names the legacy module in a dynamic import string")
    assert scanned > 200, "the AST scan must actually cover the application"
    assert not violations, "production code must not reach the retired legacy orchestrator:\n" + "\n".join(violations)
    # positive control: the one canonical use of the preserved helper really exists
    canonical = (APP / "services" / "canonical_project_economics.py").read_text(encoding="utf-8")
    assert "from app.services.project_evaluation import _derive_home_jurisdiction" in canonical


def _module_file(dotted: str) -> pathlib.Path | None:
    base = BACKEND.joinpath(*dotted.split("."))
    if base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return None


def _eager_imports(path: pathlib.Path) -> set[str]:
    """Application modules imported when `path` is imported: import statements that execute at import time
    (module level, including inside if/try/class bodies) -- NOT those inside function bodies, which run only
    when the function is called."""
    found: set[str] = set()

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(child, ast.ImportFrom) and child.module and child.module.split(".")[0] == "app":
                found.add(child.module)
                for alias in child.names:  # `from app.services import project_evaluation` names a submodule
                    if _module_file(f"{child.module}.{alias.name}") is not None:
                        found.add(f"{child.module}.{alias.name}")
            elif isinstance(child, ast.Import):
                found.update(a.name for a in child.names if a.name.split(".")[0] == "app")
            visit(child)

    visit(ast.parse(path.read_text(encoding="utf-8")))
    return found


def test_the_legacy_module_is_not_in_the_eager_import_closure_of_the_application():
    """Static, in-process (no child process): starting from app.main, follow every import that executes at
    import time. The legacy module is never reached, so the running application does not even load it; its only
    consumer is the function-level (lazy) import of the preserved helper."""
    seen, queue = set(), ["app.main"]
    while queue:
        module = queue.pop()
        if module in seen:
            continue
        seen.add(module)
        path = _module_file(module)
        if path is None:
            continue
        for imported in _eager_imports(path):
            if imported not in seen:
                queue.append(imported)
        parent = module.rpartition(".")[0]  # importing a.b.c executes a and a.b packages too
        while parent:
            queue.append(parent)
            parent = parent.rpartition(".")[0]
    print(f"\neager import closure of app.main: {len(seen)} modules; legacy module reached: {LEGACY_MODULE in seen}")
    assert len(seen) > 100, "the closure must actually cover the application"
    assert LEGACY_MODULE not in seen


def _iter_endpoint_routes(routes):
    """Every route that has an endpoint, descending into included routers (FastAPI wraps each
    include_router() in an _IncludedRouter, so a flat scan of app.routes sees almost none of them)."""
    for route in routes:
        if hasattr(route, "endpoint"):
            yield route
        elif hasattr(route, "original_router"):
            yield from _iter_endpoint_routes(route.original_router.routes)
        elif hasattr(route, "routes"):
            yield from _iter_endpoint_routes(route.routes)


def test_no_openapi_route_is_served_from_the_legacy_module():
    """The real route table (OpenAPI): no route's endpoint lives in, or is named after, the legacy module. The
    positive controls -- the canonical begin route in app.api.v1.evaluation, dozens of routes across every API
    module -- prove the walk actually sees the application's routes."""
    import app.main as application

    endpoint_routes = list(_iter_endpoint_routes(application.app.routes))
    endpoint_modules = {r.endpoint.__module__ for r in endpoint_routes}
    paths = application.app.openapi()["paths"]
    print(f"\nOpenAPI: {len(paths)} paths; {len(endpoint_routes)} endpoint routes across {len(endpoint_modules)} "
          f"endpoint modules; legacy module among them: {LEGACY_MODULE in endpoint_modules}")
    # positive controls: the walk can see the real application
    assert len(endpoint_routes) > 50 and len(endpoint_modules) > 10
    assert "app.api.v1.evaluation" in endpoint_modules and "app.api.v1.structures" in endpoint_modules
    assert any(r.path.endswith("/evaluation/begin") and r.endpoint.__module__ == "app.api.v1.evaluation"
               for r in endpoint_routes)
    assert "/api/v1/projects/{project_id}/evaluation/begin" in paths
    # the guard itself
    assert LEGACY_MODULE not in endpoint_modules
    assert [p for p in paths if "project_evaluation" in p or "begin_evaluation" in p] == []
    for route in endpoint_routes:
        assert getattr(route.endpoint, "__name__", "") not in RETIRED_NAMES


# ── the preserved, canonically-used helper ───────────────────────────────────────────────

async def test_preserved_helper_still_derives_home_jurisdiction_from_the_budget_filename(
    db: AsyncSession, project: Project,
):
    """Generic geography derivation: a jurisdiction name present in the budget's own filename -- here Malta --
    is picked up as the base. Nothing about Malta is hardcoded in the helper. (This was previously exercised
    through the retired orchestrator; it is now tested directly.)"""
    from app.services.project_evaluation import _derive_home_jurisdiction

    assert await _derive_home_jurisdiction(db, project) is None  # no budget evidence -> never fabricated
    db.add(BudgetDocument(project_id=project.id, filename="Production Budget - Malta Shoot.csv", file_type="csv"))
    await db.flush()
    derived = await _derive_home_jurisdiction(db, project)
    assert derived is not None and derived.name == "Malta"

    # never overrides an already-confirmed value
    other = (await db.execute(select(Jurisdiction).where(Jurisdiction.name != "Malta", Jurisdiction.is_active.is_(True)))).scalars().first()
    project.home_jurisdiction_id = other.id
    assert (await _derive_home_jurisdiction(db, project)).id == other.id


async def test_project_evaluation_module_contains_no_project_specific_code():
    """Regression guard matching test_material_routing.py's own: no
    per-project runner or hardcoded jurisdiction/project branch in the
    orchestration code itself. Checked against function/branch
    definitions only — the module's own docstring legitimately names FVD/
    Little Utopia in prose to explain what it does NOT special-case, same
    convention as test_material_routing.py's equivalent guard."""
    import inspect

    from app.services import project_evaluation as mod

    src = inspect.getsource(mod)
    for banned in (
        "def run_fvd", "def run_little_utopia", "def _route_fvd",
        'code == "GR"', 'code == "MU"', 'jurisdiction_code == "GR"', 'jurisdiction_code == "MU"',
    ):
        assert banned not in src, f"project_evaluation.py must stay project-agnostic; found {banned!r}"
