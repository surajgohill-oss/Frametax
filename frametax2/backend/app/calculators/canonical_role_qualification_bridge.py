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

Worldwide Qualification Consumption Closeout (2026-08-19): the 16
programs Queue B resolved with real cultural-test doctrine (point tables
or a confirmed non-point-table mechanism) but which cultural_
qualification_model.py's 24-slug role registry does not cover were
DISCONNECTED from the served qualification path — real, researched
doctrine sitting in program_requirements.py/cultural_point_tables.py
that canonical_role_qualification_bridge.py never consulted. This module
now dispatches through THREE registries (role-gate rows, cultural point
tables, discretionary/definitional single-criterion programs) into the
SAME CanonicalQualificationResult contract — one consumption path, three
accepted doctrine sources, never a second full duplicate of any of them.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.canonical_qualification_result import (
    QUAL_AUTHORITY_UNRESOLVED,
    QUAL_CURABLE_GAP,
    QUAL_HARD_FAIL,
    QUAL_NOT_APPLICABLE,
    QUAL_QUALIFIES,
    QUAL_RULE_DATA_INCOMPLETE,
    QUAL_SCRIPT_FACT_REQUIRED,
    QUAL_USER_FACT_REQUIRED,
    CanonicalQualificationResult,
    RoleGateFinding,
)
from app.data.cultural_point_tables import (
    CATEGORY_ROLE,
    CRITERION_MANDATORY,
    CULTURAL_POINT_TABLES,
    DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS,
    FACT_KIND_EITHER,
    FACT_KIND_NATIONALITY,
    FACT_SCRIPT,
    FACT_USER,
    TABLE_AUTHORITY_INCOMPLETE,
    TABLE_COMPLETE,
    TABLE_PARTIAL_WITH_KNOWN_HEADROOM,
    TABLE_PARTIAL_WITH_UNKNOWN_HEADROOM,
    _script_fact_matches,
)
from app.data.cultural_qualification_model import (
    NATIONALITY_REQUIREMENTS,
    GateStatus,
    evaluate_program_eligibility,
    get_requirements,
    is_spend_only_program,
)
from app.data.program_requirements import get_program_requirements
from app.models.project_person import ProjectPerson
from app.models.screenplay import ExtractedScriptElement, ScreenplayDocument
from app.models.talent import TalentProfile

CANONICAL_ROLE_QUALIFICATION_BRIDGE_VERSION = "1.2.0"
# 1.1.0 — Worldwide Program Qualification + Cultural Test Completion:
# adds AUTHORITY_UNRESOLVED_PROGRAMS, distinct from the generic
# RULE_DATA_INCOMPLETE branch. RULE_DATA_INCOMPLETE means "never
# researched"; AUTHORITY_UNRESOLVED means "real external primary-
# authority research WAS performed this pass and no confirming (or
# confirming-absence) source could be located" — a genuinely different,
# stronger claim, never conflated with simple incompleteness.
# 1.2.0 — Worldwide Qualification Consumption Closeout: adds the point-
# table and discretionary/definitional consumption paths (see module
# docstring). Every program Queue B resolved with real doctrine now
# reaches a real terminal state (QUALIFIES/HARD_FAIL/CURABLE_GAP/
# USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED/NOT_APPLICABLE) instead of
# RULE_DATA_INCOMPLETE. Disclosure-only, as this entire bridge always
# has been — no pricing/ranking path consumes these results; qualifying-
# admission state changes are visible in the served trace only.

#: The exact set of program slugs cultural_qualification_model.py has
#: real rule data for — computed once from the module's own registry,
#: never hand-maintained as a second list that could drift out of sync.
ROLE_QUALIFICATION_COVERED_SLUGS: frozenset[str] = frozenset(
    r.program_slug for r in NATIONALITY_REQUIREMENTS
)

#: Programs where real external research WAS performed this pass and the
#: cultural-test-applicability question genuinely could not be resolved
#: from any primary or reasonably reliable secondary source checked —
#: see program_requirements.py's own evidence notes for the exact
#: research trail per slug (both remain cultural_test_required=None
#: there, the honest "not yet determined" value).
AUTHORITY_UNRESOLVED_PROGRAMS: dict[str, tuple[str, ...]] = {
    "mu_edb_incentive": (
        "CULTURAL_TEST_APPLICABILITY_UNCONFIRMED — the only specific claim found "
        "(a 90%-Mauritius-filming condition for the 40% tier) was already "
        "investigated and REJECTED by a prior cross-verification (National "
        "Assembly Hansard, 14 May 2019) as belonging to a different government "
        "measure. Two further claims (dialogue mention of 'Mauritius', EDB/"
        "'Film In Mauritius' logo credit, video testimonial) found this pass are "
        "sourced only to non-government production-services sites, not "
        "corroborated by the VERIFIED-tier EDB Submission Procedures document "
        "already on file. No primary confirmation either way.",
    ),
    "fj_film_rebate": (
        "CULTURAL_TEST_APPLICABILITY_UNCONFIRMED — Fiji Income Tax "
        "(Film-making and Audio-Visual Incentives) Regulations 2016, Regulation "
        "6 is the real, cited statutory basis, but no source checked this pass "
        "(including Film Fiji's own site) confirms or denies a cultural/content "
        "test component.",
    ),
}
# NOTE: cy_film_rebate is deliberately NOT in this dict — its
# cultural_test_required=True is CONFIRMED (Council of Ministers Decision
# 83.415/2017, read in full, all 36 pages), a materially different,
# narrower claim than "whether a test applies at all is unconfirmed". It
# has its OWN dict below (Worldwide Qualification Consumption Closeout)
# because leaving it to fall through to QUAL_RULE_DATA_INCOMPLETE would
# have wrongly re-labelled a maximally-researched, confirmed authority
# residual as "never researched".

#: Programs where cultural_test_required=True is CONFIRMED but the exact
#: scoring criteria are a genuine, confirmed authority residual — the
#: primary authority itself withholds the document (never merely "not
#: found this pass"). Distinct from AUTHORITY_UNRESOLVED_PROGRAMS above
#: (which is scoped to applicability itself being unconfirmed) and from
#: CULTURAL_POINT_TABLES (which requires the actual criteria to be on
#: file). Worldwide Qualification Consumption Closeout, 2026-08-19 —
#: Task 6's PARTIALLY_CONSUMED_WITH_EXACT_AUTHORITY_RESIDUAL state: the
#: program-level doctrine (a test applies) IS consumed; only the
#: role/point-level detail remains a genuine residual.
CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS: dict[str, tuple[str, ...]] = {
    "cy_film_rebate": (
        "CULTURAL_TEST_SCORING_TABLE_WITHHELD_BY_PRIMARY_AUTHORITY — cultural_test_required=True is "
        "confirmed (Council of Ministers Decision 83.415/2017, read in full, all 36 pages including "
        "every appendix, 2026-08-19), but the exact point table/scoring breakdown by role is not "
        "published in the primary legal instrument itself or in any secondary source checked "
        "(irglobal.com, exectus.com.cy, Cyprus Production Service all independently confirm it is "
        "disclosed only 'upon request' by the Cyprus Film Commission/Invest Cyprus to real applicants). "
        "Required fact type: authority research only resolvable by the Cyprus Film Commission directly "
        "disclosing the scoring document, not a project or Script Analyzer fact.",
    ),
}


def _authority_unresolved_result(program_slug: str, jurisdiction_code: str | None) -> CanonicalQualificationResult:
    propositions = AUTHORITY_UNRESOLVED_PROGRAMS[program_slug]
    return CanonicalQualificationResult(
        regime_id=program_slug, jurisdiction_code=jurisdiction_code,
        state=QUAL_AUTHORITY_UNRESOLVED, qualification_route="role_nationality_gate",
        missing_facts=propositions,
        reasoning_trace=(
            f"Real external research was performed for {program_slug} this pass "
            "(Worldwide Program Qualification + Cultural Test Completion, "
            "2026-08-19) and did not resolve cultural-test applicability -- "
            "see program_requirements.py's evidence notes for the full trail.",
        ),
        confidence_state="LOW",
    )


def _confirmed_test_scoring_withheld_result(program_slug: str, jurisdiction_code: str | None) -> CanonicalQualificationResult:
    propositions = CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS[program_slug]
    return CanonicalQualificationResult(
        regime_id=program_slug, jurisdiction_code=jurisdiction_code,
        state=QUAL_AUTHORITY_UNRESOLVED, qualification_route="cultural_point_table",
        missing_facts=propositions,
        authority_basis="Program-level applicability CONFIRMED; role/point-level scoring detail is a "
                         "genuine, confirmed authority residual (primary authority withholds the document).",
        reasoning_trace=(
            f"{program_slug}: PARTIALLY_CONSUMED_WITH_EXACT_AUTHORITY_RESIDUAL — cultural-test "
            "applicability is real, confirmed doctrine (consumed); the scoring table itself is a "
            "maximally-researched genuine authority residual, not an unresearched gap.",
        ),
        confidence_state="LOW",
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


async def typed_personnel_facts_from_project(session: AsyncSession, project_id: str) -> dict[str, dict[str, tuple[str, ...]]]:
    """CBA-004 fix (Codex audit 4db2cea, finding 5) — the SEPARATE-typed
    counterpart to role_known_codes_from_project() above. That function
    is kept UNCHANGED for the pre-existing 24-slug role-gate registry
    (cultural_qualification_model.py's NationalityRequirement rows do not
    themselves distinguish which real programs require strict nationality
    vs. which accept residency -- re-deriving that per-program distinction
    across all 24 real regimes is a genuine, disclosed, out-of-scope
    research task, not attempted here to avoid destabilizing tested,
    already-correct legacy behavior on unverified assumptions).

    This function is the typed fact source for NEW consumption paths
    (cultural_point_tables.py's role criteria) that can safely use it:
    returns, per role, `{"nationality": (...), "residency": (...)}` as
    two genuinely separate tuples -- never merged into one untyped set."""
    rows = (await session.execute(
        select(ProjectPerson.role, TalentProfile.primary_nationality, TalentProfile.known_residencies)
        .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
        .where(ProjectPerson.project_id == project_id)
    )).all()

    _ROLE_ALIASES = {
        "director": "director", "writer": "writer", "producer": "producer",
        "lead_cast": "lead_cast", "cast": "supporting_cast",
        "editor": "editor", "composer": "composer",
    }

    facts: dict[str, dict[str, set[str]]] = {}
    for role_text, nationality, known_residencies in rows:
        role = _ROLE_ALIASES.get((role_text or "").strip().lower())
        if role is None:
            continue
        bucket = facts.setdefault(role, {"nationality": set(), "residency": set()})
        if nationality:
            bucket["nationality"].add(nationality.upper())
        for entry in (known_residencies or []):
            code = (entry or {}).get("jurisdiction_code") if isinstance(entry, dict) else None
            if code and (entry.get("confirmed") is not False):
                bucket["residency"].add(str(code).upper())

    return {
        role: {kind: tuple(sorted(vals)) for kind, vals in kinds.items()}
        for role, kinds in facts.items()
    }


@dataclass(frozen=True)
class RoleAttachmentFacts:
    """PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING — the real,
    CONFIRMED-vs-unconfirmed attachment state for one role, typed
    separately for nationality and residency, never merged. Distinct
    from typed_personnel_facts_from_project (which does not filter on
    ProjectPerson.is_confirmed at all -- correct for the 24-slug legacy
    registry it exists for, per that function's own docstring, but wrong
    for a NEW gate that must never credit an unconfirmed attachment as
    current eligibility)."""
    confirmed_nationality: tuple[str, ...] = ()
    confirmed_residency: tuple[str, ...] = ()
    #: A confirmed ProjectPerson row exists for this role, but
    #: TalentProfile.primary_nationality (or known_residencies) is None/
    #: empty -- a real, attached, confirmed person whose fact is simply
    #: not on file. Distinct from "no one is attached at all."
    confirmed_attached_unknown_nationality: bool = False
    confirmed_attached_unknown_residency: bool = False
    #: At least one ProjectPerson row exists for this role with
    #: is_confirmed=False -- a real, proposed attachment that must never
    #: be credited as current eligibility, only ever surfaced as a
    #: conditional lever ("confirm this attachment").
    has_unconfirmed_attachment: bool = False
    #: No ProjectPerson row at all for this role -- an open slot.
    has_any_attachment: bool = False


async def role_attachment_facts_from_project(
    session: AsyncSession, project_id: str,
) -> dict[str, RoleAttachmentFacts]:
    """PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING — the fact
    source for treaty/framework personnel gates (treaty_engine.
    PersonnelRequirement, evaluate_treaty_personnel_gate below). Reads
    the SAME real ProjectPerson/TalentProfile rows role_known_codes_
    from_project and typed_personnel_facts_from_project already read
    (no new person/nationality/treaty model), but additionally exposes
    ProjectPerson.is_confirmed per row and distinguishes "no attachment"
    from "unconfirmed attachment" from "confirmed attachment with an
    unknown fact" -- three genuinely different conditional states this
    module's existing two accessors collapse into one merged set."""
    rows = (await session.execute(
        select(
            ProjectPerson.role, ProjectPerson.is_confirmed,
            TalentProfile.primary_nationality, TalentProfile.known_residencies,
        )
        .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
        .where(ProjectPerson.project_id == project_id)
    )).all()

    _ROLE_ALIASES = {
        "director": "director", "writer": "writer", "producer": "producer",
        "lead_cast": "lead_cast", "cast": "supporting_cast",
        "editor": "editor", "composer": "composer",
    }

    by_role: dict[str, dict] = {}
    for role_text, is_confirmed, nationality, known_residencies in rows:
        role = _ROLE_ALIASES.get((role_text or "").strip().lower())
        if role is None:
            continue
        bucket = by_role.setdefault(role, {
            "confirmed_nationality": set(), "confirmed_residency": set(),
            "confirmed_attached_unknown_nationality": False,
            "confirmed_attached_unknown_residency": False,
            "has_unconfirmed_attachment": False, "has_any_attachment": False,
        })
        bucket["has_any_attachment"] = True
        if not is_confirmed:
            bucket["has_unconfirmed_attachment"] = True
            continue
        if nationality:
            bucket["confirmed_nationality"].add(nationality.upper())
        else:
            bucket["confirmed_attached_unknown_nationality"] = True
        residencies = {
            str((entry or {}).get("jurisdiction_code")).upper()
            for entry in (known_residencies or [])
            if isinstance(entry, dict) and entry.get("jurisdiction_code") and entry.get("confirmed") is not False
        }
        if residencies:
            bucket["confirmed_residency"] |= residencies
        else:
            bucket["confirmed_attached_unknown_residency"] = True

    return {
        role: RoleAttachmentFacts(
            confirmed_nationality=tuple(sorted(b["confirmed_nationality"])),
            confirmed_residency=tuple(sorted(b["confirmed_residency"])),
            confirmed_attached_unknown_nationality=b["confirmed_attached_unknown_nationality"],
            confirmed_attached_unknown_residency=b["confirmed_attached_unknown_residency"],
            has_unconfirmed_attachment=b["has_unconfirmed_attachment"],
            has_any_attachment=b["has_any_attachment"],
        )
        for role, b in by_role.items()
    }


#: Roles a production can still legally cast/hire/change before filing --
#: an open slot in one of these is a CURABLE gap, never a hard failure or
#: a silent "missing fact." Mirrors cultural_point_tables.py's own
#: _SINGLE_SLOT_ROLES convention (kept as a separate constant here since
#: a treaty's curability is a treaty-specific legal question, never
#: inferred from a different regime's own table).
_TREATY_CURABLE_ROLES: frozenset[str] = frozenset({"director", "writer", "producer", "lead_cast"})


def evaluate_treaty_personnel_gate(
    requirement, party_codes: tuple[str, ...],
    attachment_facts: dict[str, "RoleAttachmentFacts"] | None,
) -> CanonicalQualificationResult:
    """PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING — evaluates
    ONE treaty's own real PersonnelRequirement (treaty_engine.py) against
    this project's real, confirmed-vs-unconfirmed attachment facts.
    `requirement` is a treaty_engine.PersonnelRequirement or None.

    Required logic (exact, never a universal rule):
      - requirement is None -> QUAL_NOT_APPLICABLE: this specific treaty
        carries no researched creative-personnel eligibility clause in
        the registry at all -- there is no rule for this gate to apply,
        so there is nothing "incomplete" about THIS project's facts. This
        is deliberately distinct from QUAL_RULE_DATA_INCOMPLETE (which
        would mean a real rule exists but this project's own facts can't
        yet resolve it) -- returning RULE_DATA_INCOMPLETE here would
        surface every one of the ~25-27 treaty opportunities on every
        project as if each had its own open data question, when in fact
        none of them do (CORRECT_COPRO_ASSUMPTION_AND_PERSONNEL_POLICY
        Requirement 3: "a treaty with no researched personnel rule must
        not receive RULE_DATA_INCOMPLETE merely because the optional
        field is empty"). Never blocks the treaty on its own either way
        (the caller combines this with the contribution-share/cultural
        gates independently, gated on `personnel_requirement is not
        None`) and is always disclosed, never silently "no requirement."
      - "any_one_of" roles: a SINGLE confirmed, satisfying role is
        immediate QUAL_QUALIFIES (Requirement 1 -- "a confirmed writer or
        director must receive immediate eligibility credit when that
        treaty/test accepts either role"), even if every OTHER eligible
        role is unattached/unknown/unconfirmed.
      - "all_of" roles: every eligible role must independently satisfy;
        any one FAILED (confirmed, known, wrong code) or unresolved
        (unattached/unconfirmed/unknown) keeps the whole gate short of
        QUALIFIES.
      - A confirmed, KNOWN fact that does not match eligible_codes is a
        real FAILED requirement (QUAL_HARD_FAIL for "all_of"; for
        "any_one_of" it only fails the WHOLE gate if every other eligible
        role also fails/unresolves) -- fail-closed, never silently
        skipped.
      - Unattached (open slot) -> QUAL_CURABLE_GAP if the role is
        castable pre-filing (_TREATY_CURABLE_ROLES), else QUAL_
        USER_FACT_REQUIRED.
      - Attached but UNCONFIRMED, or confirmed with an unknown fact ->
        QUAL_USER_FACT_REQUIRED -- a real conditional question, never
        credited as current eligibility, never silently dropped.
      - Nationality-only requirements never accept a residency fact as a
        substitute, and vice versa (fact_kind="either" is the ONLY case
        that accepts both) -- enforced by only ever reading the ONE
        typed field `requirement.fact_kind` names.
    """
    role_findings: list[RoleGateFinding] = []
    resolved: list[str] = []
    missing: list[str] = []
    failed: list[str] = []
    curable: list[str] = []
    levers: list[str] = []

    if requirement is None:
        return CanonicalQualificationResult(
            regime_id="treaty_personnel_gate", jurisdiction_code=None,
            state=QUAL_NOT_APPLICABLE, qualification_route="bilateral_treaty_personnel",
            missing_facts=(),
            available_levers=("Research and cite this treaty's own personnel-eligibility article "
                               "if one exists, to bring a real rule into this gate.",),
            authority_basis=None, confidence_state="LOW",
        )

    facts = attachment_facts or {}
    any_satisfied = False
    any_failed = False
    any_unresolved = False
    next_question: str | None = None

    for role in requirement.eligible_roles:
        role_facts = facts.get(role) or RoleAttachmentFacts()
        known_codes = (
            role_facts.confirmed_nationality if requirement.fact_kind == "nationality" else
            role_facts.confirmed_residency if requirement.fact_kind == "residency" else
            tuple(sorted(set(role_facts.confirmed_nationality) | set(role_facts.confirmed_residency)))
        )
        unknown_confirmed = (
            role_facts.confirmed_attached_unknown_nationality if requirement.fact_kind == "nationality" else
            role_facts.confirmed_attached_unknown_residency if requirement.fact_kind == "residency" else
            role_facts.confirmed_attached_unknown_nationality and role_facts.confirmed_attached_unknown_residency
        )
        matched = [c for c in known_codes if c in requirement.eligible_codes]
        if matched:
            any_satisfied = True
            resolved.append(f"{role} {requirement.fact_kind} {matched[0]} matches an eligible party code.")
            role_findings.append(RoleGateFinding(
                role=role, required_jurisdiction=None, status="satisfied",
                known_codes=known_codes, notes=f"Confirmed {role} {requirement.fact_kind} satisfies the treaty's own rule.",
            ))
            continue
        if known_codes:
            # a real, confirmed, KNOWN fact that does not match — a genuine failure, never silently skipped
            any_failed = True
            failed.append(f"{role} {requirement.fact_kind} {known_codes} does not match this treaty's eligible party codes {requirement.eligible_codes}.")
            role_findings.append(RoleGateFinding(
                role=role, required_jurisdiction=None, status="failed",
                known_codes=known_codes, notes="Confirmed fact known but does not satisfy the treaty's own rule.",
            ))
            continue
        # unresolved: unattached, unconfirmed, or confirmed-with-unknown-fact
        any_unresolved = True
        if not role_facts.has_any_attachment:
            if role in _TREATY_CURABLE_ROLES:
                curable.append(f"{role} is not yet attached — casting a {requirement.fact_kind} role from an eligible party country is a real, legal option before filing.")
                levers.append(f"Attach a {role} whose {requirement.fact_kind} is one of {requirement.eligible_codes}.")
                next_question = next_question or f"Has a {role} been attached, and what is their {requirement.fact_kind}?"
            else:
                missing.append(f"{role} is not attached and this role is not treated as pre-filing-castable for this gate.")
        elif role_facts.has_unconfirmed_attachment:
            missing.append(f"{role} has a proposed (unconfirmed) attachment — not yet credited as current eligibility.")
            levers.append(f"Confirm the proposed {role} attachment.")
            next_question = next_question or f"Should the proposed {role} attachment be confirmed?"
        else:
            # Confirmed attachment, but this exact fact_kind is not on
            # file for them (unknown_confirmed=True, OR a fact_kind
            # mismatch such as a residency-only record evaluated against
            # a nationality-only rule) — always a real, disclosed
            # conditional question, never silently dropped.
            missing.append(f"{role} is confirmed but their {requirement.fact_kind} is not on file.")
            levers.append(f"Record the confirmed {role}'s {requirement.fact_kind}.")
            next_question = next_question or f"What is the confirmed {role}'s {requirement.fact_kind}?"
        role_findings.append(RoleGateFinding(
            role=role, required_jurisdiction=None, status="indeterminate",
            known_codes=known_codes, notes="Unresolved — unattached, unconfirmed, or fact not on file.",
        ))

    if requirement.role_mode == "any_one_of":
        if any_satisfied:
            state = QUAL_QUALIFIES
        elif any_unresolved:
            state = QUAL_CURABLE_GAP if curable and not missing else QUAL_USER_FACT_REQUIRED
        else:
            state = QUAL_HARD_FAIL
    else:  # all_of
        if any_failed:
            state = QUAL_HARD_FAIL
        elif any_unresolved:
            state = QUAL_CURABLE_GAP if curable and not missing else QUAL_USER_FACT_REQUIRED
        elif any_satisfied:
            state = QUAL_QUALIFIES
        else:
            state = QUAL_RULE_DATA_INCOMPLETE

    return CanonicalQualificationResult(
        regime_id="treaty_personnel_gate", jurisdiction_code=None, state=state,
        qualification_route="bilateral_treaty_personnel",
        role_findings=tuple(role_findings),
        resolved_facts=tuple(resolved), missing_facts=tuple(missing),
        failed_requirements=tuple(failed), curable_requirements=tuple(curable),
        available_levers=tuple(levers),
        authority_basis=requirement.citation, confidence_state="HIGH" if requirement.citation else "LOW",
        reasoning_trace=(next_question,) if next_question else (),
    )


#: Maps a cultural-point-table criterion's CATEGORY to the real,
#: pre-existing ExtractedScriptElement.element_type it corresponds to
#: (see that model's own docstring: "location", "environment", "climate",
#: "character_nationality", "language", "cultural_reference",
#: "would_not_work_in"). No new taxonomy invented -- reuses exactly what
#: the Script Analyzer model already defines.
_SCRIPT_ELEMENT_TYPES_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "STORY_SETTING": ("location", "environment"),
    "LANGUAGE": ("language",),
    "SUBJECT_MATTER": ("cultural_reference", "character_nationality"),
}


async def script_facts_from_project(session: AsyncSession, project_id: str) -> dict[str, tuple[str, ...]]:
    """Real, DB-backed script-fact lookup, the SCRIPT_FACT counterpart to
    role_known_codes_from_project() above. Reads the project's actual
    persisted ExtractedScriptElement rows (via their owning
    ScreenplayDocument) and groups them by element_type. Presence of a
    row is treated as real evidence (consistent with the Script Analyzer
    SA-1 model's own documented convention: "presence is evidence, scale
    is not") -- absence is never silently treated as satisfying or
    failing a criterion, only as SCRIPT_FACT_REQUIRED (Task 4)."""
    rows = (await session.execute(
        select(ExtractedScriptElement.element_type, ExtractedScriptElement.normalized_value,
               ExtractedScriptElement.value)
        .join(ScreenplayDocument, ExtractedScriptElement.screenplay_id == ScreenplayDocument.id)
        .where(ScreenplayDocument.project_id == project_id)
    )).all()

    facts: dict[str, set[str]] = {}
    for element_type, normalized_value, value in rows:
        if not element_type:
            continue
        bucket = facts.setdefault(element_type, set())
        v = normalized_value or value
        if v:
            bucket.add(str(v))
    return {k: tuple(sorted(v)) for k, v in facts.items()}


#: cultural_qualification_model.role_known_codes_from_project()'s own
#: alias vocabulary (director/writer/producer/lead_cast/supporting_cast/
#: editor/composer) -- the exact set of CATEGORY_ROLE criterion `role`
#: values for which "no key present" reliably means "no person assigned
#: to this single-slot role yet" (a genuine, actionable CURABLE opening),
#: as opposed to an aggregate/whole-crew role (e.g. "entity") or a role
#: this project-personnel model doesn't yet capture at all (e.g.
#: "dop"/"vfx_supervisor"), where absence is a genuine missing PROJECT
#: FACT, not a known-open single slot.
_SINGLE_SLOT_ROLES: frozenset[str] = frozenset({
    "director", "writer", "producer", "lead_cast", "supporting_cast", "editor", "composer",
})


def evaluate_point_table_qualification(
    program_slug: str,
    jurisdiction_code: str | None,
    role_known_codes: dict[str, tuple[str, ...]],
    script_facts: dict[str, tuple[str, ...]],
    typed_personnel_facts: dict[str, dict[str, tuple[str, ...]]] | None = None,
) -> CanonicalQualificationResult:
    """Worldwide Qualification Consumption Closeout, Tasks 2/3/5/6 — the
    ONE consumption path for programs whose real, researched doctrine is
    a cultural POINT TABLE (cultural_point_tables.CULTURAL_POINT_TABLES),
    never forcing that data through the role-gate shape. Reuses the same
    project facts (role_known_codes, script_facts) the role-gate path
    already reads -- no new fact source, no new economics.

    typed_personnel_facts (Final Consolidated Backend Correction, Part
    4/CBA-004): the SEPARATE nationality-vs-residency breakdown from
    typed_personnel_facts_from_project(). Consumed ONLY for a criterion
    whose own fact_kind is NATIONALITY or RESIDENCY specifically (never
    EITHER, the default for every criterion not yet individually
    re-researched to confirm which one its real statutory wording
    requires) -- see the role-criterion branch below. Omitted (None)
    means every criterion falls back to the merged role_known_codes set,
    i.e. FACT_KIND_EITHER behavior regardless of any criterion's own
    declared fact_kind (a caller that hasn't fetched the typed facts
    cannot honor a distinction it has no data for -- never silently
    treated as a satisfied or failed nationality/residency check)."""
    table = CULTURAL_POINT_TABLES[program_slug]
    home_code = (jurisdiction_code or "").split("-")[0].upper() or None

    satisfied: list[tuple[str, float]] = []
    failed: list[tuple[str, float, str]] = []
    curable: list[tuple[str, float, str]] = []
    missing_user: list[tuple[str, float, str]] = []
    missing_script: list[tuple[str, float, str]] = []
    mandatory_failed: list[tuple[str, str]] = []

    for c in table.criteria:
        if c.category == CATEGORY_ROLE and c.fact_type == FACT_USER:
            # Final Consolidated Backend Correction, Part 4/CBA-004 -- a
            # criterion whose real fact_kind is confirmed NATIONALITY or
            # RESIDENCY reads the SEPARATE typed set for that kind only;
            # everything else (the default FACT_KIND_EITHER, or no typed
            # facts supplied at all) falls back to the merged
            # role_known_codes set -- byte-identical to prior behavior.
            if c.fact_kind != FACT_KIND_EITHER and typed_personnel_facts is not None:
                typed_kind = "nationality" if c.fact_kind == FACT_KIND_NATIONALITY else "residency"
                known = (typed_personnel_facts.get(c.role or "") or {}).get(typed_kind, ())
            else:
                known = role_known_codes.get(c.role or "")
            if known:
                if home_code and home_code in known:
                    satisfied.append((c.key, c.max_points))
                else:
                    note = f"{c.description} — known personnel do not match ({known})"
                    failed.append((c.key, c.max_points, note))
                    if c.hardness == CRITERION_MANDATORY:
                        mandatory_failed.append((c.key, note))
            elif c.role in _SINGLE_SLOT_ROLES:
                curable.append((c.key, c.max_points, f"{c.description} — role not yet cast/hired"))
            else:
                missing_user.append((c.key, c.max_points, f"{c.description} — no project fact on file for role '{c.role}'"))
        elif c.fact_type == FACT_SCRIPT:
            # CBA-003 fix (Codex audit 4db2cea, finding 3) — element_type
            # PRESENCE was previously treated as sufficient to satisfy any
            # criterion of that type, with no comparison to the criterion's
            # own jurisdiction. A Tokyo/US-English fact set could falsely
            # satisfy France-specific criteria for fr_trip purely because
            # a 'location'/'language' fact existed at all. Fixed: a real
            # semantic match (_script_fact_matches) against the criterion's
            # own jurisdiction_code (or the candidate's home_code as the
            # table's implicit "domestic" jurisdiction) is now required.
            element_types = _SCRIPT_ELEMENT_TYPES_BY_CATEGORY.get(c.category, ())
            extracted_values = [v for et in element_types for v in script_facts.get(et, ())]
            criterion_jurisdiction = c.jurisdiction_code or home_code
            if not extracted_values:
                missing_script.append((c.key, c.max_points, f"{c.description} — no Script Analyzer fact extracted"))
            elif any(_script_fact_matches(v, criterion_jurisdiction, c.expected_values) for v in extracted_values):
                satisfied.append((c.key, c.max_points))
            else:
                # A real fact WAS extracted (e.g. "Tokyo", "English") but
                # does not name this criterion's own jurisdiction — a
                # genuine, known NEGATIVE, not a missing fact. Never
                # silently treated as satisfied, never treated as merely
                # unknown (that would re-permit the same false positive
                # this fix closes, one level removed).
                failed.append((c.key, c.max_points,
                               f"{c.description} — extracted fact(s) {extracted_values} do not name "
                               f"{criterion_jurisdiction or 'the required jurisdiction'}"))
        else:
            # FACT_PRODUCTION — a project/production-plan fact (shoot days,
            # post-production location, spend split) this codebase does not
            # yet query live; Task 4 groups this with USER/PROJECT facts.
            missing_user.append((c.key, c.max_points, f"{c.description} — no production-plan fact on file"))

    if mandatory_failed:
        # Task 3 — a MANDATORY criterion is a hard gate, never merely a
        # points contribution: a known, confirmed violation HARD_FAILs
        # immediately regardless of how many points remain reachable
        # elsewhere in the table (mirrors the pre-existing role-gate
        # path's own has_failure -> QUAL_HARD_FAIL behavior exactly).
        return CanonicalQualificationResult(
            regime_id=program_slug, jurisdiction_code=jurisdiction_code,
            state=QUAL_HARD_FAIL, qualification_route="cultural_point_table",
            failed_requirements=tuple(f"{k}: {n}" for k, n in mandatory_failed),
            authority_basis=table.source_note,
            confidence_state="HIGH",
            reasoning_trace=(
                f"{program_slug}: a MANDATORY criterion is confirmed violated by known project facts — "
                "this hard-fails regardless of the point total, exactly like a mandatory role-gate "
                "violation.",
            ),
        )

    def _pts(items: list[tuple]) -> float:
        return sum(x[1] for x in items)

    confirmed_points = _pts(satisfied)
    # Several tables' structured criteria are a documented SUBSET of the
    # official point scale (e.g. Austria: 12 itemised criteria covering
    # 34 of the table's real 80 points -- Part B/C's remaining named
    # categories were not individually itemised here). Never let that
    # modeling gap silently produce a false HARD_FAIL: any gap between
    # the table's own declared total_points and the sum of the itemised
    # criteria is added to the CEILING only (never to confirmed_points),
    # disclosed as genuinely unmodeled headroom rather than fabricated
    # as a specific satisfied/missing criterion.
    modeled_max = sum(c.max_points for c in table.criteria)
    unmodeled_headroom = max(0.0, (table.total_points or modeled_max) - modeled_max)
    ceiling_points = confirmed_points + _pts(curable) + _pts(missing_user) + _pts(missing_script) + unmodeled_headroom

    def _sub_ok(min_required: float, keys: tuple[str, ...], pool: list[tuple[str, float]]) -> bool:
        return sum(p for k, p in pool if k in keys) >= min_required

    resolved_facts = tuple(f"{k}=satisfied(+{p}pt)" for k, p in satisfied)
    failed_requirements = tuple(f"{k}: {n}" for k, _, n in failed)
    curable_requirements = tuple(f"{k}: {n}" for k, _, n in curable)
    missing_facts = tuple(f"{k}: {n}" for k, _, n in (*missing_user, *missing_script))
    if unmodeled_headroom > 0:
        missing_facts = missing_facts + (
            f"unmodeled_headroom: +{unmodeled_headroom} pt available in official categories not yet "
            "individually itemised in cultural_point_tables.py — counted toward the ceiling, never toward "
            "confirmed_points, so this modeling gap can never produce a false QUALIFIES.",
        )
    available_levers = tuple(sorted({k for k, _, _ in curable}))

    common = dict(
        regime_id=program_slug, jurisdiction_code=jurisdiction_code,
        qualification_route="cultural_point_table",
        current_points=confirmed_points, required_points=table.threshold,
        role_findings=tuple(
            RoleGateFinding(role=c.role or c.key, required_jurisdiction=home_code,
                             status=(GateStatus.SATISFIED if c.key in {s[0] for s in satisfied}
                                     else GateStatus.FAILED if c.key in {f[0] for f in failed}
                                     else GateStatus.INDETERMINATE),
                             known_codes=role_known_codes.get(c.role or "", ()), notes=c.description)
            for c in table.criteria if c.category == CATEGORY_ROLE
        ),
        resolved_facts=resolved_facts, failed_requirements=failed_requirements,
        curable_requirements=curable_requirements, missing_facts=missing_facts,
        available_levers=available_levers,
        authority_basis=table.source_note,
    )

    if table.threshold is None:
        # An OPTIONAL rate-uplift table (e.g. Malaysia's FIMI +5%), not a
        # base-eligibility gate — the base program never depends on this
        # score. Real points are still disclosed (current_points/
        # available_levers) but the gate itself is NOT_APPLICABLE.
        return CanonicalQualificationResult(
            state=QUAL_NOT_APPLICABLE,
            confidence_state="HIGH",
            reasoning_trace=(
                f"{program_slug}: cultural point table confirmed ({len(table.criteria)} criteria, "
                f"{confirmed_points} of {table.total_points} confirmed points) but this table gates an "
                "OPTIONAL rate uplift, not base-program eligibility — no pass/fail threshold applies to "
                "the base incentive itself.",
            ),
            **common,
        )

    sub_ok = all(_sub_ok(min_pts, keys, satisfied) for _, min_pts, keys in table.sub_thresholds)
    sub_ceiling_ok = all(
        _sub_ok(min_pts, keys, satisfied + [(k, p) for k, p, _ in (*curable, *missing_user, *missing_script)])
        for _, min_pts, keys in table.sub_thresholds
    )

    if confirmed_points >= table.threshold and sub_ok:
        if table.completeness == TABLE_AUTHORITY_INCOMPLETE:
            # Part 3 / CBA-003 — quarantine. An aggregate/approximate
            # table (e.g. Croatia's real 8-item, 3-category-floor test
            # collapsed into one all-or-nothing 34-point row) can cross
            # its OWN threshold arithmetically without that being safe
            # deterministic evidence the real, itemised official test
            # would also pass — the aggregate cannot verify the real
            # sub-category floors or role-level allocation. Never emits
            # QUALIFIES from an authority-incomplete table; the real
            # official item-level breakdown remains a genuine, disclosed
            # authority residual.
            return CanonicalQualificationResult(
                state=QUAL_AUTHORITY_UNRESOLVED, confidence_state="LOW",
                qualification_route="cultural_point_table",
                regime_id=program_slug, jurisdiction_code=jurisdiction_code,
                current_points=confirmed_points, required_points=table.threshold,
                authority_basis=table.source_note,
                missing_facts=(
                    f"{program_slug}: the aggregate table's own arithmetic would cross the "
                    f"{table.threshold}-point threshold ({confirmed_points} confirmed), but this table is "
                    "AUTHORITY_INCOMPLETE (an aggregate/approximate representation, not the real itemised "
                    "official criteria) — quarantined from deterministic QUALIFIES per CBA-003. Required "
                    "fact type: the program's own official item-level point breakdown.",
                ),
                reasoning_trace=(
                    f"{program_slug}: AUTHORITY_INCOMPLETE table quarantined from deterministic admission — "
                    "see missing_facts for the exact residual.",
                ),
            )
        return CanonicalQualificationResult(
            state=QUAL_QUALIFIES, confidence_state="HIGH",
            reasoning_trace=(
                f"{program_slug}: confirmed {confirmed_points} of {table.threshold} required points "
                f"(table max {table.total_points}) — all sub-thresholds satisfied.",
            ),
            **common,
        )
    if ceiling_points < table.threshold or not sub_ceiling_ok:
        return CanonicalQualificationResult(
            state=QUAL_HARD_FAIL, confidence_state="HIGH",
            reasoning_trace=(
                f"{program_slug}: even crediting every curable/unknown criterion, the maximum reachable "
                f"score is {ceiling_points} against a required {table.threshold} (or a sub-threshold "
                "cannot mathematically be met) — this production cannot pass this cultural test as "
                "currently known.",
            ),
            **common,
        )
    if curable:
        return CanonicalQualificationResult(
            state=QUAL_CURABLE_GAP, confidence_state="MEDIUM",
            reasoning_trace=(
                f"{program_slug}: {confirmed_points} of {table.threshold} points confirmed; "
                f"{len(curable)} open role(s) not yet cast could close the gap "
                f"(+{_pts(curable)} pts available).",
            ),
            **common,
        )
    if missing_script:
        return CanonicalQualificationResult(
            state=QUAL_SCRIPT_FACT_REQUIRED, confidence_state="MEDIUM",
            reasoning_trace=(
                f"{program_slug}: {confirmed_points} of {table.threshold} points confirmed; "
                f"{len(missing_script)} script-derived criterion/criteria not yet extracted by the "
                "Script Analyzer.",
            ),
            **common,
        )
    return CanonicalQualificationResult(
        state=QUAL_USER_FACT_REQUIRED, confidence_state="MEDIUM",
        reasoning_trace=(
            f"{program_slug}: {confirmed_points} of {table.threshold} points confirmed; "
            f"{len(missing_user)} project/production-plan fact(s) still needed.",
        ),
        **common,
    )


def evaluate_discretionary_qualification(
    program_slug: str,
    jurisdiction_code: str | None,
) -> CanonicalQualificationResult:
    """Worldwide Qualification Consumption Closeout, Task 3/5 — the
    consumption path for programs whose real, confirmed mechanism is NOT
    a point table at all (cultural_point_tables.
    DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS): a binary legal-status
    determination (Belgium), an explicitly non-evaluated definitional
    gate (Finland), a discretionary committee (Luxembourg), or a
    competitive ranked-scoring scheme with no fixed threshold (Denmark).
    Each is genuinely resolved doctrine, not a research residual — never
    routed to RULE_DATA_INCOMPLETE or AUTHORITY_UNRESOLVED."""
    entry = DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS[program_slug]
    if entry["fact_type"] is None:
        # Finland: the Government Decree explicitly states artistic
        # content is NOT subject to evaluation — every qualifying-format
        # production automatically satisfies this dimension by design.
        return CanonicalQualificationResult(
            regime_id=program_slug, jurisdiction_code=jurisdiction_code,
            state=QUAL_QUALIFIES, qualification_route="non_evaluated_definitional_gate",
            authority_basis=entry["mechanism"],
            confidence_state="HIGH",
            reasoning_trace=(entry["description"],),
        )
    return CanonicalQualificationResult(
        regime_id=program_slug, jurisdiction_code=jurisdiction_code,
        state=QUAL_USER_FACT_REQUIRED, qualification_route="discretionary_or_definitional",
        missing_facts=(
            f"{program_slug}: {entry['mechanism']} — {entry['description']}",
        ),
        authority_basis=entry["mechanism"],
        confidence_state="MEDIUM",
        reasoning_trace=(
            f"{program_slug}'s cultural-qualification mechanism is confirmed ({entry['mechanism']}), but "
            "it resolves to a project-level fact (an authority determination on THIS specific project) "
            "that cannot be computed from personnel/script facts alone.",
        ),
    )


def evaluate_role_qualification(
    program_slug: str,
    jurisdiction_code: str | None,
    role_known_codes: dict[str, tuple[str, ...]],
    treaty_partner_code: str | None = None,
    script_facts: dict[str, tuple[str, ...]] | None = None,
    typed_personnel_facts: dict[str, dict[str, tuple[str, ...]]] | None = None,
) -> CanonicalQualificationResult:
    """Task 3/4/5 — the repaired seam. Reuses cultural_qualification_
    model.get_requirements()/evaluate_program_eligibility() UNCHANGED;
    this function only classifies the result into the canonical
    qualification-state vocabulary (Task 4) and preserves per-role
    findings (Task 5) rather than collapsing to one boolean.

    Worldwide Qualification Consumption Closeout (2026-08-19): before
    falling through to RULE_DATA_INCOMPLETE, this now checks TWO more
    accepted canonical doctrine sources — cultural_point_tables.
    CULTURAL_POINT_TABLES and .DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS —
    so real, researched Queue B doctrine that isn't shaped like a
    NationalityRequirement role gate still reaches a real terminal
    state. script_facts defaults to {} (never None passed through), so
    every caller not yet updated to supply it still gets a correct,
    conservative SCRIPT_FACT_REQUIRED / USER_FACT_REQUIRED result rather
    than an exception."""
    script_facts = script_facts or {}
    requirements = get_requirements(program_slug)
    if not requirements:
        if program_slug in AUTHORITY_UNRESOLVED_PROGRAMS:
            return _authority_unresolved_result(program_slug, jurisdiction_code)
        if program_slug in CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS:
            return _confirmed_test_scoring_withheld_result(program_slug, jurisdiction_code)
        if program_slug in CULTURAL_POINT_TABLES:
            return evaluate_point_table_qualification(
                program_slug, jurisdiction_code, role_known_codes, script_facts,
                typed_personnel_facts=typed_personnel_facts,
            )
        if program_slug in DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS:
            return evaluate_discretionary_qualification(program_slug, jurisdiction_code)
        # CBA-005 fix (Codex audit 4db2cea, finding 5) — NOT_APPLICABLE is
        # now derived DIRECTLY from program_requirements.py's own
        # cultural_test_required field (the single authoritative source),
        # never from a hand-maintained allowlist that can silently drift
        # out of sync with it. Confirmed defect this closes: 46 of 48
        # programs with cultural_test_required=False (every one NOT on
        # the old _SPEND_ONLY_SLUGS 2-entry allowlist) fell through to
        # RULE_DATA_INCOMPLETE despite their own canonical profile
        # already, correctly, recording that no cultural test applies.
        # is_spend_only_program() is kept as a redundant, harmless
        # secondary check (its 1-entry allowlist, au_location_offset, is
        # a strict subset of what the profile-driven check below already
        # covers) rather than deleted, to avoid a behavior change for any
        # caller that imports it directly.
        _profile = get_program_requirements(program_slug)
        if is_spend_only_program(program_slug) or (_profile is not None and _profile.cultural_test_required is False):
            return CanonicalQualificationResult(
                regime_id=program_slug, jurisdiction_code=jurisdiction_code,
                state=QUAL_NOT_APPLICABLE, qualification_route="role_nationality_gate",
                reasoning_trace=(
                    "Confirmed no-cultural-test program per program_requirements.py's own "
                    "cultural_test_required=False -- no nationality/role gate applies.",
                ),
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
