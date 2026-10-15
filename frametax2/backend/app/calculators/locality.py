"""The ONE canonical locality resolver (NA-RECONCILIATION-23).

Locality is never inferred from a jurisdiction alone. The inputs are explicit production locations - a retained schedule location or a location the producer selected for a scenario - each with a
jurisdiction, optionally a city, a county, shooting days, and attributes the producer or an authority asserted (each with its source, method and confidence). This module is pure: it resolves
each location against the classification datasets the repository actually holds, reports every classification it could NOT resolve with the exact source still required, and reduces the
locations to numeric `locality:*` facts (days at qualifying / non-qualifying / unclassified locations per jurisdiction) that flow through the existing amount-fact path and the evaluation fingerprint.

Datasets held (each record carries source, version and effective date):
  * Missouri county classification (RSMo 48.020), Missouri Association of Counties "Counties by Classification" (published May 2025): a county named in the list is resolved; a county absent from it is
    Unknown. The published list transcribes 113 of the 114 counties (its class-1 row shows 12 of 13), so one class-1 county is not in the dataset and resolves to Unknown, never guessed.
Datasets NOT held, left OPEN (see OPEN_CLASSIFICATIONS): rural / blighted status of a place, the BC designated Vancouver area boundary, and the official coordinates of the Halifax, Fredericton, Moncton,
Saint John, Regina and Saskatoon reference points. Until they exist, those classifications are resolved only from an explicit attribute with its provenance (a producer-measured distance or a stated zone).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Mapping

# ── datasets ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
MO_COUNTY_DATASET = {
    "id": "MO_COUNTY_CLASSIFICATION_2025",
    "source": "Missouri Association of Counties, 'Missouri Counties by Classification' (published May 2025; classes defined by RSMo 48.020)",
    "url": "https://www.mocounties.com/s/Missouri-Counties-by-Classification-2025.pdf",
    "version": "2025-05",
    "effective_date": "2025-05-01",
    "retrieved": "2026-10-15",
    "confidence": "HIGH_FOR_LISTED_COUNTIES",
    "stated_totals": {"charter": 5, "1": 13, "2": 3, "3": 89, "4": 4},
}
_MO_CLASSES: dict[str, tuple[str, ...]] = {
    "charter": ("Clay", "Jackson", "Jefferson", "St. Charles", "St. Louis"),
    "1": ("Boone", "Buchanan", "Camden", "Cape Girardeau", "Cass", "Christian", "Franklin", "Greene", "Jasper", "Platte", "St. Francois", "Taney"),
    "2": ("Callaway", "Lincoln", "Newton"),
    "3": ("Adair", "Andrew", "Atchison", "Audrain", "Barry", "Barton", "Bates", "Benton", "Bollinger", "Butler", "Caldwell", "Carroll", "Carter", "Cedar", "Chariton", "Clark", "Clinton", "Cooper",
          "Crawford", "Dade", "Dallas", "Daviess", "DeKalb", "Dent", "Douglas", "Dunklin", "Gasconade", "Gentry", "Grundy", "Harrison", "Henry", "Hickory", "Holt", "Howard", "Howell", "Iron", "Knox",
          "Laclede", "Lawrence", "Lewis", "Linn", "Livingston", "McDonald", "Macon", "Madison", "Maries", "Marion", "Mercer", "Miller", "Mississippi", "Moniteau", "Monroe", "Montgomery", "Morgan",
          "New Madrid", "Nodaway", "Oregon", "Osage", "Ozark", "Pemiscot", "Perry", "Phelps", "Pike", "Polk", "Pulaski", "Putnam", "Ralls", "Randolph", "Ray", "Reynolds", "Ripley", "St. Clair",
          "Ste. Genevieve", "Schuyler", "Scotland", "Scott", "Shannon", "Shelby", "Stoddard", "Stone", "Sullivan", "Texas", "Vernon", "Warren", "Washington", "Wayne", "Webster", "Worth", "Wright"),
    "4": ("Johnson", "Lafayette", "Pettis", "Saline"),
}
#: RSMo 135.750 subsection 3(6): a project in a county of the second, third or fourth class.
MO_QUALIFYING_CLASSES = frozenset({"2", "3", "4"})


def _norm_county(name: str) -> str:
    n = re.sub(r"\bcounty\b", "", str(name or "").lower())
    n = re.sub(r"\bsaint\b", "st", n)
    n = re.sub(r"\bste\b", "ste", n)
    return re.sub(r"[^a-z]", "", n)


_MO_INDEX = {_norm_county(c): cls for cls, names in _MO_CLASSES.items() for c in names}

#: Classifications the repository holds no dataset for, with the exact source still required.
OPEN_CLASSIFICATIONS: dict[str, str] = {
    "mo_rural_or_blighted": "A Missouri Department of Economic Development determination (or the statutory definitions of 'rural' and 'blighted area' applied to a place dataset) for each filming location; the producer may assert it per location with the source.",
    "bc_zone": "The Film and Television Tax Credit Regulation / Creative BC regional and distant location map: a machine-readable boundary of the designated Vancouver area (and of 'the area that extends north to Whistler and east to Hope').",
    "ns_distance": "Official coordinates of Halifax City Hall and a geocoder for the filming location (NSFPIF Guidelines s.6.1: more than 100 km, more than 150 km).",
    "nb_distance": "Official coordinates of Fredericton, Moncton and Saint John City Halls and a geocoder for the filming location (LIFT 2026/2027: 30-150 km, 151 km and over).",
    "sk_distance": "Official coordinates of the centre-most points of Regina and Saskatoon and a geocoder for the filming location (FFTV Guidelines: at least 50 km outside).",
}

# ── entries ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ATTRIBUTES = ("rural_or_blighted", "bc_zone", "ns_distance_km", "nb_distance_km", "sk_distance_km")
BC_ZONES = ("vancouver", "regional", "distant")
RESOLUTION_METHODS = ("PRODUCER_ASSERTED", "PRODUCER_MEASURED", "AUTHORITY_DETERMINATION", "DATASET_LOOKUP")
CONFIDENCES = ("STATED", "MEASURED", "AUTHORITATIVE")
JURISDICTION_RE = re.compile(r"^[A-Z]{2}(-[A-Z0-9]{1,4})?$")


@dataclass(frozen=True)
class Predicate:
    key: str
    jurisdiction: str
    label: str
    mode: str                     # "share" (a share of the days) | "all" (every location)
    fact_key: str | None = None   # the boolean evidence key it establishes
    day_fact: str | None = None   # the amount fact (day count) it establishes
    min_share: float | None = None


PREDICATES: tuple[Predicate, ...] = (
    Predicate("mo_county_qualifying", "US-MO", "second-, third- or fourth-class county", "all", fact_key="mo_second_third_fourth_class_county_confirmed"),
    Predicate("mo_rural_or_blighted", "US-MO", "rural or blighted area", "share", fact_key="mo_rural_or_blighted_15pct_confirmed", min_share=0.15),
    Predicate("bc_outside_vancouver", "CA-BC", "outside the designated Vancouver area", "share", day_fact="ca_bc_principal_photography_days_outside_vancouver"),
    Predicate("bc_distant", "CA-BC", "distant location", "share", day_fact="ca_bc_principal_photography_days_distant_location"),
    Predicate("ns_zone_a", "CA-NS", "more than 100 km and up to 150 km from Halifax City Hall", "share", day_fact="ca_ns_principal_photography_days_100_to_150km"),
    Predicate("ns_zone_b", "CA-NS", "more than 150 km from Halifax City Hall", "share", day_fact="ca_ns_principal_photography_days_over_150km"),
    Predicate("nb_rural", "CA-NB", "30 to 150 km from the nearest NB city hall", "share", day_fact="ca_nb_days_rural_30_to_150km"),
    Predicate("nb_remote", "CA-NB", "151 km or more from the nearest NB city hall", "share", day_fact="ca_nb_days_remote_151km_plus"),
    Predicate("sk_rural50", "CA-SK", "at least 50 km outside Regina and Saskatoon", "share", day_fact="ca_sk_days_50km_outside_regina_saskatoon"),
)
PREDICATE_BY_KEY = {p.key: p for p in PREDICATES}


@dataclass(frozen=True)
class LocationEntry:
    id: str
    label: str
    jurisdiction_code: str
    role: str = "SELECTED"                      # SELECTED (a location chosen for a scenario) | SCHEDULE (a retained schedule location)
    city: str | None = None
    county: str | None = None
    days: int | None = None
    attributes: Mapping = field(default_factory=dict)     # name -> value
    evidence: Mapping = field(default_factory=dict)       # name -> {source, method, confidence, version?, effective_date?}


@dataclass(frozen=True)
class ResolvedLocation:
    entry: LocationEntry
    states: dict                                # predicate key -> True | False | None
    resolution: dict                            # predicate key (or 'county_class') -> {value, source, method, confidence, version, effective_date}
    unresolved: dict                            # classification -> exact source still required


def validate_entry(raw: Mapping) -> LocationEntry:
    """ValueError for an invalid location; nothing is defaulted."""
    eid = str(raw.get("id") or "").strip()
    if not eid or len(eid) > 40:
        raise ValueError("a location needs an id of at most 40 characters")
    code = str(raw.get("jurisdiction_code") or "").strip().upper()
    if not JURISDICTION_RE.match(code):
        raise ValueError(f"location {eid}: jurisdiction_code must be a jurisdiction code such as US-MO")
    role = raw.get("role") or "SELECTED"
    if role not in ("SELECTED", "SCHEDULE"):
        raise ValueError(f"location {eid}: role must be SELECTED or SCHEDULE")
    days = raw.get("days")
    if days is not None:
        if isinstance(days, bool) or not isinstance(days, (int, float)) or not math.isfinite(days) or abs(days - round(days)) > 1e-9 or days < 0 or days > 2000:
            raise ValueError(f"location {eid}: days must be a whole number between 0 and 2000, or null (Unknown)")
        days = int(round(days))
    attrs, evid = {}, {}
    for name, value in (raw.get("attributes") or {}).items():
        if name not in ATTRIBUTES:
            raise ValueError(f"location {eid}: '{name}' is not a locality attribute")
        ev = (raw.get("evidence") or {}).get(name) or {}
        if not str(ev.get("source") or "").strip():
            raise ValueError(f"location {eid}: attribute '{name}' needs its source")
        if ev.get("method") not in RESOLUTION_METHODS or ev.get("confidence") not in CONFIDENCES:
            raise ValueError(f"location {eid}: attribute '{name}' needs a method {RESOLUTION_METHODS} and a confidence {CONFIDENCES}")
        if value is None:
            continue
        if name == "rural_or_blighted" and not isinstance(value, bool):
            raise ValueError(f"location {eid}: rural_or_blighted must be true or false")
        if name == "bc_zone" and value not in BC_ZONES:
            raise ValueError(f"location {eid}: bc_zone must be one of {BC_ZONES}")
        if name.endswith("_distance_km") and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or value > 5000):
            raise ValueError(f"location {eid}: {name} must be a finite number of kilometres between 0 and 5000")
        attrs[name] = value
        evid[name] = {k: ev.get(k) for k in ("source", "method", "confidence", "version", "effective_date")}
    return LocationEntry(eid, str(raw.get("label") or eid)[:120], code, role, (str(raw["city"]).strip() or None) if raw.get("city") else None,
                         (str(raw["county"]).strip() or None) if raw.get("county") else None, days, attrs, evid)


def mo_county_class(county: str | None) -> str | None:
    return _MO_INDEX.get(_norm_county(county)) if county else None


def resolve(entry: LocationEntry) -> ResolvedLocation:
    states: dict = {}
    resolution: dict = {}
    unresolved: dict = {}
    code = entry.jurisdiction_code

    def attr_res(name):
        ev = dict(entry.evidence.get(name) or {})
        ev["value"] = entry.attributes.get(name)
        return ev

    if code == "US-MO":
        cls = mo_county_class(entry.county)
        if cls is not None:
            states["mo_county_qualifying"] = cls in MO_QUALIFYING_CLASSES
            resolution["county_class"] = {"value": cls, "source": MO_COUNTY_DATASET["source"], "method": "DATASET_LOOKUP", "confidence": MO_COUNTY_DATASET["confidence"],
                                          "version": MO_COUNTY_DATASET["version"], "effective_date": MO_COUNTY_DATASET["effective_date"]}
        else:
            states["mo_county_qualifying"] = None
            unresolved["county_class"] = ("no county stated" if not entry.county else f"'{entry.county}' is not in the {MO_COUNTY_DATASET['version']} published list (113 of 114 counties transcribed)")
        if "rural_or_blighted" in entry.attributes:
            states["mo_rural_or_blighted"] = bool(entry.attributes["rural_or_blighted"])
            resolution["mo_rural_or_blighted"] = attr_res("rural_or_blighted")
        else:
            states["mo_rural_or_blighted"] = None
            unresolved["rural_or_blighted"] = OPEN_CLASSIFICATIONS["mo_rural_or_blighted"]
    elif code == "CA-BC":
        zone = entry.attributes.get("bc_zone")
        if zone in BC_ZONES:
            states["bc_outside_vancouver"] = zone in ("regional", "distant")
            states["bc_distant"] = zone == "distant"
            resolution["bc_zone"] = attr_res("bc_zone")
        else:
            states["bc_outside_vancouver"] = states["bc_distant"] = None
            unresolved["bc_zone"] = OPEN_CLASSIFICATIONS["bc_zone"]
    elif code == "CA-NS":
        d = entry.attributes.get("ns_distance_km")
        if d is not None:
            states["ns_zone_a"] = 100 < d <= 150
            states["ns_zone_b"] = d > 150
            resolution["ns_distance_km"] = attr_res("ns_distance_km")
        else:
            states["ns_zone_a"] = states["ns_zone_b"] = None
            unresolved["ns_distance"] = OPEN_CLASSIFICATIONS["ns_distance"]
    elif code == "CA-NB":
        d = entry.attributes.get("nb_distance_km")
        if d is not None:
            if 150 < d < 151:
                states["nb_rural"] = states["nb_remote"] = None          # the guideline bands are whole kilometres (30-150, 151+): a fraction between them is undefined
                unresolved["nb_distance"] = "a distance between 150 and 151 km falls between the guideline's whole-kilometre bands; state a whole-kilometre measurement"
            else:
                states["nb_rural"] = 30 <= d <= 150
                states["nb_remote"] = d >= 151
                resolution["nb_distance_km"] = attr_res("nb_distance_km")
        else:
            states["nb_rural"] = states["nb_remote"] = None
            unresolved["nb_distance"] = OPEN_CLASSIFICATIONS["nb_distance"]
    elif code == "CA-SK":
        d = entry.attributes.get("sk_distance_km")
        if d is not None:
            states["sk_rural50"] = d >= 50
            resolution["sk_distance_km"] = attr_res("sk_distance_km")
        else:
            states["sk_rural50"] = None
            unresolved["sk_distance"] = OPEN_CLASSIFICATIONS["sk_distance"]
    return ResolvedLocation(entry, states, resolution, unresolved)


# ── reduction to numeric facts ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LOC = "locality:"


def locality_amount_facts(entries: list[LocationEntry]) -> dict[str, float]:
    """Numeric reduction (flows through amount_facts and the fingerprint). Per jurisdiction J: locality:days:J (dated days), locality:undated:J (locations without days), locality:n:J; per applicable
    predicate P: locality:P:T:J / :F:J (days at qualifying / non-qualifying dated locations) and locality:P:Tn:J / :Fn:J / :Un:J (location counts). Totals across all jurisdictions: locality:days:ALL, :undated:ALL."""
    out: dict[str, float] = {}
    resolved = [resolve(e) for e in entries]
    total_days = sum(e.days for e in entries if e.days is not None)
    if entries:
        out[LOC + "days:ALL"] = float(total_days)
        out[LOC + "undated:ALL"] = float(sum(1 for e in entries if e.days is None))
    for j in sorted({e.jurisdiction_code for e in entries}):
        here = [r for r in resolved if r.entry.jurisdiction_code == j]
        out[f"{LOC}days:{j}"] = float(sum(r.entry.days for r in here if r.entry.days is not None))
        out[f"{LOC}undated:{j}"] = float(sum(1 for r in here if r.entry.days is None))
        out[f"{LOC}n:{j}"] = float(len(here))
        for p in PREDICATES:
            if p.jurisdiction != j:
                continue
            t = [r for r in here if r.states.get(p.key) is True]
            f = [r for r in here if r.states.get(p.key) is False]
            u = [r for r in here if r.states.get(p.key) is None]
            out[f"{LOC}{p.key}:T:{j}"] = float(sum(r.entry.days or 0 for r in t))
            out[f"{LOC}{p.key}:F:{j}"] = float(sum(r.entry.days or 0 for r in f))
            out[f"{LOC}{p.key}:Tn:{j}"] = float(len(t))
            out[f"{LOC}{p.key}:Fn:{j}"] = float(len(f))
            out[f"{LOC}{p.key}:Un:{j}"] = float(len(u))
    return out


def describe(entries: list[LocationEntry]) -> list[dict]:
    """The served view of the locations: each with its resolved classifications, their provenance and what is still unresolved."""
    out = []
    for r in map(resolve, entries):
        e = r.entry
        out.append({"id": e.id, "label": e.label, "role": e.role, "jurisdiction_code": e.jurisdiction_code, "city": e.city, "county": e.county, "days": e.days,
                    "classifications": {k: v for k, v in r.resolution.items()}, "states": {k: v for k, v in r.states.items()}, "unresolved": r.unresolved})
    return out
