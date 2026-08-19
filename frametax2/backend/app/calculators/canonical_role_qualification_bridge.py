"""
canonical_role_qualification_bridge.py

Canonical Co-production Qualification Reconnection — repairs the first
shared disconnect Codex's audit identified: canonical_evaluation.
_opportunities_for_candidate() never calls production_package_to_role_
known_codes(), evaluate_program_eligibility(), or any of the existing
role/nationality qualification machinery in cultural_qualification_model.py.
Both of those modules are EXISTS_BUT_DISCONNECTED, real, engine-agnostic,
and reused UNCHANGED here — no new qualification engine, no new gate
logic, no new economics.

Scope discipline (Codex's own finding): cultural_qualification_model.py
carries real role/nationality rule data for exactly 24 program slugs
(_REQUIREMENTS). This bridge reconnects ONLY those 24 to the canonical
served path. Every other regime correctly returns RULE_DATA_INCOMPLETE —
never fabricated, never generalized from another regime's rules (Task 5's
explicit prohibition).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.canonical_qualification_result import (
    QUAL_HARD_FAIL,
    QUAL_NOT_APPLICABLE,
    QUAL_QUALIFIES,
    QUAL_RULE_DATA_INCOMPLETE,
    QUAL_USER_FACT_REQUIRED,
    CanonicalQualificationResult,
    RoleGateFinding,
)
from app.data.cultural_qualification_model import (
    NATIONALITY_REQUIREMENTS,
    GateStatus,
    evaluate_program_eligibility,
    get_requirements,
    is_spend_only_program,
)
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile

CANONICAL_ROLE_QUALIFICATION_BRIDGE_VERSION = "1.0.0"

#: The exact set of program slugs cultural_qualification_model.py has
#: real rule data for — computed once from the module's own registry,
#: never hand-maintained as a second list that could drift out of sync.
ROLE_QUALIFICATION_COVERED_SLUGS: frozenset[str] = frozenset(
    r.program_slug for r in NATIONALITY_REQUIREMENTS
)


async def role_known_codes_from_project(session: AsyncSession, project_id: str) -> dict[str, tuple[str, ...]]:
    """Real, DB-backed replacement for production_package_to_role_known_
    codes() when no in-memory ProductionPackage exists yet: reads the
    project's actual persisted ProjectPerson -> TalentProfile rows
    (nationality/known_residencies — the same fields the Personnel UI
    already persists) and reshapes them into EXACTLY the role_known_codes
    shape evaluate_program_eligibility() already accepts. No new person
    model, no duplicate query path — TalentProfile remains the one source
    of identity/nationality/residency facts."""
    rows = (await session.execute(
        select(ProjectPerson.role, TalentProfile.primary_nationality, TalentProfile.known_residencies)
        .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
        .where(ProjectPerson.project_id == project_id)
    )).all()

    # cultural_qualification_model's own role vocabulary: director/writer/
    # producer/lead_cast/supporting_cast/editor/composer/dop/vfx_supervisor/entity.
    # ProjectPerson.role free text is normalized to that vocabulary only
    # where the mapping is unambiguous — never guessed.
    _ROLE_ALIASES = {
        "director": "director", "writer": "writer", "producer": "producer",
        "lead_cast": "lead_cast", "cast": "supporting_cast",
        "editor": "editor", "composer": "composer",
    }

    codes: dict[str, set[str]] = {}
    for role_text, nationality, known_residencies in rows:
        role = _ROLE_ALIASES.get((role_text or "").strip().lower())
        if role is None:
            continue
        bucket = codes.setdefault(role, set())
        if nationality:
            bucket.add(nationality.upper())
        for entry in (known_residencies or []):
            code = (entry or {}).get("jurisdiction_code") if isinstance(entry, dict) else None
            if code and (entry.get("confirmed") is not False):
                bucket.add(str(code).upper())

    return {role: tuple(sorted(vals)) for role, vals in codes.items()}


def evaluate_role_qualification(
    program_slug: str,
    jurisdiction_code: str | None,
    role_known_codes: dict[str, tuple[str, ...]],
    treaty_partner_code: str | None = None,
) -> CanonicalQualificationResult:
    """Task 3/4/5 — the repaired seam. Reuses cultural_qualification_
    model.get_requirements()/evaluate_program_eligibility() UNCHANGED;
    this function only classifies the result into the canonical
    qualification-state vocabulary (Task 4) and preserves per-role
    findings (Task 5) rather than collapsing to one boolean."""
    requirements = get_requirements(program_slug)
    if not requirements:
        # Codex's GENUINELY_MISSING_RULE_DATA / spend-only classification:
        # no role/nationality rule data exists for this slug at all in
        # cultural_qualification_model.py. is_spend_only_program() checks
        # the explicit, real allowlist -- those are NOT_APPLICABLE (a
        # genuine "no rule needed" fact); everything else with zero rows
        # is RULE_DATA_INCOMPLETE (genuinely missing, never silently
        # treated as passing or as "not required").
        if is_spend_only_program(program_slug):
            return CanonicalQualificationResult(
                regime_id=program_slug, jurisdiction_code=jurisdiction_code,
                state=QUAL_NOT_APPLICABLE, qualification_route="role_nationality_gate",
                reasoning_trace=("Confirmed spend-only program -- no nationality/role gate applies.",),
                confidence_state="HIGH",
            )
        return CanonicalQualificationResult(
            regime_id=program_slug, jurisdiction_code=jurisdiction_code,
            state=QUAL_RULE_DATA_INCOMPLETE, qualification_route="role_nationality_gate",
            reasoning_trace=(
                "cultural_qualification_model.py has no NationalityRequirement rows "
                f"for '{program_slug}' -- role/nationality rule data is genuinely "
                "missing, not merely unwired (Codex GENUINELY_MISSING_RULE_DATA).",
            ),
            confidence_state="LOW",
        )

    gate = evaluate_program_eligibility(program_slug, role_known_codes, treaty_partner_code)
    if not gate.checks:
        # Real requirement rows exist for this slug, but none carry
        # status=="required" (e.g. uk_avec: every row is point-bearing/
        # weighted) -- the hard-gate layer has nothing to enforce. Never
        # QUALIFIES from an empty gate list (that would silently treat
        # "no hard gate" as "passed a hard gate").
        return CanonicalQualificationResult(
            regime_id=program_slug, jurisdiction_code=jurisdiction_code,
            state=QUAL_NOT_APPLICABLE, qualification_route="role_nationality_gate",
            reasoning_trace=(
                f"{len(requirements)} real requirement row(s) on file for {program_slug}, "
                "none with status=='required' -- no hard role/nationality gate to enforce "
                "(point-bearing/weighted/optional criteria are a separate, unscored dimension).",
            ),
            confidence_state="HIGH",
        )
    findings = tuple(
        RoleGateFinding(
            role=c.role, required_jurisdiction=c.required_jurisdiction,
            status=c.status, known_codes=c.known_codes, notes=c.notes,
        )
        for c in gate.checks
    )
    resolved = tuple(f"{f.role}={f.status}" for f in findings if f.status == GateStatus.SATISFIED)
    failed = tuple(f"{f.role}: {f.notes}" for f in findings if f.status == GateStatus.FAILED)
    missing = tuple(f"{f.role}: {f.notes}" for f in findings if f.status == GateStatus.INDETERMINATE)

    if gate.has_failure:
        state = QUAL_HARD_FAIL
    elif gate.indeterminate_roles:
        state = QUAL_USER_FACT_REQUIRED
    elif gate.passes:
        state = QUAL_QUALIFIES
    else:
        # No requirements were "required" status (only optional/weighted) —
        # the hard-gate layer has nothing to fail or wait on.
        state = QUAL_NOT_APPLICABLE

    return CanonicalQualificationResult(
        regime_id=program_slug, jurisdiction_code=jurisdiction_code,
        state=state, qualification_route="role_nationality_gate",
        role_findings=findings,
        resolved_facts=resolved, missing_facts=missing, failed_requirements=failed,
        available_levers=tuple(sorted({f.role for f in findings if f.status != GateStatus.SATISFIED})),
        authority_basis=f"cultural_qualification_model.py NationalityRequirement rows for {program_slug}",
        confidence_state="HIGH" if not missing else "MEDIUM",
        reasoning_trace=(
            f"{len(requirements)} real requirement row(s) on file for {program_slug}; "
            f"{len(resolved)} satisfied, {len(failed)} failed, {len(missing)} indeterminate.",
        ),
    )
