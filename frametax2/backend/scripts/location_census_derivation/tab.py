import pickle, json, re, csv, io, collections
from shapely import wkb
from shapely.geometry import Point
import shapefile
from shapely.geometry import shape
from geoms import NAT

G = {c: wkb.loads(w) for c, (w, s) in pickle.load(open("geoms.pkl", "rb")).items()}
out = {c: {} for c in G}

# ---- World Bank (FAO forest area, UN rural share): most recent non-empty value
wb = {}
for ind in ("AG.LND.FRST.ZS", "SP.RUR.TOTL.ZS", "SP.URB.TOTL.IN.ZS", "AG.LND.AGRI.ZS"):
    d = json.load(open(f"wb_{ind}.json"))
    meta = d[0]
    for r in d[1]:
        if r["value"] is not None:
            wb.setdefault(r["countryiso3code"], {})[ind] = (r["value"], r["date"], meta["lastupdated"])
for c, a3 in NAT.items():
    out[c]["wb"] = wb.get(a3, {})

# ---- UN WUP 2025 F01 degree of urbanisation (thousands of people, year 2025)
import openpyxl
wbk = openpyxl.load_workbook("wup_f01.xlsx", read_only=True, data_only=True)
wup = {}
for name in ("Rural", "Towns", "Cities", "Total"):
    rows = list(wbk[name].iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[0] == "Index")
    yi = hdr.index("2025") if "2025" in hdr else hdr.index(2025)
    for r in rows:
        if r and r[5] and len(str(r[5])) == 2:
            wup.setdefault(r[5], {})[name] = float(r[yi])
for c in NAT:
    out[c]["wup"] = wup.get(c)
print("wup SG", wup.get("SG"), "wup TW", wup.get("TW"))

# ---- UNESCO World Heritage List (UNESCO open data, 1,273 properties)
rows = list(csv.DictReader(io.StringIO(open("whc_full.csv", encoding="utf-8-sig").read()), delimiter=";"))
print("whc", len(rows))
adm1 = shapefile.Reader("ne/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces")
KW = {
    "historic_old_world": re.compile(r"\b(historic|historical|old|ancient city|colonial|medieval|medina|fortified|walled|hanseatic|castles?|citadel|kasbah|ksar|baroque|old and new towns|city of|town of)\b", re.I),
    "historic_desc": re.compile(r"\b(historic|old|medieval|colonial|walled|fortified|hanseatic) (centre|center|town|city|quarter|quarters|core|port|district|streets)\b", re.I),
    "mountains_alpine": re.compile(r"\b(mountains?|alpine|alps|mountain range|peaks?|himalaya|andes|pyrenees|dolomites|massif)\b", re.I),
    "forest_woodland": re.compile(r"\bforests?\b|woodlands?", re.I),
    "jungle_rainforest": re.compile(r"rain ?forests?|tropical (moist |rain )?forests?|jungle|cloud forest", re.I),
    "desert_arid": re.compile(r"\bdeserts?\b|sahara", re.I),
    "snow_arctic": re.compile(r"\bglaciers?\b|ice ?caps?|icefield|\bsnow\b|arctic|tundra|polar", re.I),
    "island_tropical": re.compile(r"\bislands?\b|archipelago|atoll", re.I),
}
props = []
for r in rows:
    comps = [(float(a), float(b)) for a, b in re.findall(r"latitude: (-?[\d.]+), longitude: (-?[\d.]+)", r["components_list"] or "")]
    if not comps and r["coordinates"]:
        try:
            la, lo = [float(x) for x in r["coordinates"].split(",")]
            comps = [(la, lo)]
        except Exception:
            pass
    props.append(dict(id=r["id_no"], name=r["name_en"], cat=r["category"], states=[s.strip() for s in r["iso_codes"].split(",") if s.strip()],
                      text=(r["name_en"] + ". " + (r["short_description_en"] or "")), comps=comps, inscribed=r["date_inscribed"]))
for c, g in G.items():
    gb = None if c in NAT else g.buffer(0.05)
    hits = collections.defaultdict(list)
    for p in props:
        if c in NAT:
            inside = c in p["states"]
        else:
            inside = any(gb.intersects(Point(lo, la)) for la, lo in p["comps"])
        if not inside:
            continue
        for cat, rx in KW.items():
            if cat == "historic_desc":
                continue
            if cat == "historic_old_world":
                if p["cat"] in ("Cultural", "Mixed") and (rx.search(p["name"]) or KW["historic_desc"].search(p["text"])):
                    hits[cat].append((p["id"], p["name"]))
            elif cat == "island_tropical":
                if rx.search(p["name"]):
                    hits["island"].append((p["id"], p["name"]))
            elif cat == "mountains_alpine":
                if p["cat"] in ("Natural", "Mixed") and rx.search(p["name"]):
                    hits[cat].append((p["id"], p["name"]))
            else:
                m = rx.search(p["text"])
                if m:
                    hits[cat].append((p["id"], p["name"], m.group(0).lower()))
    out[c]["unesco"] = {k: v[:4] for k, v in hits.items()}
pickle.dump(out, open("facts_tab.pkl", "wb"))
for c in ("QA", "IL", "US-AZ", "AU-QLD", "CA-QC", "AT", "US-WA"):
    print(c, out[c]["unesco"], out[c].get("wb"))
