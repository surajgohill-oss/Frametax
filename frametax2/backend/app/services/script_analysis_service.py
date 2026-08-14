"""
script_analysis_service.py

Script Analyzer SA-1, Parts A / C / E / F / G.

Connects universal document ingestion to screenplay semantic processing and
persists the deterministic result:

    DocumentVersion
      -> ScreenplayDocument (typed projection, version-scoped)
      -> deterministic structural parse
      -> Scene / Character / SceneElement rows
      -> derived ProjectFacts
      -> ProductionRequirements
      -> LocationRequirements

Invariants enforced here:

  * DocumentVersion.checksum_sha256 — not filename — is source identity.
  * A parse is scoped to exactly one DocumentVersion. Re-running against an
    unchanged version with the same parser is a no-op (idempotent).
  * A revised screenplay is a different DocumentVersion and therefore gets
    its OWN ScreenplayDocument row; the prior version's parse is never
    overwritten or deleted.
  * Nothing here estimates. A failed or scan-only source produces a blocking
    status, never substitute facts.
  * Presence is recorded; quantity, scale and complexity are not inferred.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.screenplay_structural_parser import (
    PARSER_VERSION,
    TAX_CHARACTER,
    TAX_DAY_NIGHT,
    TAX_DIALOGUE_ROLE,
    TAX_EXPLICIT_ANIMAL,
    TAX_EXPLICIT_MINOR,
    TAX_EXPLICIT_PROP,
    TAX_EXPLICIT_VEHICLE,
    TAX_EXPLICIT_WEAPON,
    TAX_INT_EXT,
    TAX_PERIOD_REFERENCE,
    TAX_SCENE,
    TAX_SCRIPTED_LOCATION,
    StructuralParseResult,
    parse_structure,
)
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.library_document import DocumentVersion
from app.models.production_requirement import (
    EVIDENCE_DETERMINISTIC_DERIVED,
    EVIDENCE_UNKNOWN,
    ProductionRequirement,
)
from app.models.project_fact import ProjectFact
from app.models.project_location_requirement import ProjectLocationRequirement
from app.models.screenplay import Character, ExtractedScriptElement, Scene, ScreenplayDocument
from app.services import script_parse_status as sps

#: Requirement-producing taxonomy keys and their requirement_key.
_REQUIREMENT_TAXONOMY = {
    TAX_SCRIPTED_LOCATION: "SCRIPTED_LOCATION",
    TAX_CHARACTER: "CHARACTER",
    TAX_EXPLICIT_VEHICLE: "EXPLICIT_VEHICLE",
    TAX_EXPLICIT_ANIMAL: "EXPLICIT_ANIMAL",
    TAX_EXPLICIT_WEAPON: "EXPLICIT_WEAPON",
    TAX_EXPLICIT_MINOR: "EXPLICIT_MINOR",
    TAX_EXPLICIT_PROP: "EXPLICIT_PROP",
    TAX_PERIOD_REFERENCE: "PERIOD_REFERENCE",
}

#: Derived-fact keys written to ProjectFact, all DETERMINISTIC_DERIVED.
DERIVED_FACT_PREFIX = "script_"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def resolve_active_screenplay(
    session: AsyncSession, project_id
) -> ScreenplayDocument | None:
    """The screenplay projection for the project's most recent screenplay
    DocumentVersion. Prefers a row bound to a current DocumentVersion;
    falls back to the most recently parsed/created row."""
    rows = (await session.execute(
        select(ScreenplayDocument)
        .where(ScreenplayDocument.project_id == project_id)
        .order_by(ScreenplayDocument.created_at.desc())
    )).scalars().all()

    for r in rows:
        if r.document_version_id is not None:
            from app.models.library_document import DocumentVersion
            dv = await session.get(DocumentVersion, r.document_version_id)
            if dv is not None and dv.is_current:
                return r

    if rows:
        return rows[0]

    from app.models.library_document import Document, DocumentVersion
    from app.ingestion.pdf_extractor import extract_text_from_pdf
    from app.core.config import get_settings
    from pathlib import Path

    current_dv = (await session.execute(
        select(DocumentVersion)
        .join(Document, DocumentVersion.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            Document.category == "screenplay",
            DocumentVersion.is_current == True
        )
        .order_by(DocumentVersion.ingested_at.desc())
    )).scalars().first()

    if not current_dv:
        return None

    settings = get_settings()
    local_path = Path(settings.LOCAL_STORAGE_PATH) / current_dv.storage_path
    
    raw_text = None
    if local_path.exists():
        suffix = local_path.suffix.lower()
        if suffix == ".pdf":
            try:
                extracted = extract_text_from_pdf(local_path, max_pages=300)
                raw_text = extracted.raw_text
            except Exception as e:
                print(f"Failed to extract text from {local_path}: {e}")
        elif suffix in [".txt", ".fdx", ".csv"]:
            try:
                raw_text = local_path.read_text(errors="replace")
            except Exception as e:
                print(f"Failed to read text from {local_path}: {e}")

    doc = await ensure_screenplay_projection(
        session,
        project_id=project_id,
        document_version=current_dv,
        raw_text=raw_text,
        filename=current_dv.original_filename
    )
    
    session.add(doc)
    await session.flush()
    return doc


async def ensure_screenplay_projection(
    session: AsyncSession,
    *,
    project_id,
    document_version: DocumentVersion,
    raw_text: str | None,
    filename: str | None = None,
) -> ScreenplayDocument:
    """Part A — semantic dispatch.

    Create or return the typed ScreenplayDocument for EXACTLY this
    DocumentVersion. Identity comes from document_version_id (backed by the
    version's checksum), never from the filename.
    """
    existing = (await session.execute(
        select(ScreenplayDocument).where(
            ScreenplayDocument.document_version_id == document_version.id
        )
    )).scalars().first()
    if existing is not None:
        if raw_text is not None and existing.raw_text != raw_text:
            existing.raw_text = raw_text
        return existing

    doc = ScreenplayDocument(
        project_id=project_id,
        filename=filename or document_version.original_filename or "screenplay",
        file_type=(filename or document_version.original_filename or "").rsplit(".", 1)[-1][:20] or "txt",
        raw_text=raw_text,
        word_count=len(raw_text.split()) if raw_text else None,
        extraction_status="extracted" if raw_text else "pending",
        document_version_id=document_version.id,
        parse_status=(
            sps.SCRIPT_PARSE_READY if raw_text else sps.SCRIPT_PARSE_BLOCKED_SCAN_ONLY
        ),
    )
    if not raw_text:
        doc.parse_error = (
            "No extractable text layer on this DocumentVersion. SA-1 supports "
            "text-based PDF and plain text only; the source is blocked rather "
            "than estimated."
        )
    session.add(doc)
    await session.flush()
    return doc


async def parse_and_persist(
    session: AsyncSession, screenplay: ScreenplayDocument, *, force: bool = False
) -> tuple[StructuralParseResult | None, bool]:
    """Parts B/C — run the deterministic parse and persist the structure.

    Returns (result, did_write). Idempotent: if the same text has already been
    parsed by the same parser version, nothing is rewritten and did_write is
    False. Pass force=True to re-parse regardless (used after a parser upgrade).
    """
    raw = screenplay.raw_text
    if not raw or not raw.strip():
        screenplay.parse_status = sps.SCRIPT_PARSE_BLOCKED_SCAN_ONLY
        screenplay.parse_error = (
            "Screenplay has no extractable text. Blocked rather than estimated."
        )
        await session.flush()
        return None, False

    fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    unchanged = (
        screenplay.input_fingerprint == fingerprint
        and screenplay.parser_version == PARSER_VERSION
        and screenplay.parse_status == sps.SCRIPT_PARSED
    )
    if unchanged and not force:
        return None, False

    try:
        result = parse_structure(raw)
    except Exception as exc:  # noqa: BLE001 — must never fall back to guesses
        screenplay.parse_status = sps.SCRIPT_PARSE_FAILED
        screenplay.parse_error = f"{type(exc).__name__}: {exc}"
        await session.flush()
        return None, False

    # Replace only THIS screenplay row's structure. Other versions untouched.
    for old in (await session.execute(
        select(Scene).where(Scene.screenplay_id == screenplay.id)
    )).scalars().all():
        await session.delete(old)
    for old_c in (await session.execute(
        select(Character).where(Character.screenplay_id == screenplay.id)
    )).scalars().all():
        await session.delete(old_c)
    for old_e in (await session.execute(
        select(ExtractedScriptElement).where(
            ExtractedScriptElement.screenplay_id == screenplay.id,
            ExtractedScriptElement.extraction_method == "DETERMINISTIC_PARSE",
        )
    )).scalars().all():
        await session.delete(old_e)
    await session.flush()

    eighths_by_seq = {s.sequence: (s.eighths or 0) for s in result.scenes}

    for ps in result.scenes:
        scene = Scene(
            screenplay_id=screenplay.id,
            sequence=ps.sequence,
            source_scene_number=ps.source_scene_number,
            raw_heading=ps.raw_heading,
            normalized_heading=ps.normalized_heading,
            int_ext=ps.int_ext,
            time_of_day=ps.time_of_day,
            scripted_location=ps.scripted_location,
            location_key=ps.location_key,
            char_start=ps.char_start,
            char_end=ps.char_end,
            page_start=ps.page_start,
            page_end=ps.page_end,
            eighths=ps.eighths,
            scene_hash=ps.scene_hash,
            parser_version=result.parser_version,
        )
        session.add(scene)
        await session.flush()

        for pe in ps.elements:
            session.add(ExtractedScriptElement(
                screenplay_id=screenplay.id,
                scene_id=scene.id,
                element_type=pe.taxonomy_key.lower(),
                value=pe.normalized_value[:512],
                taxonomy_key=pe.taxonomy_key,
                normalized_value=pe.normalized_value[:512],
                context_excerpt=pe.raw_evidence[:2000],
                char_start=pe.char_start,
                char_end=pe.char_end,
                evidence_hash=pe.evidence_hash,
                extraction_method=pe.extraction_method,
                evidence_state=pe.evidence_state,
                is_interpretation=pe.is_interpretation,
                parser_version=result.parser_version,
                page_reference=ps.page_start,
            ))

    for pc in result.characters:
        session.add(Character(
            screenplay_id=screenplay.id,
            canonical_name=pc.canonical_name,
            aliases=pc.aliases or [],
            scene_sequences=pc.scene_sequences,
            scene_count=len(pc.scene_sequences),
            dialogue_block_count=pc.dialogue_block_count,
            dialogue_word_count=pc.dialogue_word_count,
            is_speaking_role=pc.is_speaking_role,
            eighths_burden=sum(eighths_by_seq.get(s, 0) for s in pc.scene_sequences),
            parser_version=result.parser_version,
        ))

    screenplay.parser_version = result.parser_version
    screenplay.input_fingerprint = result.input_fingerprint
    screenplay.page_basis = result.page_basis
    screenplay.page_count = result.page_count
    screenplay.word_count = result.word_count
    screenplay.total_eighths = result.total_eighths
    screenplay.parse_status = sps.SCRIPT_PARSED
    screenplay.parse_error = None
    screenplay.parsed_at = _now()
    screenplay.parse_warnings = list(result.warnings)

    await session.flush()
    return result, True


def derive_core_facts(result: StructuralParseResult) -> dict[str, object]:
    """Part E — derived core production facts. Pure function of the parse."""
    scenes = result.scenes
    loc_counts: dict[str, int] = {}
    for s in scenes:
        if s.location_key:
            loc_counts[s.location_key] = loc_counts.get(s.location_key, 0) + 1

    speaking = [c for c in result.characters if c.is_speaking_role]
    top = sorted(
        speaking,
        key=lambda c: (c.dialogue_block_count, c.dialogue_word_count, len(c.scene_sequences)),
        reverse=True,
    )[:10]

    def _has(tax: str) -> bool:
        return any(e.taxonomy_key == tax for s in scenes for e in s.elements)

    return {
        "script_total_scenes": len(scenes),
        "script_total_eighths": result.total_eighths,
        "script_page_count": result.page_count,
        "script_page_basis": result.page_basis,
        "script_int_scene_count": sum(1 for s in scenes if s.int_ext == "INT"),
        "script_ext_scene_count": sum(1 for s in scenes if s.int_ext == "EXT"),
        "script_int_ext_scene_count": sum(1 for s in scenes if s.int_ext == "INT_EXT"),
        "script_unknown_int_ext_count": sum(1 for s in scenes if s.int_ext == "UNKNOWN"),
        "script_day_scene_count": sum(1 for s in scenes if s.time_of_day == "DAY"),
        "script_night_scene_count": sum(1 for s in scenes if s.time_of_day == "NIGHT"),
        "script_unknown_time_of_day_count": sum(1 for s in scenes if s.time_of_day == "UNKNOWN"),
        "script_unique_scripted_locations": len(loc_counts),
        "script_recurring_scripted_locations": sum(1 for v in loc_counts.values() if v > 1),
        "script_speaking_character_count": len(speaking),
        "script_top_character_burden": [
            {
                "character": c.canonical_name,
                "scenes": len(c.scene_sequences),
                "dialogue_blocks": c.dialogue_block_count,
                "dialogue_words": c.dialogue_word_count,
            }
            for c in top
        ],
        "script_has_explicit_vehicle": _has(TAX_EXPLICIT_VEHICLE),
        "script_has_explicit_animal": _has(TAX_EXPLICIT_ANIMAL),
        "script_has_explicit_weapon": _has(TAX_EXPLICIT_WEAPON),
        "script_has_explicit_minor": _has(TAX_EXPLICIT_MINOR),
        "script_has_period_reference": _has(TAX_PERIOD_REFERENCE),
    }


async def persist_derived_facts(
    session: AsyncSession, *, project_id, screenplay: ScreenplayDocument, facts: dict
) -> int:
    """Write derived facts to ProjectFact with full provenance. Never a bare
    constant: every row records the screenplay version it came from."""
    import json as _json

    written = 0
    for key, value in facts.items():
        if isinstance(value, bool):
            v, vtype = ("true" if value else "false"), "boolean"
        elif isinstance(value, (int, float)):
            v, vtype = str(value), "number"
        elif isinstance(value, (list, dict)):
            v, vtype = _json.dumps(value, sort_keys=True), "json"
        elif value is None:
            continue
        else:
            v, vtype = str(value), "string"

        existing = (await session.execute(
            select(ProjectFact).where(
                ProjectFact.project_id == project_id, ProjectFact.fact_key == key
            )
        )).scalars().first()
        if existing is None:
            session.add(ProjectFact(
                project_id=project_id, fact_key=key, value=v, value_type=vtype,
                source_type=ProjectFactSourceType.EXTRACTED,
                source_document_version_id=screenplay.document_version_id,
                source_location=f"deterministic parse {screenplay.parser_version}",
                review_status=ReviewStatus.PENDING,
            ))
            written += 1
        elif existing.source_type == ProjectFactSourceType.USER_OVERRIDE:
            # Canonical precedence: a user override outranks a derived value.
            continue
        else:
            existing.value = v
            existing.value_type = vtype
            existing.source_document_version_id = screenplay.document_version_id
            existing.source_location = f"deterministic parse {screenplay.parser_version}"
            written += 1
    await session.flush()
    return written


async def build_requirements(
    session: AsyncSession, *, project_id, screenplay: ScreenplayDocument,
    result: StructuralParseResult,
) -> tuple[int, int]:
    """Parts F/G — evidence-backed ProductionRequirements and scripted
    LocationRequirements. Returns (requirement_count, location_count).

    Quantities are deliberately left NULL: presence is evidence, scale is a
    later interpretation/confirmation step.
    """
    # Clear only rows this screenplay produced — never a user's own rows.
    for old in (await session.execute(
        select(ProductionRequirement).where(
            ProductionRequirement.project_id == project_id,
            ProductionRequirement.source_screenplay_id == screenplay.id,
        )
    )).scalars().all():
        await session.delete(old)
    for old_l in (await session.execute(
        select(ProjectLocationRequirement).where(
            ProjectLocationRequirement.project_id == project_id,
            ProjectLocationRequirement.source_screenplay_id == screenplay.id,
        )
    )).scalars().all():
        await session.delete(old_l)
    await session.flush()

    # ── aggregate evidence per (requirement_key, normalized_value) ─────────
    agg: dict[tuple[str, str], dict] = {}
    for s in result.scenes:
        for e in s.elements:
            rkey = _REQUIREMENT_TAXONOMY.get(e.taxonomy_key)
            if rkey is None:
                continue
            k = (rkey, e.normalized_value)
            rec = agg.setdefault(k, {"scenes": set(), "count": 0, "sample": e.raw_evidence})
            rec["scenes"].add(s.sequence)
            rec["count"] += 1

    for (rkey, value), rec in sorted(agg.items()):
        session.add(ProductionRequirement(
            project_id=project_id,
            requirement_key=rkey,
            normalized_value=value[:512],
            description=f"{rkey.replace('_', ' ').title()} evidenced in "
                        f"{len(rec['scenes'])} scene(s).",
            quantity=None, quantity_max=None, unit=None,   # scale is NOT inferred
            evidence_state=EVIDENCE_DETERMINISTIC_DERIVED,
            is_interpretation=False,
            requires_confirmation=(rkey not in ("SCRIPTED_LOCATION", "CHARACTER")),
            source_screenplay_id=screenplay.id,
            source_document_version_id=screenplay.document_version_id,
            source_scene_sequences=sorted(rec["scenes"]),
            evidence_count=rec["count"],
            sample_evidence=(rec["sample"] or "")[:2000],
            parser_version=result.parser_version,
        ))

    # ── scripted location requirements ─────────────────────────────────────
    by_loc: dict[str, list] = {}
    for s in result.scenes:
        if s.location_key:
            by_loc.setdefault(s.location_key, []).append(s)

    for key, scs in sorted(by_loc.items()):
        session.add(ProjectLocationRequirement(
            project_id=project_id,
            description=scs[0].scripted_location or key,
            is_flexible=None,          # not assessed by the parser
            location_key=key,
            source_screenplay_id=screenplay.id,
            source_document_version_id=screenplay.document_version_id,
            scene_sequences=[s.sequence for s in scs],
            scene_count=len(scs),
            eighths_total=sum(s.eighths or 0 for s in scs),
            int_count=sum(1 for s in scs if s.int_ext in ("INT", "INT_EXT")),
            ext_count=sum(1 for s in scs if s.int_ext in ("EXT", "INT_EXT")),
            day_count=sum(1 for s in scs if s.time_of_day == "DAY"),
            night_count=sum(1 for s in scs if s.time_of_day == "NIGHT"),
            is_recurring=len(scs) > 1,
            production_approach="UNKNOWN",   # stage vs practical is a producer call
            production_location=None,        # real location is a producer call
            evidence_state=EVIDENCE_DETERMINISTIC_DERIVED,
            parser_version=result.parser_version,
        ))

    await session.flush()
    return len(agg), len(by_loc)


async def analyze_project_script(
    session: AsyncSession, *, project_id, force: bool = False
) -> dict:
    """Full SA-1 script pipeline for one project. Returns a status summary."""
    screenplay = await resolve_active_screenplay(session, project_id)
    if screenplay is None:
        return {
            "status": sps.SCRIPT_NOT_PRESENT,
            "blocker": sps.blocker_for(sps.SCRIPT_NOT_PRESENT),
            "screenplay_id": None,
        }

    result, did_write = await parse_and_persist(session, screenplay, force=force)
    if result is None:
        return {
            "status": screenplay.parse_status,
            "blocker": sps.blocker_for(screenplay.parse_status or ""),
            "screenplay_id": str(screenplay.id),
            "parse_error": screenplay.parse_error,
            "reparsed": False,
        }

    facts = derive_core_facts(result)
    fact_count = await persist_derived_facts(
        session, project_id=project_id, screenplay=screenplay, facts=facts
    )
    req_count, loc_count = await build_requirements(
        session, project_id=project_id, screenplay=screenplay, result=result
    )

    return {
        "status": sps.SCRIPT_PARSED,
        "blocker": None,
        "screenplay_id": str(screenplay.id),
        "document_version_id": str(screenplay.document_version_id) if screenplay.document_version_id else None,
        "parser_version": result.parser_version,
        "input_fingerprint": result.input_fingerprint,
        "page_basis": result.page_basis,
        "reparsed": did_write,
        "scenes": len(result.scenes),
        "characters": len(result.characters),
        "elements": sum(len(s.elements) for s in result.scenes),
        "derived_facts": fact_count,
        "production_requirements": req_count,
        "location_requirements": loc_count,
        "warnings": list(result.warnings),
    }
