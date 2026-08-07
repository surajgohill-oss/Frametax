"""
Manual / file-based Bridge mode (spec: "Manual Multi-Model Bridge
Enablement"). Lets a validation package be exported to a self-contained
directory, independently reviewed by Claude/Codex/Gemini WITHOUT any
paid API call from this codebase, and the resulting response JSON files
imported back into the existing persistence/reconciliation path.

This is NOT a second Bridge. It reuses, unchanged:
  - package_builder.build_package()   — the one real package source
  - schema.py's AuditPackage / ReviewResponse / REVIEW_RESPONSE_JSON_SCHEMA
  - reconciliation.py's reconcile() / suggest_disposition()
  - persistence.py's ProviderResponseRecord / ReconciliationClusterRecord

Directory layout, one per run (run_id == the content-derived package_id):

    .bridge_runs/<package_id>/
        package.json        — the exact AuditPackage, unmodified
        instructions.md      — one canonical instruction, self-contained
        responses/
            claude.json       — Anthropic's response (filename is fixed —
            openai.json       — not provider-name-derived — so every run
            gemini.json       — has the same three expected filenames)
        reconciliation.json  — written by reconcile_run()

Nothing here ever calls a provider adapter or reads a provider API key —
that stays exactly as implemented (adapters/*.py), untouched.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.bridge.package_builder import build_package
from app.bridge.persistence import (
    PackageRecord, ProviderResponseRecord, ReconciliationClusterRecord, get_session,
)
from app.bridge.reconciliation import reconcile, suggest_disposition
from app.bridge.schema import (
    REVIEW_RESPONSE_JSON_SCHEMA, AuditPackage, ConfidentialityClassification,
    OperationType, ProviderID, ReviewResponse, new_id,
)

RUNS_ROOT = Path("./.bridge_runs")

# Fixed, provider-labeled filenames — every run has the same three expected
# response paths regardless of which providers actually respond, so
# "give this run to Claude, it writes responses/claude.json" never needs
# per-run instructions of its own.
_RESPONSE_FILENAME = {
    ProviderID.ANTHROPIC: "claude.json",
    ProviderID.OPENAI: "openai.json",
    ProviderID.GEMINI: "gemini.json",
}
_FILENAME_TO_PROVIDER = {v: k for k, v in _RESPONSE_FILENAME.items()}


class ManualRunError(ValueError):
    """Raised on malformed/mismatched input — never silently coerced."""


def _instructions_md(pkg: AuditPackage) -> str:
    schema_json = json.dumps(REVIEW_RESPONSE_JSON_SCHEMA, indent=2)
    filenames = ", ".join(f"`responses/{f}`" for f in _RESPONSE_FILENAME.values())
    return f"""# CineGlobe Bridge Validation Run — {pkg.package_id}

You are independently reviewing ONE CineGlobe production-economics package.
This is a validation/research task. You are NOT asked to recompute the
production's economics from scratch, replace CineGlobe's deterministic
optimizer, or produce a new number to substitute for its result — you are
auditing the CALCULATION CineGlobe already produced, using ONLY the facts,
rules, and evidence supplied in `package.json` (same directory as this file).

Operation: **{pkg.operation.value}**
Production/scenario: **{pkg.production_or_scenario_id}**
Package ID: **{pkg.package_id}**

## What to do

1. Independently evaluate the calculation described in `package.json`
   (section F, `economics`) against its own inputs (sections B–E).
2. For `qpe_audit` specifically: evaluate `budget_qpe_trace` line by line —
   for each line, does its `included_in_qpe` value and `exclusion_authority`
   (if any) look correct given the line's own `normalized_category`,
   `component`, and `jurisdiction_code`?
3. State explicitly whether you AGREE or DISAGREE with each part of
   CineGlobe's result you review. Do not stay silent on agreement — a
   confirmed-correct line is itself a useful finding.
4. Distinguish conclusions you can support directly from the supplied
   `evidence` (section G) from conclusions that are your own inference.
   Say which is which.
5. Cite the specific supplied evidence/rule you relied on (by
   `source_title` from section G, or by the specific budget line/field you
   examined) for every finding — never a bare assertion.
6. If a fact you would need is simply not present in `package.json`,
   say so as an `unresolved_question` or an `insufficient_evidence`
   finding. NEVER invent a fact, rate, source, or number that is not in
   the package.
7. Return ONLY a single JSON object matching the schema below — no prose
   before or after, no markdown code fence — as your ENTIRE response,
   saved to your assigned response file: {filenames} (use the ONE file
   matching which model you are).

## Required response JSON Schema

This is generated directly from CineGlobe's own `ReviewResponse` pydantic
model — your output will be validated against this exact schema on import.

```json
{schema_json}
```

## Required top-level fields on your response

- `review_id`: any unique string you generate (e.g. `"review_" + a short id`)
- `package_id`: **must equal** `"{pkg.package_id}"` exactly — this is how
  your response is matched back to this run
- `provider`: one of `"anthropic"` | `"openai"` | `"gemini"` — use the one
  that matches which model you are (Claude → `"anthropic"`, ChatGPT/Codex →
  `"openai"`, Gemini → `"gemini"`)
- `model`: your own model name/version string, whatever you know it to be
- `operation`: `"{pkg.operation.value}"`

## What NOT to do

- Do not fabricate a source, statute citation, or rate not present in
  `package.json`.
- Do not "fix" the number and present it as the new answer — report a
  disagreement as a `finding` with `classification` and `expected_result`/
  `observed_result`; a human reviews and dispositions it afterward.
- Do not omit `package_id` or use a different one.
"""


def export_run(
    *,
    operation: OperationType,
    structure_id: str | None = None,
    confidentiality: ConfidentialityClassification = ConfidentialityClassification.INTERNAL,
    production_or_scenario_id: str = "little-utopia",
    runs_root: Path = RUNS_ROOT,
) -> Path:
    """Builds the real AuditPackage via the existing package_builder (no
    duplicate schema/logic), persists it exactly as the HTTP/CLI dispatch
    paths already do, and writes the portable run directory."""
    pkg = build_package(
        operation=operation, confidentiality=confidentiality,
        structure_id=structure_id, production_or_scenario_id=production_or_scenario_id,
    )

    session = get_session()
    try:
        existing = session.get(PackageRecord, pkg.package_id)
        if existing is None:
            session.add(PackageRecord(
                package_id=pkg.package_id, package_schema_version=pkg.package_schema_version,
                production_or_scenario_id=pkg.production_or_scenario_id, operation=pkg.operation.value,
                confidentiality=pkg.confidentiality.value, repository_commit=pkg.repository_commit,
                generated_at=pkg.generated_at, package_json=pkg.model_dump_json(),
            ))
            session.commit()
    finally:
        session.close()

    run_dir = runs_root / pkg.package_id
    (run_dir / "responses").mkdir(parents=True, exist_ok=True)
    (run_dir / "package.json").write_text(pkg.model_dump_json(indent=2))
    (run_dir / "instructions.md").write_text(_instructions_md(pkg))
    return run_dir


def import_response(run_dir: Path, provider: ProviderID, source_path: Path) -> ReviewResponse:
    """Validates a completed response JSON file against ReviewResponse and
    the run's own package_id, copies it to the run's canonical
    responses/<provider>.json, and persists it via the SAME
    ProviderResponseRecord table the live dispatch path writes to."""
    pkg = _load_package(run_dir)

    if not source_path.is_file():
        raise ManualRunError(f"No such response file: {source_path}")
    try:
        raw = json.loads(source_path.read_text())
    except json.JSONDecodeError as exc:
        raise ManualRunError(f"{source_path}: not valid JSON — {exc}") from exc

    try:
        response = ReviewResponse.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError — reported verbatim, never coerced
        raise ManualRunError(f"{source_path}: does not match ReviewResponse schema — {exc}") from exc

    if response.provider != provider:
        raise ManualRunError(
            f"{source_path}: response.provider={response.provider.value!r} does not match "
            f"the declared provider {provider.value!r} for this import."
        )
    if response.package_id != pkg.package_id:
        raise ManualRunError(
            f"{source_path}: response.package_id={response.package_id!r} does not match "
            f"this run's package_id {pkg.package_id!r} — wrong run, not imported."
        )

    dest = run_dir / "responses" / _RESPONSE_FILENAME[provider]
    dest.write_text(response.model_dump_json(indent=2))

    session = get_session()
    try:
        session.add(ProviderResponseRecord(
            response_id=new_id("resp"), package_id=pkg.package_id, provider=provider.value,
            model_id=response.model, operation=response.operation.value,
            request_json=json.dumps({"manual_import": True, "source_path": str(source_path)}),
            response_text=response.model_dump_json(),
            parsed_response_json=response.model_dump_json(),
            usage_json=json.dumps(response.usage_metadata),
            provider_request_id=None, latency_ms=None,
            error_category="none", error_message=None, fallback_used=False,
            request_content_hash=new_id("manual", pkg.package_id, provider.value, response.review_id),
        ))
        session.commit()
    finally:
        session.close()
    return response


def _load_package(run_dir: Path) -> AuditPackage:
    package_path = run_dir / "package.json"
    if not package_path.is_file():
        raise ManualRunError(f"No package.json in {run_dir} — export the run first.")
    return AuditPackage.model_validate_json(package_path.read_text())


def _load_available_responses(run_dir: Path) -> list[ReviewResponse]:
    responses = []
    for filename in _RESPONSE_FILENAME.values():
        path = run_dir / "responses" / filename
        if path.is_file():
            responses.append(ReviewResponse.model_validate_json(path.read_text()))
    return responses


def reconcile_run(run_dir: Path) -> dict[str, Any]:
    """Loads every response file present (1, 2, or 3 — never requires all
    three), runs the existing reconcile()/suggest_disposition(), persists
    clusters via ReconciliationClusterRecord, and writes reconciliation.json.
    Never writes a human disposition itself (record_disposition() still
    requires an explicit human actor — this only surfaces a SUGGESTION)."""
    pkg = _load_package(run_dir)
    responses = _load_available_responses(run_dir)
    if not responses:
        raise ManualRunError(f"No response files found in {run_dir / 'responses'} — import at least one first.")

    clusters = reconcile(pkg.package_id, responses)

    session = get_session()
    try:
        for cluster in clusters:
            session.add(ReconciliationClusterRecord(
                cluster_id=cluster.cluster_id, package_id=cluster.package_id,
                jurisdiction_or_program=cluster.jurisdiction_or_program,
                agreement_kind=cluster.agreement_kind.value, cluster_json=cluster.model_dump_json(),
            ))
        session.commit()
    finally:
        session.close()

    out = {
        "package_id": pkg.package_id,
        "operation": pkg.operation.value,
        "production_or_scenario_id": pkg.production_or_scenario_id,
        "cineglobe_deterministic_result": pkg.economics.model_dump(mode="json"),
        "providers_reviewed": sorted({r.provider.value for r in responses}),
        "provider_conclusions": [
            {
                "provider": r.provider.value, "model": r.model,
                "overall_disposition": r.overall_disposition.value,
                "executive_summary": r.executive_summary,
                "finding_count": len(r.findings),
            }
            for r in responses
        ],
        "consensus": [
            {
                "cluster_id": c.cluster_id, "jurisdiction_or_program": c.jurisdiction_or_program,
                "agreement_kind": c.agreement_kind.value, "member_finding_ids": c.member_finding_ids,
                "suggested_disposition": suggest_disposition(c, responses).value,
            }
            for c in clusters
        ],
        "unresolved_questions": sorted({q for r in responses for q in r.unresolved_questions}),
        "note": (
            "Consensus/suggested_disposition above is evidence for human review only. "
            "It does NOT modify any CineGlobe rule, calculation, or optimizer output. "
            "A real disposition requires reconciliation.record_disposition() with an "
            "explicit human actor — not performed by this export."
        ),
    }
    (run_dir / "reconciliation.json").write_text(json.dumps(out, indent=2))
    return out
