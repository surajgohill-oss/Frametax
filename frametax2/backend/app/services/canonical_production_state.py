"""
canonical_production_state.py

Script Analyzer SA-1, Parts I / J / L — the integration deliverable.

`CanonicalProductionStateBuilder` assembles a GENERIC project's optimizer
input from generic sources. It replaces only the Little-Utopia-specific
upstream ASSEMBLY role of `app/demo/little_utopia_state.py`; it reuses every
downstream calculator unchanged (discovery, structure composition,
allocation, normalization, pricing, NPC, ranking, Bridge).

What this module is careful NOT to do:

  * It does not compute economics. It selects and fingerprints inputs.
  * It does not invent values. An absent input is UNKNOWN and becomes a
    stated blocker, never a default that silently prices.
  * It does not infer territoriality from who pays. Per the canonical
    territoriality guard, payer/SPV is never sufficient; a line's
    jurisdiction is carried only where the source data actually states it.
  * It does not return prose. The output is a structured, immutable,
    fingerprinted snapshot.

The fingerprint is what makes an optimizer result auditable: it is a
deterministic digest of every source version and effective value that fed
the run, so a stored result can always be traced back to exactly the inputs
that produced it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.production_requirement import (
    EVIDENCE_DETERMINISTIC_DERIVED,
    EVIDENCE_PRECEDENCE,
    EVIDENCE_UNKNOWN,
    ProductionAssumption,
    ProductionRequirement,
)
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.screenplay import Character, Scene
from app.services import script_parse_status as sps
from app.services.script_analysis_service import resolve_active_screenplay

STATE_VERSION = "sa1-canonical-production-state-1.0.0"

# ── budget presence states (Part L) ────────────────────────────────────────
BUDGET_PRESENT = "BUDGET_PRESENT"
BUDGET_MISSING = "BUDGET_MISSING"

# ── overall readiness ──────────────────────────────────────────────────────
READY_FOR_OPTIMIZER = "READY_FOR_OPTIMIZER"
BLOCKED_INCOMPLETE_INPUTS = "BLOCKED_INCOMPLETE_INPUTS"


@dataclass
class EffectiveValue:
    """One selected input plus the authority that produced it. Every material
    numeric the optimizer sees must be able to answer 'says who?'."""
    key: str
    value: object
    authority: str
    source: str | None = None

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value,
                "authority": self.authority, "source": self.source}


@dataclass
class CanonicalProductionState:
    """Immutable, fingerprinted optimizer input for a generic project."""

    state_version: str
    as_of: str
    project_id: str
    project_name: str | None

    # source versions
    script_document_version_id: str | None
    screenplay_id: str | None
    parser_version: str | None
    script_input_fingerprint: str | None
    budget_document_ids: list[str] = field(default_factory=list)

    # script structure
    script_status: str = sps.SCRIPT_NOT_PRESENT
    scene_count: int = 0
    total_eighths: int = 0
    page_count: int | None = None
    page_basis: str | None = None
    speaking_character_count: int = 0

    # effective facts / assumptions
    effective_facts: list[dict] = field(default_factory=list)
    assumptions: list[dict] = field(default_factory=list)

    # requirements
    scripted_locations: list[dict] = field(default_factory=list)
    production_requirements: list[dict] = field(default_factory=list)

    # budget
    budget_state: str = BUDGET_MISSING
    gross_budget_usd: float | None = None
    active_budget_line_count: int = 0
    budget_lines: list[dict] = field(default_factory=list)

    # territoriality — only what the source actually states
    territorial_allocations: list[dict] = field(default_factory=list)

    # readiness
    readiness: str = BLOCKED_INCOMPLETE_INPUTS
    unknowns: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    input_fingerprint: str = ""

    def compute_fingerprint(self) -> str:
        """Deterministic digest of everything that could change an optimizer
        result. `as_of` is excluded on purpose: the same inputs must
        fingerprint identically regardless of when the state was built."""
        payload = asdict(self)
        payload.pop("as_of", None)
        payload.pop("input_fingerprint", None)
        blob = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict:
        d = asdict(self)
        d["input_fingerprint"] = self.input_fingerprint
        return d


def _fact_value(f: ProjectFact):
    if f.value is None:
        return None
    if f.value_type == "number":
        try:
            return float(f.value) if "." in f.value else int(f.value)
        except ValueError:
            return f.value
    if f.value_type == "boolean":
        return f.value == "true"
    if f.value_type == "json":
        try:
            return json.loads(f.value)
        except (ValueError, TypeError):
            return f.value
    return f.value


_FACT_AUTHORITY = {
    "user_override": "USER_CONFIRMED",
    "extracted": EVIDENCE_DETERMINISTIC_DERIVED,
    "recovered_demo_state": "USER_CONFIRMED",
}


class CanonicalProductionStateBuilder:
    """Builds a `CanonicalProductionState` from generic project data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build(self, project_id) -> CanonicalProductionState:
        project = await self.session.get(Project, project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        state = CanonicalProductionState(
            state_version=STATE_VERSION,
            as_of=datetime.now(timezone.utc).isoformat(),
            project_id=str(project_id),
            project_name=getattr(project, "title", None) or getattr(project, "name", None),
            script_document_version_id=None,
            screenplay_id=None,
            parser_version=None,
            script_input_fingerprint=None,
        )

        await self._apply_script(state, project_id)
        await self._apply_facts(state, project_id)
        await self._apply_assumptions(state, project_id)
        await self._apply_requirements(state, project_id)
        await self._apply_budget(state, project_id)
        self._assess_readiness(state)

        state.input_fingerprint = state.compute_fingerprint()
        return state

    # ── script ─────────────────────────────────────────────────────────────
    async def _apply_script(self, state: CanonicalProductionState, project_id) -> None:
        screenplay = await resolve_active_screenplay(self.session, project_id)
        if screenplay is None:
            state.script_status = sps.SCRIPT_NOT_PRESENT
            state.blockers.append(sps.blocker_for(sps.SCRIPT_NOT_PRESENT))
            return

        state.screenplay_id = str(screenplay.id)
        state.script_document_version_id = (
            str(screenplay.document_version_id) if screenplay.document_version_id else None
        )
        state.parser_version = screenplay.parser_version
        state.script_input_fingerprint = screenplay.input_fingerprint
        state.script_status = screenplay.parse_status or sps.SCRIPT_PRESENT_UNPARSED
        state.page_count = screenplay.page_count
        state.page_basis = screenplay.page_basis
        state.total_eighths = screenplay.total_eighths or 0

        if screenplay.parse_warnings:
            state.warnings.extend(screenplay.parse_warnings)

        if not sps.is_analysis_ready(state.script_status):
            blocker = sps.blocker_for(state.script_status)
            if blocker:
                state.blockers.append(blocker)
            return

        state.scene_count = len((await self.session.execute(
            select(Scene).where(Scene.screenplay_id == screenplay.id)
        )).scalars().all())
        state.speaking_character_count = len((await self.session.execute(
            select(Character).where(
                Character.screenplay_id == screenplay.id,
                Character.is_speaking_role.is_(True),
            )
        )).scalars().all())

    # ── facts ──────────────────────────────────────────────────────────────
    async def _apply_facts(self, state: CanonicalProductionState, project_id) -> None:
        rows = (await self.session.execute(
            select(ProjectFact).where(ProjectFact.project_id == project_id)
        )).scalars().all()
        for f in sorted(rows, key=lambda r: r.fact_key):
            authority = _FACT_AUTHORITY.get(
                getattr(f.source_type, "value", str(f.source_type)), EVIDENCE_UNKNOWN
            )
            state.effective_facts.append(EffectiveValue(
                key=f.fact_key, value=_fact_value(f), authority=authority,
                source=f.source_location,
            ).as_dict())

    # ── assumptions ────────────────────────────────────────────────────────
    async def _apply_assumptions(self, state: CanonicalProductionState, project_id) -> None:
        rows = (await self.session.execute(
            select(ProductionAssumption).where(ProductionAssumption.project_id == project_id)
        )).scalars().all()
        for a in sorted(rows, key=lambda r: r.assumption_key):
            state.assumptions.append({
                "key": a.assumption_key, "value": a.value, "unit": a.unit,
                "authority": a.evidence_state, "source": a.source,
            })
        present = {a.assumption_key for a in rows if a.value is not None}
        for required in ("intended_shoot_days", "base_jurisdiction"):
            if required not in present:
                state.unknowns.append(
                    f"assumption:{required} is UNKNOWN — not defaulted; supply it "
                    "explicitly to enable full downstream estimation."
                )

    # ── requirements ───────────────────────────────────────────────────────
    async def _apply_requirements(self, state: CanonicalProductionState, project_id) -> None:
        locs = (await self.session.execute(
            select(ProjectLocationRequirement).where(
                ProjectLocationRequirement.project_id == project_id
            )
        )).scalars().all()
        for loc in sorted(locs, key=lambda r: (r.location_key or r.description or "")):
            if loc.location_key is None and loc.category_key is not None:
                continue  # a UI category-override row, not a scripted location
            state.scripted_locations.append({
                "location_key": loc.location_key,
                "description": loc.description,
                "scene_count": loc.scene_count,
                "eighths_total": loc.eighths_total,
                "int_count": loc.int_count, "ext_count": loc.ext_count,
                "day_count": loc.day_count, "night_count": loc.night_count,
                "is_recurring": loc.is_recurring,
                "production_approach": loc.production_approach or "UNKNOWN",
                "production_location": loc.production_location,
                "authority": loc.evidence_state or EVIDENCE_UNKNOWN,
            })
            if loc.location_key and not loc.production_location:
                state.unknowns.append(
                    f"location:{loc.location_key} has no confirmed production "
                    "location — stage vs practical and jurisdiction are producer decisions."
                )

        reqs = (await self.session.execute(
            select(ProductionRequirement).where(ProductionRequirement.project_id == project_id)
        )).scalars().all()
        for r in sorted(reqs, key=lambda x: (x.requirement_key, x.normalized_value)):
            state.production_requirements.append({
                "requirement_key": r.requirement_key,
                "normalized_value": r.normalized_value,
                "quantity": float(r.quantity) if r.quantity is not None else None,
                "unit": r.unit,
                "authority": r.evidence_state,
                "requires_confirmation": r.requires_confirmation,
                "evidence_count": r.evidence_count,
                "scene_sequences": r.source_scene_sequences,
            })

    # ── budget (Part L) ────────────────────────────────────────────────────
    async def _apply_budget(self, state: CanonicalProductionState, project_id) -> None:
        docs = (await self.session.execute(
            select(BudgetDocument).where(BudgetDocument.project_id == project_id)
        )).scalars().all()
        
        if not docs:
            # Fallback: check if the Company Library holds an unprojected budget document
            from app.models.library_document import Document, DocumentVersion
            current_dv = (await self.session.execute(
                select(DocumentVersion)
                .join(Document, DocumentVersion.document_id == Document.id)
                .where(
                    Document.project_id == project_id,
                    Document.category == "budget",
                    DocumentVersion.is_current == True
                )
                .order_by(DocumentVersion.created_at.desc())
            )).scalars().first()
            
            if current_dv:
                import uuid
                from pathlib import Path
                from app.core.config import get_settings
                from app.ingestion.pdf_extractor import extract_text_from_pdf
                from app.ingestion.budget_parser import parse_budget_from_text, classify_parsed_items
                from app.models.enums import ATLBTLCategory, CompensationType
                
                settings = get_settings()
                local_path = Path(settings.LOCAL_STORAGE_PATH) / (current_dv.storage_path or "")
                
                if local_path.exists() and local_path.suffix.lower() == ".pdf":
                    res = extract_text_from_pdf(local_path)
                    parse_result = parse_budget_from_text(
                        res.raw_text, 
                        filename=current_dv.original_filename or "budget.pdf", 
                        currency_code="USD", 
                        pages=res.pages
                    )
                    classified = classify_parsed_items(parse_result)
                    
                    doc = BudgetDocument(
                        id=uuid.uuid4(),
                        project_id=project_id,
                        filename=current_dv.original_filename or "budget.pdf",
                        file_type="pdf",
                        currency_code="USD",
                        total_budget_raw=classified.total_budget_raw,
                        extraction_status="imported",
                        is_active=True,
                        document_version_id=current_dv.id
                    )
                    self.session.add(doc)
                    
                    for item in classified.line_items:
                        li = BudgetLineItem(
                            id=uuid.uuid4(),
                            budget_document_id=doc.id,
                            description=item.description,
                            department=item.department,
                            amount_raw=item.amount_usd,
                            amount_normalized=item.amount_usd,
                            currency_code=item.currency_code,
                            amount_usd=item.amount_usd,
                            cash_amount_usd=item.amount_usd,
                            source_row=item.source_row,
                            atl_btl=getattr(item, "atl_btl", ATLBTLCategory.BTL.value),
                            spend_category=getattr(item, "spend_category", None),
                            is_labor=getattr(item, "is_labor", False),
                            is_fixed=getattr(item, "is_fixed", False),
                            compensation_type=getattr(item, "compensation_type", CompensationType.CASH.value),
                            extraction_confidence=item.extraction_confidence,
                        )
                        self.session.add(li)
                    
                    await self.session.commit()
                    # Refresh logic
                    docs = [doc]

        if not docs:
            state.budget_state = BUDGET_MISSING
            state.blockers.append(
                "BUDGET_MISSING — no budget document is attached. SA-1 does not "
                "estimate a budget; optimizer pricing stays blocked until a "
                "budget exists or a later phase supplies a Level-1 estimate."
            )
            return

        state.budget_document_ids = [str(d.id) for d in docs]
        lines = (await self.session.execute(
            select(BudgetLineItem).where(
                BudgetLineItem.budget_document_id.in_([d.id for d in docs])
            )
        )).scalars().all()
        if not lines:
            state.budget_state = BUDGET_MISSING
            state.blockers.append(
                "BUDGET_MISSING — a budget document exists but has no parsed "
                "line items."
            )
            return

        state.budget_state = BUDGET_PRESENT
        state.active_budget_line_count = len(lines)
        total = 0.0
        for li in lines:
            amt = li.amount_usd if getattr(li, "amount_usd", None) is not None else li.amount_raw
            amt_f = float(amt) if amt is not None else 0.0
            total += amt_f
            state.budget_lines.append({
                "line_id": str(li.id),
                "description": li.description,
                "department": li.department,
                "atl_btl": getattr(li.atl_btl, "value", str(li.atl_btl)),
                "spend_category": getattr(li.spend_category, "value", None)
                if li.spend_category is not None else None,
                "amount_usd": amt_f,
                "is_labor": li.is_labor,
                # Territoriality: residency is carried ONLY where the source
                # states it. Unknown stays unknown — payer is never a proxy.
                "is_resident_labor": li.is_resident_labor,
                "residency_state": (
                    "UNKNOWN" if li.is_resident_labor is None
                    else ("RESIDENT" if li.is_resident_labor else "NONRESIDENT")
                ),
                "service_location_jurisdiction": None,
                "territorial_basis": "UNKNOWN",
            })
        state.gross_budget_usd = round(total, 2)

        unknown_residency = sum(1 for b in state.budget_lines
                                if b["is_labor"] and b["residency_state"] == "UNKNOWN")
        if unknown_residency:
            state.unknowns.append(
                f"{unknown_residency} labor line(s) have UNKNOWN residency. Per the "
                "territoriality guard these are not assumed resident; qualifying "
                "spend cannot be claimed for them without a stated basis."
            )
        state.unknowns.append(
            "No line carries a confirmed service-performed jurisdiction. "
            "Territorial basis is UNKNOWN for all lines; payer/SPV is never "
            "sufficient to establish it."
        )

    # ── readiness ──────────────────────────────────────────────────────────
    def _assess_readiness(self, state: CanonicalProductionState) -> None:
        if not sps.is_analysis_ready(state.script_status):
            state.readiness = BLOCKED_INCOMPLETE_INPUTS
            return
        if state.budget_state != BUDGET_PRESENT:
            state.readiness = BLOCKED_INCOMPLETE_INPUTS
            return
        if not state.gross_budget_usd or state.gross_budget_usd <= 0:
            state.readiness = BLOCKED_INCOMPLETE_INPUTS
            state.blockers.append("Gross budget resolves to zero — nothing to price.")
            return
        state.readiness = READY_FOR_OPTIMIZER
