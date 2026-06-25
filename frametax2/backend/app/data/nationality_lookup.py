"""
nationality_lookup.py

Nationality and residency verification for key production personnel.

Purpose:
  - Cultural tests
  - Treaty eligibility checks
  - Co-production qualification
  - Nationality-point optimization

Rules:
  - NEVER invent nationality. If a person is not in the verified static database,
    return confidence=UNKNOWN and flag for manual confirmation.
  - Only publicly verifiable, source-backed records are stored.
  - Residency is included only when publicly known.
  - Source URLs point to official records, Wikipedia, or press sources.

Roles tracked:
  cast, director, writer, producer, editor, composer,
  cinematographer, vfx_supervisor, animation_lead

Confidence tiers:
  HIGH    — government or official industry registry confirmed
  MEDIUM  — multiple corroborating public sources (press, Wikipedia)
  LOW     — single public source; may need verification
  UNKNOWN — not in database; manual confirmation required
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


LOOKUP_VERSION = "1.0.0"

ELIGIBLE_ROLES = frozenset({
    "cast",
    "director",
    "writer",
    "producer",
    "editor",
    "composer",
    "cinematographer",
    "vfx_supervisor",
    "animation_lead",
})


class ConfidenceTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class PersonNationality:
    name: str
    role: str

    citizenship: Optional[str]       # ISO2 country code or None
    dual_citizenship: list[str]       # additional ISO2 codes (may be empty)
    residency: Optional[str]          # ISO2 country code or None

    source_url: Optional[str]
    source_description: str           # e.g. "Wikipedia – 2024-11", "BAFTA registry"

    confidence: ConfidenceTier
    notes: str

    verified: bool
    manual_confirmation_required: bool

    # Point system helpers (populated by caller based on treaty rules)
    qualifies_uk_cultural_test: Optional[bool] = None
    qualifies_eu_coproduction: Optional[bool] = None
    nationality_points: dict[str, int] = field(default_factory=dict)

    def primary_citizenship_iso2(self) -> Optional[str]:
        return self.citizenship

    def all_citizenships(self) -> list[str]:
        result = []
        if self.citizenship:
            result.append(self.citizenship)
        result.extend(self.dual_citizenship)
        return result

    def is_eligible_for_treaty(self, treaty_country_iso2: str) -> Optional[bool]:
        """
        Returns True if person holds citizenship in treaty_country_iso2.
        Returns None if confidence is UNKNOWN (cannot determine).
        """
        if self.confidence == ConfidenceTier.UNKNOWN:
            return None
        return treaty_country_iso2.upper() in [c.upper() for c in self.all_citizenships()]

    def unknown_note(self) -> str:
        if not self.manual_confirmation_required:
            return ""
        return (
            f"[MANUAL CONFIRMATION REQUIRED] Nationality for '{self.name}' ({self.role}) "
            f"is not verified in the FrameTax database. "
            f"Provide citizenship documentation or a reliable public source to enable "
            f"cultural test scoring and treaty eligibility checks."
        )


# ---------------------------------------------------------------------------
# Static verified database
# ---------------------------------------------------------------------------
# Format per entry:
#   normalized_name (lowercase, stripped) → dict of fields
#
# Policy:
#   Only real, publicly documented persons may appear here.
#   Nationality must be supported by a citable public source.
#   Never add an entry for a private individual.
#   Data is sourced from Wikipedia, official government databases,
#   BAFTA/BFI/SAG-AFTRA registry records, or peer-reviewed industry sources.
#
# This database is intentionally sparse.
# The framework's value is in the UNKNOWN-handling and manual-confirm flow,
# not in enumerating every public figure.
# ---------------------------------------------------------------------------

_KNOWN_PERSONS: dict[str, dict] = {
    # Format: name_key → {citizenship, dual_citizenship, residency, source_url,
    #                      source_description, confidence, notes}
    # ------------------------------------------------------------------
    # Example entries for testing (all publicly documented):
    # ------------------------------------------------------------------
}

# NOTE: The database above is intentionally empty beyond documentation.
# Production-quality nationality data for specific projects should be
# entered via the FrameTax UI or imported from a signed talent contract.
# Automated enrichment requires explicit production company authorization
# and must not use AI-inferred nationality.


# ---------------------------------------------------------------------------
# Lookup engine
# ---------------------------------------------------------------------------

def _normalize_name(name: str) -> str:
    return " ".join(name.lower().strip().split())


def lookup_nationality(name: str, role: str) -> PersonNationality:
    """
    Look up nationality and residency for a named person.

    If the person is in the verified static database, returns their record.
    Otherwise, returns an UNKNOWN record flagged for manual confirmation.

    Args:
        name: Full name as entered or parsed from the project (cast list, contract, etc.)
        role: One of ELIGIBLE_ROLES; normalized to lowercase automatically.

    Returns:
        PersonNationality with confidence and manual_confirmation_required set.
    """
    role_norm = role.lower().strip()
    key = _normalize_name(name)

    if key in _KNOWN_PERSONS:
        data = _KNOWN_PERSONS[key]
        return PersonNationality(
            name=name,
            role=role_norm,
            citizenship=data.get("citizenship"),
            dual_citizenship=data.get("dual_citizenship", []),
            residency=data.get("residency"),
            source_url=data.get("source_url"),
            source_description=data.get("source_description", ""),
            confidence=ConfidenceTier(data.get("confidence", "MEDIUM")),
            notes=data.get("notes", ""),
            verified=True,
            manual_confirmation_required=False,
        )

    # Not in database → UNKNOWN, flag for manual confirmation
    return PersonNationality(
        name=name,
        role=role_norm,
        citizenship=None,
        dual_citizenship=[],
        residency=None,
        source_url=None,
        source_description="",
        confidence=ConfidenceTier.UNKNOWN,
        notes=(
            f"'{name}' is not in the FrameTax verified nationality database. "
            f"Manual confirmation required for cultural test scoring and treaty eligibility."
        ),
        verified=False,
        manual_confirmation_required=True,
    )


def lookup_batch(
    persons: list[tuple[str, str]],
) -> list[PersonNationality]:
    """
    Batch lookup for a crew/cast list.

    Args:
        persons: list of (name, role) tuples

    Returns:
        list of PersonNationality (one per input, preserving order)
    """
    return [lookup_nationality(name, role) for name, role in persons]


@dataclass
class NationalityReport:
    """
    Summary of nationality lookup results for a project's key personnel.
    Used for cultural test scoring and treaty eligibility assessment.
    """
    total_persons: int
    verified_count: int
    unknown_count: int
    manual_confirmation_required: list[str]
    by_citizenship: dict[str, list[str]]   # ISO2 → list of names
    persons: list[PersonNationality]
    confidence: str
    warnings: list[str]


def build_nationality_report(
    persons: list[tuple[str, str]],
) -> NationalityReport:
    """
    Run batch lookup and produce a summary report.

    Args:
        persons: list of (name, role) tuples

    Returns:
        NationalityReport with per-jurisdiction groupings and warnings.
    """
    results = lookup_batch(persons)

    verified = [p for p in results if p.verified]
    unknown = [p for p in results if not p.verified]

    by_citizenship: dict[str, list[str]] = {}
    for p in verified:
        for c in p.all_citizenships():
            if c:
                by_citizenship.setdefault(c.upper(), []).append(p.name)

    manual_needed = [p.name for p in unknown]

    warnings: list[str] = []
    if unknown:
        warnings.append(
            f"{len(unknown)} of {len(results)} persons have UNKNOWN nationality. "
            f"Cultural test scores and treaty eligibility cannot be calculated until "
            f"these are manually confirmed."
        )
    if not results:
        warnings.append("No persons submitted for nationality lookup.")

    confidence = "HIGH" if not unknown else ("MEDIUM" if len(unknown) < len(results) / 2 else "LOW")

    return NationalityReport(
        total_persons=len(results),
        verified_count=len(verified),
        unknown_count=len(unknown),
        manual_confirmation_required=manual_needed,
        by_citizenship=by_citizenship,
        persons=results,
        confidence=confidence,
        warnings=warnings,
    )


def add_verified_person(
    name: str,
    citizenship: str,
    dual_citizenship: Optional[list[str]] = None,
    residency: Optional[str] = None,
    source_url: Optional[str] = None,
    source_description: str = "",
    confidence: str = "MEDIUM",
    notes: str = "",
) -> None:
    """
    Register a verified person in the runtime lookup table.

    This function is for use by the FrameTax application layer when a user
    submits a verified nationality record (e.g., from a signed contract or
    production application). Data is NOT persisted to disk here — the
    caller is responsible for persistence.

    IMPORTANT: Never call this function with AI-inferred or guessed data.
    Only use when nationality is supported by a citable source.
    """
    if not citizenship or len(citizenship) != 2:
        raise ValueError(f"citizenship must be a 2-letter ISO country code, got: {citizenship!r}")

    key = _normalize_name(name)
    _KNOWN_PERSONS[key] = {
        "citizenship": citizenship.upper(),
        "dual_citizenship": [c.upper() for c in (dual_citizenship or [])],
        "residency": residency.upper() if residency else None,
        "source_url": source_url,
        "source_description": source_description,
        "confidence": confidence,
        "notes": notes,
    }
