"""CONTENT / CENSORSHIP / CULTURAL-SUITABILITY GATES (2026-10-02) -- the one serving-time reader that turns the
content-related requirements the canonical registries ALREADY hold into typed, producer-facing gates.

Nothing here is new rule data and nothing is researched: every gate is derived from

  * ``ProgramRequirementsProfile`` structured fields (cultural test, mandatory pre-approval, local entity /
    co-producer, treaty requirement), and
  * the profile's ``additional_facts`` keys (free text that names a content-clearance / content-approval /
    content-exclusion / nationality-or-language / cultural-usage requirement), and
  * the program's RateRule conditions of kind ``cultural_test_required`` (the one content gate the pricing
    kernel actually evaluates).

Each gate is classified honestly into exactly one of

  CONFIRMED_MANDATORY_ELIGIBILITY_GATE   a statutory/administrative approval the program states it requires
  PROJECT_FACT_REQUIRED                  needs a project fact to resolve (a confirmation or a script content fact)
  ADVISORY_BUSINESS_RISK                 disclosed risk that is NOT program ineligibility (e.g. general censorship)
  MISSING_CANONICAL_DATA                 the requirement exists but no structured data/fact key exists to evaluate it

and carries ``consumed_by_optimizer`` (does pricing evaluate it) and the ProjectFact key under which a producer's
confirmation is stored (``evidenced_program_fact:<fact_key>``), so a stored confirmation is read, never ignored.

Rules (PROJECT_RULES / task contract):
  * a confirmed legal prohibition may be a hard block -- none is invented here; a gate is only a hard block when a
    stored fact says the approval was REFUSED (``refused``), never from country identity;
  * a missing approval / cultural fact is amber (needs facts);
  * general censorship / distribution risk is disclosed as advisory, never silently treated as program ineligibility;
  * a jurisdiction is never discarded because no content-risk profile exists.
"""
from __future__ import annotations

import re

CONFIRMED_MANDATORY = "CONFIRMED_MANDATORY_ELIGIBILITY_GATE"
PROJECT_FACT = "PROJECT_FACT_REQUIRED"
ADVISORY = "ADVISORY_BUSINESS_RISK"
MISSING_DATA = "MISSING_CANONICAL_DATA"

KIND_SCRIPT_CONTENT_CLEARANCE = "SCRIPT_CONTENT_CLEARANCE"
KIND_FILMING_NON_OBJECTION = "FILMING_NON_OBJECTION_CERTIFICATE"
KIND_CONTENT_APPROVAL = "CONTENT_APPROVAL"
KIND_PROHIBITED_CONTENT = "PROHIBITED_OR_EXCLUDED_CONTENT"
KIND_CULTURAL_TEST = "CULTURAL_TEST"
KIND_AGENCY_APPROVAL = "GOVERNMENT_AGENCY_PREAPPROVAL"
KIND_NATIONALITY_LANGUAGE = "NATIONALITY_OR_LANGUAGE_REQUIREMENT"
KIND_LOCAL_ENTITY = "LOCAL_ENTITY_OR_PARTNER"

#: additional_facts key / text patterns -> gate kind (first match wins). Keys are the canonical registry's own.
_KEY_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"content[_ ]?clearance", re.I), KIND_SCRIPT_CONTENT_CLEARANCE),
    (re.compile(r"content[_ ]?approval", re.I), KIND_CONTENT_APPROVAL),
    (re.compile(r"content[_ ]?exclusion|express[_ ]?exclusion|origin[_ ]?exclusion|no_canadian_content|eligible_work", re.I),
     KIND_PROHIBITED_CONTENT),
    (re.compile(r"cultural[_ ]?(test|usage|criterion)|culture[_ ]?test", re.I), KIND_CULTURAL_TEST),
    (re.compile(r"nationality|crew_nationality|language", re.I), KIND_NATIONALITY_LANGUAGE),
)
_NOC_TEXT = re.compile(r"non-?objection", re.I)
_CLEARANCE_TEXT = re.compile(r"script content clearance", re.I)

#: stored-value spellings
_TRUE = {"true", "1", "yes", "confirmed", "granted", "approved"}
_REFUSED = {"refused", "denied", "rejected", "prohibited"}


#: ProjectFact.fact_key is VARCHAR(100) including the 23-character storage prefix: the longest kind label is shortened.
_KEY_KIND = {KIND_AGENCY_APPROVAL: "agency_preapproval"}


def gate_effect(category: str, status: str) -> str:
    """The served effect of a gate's recorded state. Only an explicit refusal of a MANDATORY approval is a hard block; a
    refusal of any other resolvable gate stays conditional; an advisory risk never blocks; a missing confirmation is
    amber; a confirmation clears the gate."""
    if category == ADVISORY:
        return "ADVISORY"
    if status == "REFUSED":
        return "HARD_BLOCK" if category == CONFIRMED_MANDATORY else "NEEDS_FACTS"
    return "NONE" if status == "CONFIRMED" else "NEEDS_FACTS"


def gate_fact_key(program_slug: str, kind: str) -> str:
    """The ProjectFact fact_key (without the storage prefix) a producer's confirmation of this gate is stored under."""
    return f"{program_slug}__{_KEY_KIND.get(kind, kind.lower())}_confirmed"


def _evaluated_by_kernel(program_slug: str) -> bool:
    from app.data.program_rate_rules import get_rate_rules

    return any(c.kind == "cultural_test_required" for r in get_rate_rules(program_slug) for c in r.conditions)


def content_gates_for_program(program_slug: str | None, facts: dict[str, str] | None = None) -> list[dict]:
    """Typed content gates for one program, with the stored confirmation (if any) read from ``facts``
    (``{"evidenced_program_fact:<key>": value}``)."""
    if not program_slug:
        return []
    from app.data.program_requirements import get_program_requirements

    facts = facts or {}
    profile = get_program_requirements(program_slug)
    gates: list[dict] = []
    seen: set[str] = set()

    def add(kind: str, category: str, description: str, source: str, *, consumed: bool = False, key: str | None = None):
        if kind in seen:
            return
        seen.add(kind)
        fact_key = key or gate_fact_key(program_slug, kind)
        stored = facts.get("evidenced_program_fact:" + fact_key)
        status = (
            "REFUSED" if str(stored).strip().lower() in _REFUSED
            else "CONFIRMED" if str(stored).strip().lower() in _TRUE
            else "NOT_ON_FILE"
        ) if stored is not None else "NOT_ON_FILE"
        gates.append({
            "kind": kind, "category": category, "description": description, "source": source,
            "consumed_by_optimizer": consumed, "fact_key": fact_key, "stored_value": stored, "status": status,
            # Only an explicit refusal of a MANDATORY approval is ever a hard block; any other refusal (a project-fact gate)
            # stays conditional, an advisory risk never blocks, and a missing confirmation is amber.
            "effect": gate_effect(category, status),
            "resolvable": category != ADVISORY,
        })

    if profile is not None:
        if profile.cultural_test_required:
            add(KIND_CULTURAL_TEST, PROJECT_FACT,
                "A cultural test must be passed; its result is a project fact.",
                "ProgramRequirementsProfile.cultural_test_required",
                consumed=_evaluated_by_kernel(program_slug))
        if profile.preapproval_mandatory:
            add(KIND_AGENCY_APPROVAL, CONFIRMED_MANDATORY,
                "Application and approval by the program's agency is mandatory before production.",
                "ProgramRequirementsProfile.preapproval_mandatory", consumed=False)
        if profile.local_entity_required or profile.local_coproducer_required:
            add(KIND_LOCAL_ENTITY, CONFIRMED_MANDATORY,
                "A local entity or local co-producer/partner is required.",
                "ProgramRequirementsProfile.local_entity_required / local_coproducer_required", consumed=False)
        for key, text in (profile.additional_facts or {}).items():
            body = f"{key} {text}"
            kind = next((k for pat, k in _KEY_PATTERNS if pat.search(key)), None)
            if kind is None and _CLEARANCE_TEXT.search(body):
                kind = KIND_SCRIPT_CONTENT_CLEARANCE
            if kind is not None:
                category = (
                    CONFIRMED_MANDATORY if kind in (KIND_SCRIPT_CONTENT_CLEARANCE, KIND_CONTENT_APPROVAL)
                    else PROJECT_FACT if kind in (KIND_CULTURAL_TEST, KIND_PROHIBITED_CONTENT, KIND_NATIONALITY_LANGUAGE)
                    else MISSING_DATA
                )
                add(kind, category, " ".join(str(text).split())[:320], f"ProgramRequirementsProfile.additional_facts[{key}]",
                    consumed=(kind == KIND_CULTURAL_TEST and _evaluated_by_kernel(program_slug)))
            if _NOC_TEXT.search(body):
                add(KIND_FILMING_NON_OBJECTION, CONFIRMED_MANDATORY,
                    "A filming non-objection certificate is required before approval.",
                    f"ProgramRequirementsProfile.additional_facts[{key}]", consumed=False)
    return gates


def content_gate_summary(gates: list[dict]) -> dict:
    """Producer-readable roll-up used by the hover card / Inspector."""
    unresolved = [g for g in gates if g["status"] == "NOT_ON_FILE"]
    refused = [g for g in gates if g["status"] == "REFUSED"]
    return {
        "total": len(gates),
        "unresolved": len(unresolved),
        "refused": len(refused),
        "disconnected": sum(1 for g in gates if not g["consumed_by_optimizer"]),
        "note": (
            "Content, censorship and cultural requirements are disclosed per program. A missing approval or "
            "cultural fact keeps the jurisdiction visible as Needs More Facts; only a refused approval is a hard "
            "block. General censorship or distribution risk is a business risk, never program ineligibility, "
            "and country identity never implies a content failure."
        ),
    }


def content_gate_inventory() -> dict:
    """The canonical content-gate census over every registered program requirements profile."""
    from app.data.program_requirements import all_program_requirements

    by_kind: dict[str, int] = {}
    by_category: dict[str, int] = {}
    consumed = 0
    total = 0
    programs_with_gates = 0
    for slug in sorted(all_program_requirements()):
        gates = content_gates_for_program(slug)
        if gates:
            programs_with_gates += 1
        for g in gates:
            total += 1
            by_kind[g["kind"]] = by_kind.get(g["kind"], 0) + 1
            by_category[g["category"]] = by_category.get(g["category"], 0) + 1
            consumed += 1 if g["consumed_by_optimizer"] else 0
    return {
        "programs_with_requirements_profile": len(all_program_requirements()),
        "programs_with_content_related_gates": programs_with_gates,
        "gates_total": total,
        "gates_consumed_by_optimizer": consumed,
        "gates_present_but_not_consumed": total - consumed,
        "by_kind": by_kind,
        "by_category": by_category,
    }


# ── Producer-facing controls: the whitelist, the stored value and the fingerprint tokens ─────────────────────────────
GATE_FACT_PREFIX = "evidenced_program_fact:"
CONTROL_CONFIRMED = "confirmed"
CONTROL_REFUSED = "refused"
CONTROL_NOT_ON_FILE = "not_on_file"
CONTROL_VALUES = (CONTROL_CONFIRMED, CONTROL_REFUSED, CONTROL_NOT_ON_FILE)
_STORED = {CONTROL_CONFIRMED: "true", CONTROL_REFUSED: "refused"}


def gate_control_whitelist() -> dict[str, dict]:
    """{gate fact_key: gate} for every RESOLVABLE gate the registry actually serves (advisory risks are never a yes/no
    question). The ONLY keys the control may write."""
    from app.data.program_requirements import all_program_requirements

    out: dict[str, dict] = {}
    for slug in sorted(all_program_requirements()):
        for g in content_gates_for_program(slug):
            if g.get("resolvable"):
                out[g["fact_key"]] = {**g, "program_slug": slug}
    return out


def stored_value_for(control: str) -> str | None:
    return _STORED.get(control)


def gate_fingerprint_tokens(fact_rows) -> frozenset[str]:
    """Fingerprint participation of every recorded gate resolution (confirmed AND refused) -- a confirmed gate is also in
    the evidenced-fact set, a refusal is not, so both get an explicit state token."""
    out: set[str] = set()
    for row in fact_rows:
        key = getattr(row, "fact_key", "") or ""
        if not key.startswith(GATE_FACT_PREFIX):
            continue
        name = key[len(GATE_FACT_PREFIX):]
        value = str(getattr(row, "value", "") or "").strip().lower()
        if "__" not in name:
            continue
        if value in _TRUE:
            out.add(f"content_gate_confirmed:{name}")
        elif value in _REFUSED:
            out.add(f"content_gate_refused:{name}")
    return frozenset(out)
