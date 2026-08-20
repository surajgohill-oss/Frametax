"""
test_no_runtime_web_dependency.py

Final Consolidated Backend Correction + Global Structuring Intelligence
Acceptance, Part 23/28/30 (runtime acceptance proof #20) — the served
evaluate_project()/build_production_and_structures() path must require
NO live web research. The worldwide incentive/treaty/qualification
database exists precisely so normal production analysis reads durable,
already-researched canonical knowledge, never the web, at request time.
Web research (WebFetch/WebSearch, this session's own tools) is
maintenance-only: initial acquisition, genuine authority residuals,
scheduled updates — never invoked from the served runtime path.
"""
from __future__ import annotations

import ast
import importlib
import inspect

_SERVED_PATH_MODULES = (
    "app.services.canonical_evaluation",
    "app.services.canonical_production_view",
    "app.services.canonical_project_economics",
    "app.services.project_workspace_view",
    "app.calculators.canonical_role_qualification_bridge",
    "app.calculators.canonical_treaty_bridge",
    "app.calculators.canonical_opportunity_bridge",
    "app.calculators.canonical_stack_bridge",
    "app.calculators.qualification_derivation",
    "app.calculators.allocation_pricing",
    "app.calculators.production_allocation",
    "app.calculators.treaty_engine",
    "app.calculators.production_discovery",
    "app.data.cultural_point_tables",
    "app.data.program_spend_rules",
    "app.data.program_rate_rules",
    "app.data.program_authority_provenance",
    "app.data.national_cultural_status",
    "app.data.structuring_opportunity_patterns",
)

#: Real HTTP/network client libraries that would indicate a live web call.
_NETWORK_MODULES = ("requests", "httpx", "aiohttp", "urllib.request", "urllib3")


def test_served_path_modules_import_no_network_client_library():
    for module_name in _SERVED_PATH_MODULES:
        module = importlib.import_module(module_name)
        source = inspect.getsource(module)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module} if node.module else set()
            else:
                continue
            offenders = names & set(_NETWORK_MODULES)
            assert not offenders, (
                f"{module_name} imports a live network client library {offenders} — "
                "the served evaluation path must require no runtime web research."
            )


def test_served_path_modules_never_call_a_raw_socket_or_open_url():
    for module_name in _SERVED_PATH_MODULES:
        module = importlib.import_module(module_name)
        source = inspect.getsource(module)
        assert "urlopen(" not in source
        assert "socket.socket(" not in source
