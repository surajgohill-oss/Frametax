"""The ONE canonical locality resolver (NA-RECONCILIATION-23).

Locality is never inferred from a jurisdiction alone. The inputs are explicit production locations - a retained schedule location or a location the producer selected for a scenario - each with a
jurisdiction, optionally a city, a county, shooting days, and attributes the producer or an authority asserted (each with its source, method and confidence). This module is pure: it resolves
each location against the classification datasets the repository actually holds, reports every classification it could NOT resolve with the exact source still required, and reduces the
locations to numeric `locality:*` facts (days at qualifying / non-qualifying / unclassified locations per jurisdiction) that flow through the existing amount-fact path and the evaluation fingerprint.

Datasets held (each record carries source, version and effective date):
  * Missouri county classification (RSMo 48.020): the Missouri Association of Counties "Counties by Classification" (May 2025, 113 of 114 counties transcribed) and the Secretary of State Official Manual
    2025-2026 (verbatim entries only). A county in one source takes it (Cole, the county missing from the Association row, is class 1 from the Official Manual); a county the sources disagree on (Newton,
    Franklin) is Unknown; a county in neither is Unknown. Nothing is guessed.
  * British Columbia (B.C. Reg. 4/99 s.1 'designated Vancouver area' and s.11 'distant location', consolidation current to 2026-10-06) and the Metro Vancouver member jurisdictions (metrovancouver.org).
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
#: Second source, the PRIMARY government record: Missouri Secretary of State, Official Manual (Blue Book) 2025-2026, "Cities and Counties" (sos.mo.gov/cmsimages/bluebook/2025-2026/8_Counties.pdf, retrieved
#: 2026-10-15). Only entries confirmed by a verbatim printed "Classification:" line in the retrieved text are stored (Cole: "Classification: First class ... Square miles: 400 ... Named for: Stephen Cole";
#: Newton: "Classification: First class ... Neosho 64850. County population: 59,386"). The PDF extraction is column-scrambled, so no other county is taken from it.
MO_OFFICIAL_MANUAL = {
    "id": "MO_SOS_OFFICIAL_MANUAL_2025_2026",
    "source": "Missouri Secretary of State, Official Manual 2025-2026, Cities and Counties (county officials), printed 'Classification:' line",
    "url": "https://www.sos.mo.gov/cmsimages/bluebook/2025-2026/8_Counties.pdf",
    "version": "2025-2026", "effective_date": "2025-01-01", "retrieved": "2026-10-15", "confidence": "PRIMARY_VERBATIM",
}
_MO_OFFICIAL_VERBATIM: dict[str, str] = {"Cole": "1", "Newton": "1"}
#: Counties the two sources disagree on (or a non-verbatim reading of the primary record contradicts): Unknown until the owner reconciles them.
MO_UNRESOLVED_CONFLICTS: dict[str, str] = {
    "Newton": "the Association list (2025-05) says class 2; the Secretary of State Official Manual 2025-2026 prints 'First class' - classification differs by source",
    "Franklin": "the Association list (2025-05) says class 1; a non-verbatim reading of the Official Manual 2025-2026 suggests 'Third class' - unverified conflict, not asserted",
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
    "mo_rural_or_blighted": ("RSMo 135.750 subsection 3(3) does not define 'rural or blighted area' (read 2026-10-15); the Department of Economic Development administers it (3(7)). The DED 'Motion Media Tax Credit Program "
                             "Guidelines' (https://ded.mo.gov/media/pdf/motion-media-tax-credit-program-guidelines) is the source that would state the method, but it is served inside a PDF viewer page whose text could not be "
                             "retrieved. Read that document, then record the method; until then the producer asserts rural / blighted per location with the DED determination as its source."),
    "bc_zone": ("Inside the Metro Vancouver Regional District only: the designated Vancouver area boundary is defined in B.C. Reg. 4/99 s.1(2) by the 5L82 BC Hydro line, the Pitt and Fraser river shores and the "
                "City of Surrey eastern boundary (Letters Patent, OIC 785/1993); their geometry is not published as data, so a polygon is not derived. State the zone per location with its source (the Creative BC "
                "regional and distant location map)."),
    "ns_distance": ("NSFPIF Guidelines s.6.1 measure the most direct DRIVING distance from Halifax City Hall; a routing mechanism and the official City Hall coordinates are not held. A great-circle distance is only a "
                    "lower bound. State the driving distance per location with its source."),
    "nb_distance": "Official coordinates of Fredericton, Moncton and Saint John City Halls (none recovered from a primary source) and the guideline's distance method; state the distance per location with its source.",
    "sk_distance": "Official coordinates of the centre-most points of Regina and Saskatoon (none recovered from a primary source) and Creative Saskatchewan's measurement method; state the distance per location with its source.",
}

# ── British Columbia: B.C. Reg. 4/99 (Film and Television Tax Credit Regulation), consolidation current to 2026-10-06, last amended 2025-01-01 by B.C. Reg. 119/2025 ─────────────────────────────────────────
BC_REGULATION = {
    "id": "BC_REG_4_99", "source": "B.C. Reg. 4/99, Film and Television Tax Credit Regulation, s.1(2) 'designated Vancouver area' and s.11 'distant location'",
    "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/4_99", "version": "consolidation current to 2026-10-06 (last amended 2025-01-01, B.C. Reg. 119/2025)",
    "effective_date": "2017-01-25", "retrieved": "2026-10-15", "confidence": "PRIMARY_VERBATIM",
    "note": ("DESIGNATED VANCOUVER AREA (principal photography on or after 2017-01-25): the portion of the Metro Vancouver Regional District south of 49 deg 24'10\" N and west of a line from 49 deg 24'10\" N 122 deg 45' W "
             "south to the 5L82 BC Hydro line, along it to the end of the paved road at the northern boundary of Minnekhada Regional Park, east to the western shore of the Pitt River, along that shore to the "
             "southern shore of the Fraser River near Douglas Island, along the Fraser to the eastern boundary of the City of Surrey (Letters Patent, OIC 785/1993) and south along that boundary. The line's "
             "geometry (the 5L82 line, the Pitt and Fraser shorelines, the Surrey boundary) is not published as data in the regulation, so a machine-readable polygon is NOT derived: a location INSIDE the Metro "
             "Vancouver Regional District is classified by an explicit sourced statement; a location OUTSIDE the regional district is outside the designated Vancouver area by construction."),
}
#: s.11: the distant location is all of BC outside the designated Vancouver area EXCEPT these areas (the Capital Regional District exception applies only before 2014-02-19 and is not modelled).
BC_DISTANT_EXCLUDED_MUNICIPALITIES = ("District of Squamish", "Resort Municipality of Whistler", "City of Abbotsford", "City of Chilliwack", "Village of Harrison Hot Springs", "District of Hope",
                                      "The Corporation of the District of Kent", "District of Mission")
#: Fraser Valley Regional District parts excluded by s.11(l) and (m) are defined by river / highway boundaries (not by municipality): a location in that regional district outside the named municipalities is Unknown.
BC_DISTANT_PARTIAL_AREAS = ("Fraser Valley Regional District",)
BC_METRO_VANCOUVER = {
    "source": "Metro Vancouver, Member Jurisdictions (21 municipalities, one electoral area, one treaty First Nation)", "url": "https://metrovancouver.org/about-us/member-jurisdictions",
    "retrieved": "2026-10-15", "version": "2026",
    "members": ("Village of Anmore", "Village of Belcarra", "Bowen Island Municipality", "City of Burnaby", "City of Coquitlam", "City of Delta", "Electoral Area A", "City of Langley", "Township of Langley",
                "Village of Lions Bay", "City of Maple Ridge", "City of New Westminster", "City of North Vancouver", "District of North Vancouver", "City of Pitt Meadows", "City of Port Coquitlam",
                "City of Port Moody", "City of Richmond", "City of Surrey", "Tsawwassen First Nation", "City of Vancouver", "District of West Vancouver", "City of White Rock"),
}


def _norm_place(name: str | None) -> str:
    n = str(name or "").lower()
    n = re.sub(r"\b(the corporation of the|resort municipality of|municipality of|corporation of|city of|district of|township of|village of|town of)\b", "", n)
    n = re.sub(r"\b(municipality|regional district|first nation)\b", "", n)
    return re.sub(r"[^a-z0-9]", "", n)


_MV_MEMBERS = frozenset(_norm_place(m) for m in BC_METRO_VANCOUVER["members"])
_BC_EXCLUDED = frozenset(_norm_place(m) for m in BC_DISTANT_EXCLUDED_MUNICIPALITIES)
_RD_METRO = frozenset({"metrovancouver", "greatervancouver"})
_RD_FRASER_VALLEY = "fraservalley"
_RD_SLRD = "squamishlillooet"


def bc_classification(regional_district: str | None, municipality: str | None) -> dict:
    """{inside_metro_vancouver, distant, basis}: True / False / None from the regulation and the Metro Vancouver membership list. Never from a description such as 'north to Whistler'."""
    rd, muni = _norm_place(regional_district), _norm_place(municipality)
    inside = True if (rd in _RD_METRO or muni in _MV_MEMBERS) else (False if rd else None)
    if inside:
        return {"inside_metro_vancouver": True, "distant": False, "basis": "inside the Metro Vancouver Regional District: never a distant location (s.11(a)); the designated Vancouver area boundary inside it is not derivable"}
    if inside is None:
        return {"inside_metro_vancouver": None, "distant": None, "basis": "regional district not stated"}
    if muni in _BC_EXCLUDED:
        return {"inside_metro_vancouver": False, "distant": False, "basis": "a municipality excluded from 'distant location' by s.11"}
    if rd == _RD_SLRD and muni in {"electoralaread", "aread"}:
        return {"inside_metro_vancouver": False, "distant": False, "basis": "Electoral Area D of the Squamish-Lillooet Regional District is excluded by s.11(e)"}
    if rd == _RD_FRASER_VALLEY:
        return {"inside_metro_vancouver": False, "distant": None, "basis": "parts of the Fraser Valley Regional District are excluded by river / highway boundaries (s.11(l),(m)); the municipality does not settle it"}
    if not muni:
        return {"inside_metro_vancouver": False, "distant": None, "basis": "municipality not stated"}
    return {"inside_metro_vancouver": False, "distant": True, "basis": "in British Columbia outside the Metro Vancouver Regional District and outside every s.11 exclusion"}


# ── reference points and the distance mechanism ──────────────────────────────────────────────────────────────────────────────────────────────────
#: Official reference coordinates. A point is USED only when status == VERIFIED; none could be recovered from a primary source (municipal sites publish street addresses and map links, not coordinates), so every
#: point is OPEN. Fredericton's own contact page links its City Hall pin; that is a map link, not a published coordinate record, so it is kept as evidence and not used.
EARTH_RADIUS_KM = 6371.0088          # IUGG mean Earth radius
REFERENCE_POINTS: dict[str, dict] = {
    "halifax_city_hall": {"group": "ns", "label": "Halifax City Hall, 1841 Argyle Street", "status": "OPEN", "lat": None, "lon": None, "required_source": "Halifax Regional Municipality published coordinates (open data) for the City Hall building"},
    "fredericton_city_hall": {"group": "nb", "label": "Fredericton City Hall, 397 Queen Street", "status": "UNVERIFIED_MAP_LINK", "lat": 45.963328, "lon": -66.6434559,
                              "evidence": "https://www.fredericton.ca/city-government/contact-directory ('View on map' link, retrieved 2026-10-15); a map pin, not a published coordinate record",
                              "required_source": "City of Fredericton published coordinates (open data) for City Hall"},
    "moncton_city_hall": {"group": "nb", "label": "Moncton City Hall, 655 Main Street", "status": "OPEN", "lat": None, "lon": None, "required_source": "City of Moncton published coordinates (open data) for City Hall"},
    "saint_john_city_hall": {"group": "nb", "label": "Saint John City Hall, 15 Market Square", "status": "OPEN", "lat": None, "lon": None, "required_source": "City of Saint John published coordinates (open data) for City Hall"},
    "regina_centre": {"group": "sk", "label": "Regina, centre-most point", "status": "OPEN", "lat": None, "lon": None, "required_source": "Creative Saskatchewan's definition of the centre-most point and the City of Regina published coordinates"},
    "saskatoon_centre": {"group": "sk", "label": "Saskatoon, centre-most point", "status": "OPEN", "lat": None, "lon": None, "required_source": "Creative Saskatchewan's definition of the centre-most point and the City of Saskatoon published coordinates"},
}


def great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine great-circle distance on the IUGG mean sphere. A straight-line distance never exceeds a road distance, so it is a LOWER bound for a driving distance."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def distance_lower_bound_km(lat: float | None, lon: float | None, group: str) -> float | None:
    """The minimum great-circle distance from the location to the group's reference points; None unless the location has coordinates and EVERY point of the group is VERIFIED."""
    pts = [p for p in REFERENCE_POINTS.values() if p["group"] == group]
    if lat is None or lon is None or not pts or any(p["status"] != "VERIFIED" or p["lat"] is None for p in pts):
        return None
    return min(great_circle_km(lat, lon, p["lat"], p["lon"]) for p in pts)


# ── entries ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ATTRIBUTES = ("rural_or_blighted", "bc_zone", "bc_regional_district", "bc_municipality", "ns_distance_km", "nb_distance_km", "sk_distance_km", "latitude", "longitude")
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
        if name in ("bc_regional_district", "bc_municipality") and (not isinstance(value, str) or not value.strip() or len(value) > 120):
            raise ValueError(f"location {eid}: {name} must be a non-empty name of at most 120 characters")
        if name in ("latitude", "longitude"):
            lim = 90 if name == "latitude" else 180
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > lim:
                raise ValueError(f"location {eid}: {name} must be a finite number within +/-{lim} degrees")
        if name.endswith("_distance_km") and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or value > 5000):
            raise ValueError(f"location {eid}: {name} must be a finite number of kilometres between 0 and 5000")
        attrs[name] = value
        evid[name] = {k: ev.get(k) for k in ("source", "method", "confidence", "version", "effective_date")}
    return LocationEntry(eid, str(raw.get("label") or eid)[:120], code, role, (str(raw["city"]).strip() or None) if raw.get("city") else None,
                         (str(raw["county"]).strip() or None) if raw.get("county") else None, days, attrs, evid)


_MO_OFFICIAL_INDEX = {_norm_county(k): v for k, v in _MO_OFFICIAL_VERBATIM.items()}
_MO_CONFLICT_INDEX = {_norm_county(k): v for k, v in MO_UNRESOLVED_CONFLICTS.items()}


def mo_county_resolution(county: str | None) -> dict:
    """{status: RESOLVED | CONFLICT | ABSENT, class, source, version, effective_date, note}. A county the two sources disagree on is CONFLICT (Unknown); a county in only one source takes that source."""
    key = _norm_county(county)
    if not key:
        return {"status": "ABSENT", "class": None, "note": "no county stated"}
    if key in _MO_CONFLICT_INDEX:
        return {"status": "CONFLICT", "class": None, "note": _MO_CONFLICT_INDEX[key]}
    assoc, official = _MO_INDEX.get(key), _MO_OFFICIAL_INDEX.get(key)
    if assoc and official and assoc != official:
        return {"status": "CONFLICT", "class": None, "note": "the two sources differ"}
    if official:
        d = MO_OFFICIAL_MANUAL
        return {"status": "RESOLVED", "class": official, "source": d["source"], "version": d["version"], "effective_date": d["effective_date"], "confidence": d["confidence"]}
    if assoc:
        d = MO_COUNTY_DATASET
        return {"status": "RESOLVED", "class": assoc, "source": d["source"], "version": d["version"], "effective_date": d["effective_date"], "confidence": d["confidence"]}
    return {"status": "ABSENT", "class": None, "note": f"'{county}' is in neither Missouri classification source"}


def mo_county_class(county: str | None) -> str | None:
    return mo_county_resolution(county)["class"]


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
        res = mo_county_resolution(entry.county)
        if res["class"] is not None:
            states["mo_county_qualifying"] = res["class"] in MO_QUALIFYING_CLASSES
            resolution["county_class"] = {"value": res["class"], "source": res["source"], "method": "DATASET_LOOKUP", "confidence": res["confidence"], "version": res["version"],
                                          "effective_date": res["effective_date"]}
        else:
            states["mo_county_qualifying"] = None
            unresolved["county_class"] = res["note"]
        if "rural_or_blighted" in entry.attributes:
            states["mo_rural_or_blighted"] = bool(entry.attributes["rural_or_blighted"])
            resolution["mo_rural_or_blighted"] = attr_res("rural_or_blighted")
        else:
            states["mo_rural_or_blighted"] = None
            unresolved["rural_or_blighted"] = OPEN_CLASSIFICATIONS["mo_rural_or_blighted"]
    elif code == "CA-BC":
        cls = bc_classification(entry.attributes.get("bc_regional_district"), entry.attributes.get("bc_municipality"))
        zone = entry.attributes.get("bc_zone")
        outside = distant = None
        if cls["inside_metro_vancouver"] is False:
            outside = True                                                  # the designated Vancouver area lies wholly inside the Metro Vancouver Regional District
        if cls["distant"] is not None:
            distant = cls["distant"]
        if cls["inside_metro_vancouver"] is not None:
            resolution["bc_regulation"] = {"value": cls["basis"], "source": BC_REGULATION["source"], "method": "DATASET_LOOKUP", "confidence": BC_REGULATION["confidence"],
                                           "version": BC_REGULATION["version"], "effective_date": BC_REGULATION["effective_date"]}
        if zone in BC_ZONES:                                                  # an explicit sourced statement fills only what the regulation does not decide
            if outside is None:
                outside = zone in ("regional", "distant")
            if distant is None:
                distant = zone == "distant"
            elif distant != (zone == "distant"):
                unresolved["bc_zone_conflict"] = "the stated zone disagrees with the regulation-derived classification; the regulation is used"
            resolution["bc_zone"] = attr_res("bc_zone")
        states["bc_outside_vancouver"], states["bc_distant"] = outside, distant
        if outside is None or distant is None:
            unresolved["bc_zone"] = ("state the regional district and municipality (distant location is decided by B.C. Reg. 4/99 s.11); " + OPEN_CLASSIFICATIONS["bc_zone"]
                                     if cls["inside_metro_vancouver"] is None else
                                     "inside the Metro Vancouver Regional District the designated Vancouver area boundary is not derivable: " + OPEN_CLASSIFICATIONS["bc_zone"])
    elif code in ("CA-NS", "CA-NB", "CA-SK"):
        grp, attr = {"CA-NS": ("ns", "ns_distance_km"), "CA-NB": ("nb", "nb_distance_km"), "CA-SK": ("sk", "sk_distance_km")}[code]
        d = entry.attributes.get(attr)
        lb = distance_lower_bound_km(entry.attributes.get("latitude"), entry.attributes.get("longitude"), grp) if d is None else None
        if code == "CA-NS":
            if d is not None:
                states["ns_zone_a"], states["ns_zone_b"] = 100 < d <= 150, d > 150
            elif lb is not None and lb > 150:                               # any road distance is at least the straight line
                states["ns_zone_a"], states["ns_zone_b"] = False, True
            else:
                states["ns_zone_a"] = states["ns_zone_b"] = None
        elif code == "CA-NB":
            if d is not None and 150 < d < 151:
                states["nb_rural"] = states["nb_remote"] = None
                unresolved["nb_distance"] = "a distance between 150 and 151 km falls between the guideline's whole-kilometre bands; state a whole-kilometre measurement"
            elif d is not None:
                states["nb_rural"], states["nb_remote"] = 30 <= d <= 150, d >= 151
            elif lb is not None and lb >= 151:
                states["nb_rural"], states["nb_remote"] = False, True
            else:
                states["nb_rural"] = states["nb_remote"] = None
        else:
            states["sk_rural50"] = (d >= 50) if d is not None else (True if (lb is not None and lb >= 50) else None)
        if d is not None:
            resolution[attr] = attr_res(attr)
        elif lb is not None:
            resolution[attr] = {"value": round(lb, 3), "source": "great-circle lower bound from verified reference points", "method": "COMPUTED_DISTANCE", "confidence": "LOWER_BOUND"}
        if all(v is None for k, v in states.items() if k.startswith(("ns_", "nb_", "sk_"))) and "nb_distance" not in unresolved:
            unresolved[f"{grp}_distance"] = OPEN_CLASSIFICATIONS[f"{grp}_distance"]
    return ResolvedLocation(entry, states, resolution, unresolved)


# ── reduction to numeric facts ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
LOC = "locality:"


def locality_amount_facts(entries: list[LocationEntry]) -> dict[str, float]:
    """Numeric reduction (flows through amount_facts and the fingerprint). Per jurisdiction J: locality:days:J (dated days), locality:undated:J (locations without days), locality:n:J; per applicable
    predicate P: locality:P:T:J / :F:J (days at qualifying / non-qualifying dated locations) and locality:P:Tn:J / :Fn:J / :Un:J (location counts). Totals across all jurisdictions: locality:days:ALL, :undated:ALL."""
    out: dict[str, float] = {}
    entries = effective_entries(entries)
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
        out.append({"id": e.id, "label": e.label, "role": e.role, "jurisdiction_code": e.jurisdiction_code, "city": e.city, "county": e.county, "days": e.days, "attributes": dict(e.attributes), "evidence": {k: dict(v) for k, v in e.evidence.items()},
                    "classifications": {k: v for k, v in r.resolution.items()}, "states": {k: v for k, v in r.states.items()}, "unresolved": r.unresolved})
    return out


# ── effective entries, conservation and duplicates ─────────────────────────────────────────────────────────────────────────────────────────────────

def effective_entries(entries: list) -> list:
    """A jurisdiction with any SELECTED planning location is planned by those locations alone (the retained SCHEDULE locations of that jurisdiction are the plan being replaced), so one jurisdiction's days are never
    counted twice. Jurisdictions with only SCHEDULE locations use them."""
    selected = {e.jurisdiction_code for e in entries if e.role == "SELECTED"}
    return [e for e in entries if e.role == "SELECTED" or e.jurisdiction_code not in selected]


def _identity(e: LocationEntry) -> tuple:
    norm = lambda v: re.sub(r"[^a-z0-9]", "", str(v or "").lower())          # noqa: E731
    return (e.jurisdiction_code, e.role, norm(e.city), norm(e.county), norm(e.label))


def check_entries(entries: list, total_days: float | None) -> None:
    """ValueError when two entries are the same location in the same role (their days would be double-counted) or when the effective days exceed the shoot total."""
    seen = {}
    for e in entries:
        k = _identity(e)
        if k in seen:
            raise ValueError(f"locations '{seen[k]}' and '{e.id}' are the same place in the same role; their days would be counted twice")
        seen[k] = e.id
    if total_days is not None:
        used = sum(e.days or 0 for e in effective_entries(entries))
        if used > total_days + 1e-9:
            raise ValueError(f"the locations carry {used} shooting days, more than the shoot total of {total_days:g}")
