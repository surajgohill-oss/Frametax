"""
little_utopia_people.py

Real, sourced key-personnel facts for The Little Utopia. Recovered from
the production's own Google Drive folder ("THE LITTLE UTOPIA") — the
real screenplay PDF, look book, and pitch deck all name the same
creative team, cross-verified against IMDb/Wikipedia:

  - Writer:    Clara Salaman (English/British novelist-screenwriter;
    "The Little Utopia" is adapted from her novel "The Boat").
  - Director:  Kim Farrant (Australian director, "Strangerland").
  - Producers: Rachel Winter (American, "Dallas Buyers Club") and
    Max Botkin (American, Major Chord Media, born Chicago, IL).
  - Lead cast: UNKNOWN. The production's own budget top sheet
    ("THE LITTLE UTOPIA Budget... CAST: tbc", dated 3 June 2025) and
    independent press coverage both confirm casting was not finalized/
    announced as of the source materials on file. A PRIOR session had
    recorded "Luke Evans" as a confirmed British lead — that fact had
    NO project-specific source (Kim Farrant worked with Luke Evans on a
    different, unrelated film, "Angel of Mine") and directly contradicts
    the production's own "CAST: tbc" notation. Corrected here: removed,
    not carried forward. Lead cast nationality is a real open question.

Residency is independently unverified for all four people (public
sources confirm citizenship/nationality, not tax/legal residency — the
two are different facts, stored separately per policy). Left UNKNOWN
rather than assumed equal to nationality.

Sources (fetched live this phase, not fabricated):
  - Clara Salaman: https://en.wikipedia.org/wiki/Clara_Salaman
  - Kim Farrant: https://en.wikipedia.org/wiki/Kim_Farrant
  - Rachel Winter: https://en.wikipedia.org/wiki/Rachel_Winter
  - Max Botkin: https://www.imdb.com/name/nm1363111/
  - Project confirmation (writer/director/producers, "CAST: tbc"):
    https://thecinemaholic.com/kim-farrant-to-direct-thriller-the-little-utopia-next/
    and the production's own budget PDF (Google Drive, "THE LITTLE
    UTOPIA" folder, "The Little Utopia Budget Mauritius 3rd June 2025").

Registers these into app.data.nationality_lookup's runtime verified-
person table (the existing, canonical nationality database — reused,
not duplicated) and exposes build_little_utopia_people(), which returns
PersonIntake objects ready for
production_package_intelligence.build_production_package(people=...).

Supports per-role nationality/residency OVERRIDE (a user-supplied
correction — e.g. once casting is announced, or a recast). Overrides
never touch the verified-person database; they are applied only at
PersonIntake-construction time, exactly like little_utopia_state.py's
existing fact-answer pattern. An override always applies to the
role's PRIMARY entry (index 0) — the only role with more than one
person is "producer" (Winter + Botkin); Botkin is not independently
overridable through this mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.calculators.production_package_intelligence import PersonIntake, PersonRole
from app.data.nationality_lookup import add_verified_person, lookup_nationality

PEOPLE_VERSION = "2.0.0"

# ── Register the real, sourced persons ───────────────────────────────────────
add_verified_person(
    "Clara Salaman", citizenship="GB", residency=None,
    source_url="https://en.wikipedia.org/wiki/Clara_Salaman",
    source_description="Wikipedia — English actress/novelist/screenwriter; wrote 'The Little Utopia', adapted from her novel 'The Boat'",
    confidence="HIGH", notes="Writer, The Little Utopia.",
)
add_verified_person(
    "Kim Farrant", citizenship="AU", residency=None,
    source_url="https://en.wikipedia.org/wiki/Kim_Farrant",
    source_description="Wikipedia/IMDb — Australian director ('Strangerland'); directing The Little Utopia",
    confidence="HIGH", notes="Director, The Little Utopia.",
)
add_verified_person(
    "Rachel Winter", citizenship="US", residency=None,
    source_url="https://en.wikipedia.org/wiki/Rachel_Winter",
    source_description="Wikipedia — American producer ('Dallas Buyers Club'); producing The Little Utopia",
    confidence="HIGH", notes="Producer, The Little Utopia.",
)
add_verified_person(
    "Max Botkin", citizenship="US", residency=None,
    source_url="https://www.imdb.com/name/nm1363111/",
    source_description="IMDb — American producer/writer, Major Chord Media, born Chicago IL; producing The Little Utopia",
    confidence="HIGH", notes="Producer, The Little Utopia.",
)
# Lead cast: deliberately NOT registered. The production's own budget top
# sheet says "CAST: tbc" (3 June 2025); no independent source confirms
# any actor's attachment. Left UNKNOWN so the Question Engine asks for
# it rather than guessing or repeating the prior session's uncorroborated
# "Luke Evans" entry.


@dataclass(frozen=True)
class PersonOverride:
    """A user-supplied correction to one role's nationality/residency,
    supported separately (a person can be a national of one country and
    a tax resident of another)."""
    nationality: Optional[str] = None
    residency: Optional[str] = None


# role key -> list of (person_id, name, PersonRole, verified-db lookup key)
_ROLE_SOURCE: dict[str, list[tuple[str, str, PersonRole, Optional[str]]]] = {
    "writer": [("writer-1", "Clara Salaman", PersonRole.WRITER, "Clara Salaman")],
    "director": [("director-1", "Kim Farrant", PersonRole.DIRECTOR, "Kim Farrant")],
    "lead_cast": [("cast-1", "Unannounced Lead Cast", PersonRole.CAST, None)],
    "producer": [
        ("producer-1", "Rachel Winter", PersonRole.PRODUCER, "Rachel Winter"),
        ("producer-2", "Max Botkin", PersonRole.PRODUCER, "Max Botkin"),
    ],
}

ROLE_KEYS: tuple[str, ...] = tuple(_ROLE_SOURCE)


def build_little_utopia_people(
    overrides: Optional[dict[str, PersonOverride]] = None,
) -> list[PersonIntake]:
    """Build the real Little Utopia PersonIntake list. `overrides` (role
    key -> PersonOverride) lets a caller correct/supply nationality or
    residency without touching the verified database — e.g. once casting
    is announced, or to model a recast for what-if propagation testing.
    Applies to the role's PRIMARY (first-listed) person only."""
    overrides = overrides or {}
    people: list[PersonIntake] = []
    for role_key, entries in _ROLE_SOURCE.items():
        override = overrides.get(role_key)
        for idx, (person_id, name, role, lookup_key) in enumerate(entries):
            if lookup_key is not None:
                verified = lookup_nationality(lookup_key, role.value)
                nationality = verified.citizenship
                residency = verified.residency
            else:
                nationality = None
                residency = None

            if override is not None and idx == 0:
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
