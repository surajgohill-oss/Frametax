"""
little_utopia_people.py

Real, verified key-personnel nationality facts for The Little Utopia —
reused verbatim from tests/validate_little_utopia_v2.py's "Team
nationality registration" section (the only place in this codebase these
facts were previously entered). NOT fabricated: every entry here already
existed, sourced from Wikipedia / producer confirmation, before this
integration phase began.

  - Writer:      British (GB). Name not on file — "confirmed by producer".
  - Director:    Australian (AU). Name not on file — "confirmed by producer".
  - Lead cast:   Luke Evans, British/Welsh (GB). Wikipedia-sourced.
  - Producer:    NOT on file anywhere in this codebase. Left UNKNOWN so
    the Question Engine (production_package_intelligence.py's
    MISSING-NATIONALITY-* mechanism) asks for it rather than guessing.

Registers these into app.data.nationality_lookup's runtime verified-
person table (the existing, canonical nationality database — reused,
not duplicated) and exposes build_little_utopia_people(), which returns
PersonIntake objects ready for
production_package_intelligence.build_production_package(people=...).

Supports per-role nationality/residency OVERRIDE (a user-supplied
correction — e.g. a real producer's name/nationality once known, or a
recast). Overrides never touch the verified-person database; they are
applied only at PersonIntake-construction time, exactly like
little_utopia_state.py's existing fact-answer pattern.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.calculators.production_package_intelligence import PersonIntake, PersonRole
from app.data.nationality_lookup import add_verified_person, lookup_nationality

PEOPLE_VERSION = "1.0.0"

# ── Register the real, sourced persons (identical to validate_little_utopia_v2.py) ──
add_verified_person(
    "Luke Evans", citizenship="GB", residency="GB",
    source_url="https://en.wikipedia.org/wiki/Luke_Evans_(actor)",
    source_description="Wikipedia — born Pontypool, Wales; British actor",
    confidence="HIGH", notes="Lead actor. Welsh/British national.",
)
add_verified_person(
    "Unknown Director", citizenship="AU", residency="AU",
    source_url="", source_description="Confirmed by producer",
    confidence="HIGH", notes="Director, The Little Utopia. Australian national.",
)
add_verified_person(
    "Unknown Writer", citizenship="GB", residency="GB",
    source_url="", source_description="Confirmed by producer",
    confidence="HIGH", notes="Writer, The Little Utopia. British national.",
)
# Producer: deliberately NOT registered. No source exists anywhere in
# this codebase for a real producer name or nationality. Left absent so
# the Question Engine surfaces MISSING-NATIONALITY-producer-1 rather
# than a guess.


@dataclass(frozen=True)
class PersonOverride:
    """A user-supplied correction to one role's nationality/residency,
    supported separately (a person can be a national of one country and
    a tax resident of another)."""
    nationality: Optional[str] = None
    residency: Optional[str] = None


# role key -> (person_id, name, PersonRole, verified-db lookup key)
_ROLE_SOURCE: dict[str, tuple[str, str, PersonRole, str]] = {
    "writer": ("writer-1", "Unknown Writer", PersonRole.WRITER, "Unknown Writer"),
    "director": ("director-1", "Unknown Director", PersonRole.DIRECTOR, "Unknown Director"),
    "lead_cast": ("cast-1", "Luke Evans", PersonRole.CAST, "Luke Evans"),
    "producer": ("producer-1", "Unknown Producer", PersonRole.PRODUCER, None),
}

ROLE_KEYS: tuple[str, ...] = tuple(_ROLE_SOURCE)


def build_little_utopia_people(
    overrides: Optional[dict[str, PersonOverride]] = None,
) -> list[PersonIntake]:
    """Build the real Little Utopia PersonIntake list. `overrides` (role
    key -> PersonOverride) lets a caller correct/supply nationality or
    residency without touching the verified database — e.g. once a real
    producer name is confirmed, or to model a recast for what-if
    propagation testing."""
    overrides = overrides or {}
    people: list[PersonIntake] = []
    for role_key, (person_id, name, role, lookup_key) in _ROLE_SOURCE.items():
        override = overrides.get(role_key)

        if lookup_key is not None:
            verified = lookup_nationality(lookup_key, role.value)
            nationality = verified.citizenship
            residency = verified.residency
        else:
            nationality = None
            residency = None

        if override is not None:
            if override.nationality is not None:
                nationality = override.nationality
            if override.residency is not None:
                residency = override.residency

        people.append(PersonIntake(
            person_id=person_id,
            name=name,
            role=role,
            nationality=nationality,
            residency=residency,
        ))
    return people
