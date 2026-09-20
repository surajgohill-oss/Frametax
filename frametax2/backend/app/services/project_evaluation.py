"""
project_evaluation.py -- RETIRED_UNREACHABLE (legacy "Begin Evaluation" orchestrator)

`begin_evaluation` and `_summarize` -- the run_full_analysis-backed orchestrator that generated and
ranked ProductionStructure/StructureCalculationResult rows outside the canonical engine -- have been
REMOVED. They were unreachable from production (no route, service or script called them: the served
evaluation is app/services/canonical_evaluation.py::evaluate_project, POST /projects/{id}/evaluation/begin),
and their read-back loaded every row of a project -- all engine versions and generations -- into
memory, which an evaluation generation of 500,000+ rows makes prohibited (PROJECT_RULES.md, LONG-RUNNING
PROCESS DISCIPLINE, rule 10).

This module is NOT a member of the canonical fingerprint's pricing-source digest
(canonical_runtime_attribution._SEMANTIC_PRICING_MODULES), so removing the entrypoint changed no fingerprint
and invalidated no persisted generation.

Still present, and still canonically used:

  * `_derive_home_jurisdiction` -- imported (lazily) by canonical_project_economics.py to derive a
    project's base jurisdiction from its budget filename. Do not remove.

Retained unchanged, unused by any production caller: `_production_type_for`, `_load_program_bundle`,
`MFNI_LIMITATION_NOTE`, `_FORMAT_TO_PRODUCTION_TYPE`.

tests/test_project_evaluation.py guards the retirement: the removed names stay removed, and no production
module may import or call anything here except `_derive_home_jurisdiction`.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument
from app.models.incentive import IncentiveProgram
from app.models.jurisdiction import Jurisdiction
from app.models.project import Project

MFNI_LIMITATION_NOTE = (
    "Regional production-cost normalization is not yet applied to this "
    "comparison — figures use this production's own nominal budget "
    "amounts, not jurisdiction-adjusted local costs."
)

#: Generic project.format -> the production_type vocabulary the incentive
#: rate/doctrine registries are keyed on. "feature_film" is the default —
#: not an FVD-specific value, the same default the registries themselves
#: use most broadly (see program_rate_rules.py's own production_types
#: tuples, which name "feature_film" far more than any other token).
_FORMAT_TO_PRODUCTION_TYPE = {
    "feature": "feature_film",
    "series": "tv_series",
    "documentary": "creative_documentary",
    "animation": "animation",
}


def _production_type_for(project: Project) -> str:
    fmt = (project.format or "").lower()
    return _FORMAT_TO_PRODUCTION_TYPE.get(fmt, "feature_film")


async def _derive_home_jurisdiction(session: AsyncSession, project: Project) -> Jurisdiction | None:
    """Generic, deterministic geography derivation from the project's own
    persisted evidence — never fabricated, never project-specific.

    Matches every active Jurisdiction's own name (whole-word, case-
    insensitive) against this project's budget document filenames — the
    same kind of source-evidence match SA-1.5 already treated F#K
    Valentine's Day's Greece basis as established by ("the source budget
    itself, not inferred"), generalized to any project's own budget
    filename rather than encoded as a fact about one project. Only ever
    runs when `project.home_jurisdiction_id` is not already set — never
    overrides a confirmed value.
    """
    if project.home_jurisdiction_id is not None:
        return await session.get(Jurisdiction, project.home_jurisdiction_id)

    docs = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalars().all()
    filenames = " ".join(d.filename or "" for d in docs)
    if not filenames.strip():
        return None
    # Filenames commonly separate words with "_"/"-"/"." rather than
    # spaces, but those are still \w characters in regex — a plain \b
    # word boundary does not fire between "_" and a letter, so
    # "V-BRAT_V8_Greece_041224" would never match \bGreece\b. Normalize
    # every non-alphanumeric run to a space first so word boundaries land
    # on real word edges regardless of the filename's own punctuation.
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", filenames)

    jurisdictions = (await session.execute(
        select(Jurisdiction).where(Jurisdiction.is_active.is_(True))
    )).scalars().all()
    # Longest name first: "United States" must not be pre-empted by a
    # shorter unrelated match, and a country should not out-match a more
    # specific state/province name also present in the filename.
    for j in sorted(jurisdictions, key=lambda x: len(x.name or ""), reverse=True):
        if not j.name or len(j.name) < 4:
            continue  # too short to word-match safely (e.g. avoid stray 2-letter clashes)
        pattern = r"\b" + re.escape(j.name) + r"\b"
        if re.search(pattern, normalized, re.IGNORECASE):
            return j
    return None


async def _load_program_bundle(session: AsyncSession, jurisdiction_id, program_slug: str) -> dict | None:
    """The same {program, qualifying_categories, uplifts, jurisdiction_spend_pct}
    shape `structures.py::calculate_structure` already builds per claimed
    program — factored out so both call sites stay byte-identical."""
    prog = (await session.execute(
        select(IncentiveProgram).where(
            IncentiveProgram.jurisdiction_id == jurisdiction_id,
            IncentiveProgram.slug == program_slug,
        )
    )).scalars().first()
    if prog is None:
        return None

    from app.models.incentive import QualifyingSpendCategory

    cats = (await session.execute(
        select(QualifyingSpendCategory).where(QualifyingSpendCategory.program_id == prog.id)
    )).scalars().all()
    return {
        "program": {
            "id": str(prog.id),
            "slug": prog.slug,
            "program_type": prog.program_type,
            "base_rate": float(prog.base_rate) if prog.base_rate else None,
            "max_rate": float(prog.max_rate) if prog.max_rate else None,
            "is_refundable": prog.is_refundable,
            "is_transferable": prog.is_transferable,
            "transferable_value_pct": float(prog.transferable_value_pct) if prog.transferable_value_pct else None,
            "is_competitive": prog.is_competitive,
            "annual_cap_local": float(prog.annual_cap_local) if prog.annual_cap_local else None,
            "confidence_tier": prog.confidence_tier,
        },
        "qualifying_categories": [
            {"spend_category": c.spend_category, "qualifies": c.qualifies,
             "jurisdiction_spend_only": c.jurisdiction_spend_only}
            for c in cats
        ],
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
        "program_id": prog.id,
    }
