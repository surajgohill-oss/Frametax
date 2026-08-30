"""
talent_nationality_resolution.py

Person Nationality Resolution — canonical talent enrichment.

Once a real person's identity has been established from project source
material (a ProjectPerson/TalentProfile row already exists), this module
attempts to resolve their documented country of citizenship from a
structured public source (Wikidata) and persists the result onto the
SAME canonical TalentProfile row — never a parallel person database.

Hard rules (enforced, not merely intended):
  * Nationality is NEVER inferred from name, appearance, residence,
    place of birth alone, or production location. Only a structured
    "country of citizenship" (Wikidata P27) claim counts as evidence.
  * A name match alone never resolves identity. The candidate's
    documented occupation (Wikidata P106) must corroborate the person's
    known project role (writer/director/producer/actor/...) before any
    citizenship claim is trusted. No corroboration -> unresolved.
  * Multiple documented citizenships are never collapsed silently — all
    are preserved in nationality_evidence; only ONE becomes
    primary_nationality (the canonical single-value field every
    qualification engine already reads), per this module's own minimal,
    documented selection rule (first-ranked/first-listed claim), because
    no richer canonical doctrine for "which of several citizenships is
    primary" exists yet.
  * An explicit producer/user value (fact precedence — ProjectPerson
    edits from the Production Facts panel) is NEVER overwritten by this
    resolver. Callers must check is_confirmed before invoking it, and
    this module itself refuses to run against a confirmed row.
  * A lookup failure (network error, no match, ambiguous match) is a
    disclosed resolution state, never a silently-skipped no-op and never
    a fabricated fallback value.
  * No re-run on every read: this is invoked explicitly (new person
    established, or an explicit refresh), never from an Overview render.

No LLM calls. One HTTP-calling external adapter, reused for both
identity search and citizenship lookup — no second resolver, no scraping.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile

WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_DATA_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
_TIMEOUT_S = 8.0
_USER_AGENT = "CineGlobe-TalentNationalityResolver/1.0 (internal production tool)"

#: Project role -> corroborating Wikidata occupation QIDs. A candidate's
#: own P106 (occupation) claims must intersect this set for the role, or
#: the match is rejected regardless of how well the name matches.
_ROLE_OCCUPATION_QIDS: dict[str, frozenset[str]] = {
    "writer": frozenset({"Q28389", "Q36180", "Q6625963"}),  # screenwriter, writer, novelist
    "director": frozenset({"Q2526255", "Q3455803"}),  # film director, director
    "producer": frozenset({"Q3282637", "Q2500638"}),  # film producer, producer
    "lead_cast": frozenset({"Q33999", "Q10800557"}),  # actor, film actor
    "lead_cast_2": frozenset({"Q33999", "Q10800557"}),
    "lead_cast_3": frozenset({"Q33999", "Q10800557"}),
    "dop": frozenset({"Q222344"}),  # cinematographer
    "editor": frozenset({"Q1114448"}),  # film editor
    "composer": frozenset({"Q36834", "Q1198887"}),  # composer, film score composer
}

RESOLVED = "resolved"
UNRESOLVED_NO_MATCH = "unresolved_no_match"
UNRESOLVED_AMBIGUOUS = "unresolved_ambiguous"
LOOKUP_FAILED = "lookup_failed"
NOT_ATTEMPTED = "not_attempted"


@dataclass(frozen=True)
class CitizenshipClaim:
    qid: str            # the country's Wikidata entity id, e.g. "Q30"
    label: str          # human-readable country name, e.g. "United States of America"
    iso2: str | None     # ISO 3166-1 alpha-2 code if the country entity states one


@dataclass(frozen=True)
class PersonResolutionResult:
    status: str  # one of the module-level status constants
    matched_entity_id: str | None = None
    matched_label: str | None = None
    match_evidence: str | None = None  # human-readable disambiguation reasoning
    citizenships: tuple[CitizenshipClaim, ...] = field(default_factory=tuple)
    primary_iso2: str | None = None
    error: str | None = None
    resolved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


async def _wikidata_search(client: httpx.AsyncClient, name: str) -> list[dict]:
    resp = await client.get(WIKIDATA_SEARCH_URL, params={
        "action": "wbsearchentities", "search": name, "language": "en",
        "type": "item", "format": "json", "limit": 5,
    }, headers={"User-Agent": _USER_AGENT}, timeout=_TIMEOUT_S)
    resp.raise_for_status()
    return resp.json().get("search", [])


async def _wikidata_entity(client: httpx.AsyncClient, qid: str) -> dict | None:
    resp = await client.get(
        WIKIDATA_ENTITY_DATA_URL.format(qid=qid),
        headers={"User-Agent": _USER_AGENT}, timeout=_TIMEOUT_S,
    )
    resp.raise_for_status()
    entities = resp.json().get("entities", {})
    return entities.get(qid)


def _claim_qids(entity: dict, prop: str) -> list[str]:
    claims = (entity.get("claims") or {}).get(prop) or []
    out = []
    for c in claims:
        try:
            out.append(c["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            continue
    return out


def _claim_string(entity: dict, prop: str) -> str | None:
    claims = (entity.get("claims") or {}).get(prop) or []
    for c in claims:
        try:
            return c["mainsnak"]["datavalue"]["value"]
        except (KeyError, TypeError):
            continue
    return None


def _english_label(entity: dict) -> str | None:
    try:
        return entity["labels"]["en"]["value"]
    except (KeyError, TypeError):
        return None


async def resolve_person_nationality(name: str, role: str) -> PersonResolutionResult:
    """Resolves ONE person's documented country of citizenship from
    Wikidata, corroborated against their known project role. Never
    raises on a network/lookup failure — returns a LOOKUP_FAILED result
    instead, so enrichment can never break the caller."""
    occupation_qids = _ROLE_OCCUPATION_QIDS.get(role)
    if not occupation_qids:
        return PersonResolutionResult(
            status=UNRESOLVED_NO_MATCH,
            error=f"No corroborating occupation vocabulary defined for role '{role}'.",
        )

    try:
        async with httpx.AsyncClient() as client:
            candidates = await _wikidata_search(client, name)
            if not candidates:
                return PersonResolutionResult(status=UNRESOLVED_NO_MATCH, error="No Wikidata entity matched this name.")

            matches: list[tuple[dict, dict]] = []  # (search_hit, full_entity)
            for hit in candidates:
                qid = hit.get("id")
                if not qid:
                    continue
                entity = await _wikidata_entity(client, qid)
                if entity is None:
                    continue
                entity_occupations = set(_claim_qids(entity, "P106"))
                if entity_occupations & occupation_qids:
                    matches.append((hit, entity))

            if not matches:
                return PersonResolutionResult(
                    status=UNRESOLVED_NO_MATCH,
                    error=(
                        f"{len(candidates)} candidate(s) matched the name, but none had a "
                        f"documented occupation corroborating role '{role}'."
                    ),
                )
            if len(matches) > 1:
                labels = ", ".join(h.get("id", "?") for h, _ in matches)
                return PersonResolutionResult(
                    status=UNRESOLVED_AMBIGUOUS,
                    error=f"Multiple candidates ({labels}) both match the name and corroborate role '{role}'.",
                )

            hit, entity = matches[0]
            qid = hit["id"]
            label = _english_label(entity) or hit.get("label") or name
            citizenship_qids = _claim_qids(entity, "P27")
            if not citizenship_qids:
                return PersonResolutionResult(
                    status=UNRESOLVED_NO_MATCH,
                    matched_entity_id=qid, matched_label=label,
                    match_evidence=f"Identity matched via occupation corroboration for role '{role}'.",
                    error="Identity matched, but no P27 (country of citizenship) claim is documented.",
                )

            citizenships: list[CitizenshipClaim] = []
            for cqid in citizenship_qids:
                country_entity = await _wikidata_entity(client, cqid)
                if country_entity is None:
                    continue
                iso2 = _claim_string(country_entity, "P297")
                citizenships.append(CitizenshipClaim(
                    qid=cqid, label=_english_label(country_entity) or cqid, iso2=iso2,
                ))

            primary_iso2 = next((c.iso2 for c in citizenships if c.iso2), None)
            return PersonResolutionResult(
                status=RESOLVED,
                matched_entity_id=qid, matched_label=label,
                match_evidence=f"Identity matched via occupation corroboration for role '{role}'.",
                citizenships=tuple(citizenships),
                primary_iso2=primary_iso2,
            )
    except httpx.HTTPError as exc:
        return PersonResolutionResult(status=LOOKUP_FAILED, error=f"{type(exc).__name__}: {exc}")


def _evidence_json(result: PersonResolutionResult) -> list[dict]:
    return [
        {"qid": c.qid, "label": c.label, "iso2": c.iso2}
        for c in result.citizenships
    ] + ([{"match_evidence": result.match_evidence}] if result.match_evidence else []) + (
        [{"error": result.error}] if result.error else []
    )


async def enrich_talent_nationality(
    session: AsyncSession, *, project_person: ProjectPerson, talent: TalentProfile,
) -> PersonResolutionResult | None:
    """Runs the resolver for ONE canonical person and persists the result
    onto the SAME TalentProfile row. Fact precedence (Section 8): a
    producer-confirmed ProjectPerson is never touched — returns None
    without calling the resolver at all. Every attempt (resolved or not)
    is recorded on the talent row; only a RESOLVED result with a real
    ISO2 code ever sets primary_nationality, and only when the row does
    not already carry an explicit value."""
    if project_person.is_confirmed:
        return None

    result = await resolve_person_nationality(talent.name, talent.role)

    talent.nationality_resolution_status = result.status
    talent.nationality_source = "wikidata"
    talent.nationality_source_entity_id = result.matched_entity_id
    talent.nationality_evidence = _evidence_json(result)
    talent.nationality_confidence = "DISCOVERY" if result.status == RESOLVED else None
    talent.nationality_resolved_at = result.resolved_at

    if result.status == RESOLVED and result.primary_iso2 and not talent.primary_nationality:
        talent.primary_nationality = result.primary_iso2

    await session.flush()
    return result


async def enrich_project_personnel(session: AsyncSession, *, project_id) -> list[dict]:
    """Batch entry point: resolves nationality for every currently-
    unconfirmed, not-yet-attempted person attached to a project. Never
    re-runs an already-attempted resolution (idempotent by design — call
    it again explicitly, e.g. a producer's "refresh" action, to retry).
    Returns one summary dict per person actually attempted."""
    rows = (await session.execute(
        select(ProjectPerson, TalentProfile)
        .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
        .where(ProjectPerson.project_id == project_id)
    )).all()

    summaries: list[dict] = []
    for pp, talent in rows:
        if pp.is_confirmed or talent.nationality_resolution_status is not None:
            continue
        result = await enrich_talent_nationality(session, project_person=pp, talent=talent)
        if result is None:
            continue
        summaries.append({
            "name": talent.name, "role": talent.role, "status": result.status,
            "matched_entity_id": result.matched_entity_id,
            "primary_nationality": talent.primary_nationality,
        })
    return summaries
