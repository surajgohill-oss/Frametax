"""
Cross-Model Bridge internal CLI (click-based — click is already an
installed dependency of this project via other libraries, now a direct
one; no new CLI framework introduced).

Run from backend/: `python -m app.bridge.cli <command>`

This CLI is internal development infrastructure — it is not wired into
any producer-facing surface.
"""
from __future__ import annotations

import asyncio
import json

import click


@click.group()
def cli():
    """CineGlobe Cross-Model Bridge — internal CLI."""


@cli.command("provider-status")
def provider_status_cmd():
    """List CONFIGURED/NOT_CONFIGURED/DISABLED for each provider — never prints a key."""
    from app.bridge.secrets import all_provider_statuses
    click.echo(json.dumps(all_provider_statuses(), indent=2))


@cli.command("model-aliases")
def model_aliases_cmd():
    """List configured model alias -> model ID resolutions."""
    from app.bridge.config import get_bridge_settings
    settings = get_bridge_settings()
    aliases = {
        f.removeprefix("BRIDGE_MODEL_").lower(): getattr(settings, f)
        for f in type(settings).model_fields if f.startswith("BRIDGE_MODEL_")
    }
    click.echo(json.dumps(aliases, indent=2))


@cli.command("create-package")
@click.option("--operation", required=True, help="OperationType value, e.g. qualification_audit")
@click.option("--structure-id", default=None, help="Structure ID; defaults to the ranked leader")
@click.option("--confidentiality", default="internal", help="safe | internal | confidential")
def create_package_cmd(operation: str, structure_id: str | None, confidentiality: str):
    """Build a real AuditPackage from the served CineGlobe pipeline and persist it."""
    from app.bridge.package_builder import build_package
    from app.bridge.persistence import PackageRecord, get_session
    from app.bridge.schema import ConfidentialityClassification, OperationType

    pkg = build_package(
        operation=OperationType(operation),
        confidentiality=ConfidentialityClassification(confidentiality),
        structure_id=structure_id,
    )
    session = get_session()
    try:
        session.add(PackageRecord(
            package_id=pkg.package_id, package_schema_version=pkg.package_schema_version,
            production_or_scenario_id=pkg.production_or_scenario_id, operation=pkg.operation.value,
            confidentiality=pkg.confidentiality.value, repository_commit=pkg.repository_commit,
            generated_at=pkg.generated_at, package_json=pkg.model_dump_json(),
        ))
        session.commit()
    finally:
        session.close()
    click.echo(json.dumps({"package_id": pkg.package_id, "size_bytes": pkg.size_bytes()}, indent=2))


@cli.command("preview-package")
@click.argument("package_id")
@click.option("--authorized", is_flag=True, default=False)
def preview_package_cmd(package_id: str, authorized: bool):
    """Dry-run: exactly what would be sent for this package, with every safety check applied."""
    from app.bridge.persistence import PackageRecord, get_session
    from app.bridge.redaction import preview_outbound_package
    from app.bridge.schema import AuditPackage

    session = get_session()
    try:
        row = session.get(PackageRecord, package_id)
        if row is None:
            raise click.ClickException(f"No package {package_id}")
        pkg = AuditPackage.model_validate_json(row.package_json)
    finally:
        session.close()
    preview = preview_outbound_package(pkg, authorized=authorized)
    click.echo(json.dumps({
        "package_id": preview.package_id, "confidentiality": preview.confidentiality.value,
        "size_bytes": preview.size_bytes, "within_size_limit": preview.within_size_limit,
        "secret_findings": len(preview.secret_findings),
        "requires_authorization": preview.requires_authorization,
        "safe_to_send": preview.safe_to_send,
    }, indent=2))


@cli.command("dispatch")
@click.argument("package_id")
@click.option("--provider", multiple=True, help="Repeatable: anthropic | openai | gemini. Omit to dispatch all configured.")
@click.option("--operation", required=True)
@click.option("--model-alias", default="fast_research")
def dispatch_cmd(package_id: str, provider: tuple[str, ...], operation: str, model_alias: str):
    """Dispatch a package to one, several, or all configured providers independently."""
    asyncio.run(_dispatch_async(package_id, provider, operation, model_alias))


async def _dispatch_async(package_id, providers, operation, model_alias):
    from app.bridge.adapters.base import get_adapter
    from app.bridge.config import get_bridge_settings
    from app.bridge.persistence import PackageRecord, ProviderResponseRecord, get_session
    from app.bridge.schema import (
        REVIEW_RESPONSE_JSON_SCHEMA, AuditPackage, ModelRequest, OperationType, ProviderID, new_id,
    )
    from app.bridge.secrets import all_provider_statuses

    settings = get_bridge_settings()
    session = get_session()
    try:
        row = session.get(PackageRecord, package_id)
        if row is None:
            raise click.ClickException(f"No package {package_id}")
        pkg = AuditPackage.model_validate_json(row.package_json)

        statuses = all_provider_statuses()
        targets = list(providers) or [p for p, s in statuses.items() if s == "configured"]
        results = {}
        for p in targets:
            pid = ProviderID(p)
            if statuses[p] != "configured":
                results[p] = {"status": statuses[p], "note": "not dispatched — not configured"}
                continue
            model_id = settings.resolve_provider_alias(p, model_alias)
            request = ModelRequest(
                provider=pid, model_id=model_id, operation=OperationType(operation),
                system_instruction=f"Audit this CineGlobe {operation} package for defects. Cite real evidence only.",
                structured_input=pkg.model_dump(mode="json"),
                required_response_schema=REVIEW_RESPONSE_JSON_SCHEMA,
            )
            adapter = get_adapter(pid)
            response = await adapter.send(request)
            session.add(ProviderResponseRecord(
                response_id=new_id("resp"), package_id=package_id, provider=p, model_id=model_id,
                operation=operation, request_json=request.model_dump_json(),
                response_text=response.response_text,
                parsed_response_json=json.dumps(response.parsed_response) if response.parsed_response else None,
                usage_json=json.dumps(response.usage), provider_request_id=response.provider_request_id,
                latency_ms=response.latency_ms, error_category=response.error_category.value,
                error_message=response.error_message, fallback_used=response.fallback_used,
                request_content_hash=request.content_hash(),
            ))
            results[p] = {"status": "dispatched", "error_category": response.error_category.value,
                          "ok": response.ok, "latency_ms": response.latency_ms}
        session.commit()
    finally:
        session.close()
    click.echo(json.dumps(results, indent=2))


@cli.command("ledger")
@click.option("--seed", is_flag=True, default=False)
def ledger_cmd(seed: bool):
    """Print (and optionally seed) the canonical project ledger."""
    from app.bridge.ledger import current_ledger, seed_ledger
    if seed:
        n = seed_ledger()
        click.echo(f"# seeded {n} new entries", err=True)
    for entry in current_ledger():
        click.echo(f"[{entry.kind:12}] {entry.status.value:28} {entry.entry_id}: {entry.title}")


@cli.command("provenance")
@click.option("--summary-only", is_flag=True, default=False)
def provenance_cmd(summary_only: bool):
    """Print the rule-provenance matrix (or just its summary counts)."""
    from app.bridge.provenance import build_provenance_matrix, hard_gate_unknown_programs, provenance_summary
    matrix = build_provenance_matrix()
    click.echo(json.dumps(provenance_summary(matrix), indent=2))
    if not summary_only:
        gaps = hard_gate_unknown_programs(matrix)
        click.echo(f"\n{len(gaps)} program(s) with >=1 unknown hard gate field.")


@cli.command("missing-requirements")
@click.option("--limit", default=10)
def missing_requirements_cmd(limit: int):
    """List executable programs still missing a requirements profile."""
    from app.bridge.requirements_workflow import select_missing_programs
    for t in select_missing_programs(limit=limit):
        click.echo(f"{t.jurisdiction_code}\t{t.program_slug}")


# ── Manual / file-based mode — no paid API call in any of these three ──

@cli.command("export-run")
@click.option("--operation", required=True, help="OperationType value, e.g. qpe_audit")
@click.option("--structure-id", default=None, help="Structure ID; defaults to the ranked leader")
@click.option("--confidentiality", default="internal", help="safe | internal | confidential")
@click.option("--production-id", default="little-utopia")
def export_run_cmd(operation: str, structure_id: str | None, confidentiality: str, production_id: str):
    """Export a portable .bridge_runs/<package_id>/ directory — package.json
    + instructions.md + an empty responses/ — for independent review by
    Claude/Codex/Gemini outside this codebase. No provider is called."""
    from app.bridge.manual_run import export_run
    from app.bridge.schema import ConfidentialityClassification, OperationType

    run_dir = export_run(
        operation=OperationType(operation), structure_id=structure_id,
        confidentiality=ConfidentialityClassification(confidentiality),
        production_or_scenario_id=production_id,
    )
    click.echo(json.dumps({"run_dir": str(run_dir)}, indent=2))


@cli.command("import-response")
@click.argument("run_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--provider", required=True, type=click.Choice(["anthropic", "openai", "gemini"]))
@click.argument("response_path", type=click.Path(exists=True, dir_okay=False))
def import_response_cmd(run_dir: str, provider: str, response_path: str):
    """Validate and import one completed response JSON file into the run's
    responses/ directory and the existing ProviderResponseRecord table."""
    from pathlib import Path
    from app.bridge.manual_run import ManualRunError, import_response
    from app.bridge.schema import ProviderID

    try:
        response = import_response(Path(run_dir), ProviderID(provider), Path(response_path))
    except ManualRunError as exc:
        raise click.ClickException(str(exc))
    click.echo(json.dumps({
        "imported": True, "provider": provider, "review_id": response.review_id,
        "overall_disposition": response.overall_disposition.value, "findings": len(response.findings),
    }, indent=2))


@cli.command("reconcile-run")
@click.argument("run_dir", type=click.Path(exists=True, file_okay=False))
def reconcile_run_cmd(run_dir: str):
    """Run the existing reconciliation.reconcile() over every response file
    present in run_dir/responses/ and write reconciliation.json. Never
    modifies any CineGlobe rule/calculation/optimizer state."""
    from pathlib import Path
    from app.bridge.manual_run import ManualRunError, reconcile_run

    try:
        result = reconcile_run(Path(run_dir))
    except ManualRunError as exc:
        raise click.ClickException(str(exc))
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()
