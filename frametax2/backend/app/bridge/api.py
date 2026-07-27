"""
Cross-Model Bridge internal API (spec section 12).

Mounted at /api/v1/bridge in app/main.py — a distinct, clearly-namespaced
prefix. NOT linked from frontend/src/api.js and NOT called by any
producer-facing screen. This is internal development infrastructure,
same status as the CLI in cli.py (which every route here delegates to
the same underlying bridge modules as, so behavior is identical either
way you drive it).
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/bridge", tags=["bridge-internal"])


@router.get("/providers")
async def get_provider_status() -> dict[str, str]:
    from app.bridge.secrets import all_provider_statuses
    return all_provider_statuses()


@router.get("/model-aliases")
async def get_model_aliases() -> dict[str, str]:
    from app.bridge.config import get_bridge_settings
    settings = get_bridge_settings()
    return {
        f.removeprefix("BRIDGE_MODEL_").lower(): getattr(settings, f)
        for f in type(settings).model_fields if f.startswith("BRIDGE_MODEL_")
    }


class CreatePackageRequest(BaseModel):
    operation: str
    structure_id: str | None = None
    confidentiality: str = "internal"


@router.post("/packages")
async def create_package(body: CreatePackageRequest) -> dict[str, Any]:
    from app.bridge.package_builder import build_package
    from app.bridge.persistence import PackageRecord, get_session
    from app.bridge.schema import ConfidentialityClassification, OperationType

    try:
        pkg = build_package(
            operation=OperationType(body.operation),
            confidentiality=ConfidentialityClassification(body.confidentiality),
            structure_id=body.structure_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

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
    return {"package_id": pkg.package_id, "size_bytes": pkg.size_bytes()}


def _load_package(package_id: str):
    from app.bridge.persistence import PackageRecord, get_session
    from app.bridge.schema import AuditPackage

    session = get_session()
    try:
        row = session.get(PackageRecord, package_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"No package {package_id}")
        return AuditPackage.model_validate_json(row.package_json)
    finally:
        session.close()


@router.get("/packages/{package_id}/preview")
async def preview_package(package_id: str, authorized: bool = False) -> dict[str, Any]:
    from app.bridge.redaction import preview_outbound_package

    pkg = _load_package(package_id)
    preview = preview_outbound_package(pkg, authorized=authorized)
    return {
        "package_id": preview.package_id, "confidentiality": preview.confidentiality.value,
        "size_bytes": preview.size_bytes, "within_size_limit": preview.within_size_limit,
        "secret_findings": [{"path": f.path, "reason": f.reason} for f in preview.secret_findings],
        "requires_authorization": preview.requires_authorization,
        "safe_to_send": preview.safe_to_send,
    }


class DispatchRequest(BaseModel):
    providers: list[str] = []  # empty = all configured
    operation: str
    model_alias: str = "fast_research"


@router.post("/packages/{package_id}/dispatch")
async def dispatch_package(package_id: str, body: DispatchRequest) -> dict[str, Any]:
    from app.bridge.adapters.base import get_adapter
    from app.bridge.config import get_bridge_settings
    from app.bridge.persistence import ProviderResponseRecord, get_session
    from app.bridge.schema import REVIEW_RESPONSE_JSON_SCHEMA, ModelRequest, OperationType, ProviderID, new_id
    from app.bridge.secrets import all_provider_statuses

    pkg = _load_package(package_id)
    settings = get_bridge_settings()
    statuses = all_provider_statuses()
    targets = body.providers or [p for p, s in statuses.items() if s == "configured"]

    session = get_session()
    results: dict[str, Any] = {}
    try:
        for p in targets:
            if statuses.get(p) != "configured":
                results[p] = {"status": statuses.get(p, "unknown"), "note": "not dispatched — not configured"}
                continue
            pid = ProviderID(p)
            model_id = settings.resolve_provider_alias(p, body.model_alias)
            request = ModelRequest(
                provider=pid, model_id=model_id, operation=OperationType(body.operation),
                system_instruction=f"Audit this CineGlobe {body.operation} package for defects. Cite real evidence only.",
                structured_input=pkg.model_dump(mode="json"),
                required_response_schema=REVIEW_RESPONSE_JSON_SCHEMA,
            )
            response = await get_adapter(pid).send(request)
            session.add(ProviderResponseRecord(
                response_id=new_id("resp"), package_id=package_id, provider=p, model_id=model_id,
                operation=body.operation, request_json=request.model_dump_json(),
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
    return results


@router.get("/packages/{package_id}/responses")
async def list_responses(package_id: str) -> list[dict[str, Any]]:
    from app.bridge.persistence import ProviderResponseRecord, get_session

    session = get_session()
    try:
        rows = session.query(ProviderResponseRecord).filter(
            ProviderResponseRecord.package_id == package_id
        ).all()
        return [{
            "response_id": r.response_id, "provider": r.provider, "model_id": r.model_id,
            "error_category": r.error_category, "latency_ms": r.latency_ms,
            "usage": json.loads(r.usage_json) if r.usage_json else {},
            "created_at": r.created_at.isoformat(),
        } for r in rows]
    finally:
        session.close()


@router.get("/ledger")
async def get_ledger() -> list[dict[str, Any]]:
    from app.bridge.ledger import current_ledger
    return [e.model_dump(mode="json") for e in current_ledger()]


@router.post("/ledger/seed")
async def seed_ledger_endpoint() -> dict[str, int]:
    from app.bridge.ledger import seed_ledger
    return {"written": seed_ledger()}


@router.get("/provenance")
async def get_provenance(summary_only: bool = True) -> dict[str, Any]:
    from app.bridge.provenance import build_provenance_matrix, hard_gate_unknown_programs, provenance_summary

    matrix = build_provenance_matrix()
    out: dict[str, Any] = {"summary": provenance_summary(matrix)}
    if not summary_only:
        out["records"] = [r.model_dump(mode="json") for r in matrix]
        out["hard_gate_unknown_programs"] = hard_gate_unknown_programs(matrix)
    return out


@router.get("/requirements/missing")
async def get_missing_requirements(limit: int = 20) -> list[dict[str, str]]:
    from app.bridge.requirements_workflow import select_missing_programs
    return [
        {"program_slug": t.program_slug, "jurisdiction_code": t.jurisdiction_code}
        for t in select_missing_programs(limit=limit)
    ]


@router.get("/usage")
async def get_usage_ledger(limit: int = 100) -> list[dict[str, Any]]:
    from app.bridge.persistence import ProviderResponseRecord, get_session

    session = get_session()
    try:
        rows = (
            session.query(ProviderResponseRecord)
            .order_by(ProviderResponseRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [{
            "provider": r.provider, "model_id": r.model_id, "operation": r.operation,
            "error_category": r.error_category, "latency_ms": r.latency_ms,
            "usage": json.loads(r.usage_json) if r.usage_json else {},
            "created_at": r.created_at.isoformat(),
        } for r in rows]
    finally:
        session.close()
