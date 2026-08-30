"""
material_routing.py

New Project Ingestor closeout — the missing link in the product flow:

    Ingestor discovers/classifies available materials
      -> creates/updates the CineGlobe production
      -> ROUTES MATERIALS TO EXISTING PROCESSORS   <-- this module
      -> opens the production workspace

`app/api/v1/ingestion.py::_commit_candidate_impl` creates the generic
Document/DocumentVersion records for any category and explicitly documents
that it "does not touch optimizer state, facts, lifecycle" — a real,
pre-existing architectural boundary this module respects rather than
violates. Routing runs AFTER a commit succeeds, as a separate step, exactly
matching the product flow diagram above: commit creates the canonical
material record; routing is what makes an already-existing processor
(the budget parser, the SA-1 screenplay pipeline) aware that a new
DocumentVersion exists for it to work on.

Both existing processors are reused untouched:
  - screenplay -> app.services.script_analysis_service (SA-1, already built)
  - budget     -> app.ingestion.budget_parser (already built) + a new
                  BudgetDocument/BudgetLineItem projection, the same
                  pattern SA-1's ScreenplayDocument already established

No category-specific project logic. No FVD, no Little Utopia. A category
with no processor (deck, schedule, artwork, other, ...) is a deliberate
no-op — those materials are already fully served by the generic
Document/DocumentVersion record commit created; there is nothing further
to route them to.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.ingestion.budget_parser import classify_parsed_items, parse_budget_csv, parse_budget_from_text
from app.ingestion.pdf_extractor import extract_text_from_pdf
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.enums import ATLBTLCategory, CompensationType, ProjectAssetKind, ProjectAssetSourceType
from app.models.library_document import Document, DocumentVersion
from app.models.project import Project
from app.models.project_asset import ProjectAsset
from app.services.script_analysis_service import analyze_project_script

#: Categories this module knows how to route to an existing processor.
ROUTABLE_CATEGORIES = frozenset({"screenplay", "budget"})

_TEXT_SUFFIXES = {".txt", ".fdx"}


def _read_source_text(local_path: Path) -> str | None:
    suffix = local_path.suffix.lower()
    if suffix == ".pdf":
        try:
            return extract_text_from_pdf(local_path, max_pages=300).raw_text
        except Exception:  # noqa: BLE001 — extraction failure must not crash commit
            return None
    if suffix in _TEXT_SUFFIXES:
        try:
            return local_path.read_text(errors="replace")
        except OSError:
            return None
    return None


async def _route_budget(
    session: AsyncSession, *, project: Project, version: DocumentVersion, local_path: Path,
) -> None:
    """Parse a committed budget DocumentVersion with the existing
    deterministic budget_parser (the same parse -> classify_parsed_items
    pipeline `POST /projects/{id}/budgets/import` already uses), project
    its result into BudgetDocument/BudgetLineItem, then set
    Project.total_budget_usd from the parser's own declared grand total —
    never a guessed or hardcoded figure. Per the SA-1.5 real-production
    corpus (docs/validation/REAL_PRODUCTION_VALIDATION_CORPUS.md), every
    resolved fixture's declared total independently equals its acceptance
    oracle even where flat leaf-line extraction under-covers, so the
    declared total — not a leaf-line sum — is the correct figure here."""
    existing = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == version.id)
    )).scalars().first()
    if existing is not None:
        return  # already routed for this exact version — idempotent

    suffix = local_path.suffix.lower()
    if suffix == ".csv":
        result = parse_budget_csv(local_path.read_bytes(), filename=version.original_filename or local_path.name)
    elif suffix == ".pdf":
        # Real per-page boundaries matter here (parse_budget_from_text's
        # own docstring: without them, a multi-page film budget degrades
        # to "one giant page" and every detail-page subaccount gets
        # mis-scanned as a top-sheet row) -- extract with pymupdf's own
        # page list directly rather than going through _read_source_text,
        # which only returns a flat, page-boundary-free string.
        try:
            extracted = extract_text_from_pdf(local_path, max_pages=300)
        except Exception:  # noqa: BLE001 — extraction failure must not crash commit
            return
        result = parse_budget_from_text(
            extracted.raw_text, filename=version.original_filename or local_path.name,
            pages=extracted.pages,
        )
    else:
        text = _read_source_text(local_path)
        if text is None:
            return  # unsupported/unreadable source — leave unrouted, never guessed
        result = parse_budget_from_text(text, filename=version.original_filename or local_path.name)

    if not result.line_items and result.total_budget_raw is None:
        return  # nothing the parser could extract — leave unrouted

    classified = classify_parsed_items(result)

    budget_doc = BudgetDocument(
        id=uuid.uuid4(),
        project_id=project.id,
        filename=version.original_filename or local_path.name,
        file_type=suffix.lstrip("."),
        storage_path=version.storage_path,
        currency_code=classified.currency_code or "USD",
        total_budget_raw=classified.total_budget_raw,
        extraction_status="extracted",
        document_version_id=version.id,
    )
    session.add(budget_doc)
    await session.flush()

    for item in classified.line_items:
        session.add(BudgetLineItem(
            id=uuid.uuid4(),
            budget_document_id=budget_doc.id,
            description=item.description,
            department=item.department,
            amount_raw=item.amount_usd,
            amount_normalized=item.amount_usd,
            currency_code=item.currency_code,
            amount_usd=item.amount_usd,
            cash_amount_usd=item.amount_usd,
            source_row=item.source_row,
            source_page=item.source_page,
            atl_btl=getattr(item, "atl_btl", ATLBTLCategory.BTL.value),
            spend_category=getattr(item, "spend_category", None),
            is_labor=getattr(item, "is_labor", False),
            is_fixed=getattr(item, "is_fixed", False),
            compensation_type=getattr(item, "compensation_type", CompensationType.CASH.value),
            extraction_confidence=item.extraction_confidence,
        ))

    if project.total_budget_usd is None:
        project.total_budget_usd = classified.total_budget_raw

    await session.flush()


async def _route_screenplay(
    session: AsyncSession, *, project: Project, version: DocumentVersion, local_path: Path,
) -> None:
    """Run the existing SA-1 pipeline (screenplay projection -> deterministic
    parse -> Scene/Character/SceneElement -> derived ProjectFacts ->
    ProductionRequirements/LocationRequirements) against the newly
    committed screenplay DocumentVersion.

    `analyze_project_script` alone is sufficient: `resolve_active_screenplay`
    already bootstraps a `ScreenplayDocument` on demand from the project's
    current screenplay `DocumentVersion` (reading the file from disk itself)
    when none exists yet — this call is the missing trigger, not new logic."""
    await analyze_project_script(session, project_id=project.id)
    # Workspace Data Completeness / Project Key Art: attempt cover-art
    # extraction from this SAME screenplay file, same commit-time trigger
    # point as script analysis above. See _extract_screenplay_artwork's own
    # docstring for the full precedence/provenance/idempotency contract.
    await _extract_screenplay_artwork(session, project=project, version=version, local_path=local_path)


async def _extract_screenplay_artwork(
    session: AsyncSession, *, project: Project, version: DocumentVersion, local_path: Path,
) -> str | None:
    """Reuses app.services.artwork_extraction.extract_pdf_cover() (Phase F —
    built, never wired to any screenplay trigger before this task) against
    the project's own real screenplay file. A screenplay whose first page
    is plain text (no embedded raster image, or only a small logo below
    MIN_PAGE_COVERAGE) correctly returns None — never rendered as a
    fallback "page as art" (that tier, render_pdf_page_as_candidate, is
    explicitly reserved for deck/lookbook categories, never screenplay —
    see its own docstring). Only a genuine, designed cover/poster page
    (a real embedded image covering most of the page) is ever persisted.

    Precedence (never violated): an existing master asset (whether user-
    assigned or already extracted) is never replaced here — this only
    ever CREATES a new candidate asset and only sets it as master when the
    project currently has none at all. A human's explicit selection via
    POST /artwork/{id}/set-master always outranks anything this function
    does, on every subsequent call.

    Idempotent per DocumentVersion: if a ProjectAsset already traces back
    to this exact screenplay version (whether a real cover was found and
    persisted, or this ran before, the same PyMuPDF page-1 scan never
    reruns twice for a version already checked."""
    existing = (await session.execute(
        select(ProjectAsset).where(
            ProjectAsset.project_id == project.id,
            ProjectAsset.source_document_version_id == version.id,
            ProjectAsset.source_type == ProjectAssetSourceType.EXTRACTED_FROM_SCREENPLAY.value,
        )
    )).scalars().first()
    if existing is not None:
        return "already_extracted"

    if local_path.suffix.lower() != ".pdf" or not local_path.exists():
        return None

    from app.services.artwork_extraction import extract_pdf_cover
    image = extract_pdf_cover(local_path)
    if image is None:
        return "no_usable_artwork"

    has_master = (await session.execute(
        select(ProjectAsset).where(ProjectAsset.project_id == project.id, ProjectAsset.is_master.is_(True))
    )).scalars().first()

    # Same storage convention commit_candidate already uses: write into the
    # project's own existing storage directory (the screenplay's own
    # parent dir), never a second directory-naming scheme.
    project_dir = (Path(settings.LOCAL_STORAGE_PATH) / version.storage_path).parent
    project_dir.mkdir(parents=True, exist_ok=True)
    dest_path = project_dir / f"screenplay-cover-{version.id}.{image.ext}"
    dest_path.write_bytes(image.data)
    storage_rel_path = str(dest_path.relative_to(settings.LOCAL_STORAGE_PATH))

    import hashlib
    checksum = hashlib.sha256(image.data).hexdigest()

    asset = ProjectAsset(
        id=uuid.uuid4(), project_id=project.id, kind=ProjectAssetKind.ARTWORK.value,
        source_type=ProjectAssetSourceType.EXTRACTED_FROM_SCREENPLAY.value,
        storage_path=storage_rel_path, checksum_sha256=checksum, file_size=len(image.data),
        is_master=(has_master is None),
        source_document_version_id=version.id,
        notes=(
            f"Extracted from screenplay page 1 (largest embedded raster image, "
            f"{image.width}x{image.height} {image.ext}) via extract_pdf_cover()."
        ),
    )
    session.add(asset)
    await session.flush()
    return "extracted"


async def ensure_screenplay_artwork_extracted(session: AsyncSession, project_id) -> str | None:
    """Retroactive counterpart to the commit-time call in _route_screenplay,
    the SAME pattern ensure_current_budget_routed already established for
    budget: a project whose screenplay DocumentVersion predates this task's
    wiring was simply never checked for cover art — not a missing asset, a
    missing TRIGGER. Called on demand from the live Evaluate path so this
    never requires a manual one-off script. Idempotent — see
    _extract_screenplay_artwork's own docstring.

    Deliberately does NOT commit (unlike ensure_current_budget_routed,
    which is called earlier in evaluate_project, before that function's
    own `project` ORM object is loaded). This function is called AFTER
    evaluate_project has already loaded and holds a live reference to its
    own `project` object, which later code keeps reading attributes off
    of — an internal commit here would expire that object (SQLAlchemy's
    default expire_on_commit=True) and crash the very next synchronous
    attribute access with MissingGreenlet. Same flush-only convention
    analyze_project_script already uses for this exact call site; the
    caller's own commit (evaluate_project's, at its natural transaction
    boundary) persists this together with everything else in one unit."""
    project = await session.get(Project, project_id)
    if project is None:
        return None

    current_dv = (await session.execute(
        select(DocumentVersion)
        .join(Document, DocumentVersion.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            Document.category == "screenplay",
            DocumentVersion.is_current == True,  # noqa: E712
        )
        .order_by(DocumentVersion.created_at.desc())
    )).scalars().first()
    if current_dv is None or not current_dv.storage_path:
        return None

    local_path = Path(settings.LOCAL_STORAGE_PATH) / current_dv.storage_path
    if not local_path.exists():
        return "source_file_missing"

    return await _extract_screenplay_artwork(session, project=project, version=current_dv, local_path=local_path)


async def ensure_current_budget_routed(session: AsyncSession, project_id) -> BudgetDocument | None:
    """Fresh Project Source-Document Ingestion: the retroactive counterpart
    to `route_committed_material`'s commit-time budget routing.

    `route_committed_material` only ever runs as a side effect of a NEW
    commit through POST /candidates/{id}/commit — real, generic, and
    already correct for any project going forward. But a project whose
    budget Document/DocumentVersion predates that wiring (bulk-seeded or
    imported before this routing existed) has a real, attached budget
    file that was simply never routed — not a missing asset, a missing
    TRIGGER. This function is that trigger, called on demand (from
    canonical_project_economics.build_project_economic_inputs, the live
    Evaluate path) rather than only at commit time.

    Reuses `_route_budget` unchanged — never a second parsing/projection
    implementation. Idempotent per DocumentVersion (`_route_budget`'s own
    existing-row check), so calling this on every Evaluate is safe and
    cheap once a project's current version has already been routed."""
    project = await session.get(Project, project_id)
    if project is None:
        return None

    current_dv = (await session.execute(
        select(DocumentVersion)
        .join(Document, DocumentVersion.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            Document.category == "budget",
            DocumentVersion.is_current == True,  # noqa: E712
        )
        .order_by(DocumentVersion.created_at.desc())
    )).scalars().first()
    if current_dv is None or not current_dv.storage_path:
        return None

    local_path = Path(settings.LOCAL_STORAGE_PATH) / current_dv.storage_path
    if not local_path.exists():
        return None

    await _route_budget(session, project=project, version=current_dv, local_path=local_path)
    await session.commit()

    return (await session.execute(
        select(BudgetDocument).where(BudgetDocument.document_version_id == current_dv.id)
    )).scalars().first()


async def route_committed_material(
    session: AsyncSession, *, project_id, category: str, document_version_id,
) -> str | None:
    """Entry point called after a commit succeeds. Returns a short result
    tag for logging/tests, or None when the category has no processor."""
    if category not in ROUTABLE_CATEGORIES:
        return None

    project = await session.get(Project, project_id)
    version = await session.get(DocumentVersion, document_version_id)
    if project is None or version is None or not version.storage_path:
        return None

    local_path = Path(settings.LOCAL_STORAGE_PATH) / version.storage_path
    if not local_path.exists():
        return "source_file_missing"

    if category == "budget":
        await _route_budget(session, project=project, version=version, local_path=local_path)
        return "budget_routed"
    if category == "screenplay":
        await _route_screenplay(session, project=project, version=version, local_path=local_path)
        return "screenplay_routed"
    return None
