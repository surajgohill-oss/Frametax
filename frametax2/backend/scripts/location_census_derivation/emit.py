import pickle, pprint, json
R = pickle.load(open("derived.pkl", "rb"))
CATS = ["island_tropical", "jungle_rainforest", "desert_arid", "mountains_alpine", "snow_arctic", "urban_major_city", "small_town_suburban",
        "rural_countryside", "forest_woodland", "historic_old_world"]
COMP_TOKENS = {"island": "island_environments", "tropical": "tropical_climate_environments"}
CAT_TOKEN = {"island_tropical": "tropical_environments", "jungle_rainforest": "jungle_environments", "desert_arid": "desert_environments",
             "mountains_alpine": "mountain_environments", "snow_arctic": "snow_environments", "urban_major_city": "urban_environments",
             "small_town_suburban": "small_town_environments", "rural_countryside": "rural_environments", "forest_woodland": "forest_environments",
             "historic_old_world": "historic_architecture"}
SOURCES = {
 "UNESCO_WHL": dict(short='UNESCO World Heritage List', title="UNESCO World Heritage List (UNESCO open data, dataset whc001)", publisher="UNESCO World Heritage Centre",
   url="https://data.unesco.org/explore/dataset/whc001/", version="1,273 properties; retrieved 2026-10-06", tier="INTERGOVERNMENTAL_DATASET",
   method="inscribed property whose name/short description states the feature (keyword rule); subnational jurisdictions by property coordinates within 0.05 degrees of the Natural Earth admin-1 polygon"),
 "GLC_SHARE": dict(short='FAO GLC-SHARE v1.0', title="Global Land Cover-SHARE (GLC-SHARE) v1.0, 30 arc-second percentage layers", publisher="FAO (Food and Agriculture Organization of the United Nations), Land and Water Division",
   url="https://data.apps.fao.org/map/catalog/us/api/records/ba4526fd-cdbf-4028-a1bd-5a559c4bff38", version="v1.0 (2014); layers 01-04, 08-10 retrieved 2026-10-06", tier="INTERGOVERNMENTAL_DATASET",
   method="cos(latitude)-weighted zonal mean of the percentage layer over the territory polygon (all-touched mask), 1 km pixels"),
 "WB_FRST": dict(short='FAO forest area (World Bank WDI)', title="World Bank WDI AG.LND.FRST.ZS Forest area (% of land area), FAO Global Forest Resources Assessment", publisher="World Bank / FAO",
   url="https://api.worldbank.org/v2/country/all/indicator/AG.LND.FRST.ZS", version="WDI last updated 2026-07-13", tier="INTERGOVERNMENTAL_DATASET",
   method="most recent non-empty national value"),
 "WUP2025": dict(short='UN WUP 2025', title="World Urbanization Prospects 2025, File F01 Population by Degree of Urbanisation (Cities / Towns and suburbs / Rural areas), 2025", publisher="United Nations DESA Population Division",
   url="https://population.un.org/wup/downloads", version="POP/DB/WUP/Rev.2025/F01; retrieved 2026-10-06", tier="INTERGOVERNMENTAL_DATASET",
   method="national population (thousands) in each degree-of-urbanisation class for 2025"),
 "NRHP": dict(short='US NPS National Register', title="National Register of Historic Places - Points (NRIS), historic districts", publisher="US National Park Service, Cultural Resources GIS",
   url="https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/0", version="live service queried 2026-10-06 (ResType='district')", tier="GOVERNMENT_DATASET",
   method="count of listed historic districts by State"),
 "AU_NHL": dict(short='Australian National Heritage List', title="National Heritage List Spatial Database (NHL) - public", publisher="Australian Government DCCEEW",
   url="https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/National_Heritage_List/MapServer/0", version="data updated 2026-02-25; queried 2026-10-06", tier="GOVERNMENT_DATASET",
   method="count of CLASS = Historic places by STATE"),
 "NZFC_LOC": dict(short='NZ Film Commission', title="New Zealand Film Commission - New Zealand Locations", publisher="New Zealand Film Commission", url="https://www.nzfilm.co.nz/inbound-productions/filming-in-nz/locations",
   version="page fetched 2026-10-06", tier="GOVERNMENT_AGENCY_PAGE", method="official film commission locations page; verbatim statement"),
 "VISIT_ICELAND": dict(short='Visit Iceland', title="The Hollywood Sights of Iceland", publisher="Visit Iceland (Promote Iceland)", url="https://www.visiticeland.com/article/famous-film-sights/",
   version="page fetched 2026-10-06", tier="GOVERNMENT_AGENCY_PAGE", method="official destination agency page; verbatim statement"),
 "NSW_NPWS": dict(short='NSW National Parks', title="Snowy Mountains | NSW National Parks", publisher="NSW National Parks and Wildlife Service", url="https://www.nationalparks.nsw.gov.au/visit-a-park/regions/snowy-mountains",
   version="page fetched 2026-10-06", tier="GOVERNMENT_AGENCY_PAGE", method="state government agency page; verbatim statement"),
 "KG2023": dict(short='Koppen-Geiger 1 km (Beck 2023)', title="High-resolution (1 km) Koppen-Geiger maps for 1901-2099 based on constrained CMIP6 projections, 1991-2020 map (Beck et al. 2023, Scientific Data 10:724)", publisher="Beck, McVicar, Vergopolan et al. (peer reviewed; figshare)",
   url="https://doi.org/10.6084/m9.figshare.21789074.v2", version="figshare v2 (2026-01-14), 1991_2020/koppen_geiger_0p00833333.tif", tier="PEER_REVIEWED_OPEN_DATASET",
   method="cos(latitude)-weighted share of classified 1 km cells per Koppen class over the territory polygon; 'present' = >= 0.5%"),
 "NE": dict(short='Natural Earth 1:10m', title="Natural Earth 1:10m physical and cultural vectors (admin-0/1, land, minor islands, geography regions, elevation points, glaciated areas)", publisher="Natural Earth (NACIS; public domain)",
   url="https://www.naturalearthdata.com/", version="admin 5.1.1/5.1.2; regions 5.0.0; retrieved 2026-10-06", tier="PEER_REVIEWED_OPEN_DATASET",
   method="spatial intersection of the territory polygon with the feature layer (0.05 degree tolerance for point layers)"),
 "NE_PP": dict(short='Natural Earth populated places', title="Natural Earth 1:10m populated places", publisher="Natural Earth (NACIS; public domain)", url="https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-populated-places/",
   version="5.1.2; retrieved 2026-10-06", tier="PEER_REVIEWED_OPEN_DATASET", method="populated places (POP_MAX) inside the territory polygon (0.05 degree tolerance)"),
}
EXTRA = {
 ("NZ", "historic_old_world"): ("SUPPORTED", "NZ Film Commission locations page: 'Renowned for its preserved Victorian streetscapes and distinctive limestone architecture' (Oamaru)", ("NZFC_LOC",), "official film commission locations page"),
 ("IS", "small_town_suburban"): ("SUPPORTED", "Visit Iceland 'The Hollywood Sights of Iceland': Dalvik ('the northern seaside community') and 'the village of Vik' are screen locations", ("VISIT_ICELAND",), "official destination agency page"),
 ("AU-NSW", "snow_arctic"): ("SUPPORTED", "NSW National Parks and Wildlife Service, Snowy Mountains: 'go skiing or snowboarding on the slopes of Perisher and Thredbo'", ("NSW_NPWS",), "state government agency page"),
}
EXTRA_ATT = {
 ("KZ", "historic_old_world"): ["Official film agency page kazakhfilm.kz (fetched 2026-10-06): no statement on historic cities"],
 ("MK", "historic_old_world"): ["mfa.gov.mk (retained lead URL, fetched 2026-10-06): site is the Ministry of Foreign Affairs; no statement on historic locations"],
 ("CA-BC", "desert_arid"): ["Destination BC (Super, Natural BC) Nk'Mip Desert Cultural Centre page (fetched 2026-10-06): no explicit statement; BC Government news release not retrievable (TLS certificate error)"],
}
GENERIC_ATT = "National/regional film-commission and agency location pages were not queried per cell (batch method authorised); the bounded sequence applied is the structured official/authoritative dataset sequence recorded for the cell, plus any retained repository agency lead for the cell that is listed with its fetch outcome"
cells = {}
for (code, cat), r in sorted(R.items()):
    status, comps, tokens, prop, srcs, method, att = r
    srcs = tuple(srcs); att = list(att)
    if (code, cat) in EXTRA and status == "UNRESOLVED_NEUTRAL":
        status, prop, srcs, method = EXTRA[(code, cat)]
        comps = {cat: status}; att = []
    if status == "UNRESOLVED_NEUTRAL":
        att = att + EXTRA_ATT.get((code, cat), [])
        missing = ""
    else:
        missing = ""
    if cat == "island_tropical":
        comp = tuple((COMP_TOKENS[k], v) for k, v in comps.items())
    else:
        comp = ((CAT_TOKEN[cat], status),)
    cells[(code, cat)] = (status, comp, prop, tuple(srcs), method, tuple(att), missing)
pickle.dump((SOURCES, cells), open("emit.pkl", "wb"))
import collections
print(collections.Counter(v[0] for v in cells.values()))
HDR = '''"""LOCATION CAPABILITY CENSUS DATA (2026-10-06, final closure) -- the 114 x 10 = 1,140 terminal cells.

DATA for the one canonical capability owner (`jurisdiction_comparison.location_capability_cells` ->
`production_requirements.jurisdiction_capability_profile` -> `production_fit`); not a registry of its own.

Every cell is exactly one of SUPPORTED / NOT_SUPPORTED / UNRESOLVED_NEUTRAL (served as AUTHORITY_VERIFIED_SUPPORTED /
AUTHORITY_VERIFIED_NOT_SUPPORTED / AUTHORITY_UNRESOLVED_NEUTRAL). SUPPORTED and NOT_SUPPORTED cells are derived deterministically
from the structured official/authoritative datasets in SOURCES (the derivation method and source version travel with each source);
an UNRESOLVED_NEUTRAL cell records the sources attempted and the missing proposition and is neutral at runtime (never a mismatch).
The earlier DISCOVERY-tier repository notes are NOT evidence and are not used. Generated by backend/scripts/location_census_derivation.
`island_tropical` is a combined category with two internal component assertions: SUPPORTED if either component is supported,
NOT_SUPPORTED only if both are, otherwise unresolved. Landlocked status alone never establishes the tropical component.
"""
from __future__ import annotations

SUPPORTED = "SUPPORTED"
NOT_SUPPORTED = "NOT_SUPPORTED"
UNRESOLVED_NEUTRAL = "UNRESOLVED_NEUTRAL"
TERMINAL_STATUS = {SUPPORTED: "AUTHORITY_VERIFIED_SUPPORTED", NOT_SUPPORTED: "AUTHORITY_VERIFIED_NOT_SUPPORTED", UNRESOLVED_NEUTRAL: "AUTHORITY_UNRESOLVED_NEUTRAL"}
UNKNOWN = UNRESOLVED_NEUTRAL

#: census category -> canonical capability token the 13 location chips already reach.
LOCATION_CENSUS_CATEGORIES: dict[str, str] = %s
#: internal component assertions of the combined island/tropical category (token per component).
COMPONENT_TOKENS: dict[str, str] = %s
#: authority tiers accepted for a verified cell, strongest first.
ACCEPTED_TIERS = ("INTERGOVERNMENTAL_DATASET", "GOVERNMENT_DATASET", "GOVERNMENT_AGENCY_PAGE", "PEER_REVIEWED_OPEN_DATASET")

#: reusable source / derivation records referenced by the cells.
SOURCES: dict[str, dict] = %s

#: (jurisdiction_code, category) -> (status, ((component_token, component_status), ...), proposition, source_ids, derivation_method,
#:                                    sources_attempted, missing_proposition). Subnational and national codes are independent keys.
CELLS: dict[tuple[str, str], tuple] = {
'''
body = []
for k, v in cells.items():
    body.append(f"    {k!r}: {v!r},")
consts = "\n#: appended to every unresolved cell's sources_attempted (the cell's own tuple lists the dataset-specific outcomes).\nGENERIC_UNRESOLVED_ATTEMPT = " + repr(GENERIC_ATT) + "\n#: the missing proposition recorded for every unresolved cell.\nMISSING_PROPOSITION = " + repr("no retained or fetched authoritative statement or dataset value establishes the capability, and nothing establishes its absence") + "\n"
open("jurisdiction_location_capability.py", "w").write(HDR % (pprint.pformat(CAT_TOKEN, width=140), pprint.pformat(COMP_TOKENS, width=140), pprint.pformat(SOURCES, width=140)) + "\n".join(body) + "\n}\n" + consts)
print("written", len(cells))
