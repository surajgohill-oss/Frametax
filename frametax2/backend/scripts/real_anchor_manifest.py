"""Generate the PROPOSED real-anchor acceptance manifest (NA-RECONCILIATION-25): static analysis only. Opens no database, evaluates nothing and executes none of the 42 controls.

For each control that stops before its assertion in the isolated database (the anchors are absent) the manifest records its node id, the anchors it names, its intended assertion, whether it is read-only, whether it calls
evaluation, whether it writes (a generation or a fact), whether a retained generation can satisfy it, and the database / environment / timeout / cleanup / authorization it needs. The control list is read from
docs/validation/INHERITED_FAILURE_RECONCILIATION_20261015.md (never edited here). Nothing is registered or deselected.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
DOC = ROOT / "docs" / "validation" / "INHERITED_FAILURE_RECONCILIATION_20261015.md"
OUT = ROOT / "docs" / "validation"
STEM = "REAL_ANCHOR_ACCEPTANCE_MANIFEST_PROPOSED_20261015"
ANCHORS = {"fa5cade5-0669-4816-bfe6-72146f8d3bae": "The Little Utopia (LU)", "ab10b319-978e-44d3-9331-af2a5f2cccc2": "Lips Like Sugar (LLS)",
           "6c6f1c13-2d49-4bbc-bafb-2a12efa93112": "F#K Valentine's Day (FVD)", "4355ae88-a636-4c18-af60-ad73b2646124": "Bad Hombres (BH)"}
EVAL_NAMES = {"evaluate_project"}
WRITE_NAMES = {"commit", "add", "delete", "flush", "write_ny_program_facts", "_upsert", "merge", "execute"}
READ_BUILDERS = {"build_production_and_structures", "build_project_economic_inputs", "build_generic_pkg_and_economics", "load_generation_summary", "current_generation_fingerprint", "current_result_fingerprint"}


def controls() -> list[str]:
    text = DOC.read_text().split("## OPEN")[1]
    return re.findall(r"\| (tests/test_[a-z_0-9]+\.py::[^ ]+) \|", text)


class Module:
    def __init__(self, path: Path):
        self.src = path.read_text()
        self.tree = ast.parse(self.src)
        self.funcs = {n.name: n for n in ast.walk(self.tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.consts = {}
        for n in self.tree.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                try:
                    v = ast.literal_eval(n.value)
                except Exception:
                    continue
                if isinstance(v, str):
                    self.consts[n.targets[0].id] = v

    def closure(self, name: str, seen=None) -> list[ast.AST]:
        seen = seen if seen is not None else set()
        if name in seen or name not in self.funcs:
            return []
        seen.add(name)
        nodes = [self.funcs[name]]
        for n in ast.walk(self.funcs[name]):
            if isinstance(n, ast.Call):
                callee = n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else None)
                if callee:
                    nodes += self.closure(callee, seen)
        return nodes


#: Manual review of what static analysis cannot see (reviewed against the test source on 2026-10-15).
MANUAL = {
    "test_populating_a_nationality_invalidates_the_evaluation_fingerprint": (
        "D_MUTATE_FACTS", "mutates the Lips Like Sugar writer's TalentProfile.primary_nationality / nationality_resolution_status, evaluates and COMMITS, and restores the values in a finally block; writes up to three generations"),
}


def analyse(node_id: str, mods: dict) -> dict:
    path, _, test = node_id.partition("::")
    name = test.split("[")[0]
    m = mods.setdefault(path, Module(BACKEND / path))
    nodes = m.closure(name)
    fn = m.funcs[name]
    names, calls, strings, has_finally = set(), set(), [], False
    for top in nodes:
        for n in ast.walk(top):
            if isinstance(n, ast.Name):
                names.add(n.id)
            elif isinstance(n, ast.Call):
                callee = n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else None)
                if callee in {"add", "delete", "merge"} and isinstance(n.func, ast.Attribute) and not (isinstance(n.func.value, ast.Name) and n.func.value.id in {"db", "session", "s", "sess"}):
                    callee = None                                    # a set / list / dict method, not a database write
                if callee:
                    calls.add(callee)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                strings.append(n.value)
            elif isinstance(n, ast.Try) and n.finalbody:
                has_finally = True
    ids = {v for k, v in m.consts.items() if k in names and v in ANCHORS} | {s for s in strings if s in ANCHORS}
    if not ids and any("CURRENT_ACCEPTANCE_PROJECT_IDS" in n for n in names):
        ids = set(ANCHORS)
    evaluates = bool(calls & EVAL_NAMES)
    sql_writes = any(re.match(r"\s*(insert|update|delete)\b", s, re.I) for s in strings)
    writes = bool(calls & (WRITE_NAMES - {"execute", "flush"})) or sql_writes
    reads_only_builders = bool(calls & READ_BUILDERS)
    doc = ast.get_docstring(fn) or ""
    asserts = [ast.get_source_segment(m.src, n) for n in ast.walk(fn) if isinstance(n, ast.Assert)]
    intended = (doc.strip().split("\n")[0] if doc else "") or (asserts[0].replace("\n", " ")[:220] if asserts else "(no assert in the test body; the helpers it calls assert)")
    mutates_facts = sql_writes or any(re.search(r"\b(ProjectPerson|ProjectFact)\b", ast.get_source_segment(m.src, t) or "") and ("update(" in (ast.get_source_segment(m.src, t) or "") or "setattr" in (ast.get_source_segment(m.src, t) or "") or ".nationality =" in (ast.get_source_segment(m.src, t) or "")) for t in nodes)
    if evaluates and writes:
        category, can_reuse = "C_EVALUATE_AND_COMMIT", "only if the retained generation's input fingerprint equals the current one; the pricing digest modules changed in NA-RECONCILIATION-22..25, so a fingerprint mismatch is expected and a new generation WOULD be written"
    elif evaluates:
        category, can_reuse = "B_EVALUATE_IDEMPOTENT", "only if the retained generation's input fingerprint equals the current one (evaluate_project returns EVALUATION_REUSED); otherwise a new generation is written"
    elif writes:
        category, can_reuse = "D_MUTATE_FACTS", "not applicable: the control changes stored facts"
    else:
        category, can_reuse = "A_READ_ONLY_RETAINED", "yes: reads the retained generation / stored rows only (build_* with read_only or allow_retained)"
    manual = MANUAL.get(name)
    if manual:
        category, mutates_facts = manual[0], True
        can_reuse = "not applicable: the control changes a stored fact and writes generations"
    return {
        "manual_review": manual[1] if manual else None,
        "node_id": node_id, "anchors": sorted(ANCHORS[i] for i in ids) or ["(none named in the body; see the helper fixtures)"], "anchor_ids": sorted(ids), "intended_assertion": intended,
        "category": category, "read_only": category == "A_READ_ONLY_RETAINED", "calls_evaluation": evaluates, "writes_generation_or_fact": ("generation + stored fact" if (evaluates and mutates_facts) else None) or ("generation" if evaluates else None) or ("fact / row" if writes else None),
        "existing_retained_generation_can_satisfy": can_reuse, "restoration_in_a_finally_block": has_finally, "also_mutates_stored_facts": bool(mutates_facts),
        "calls": sorted(c for c in calls if c in EVAL_NAMES | WRITE_NAMES | READ_BUILDERS),
    }


def build() -> dict:
    mods: dict = {}
    rows = [analyse(n, mods) for n in controls()]
    order = {"A_READ_ONLY_RETAINED": 1, "B_EVALUATE_IDEMPOTENT": 2, "C_EVALUATE_AND_COMMIT": 3, "D_MUTATE_FACTS": 4}
    rows.sort(key=lambda r: (order[r["category"]], r["node_id"]))
    by_file: dict = {}
    for r in rows:
        by_file.setdefault(r["node_id"].split("::")[0], []).append(r)
    steps = []
    for cat, label in ((1, "A: read-only retained-state controls"), (2, "B: evaluate-idempotent controls (run only after step 0 shows the retained fingerprints equal the current ones)"),
                       (3, "C: controls that may create a generation"), (4, "D: controls that mutate and restore a fact")):
        files = sorted({r["node_id"].split("::")[0] for r in rows if order[r["category"]] == cat})
        steps.append({"step": cat, "label": label, "files": files, "controls": [r["node_id"] for r in rows if order[r["category"]] == cat]})
    return {
        "status": "PROPOSED - NOT EXECUTED - requires explicit user authorization",
        "controls": rows, "count": len(rows), "categories": {c: sum(1 for r in rows if r["category"] == c) for c in order},
        "requirements": {
            "database": "frametax2_claude_optimizer_acceptance_20260919 (the acceptance database named in .claude/launch.json): the only database that holds the four anchors. NOT touched by this pass.",
            "environment": ["DATABASE_URL pointing at that database (set explicitly by the authorizing user)", "CURRENT_ORGANIZATION_ID=<the acceptance organization id>",
                            "CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS=<comma-separated anchor ids actually needed by the step>", "PYTHONPATH=. ; the backend venv"],
            "timeout": "one pytest process per test file with a hard 720-second alarm (PROJECT_RULES long-running discipline); read-only files expected well under 120 seconds; evaluating files up to the alarm",
            "cleanup": "A: none. B/C: no cleanup possible for a written generation: record the generation id before and after (a new row is the expected side effect and must be authorized). D: verify the finally-block restoration and re-read the fact afterwards.",
            "authorization": "explicit, per step, by the user: the conftest write guard refuses any write naming an anchor unless CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS names it; do not lift it by registering, deselecting or renaming the tests.",
            "prohibited": ["registering or deselecting any of the 42", "copying anchors into the isolated test database", "creating fake anchor records", "changing node ids to make a control pass", "restarting the acceptance backend"],
        },
        "execution_order": [
            {"step": 0, "what": "Read-only preflight (no test run): for each anchor read the retained generation's engine version and input fingerprint and compare with the current fingerprint (GET /state with the retained-only guard). This decides whether B controls can reuse a generation or would write one."},
            *steps,
            {"step": 5, "what": "Stop after each step; report the exact pass/fail per node id; never rerun green controls."},
        ],
        "by_file": {f: [r["node_id"] for r in rs] for f, rs in by_file.items()},
    }


def render_md(m: dict) -> str:
    out = ["# Real-anchor acceptance manifest - PROPOSED, NOT EXECUTED (NA-RECONCILIATION-25)\n", "**Status: " + m["status"] + ".** Generated statically by `backend/scripts/real_anchor_manifest.py` (no database opened, nothing evaluated, none of the 42 controls run). "
           "The 42 controls remain OPEN, unregistered and unmodified; they stop before their intended assertion because the isolated `frametax2_pytest` database does not contain the four anchors.\n",
           "## Requirements common to every step\n"]
    for k, v in m["requirements"].items():
        out.append(f"- **{k}:** " + (v if isinstance(v, str) else "; ".join(v)))
    out.append("\n## Categories\n")
    for c, n in m["categories"].items():
        out.append(f"- `{c}`: {n}")
    out.append("\n## Smallest safe execution order (do not execute without authorization)\n")
    for s in m["execution_order"]:
        if "what" in s:
            out.append(f"{s['step']}. {s['what']}")
        else:
            out.append(f"{s['step']}. **{s['label']}** - files: {', '.join('`' + f + '`' for f in s['files']) or 'none'} ({len(s['controls'])} controls)")
    out.append("\n## Controls\n")
    out.append("| Node id | Anchors | Intended assertion | Category | Read-only | Calls evaluation | Writes | Mutates stored facts | Retained generation can satisfy | Restoration (finally) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in m["controls"]:
        out.append("| " + " | ".join([f"`{r['node_id']}`", "; ".join(r["anchors"]).replace("|", "/"), r["intended_assertion"].replace("|", "/").replace("\n", " ")[:200], r["category"], "yes" if r["read_only"] else "no",
                                       "yes" if r["calls_evaluation"] else "no", r["writes_generation_or_fact"] or "no", "yes" if r["also_mutates_stored_facts"] else "no", r["existing_retained_generation_can_satisfy"].replace("|", "/"), "yes" if r["restoration_in_a_finally_block"] else "no"]) + " |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    manifest = build()
    (OUT / f"{STEM}.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    (OUT / f"{STEM}.md").write_text(render_md(manifest))
    print(manifest["count"], manifest["categories"])
