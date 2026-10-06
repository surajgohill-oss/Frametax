import pickle, collections, json
V = pickle.load(open("facts_vec.pkl", "rb"))
T = pickle.load(open("facts_tab.pkl", "rb"))
K = pickle.load(open("facts_kg.pkl", "rb"))
GL = pickle.load(open("facts_glc.pkl", "rb"))
import json as _j
NRHP = {k.title(): v for k, v in {f["attributes"]["STATE"]: f["attributes"]["n"] for f in _j.load(open("nrhp_districts.json"))["features"]}.items()}
_au = _j.load(open("au_nhl.geojson"))
AU_HIST = {}
for f in _au["features"]:
    if f["properties"]["CLASS"] == "Historic":
        AU_HIST.setdefault(f["properties"]["STATE"], []).append(f["properties"]["NAME"])
US_NAME = {"US-AL":"Alabama","US-AZ":"Arizona","US-CA":"California","US-CO":"Colorado","US-CT":"Connecticut","US-GA":"Georgia","US-HI":"Hawaii","US-IL":"Illinois","US-KY":"Kentucky","US-LA":"Louisiana","US-MA":"Massachusetts","US-MD":"Maryland","US-MN":"Minnesota","US-MS":"Mississippi","US-NC":"North Carolina","US-NM":"New Mexico","US-NV":"Nevada","US-NY":"New York","US-OK":"Oklahoma","US-OR":"Oregon","US-PA":"Pennsylvania","US-PR":"Puerto Rico","US-RI":"Rhode Island","US-SC":"South Carolina","US-TN":"Tennessee","US-TX":"Texas","US-UT":"Utah","US-VA":"Virginia","US-WA":"Washington"}
AU_STATE = {"AU-NSW":"NSW","AU-QLD":"QLD","AU-SA":"SA","AU":None}
NATS = set(__import__("geoms").NAT)
SUP, NOT, UNR = "SUPPORTED", "NOT_SUPPORTED", "UNRESOLVED_NEUTRAL"
CATS = ["island_tropical", "jungle_rainforest", "desert_arid", "mountains_alpine", "snow_arctic", "urban_major_city", "small_town_suburban",
        "rural_countryside", "forest_woodland", "historic_old_world"]
GRP = {"A": range(1, 4), "AfAm": (1, 2), "BW": (4, 5), "BS": (6, 7), "B": range(4, 8), "C": range(8, 17), "D": range(17, 29), "E": (29, 30)}
PRESENT = 0.005


def ks(code):
    c = {k: v for k, v in K[code].items() if k != 0}
    tot = sum(c.values())
    if tot <= 0:
        return None
    return {g: sum(c.get(i, 0) for i in r) / tot for g, r in GRP.items()}, tot


def fmt(d):
    return ", ".join(f"{g} {v*100:.1f}%" for g, v in d.items() if v > 0)


def cell(code, cat):
    """-> (status, components dict, tokens, proposition, sources[list of ids], method, attempted[list])"""
    v, t, k = V[code], T[code], ks(code)
    un = t.get("unesco", {})
    att = []
    comps = {}
    src = []
    prop = []
    nat = code in NATS
    if cat == "island_tropical":
        # island component
        isl_hits = v["island_n"] > 0 or bool(un.get("island"))
        if isl_hits:
            comps["island"] = SUP
            prop.append(f"island: territory intersects {v['island_n']} island landmass(es) in Natural Earth ne_10m_land/minor_islands" + (f"; UNESCO property '{un['island'][0][1]}'" if un.get("island") else ""))
            src += ["NE"] + (["UNESCO_WHL"] if un.get("island") else [])
        elif not v["coast"]:
            comps["island"] = NOT
            prop.append("island: territory has no marine coastline (Natural Earth ne_10m_land) and intersects no island landmass: no sea islands possible")
            src += ["NE"]
        else:
            comps["island"] = UNR
            att.append("Natural Earth ne_10m_land/minor_islands: coastal territory, no island landmass intersected")
        # tropical component
        if k is None:
            comps["tropical"] = UNR; att.append("Beck 2023 Koppen-Geiger 1km: no classified cell in territory")
        else:
            sh, _ = k
            if sh["A"] >= PRESENT:
                comps["tropical"] = SUP; prop.append(f"tropical: Koppen-Geiger group A (tropical) covers {sh['A']*100:.1f}% of the territory ({fmt({x: sh[x] for x in ('AfAm',)})} Af/Am)"); src += ["KG2023"]
            elif sh["A"] == 0:
                comps["tropical"] = NOT; prop.append(f"tropical: no Koppen-Geiger group A (tropical) cell in the territory (classes: {fmt({g: sh[g] for g in ('B','C','D','E')})})"); src += ["KG2023"]
            else:
                comps["tropical"] = UNR; att.append(f"Beck 2023 Koppen-Geiger: tropical group A covers only {sh['A']*100:.2f}% (< {PRESENT*100:.1f}% threshold)")
        s = SUP if SUP in comps.values() else (NOT if all(x == NOT for x in comps.values()) else UNR)
        return s, comps, "tropical_environments;island_environments;tropical_climate_environments", " | ".join(prop), sorted(set(src)), "OR(island, tropical)", att
    if cat == "jungle_rainforest":
        if un.get("jungle_rainforest"):
            h = un["jungle_rainforest"][0]; prop.append(f"UNESCO World Heritage property '{h[1]}' (id {h[0]}) describes rainforest ('{h[2]}')"); src += ["UNESCO_WHL"]
        if k and k[0]["AfAm"] >= PRESENT:
            prop.append(f"Koppen-Geiger Af/Am (tropical rainforest/monsoon) covers {k[0]['AfAm']*100:.1f}% of the territory"); src += ["KG2023"]
        if prop:
            return SUP, {"jungle_rainforest": SUP}, "jungle_environments", " | ".join(prop), sorted(set(src)), "OR(UNESCO rainforest property, Koppen Af/Am >= 0.5%)", att
        if k and k[0]["A"] == 0 and k[0]["C"] == 0:
            return NOT, {"jungle_rainforest": NOT}, "jungle_environments", f"Koppen-Geiger classes in the territory are only arid/cold/polar ({fmt(k[0])}): no tropical (A) or temperate (C) rainforest climate exists", ["KG2023"], "Koppen groups A and C both absent", att
        att.append("UNESCO WHL: no rainforest property"); att.append("Beck 2023 Koppen-Geiger: Af/Am < 0.5% and not excluded (tropical savannah or temperate classes present)" if k else "no classified cell")
        return UNR, {"jungle_rainforest": UNR}, "jungle_environments", "", [], "", att
    if cat == "desert_arid":
        ne = v["desert_ne"]
        if k and (k[0]["BW"] >= PRESENT or k[0]["BS"] >= 0.10):
            prop.append(f"Koppen-Geiger arid group B covers {k[0]['B']*100:.1f}% of the territory (BW desert {k[0]['BW']*100:.1f}%, BS semi-arid steppe {k[0]['BS']*100:.1f}%)"); src += ["KG2023"]
        if ne:
            prop.append("Natural Earth desert region(s) intersect: " + ", ".join(ne[:3])); src += ["NE"]
        if un.get("desert_arid"):
            h = un["desert_arid"][0]; prop.append(f"UNESCO World Heritage property '{h[1]}' (id {h[0]}) describes desert"); src += ["UNESCO_WHL"]
        gl = GL[code]; bs = (gl["bare"][0] or 0) + (gl["sparse"][0] or 0)
        if bs >= 25:
            prop.append(f"FAO GLC-SHARE v1.0: bare soil + sparse vegetation cover {bs:.0f}% of the territory"); src += ["GLC_SHARE"]
        if prop:
            return SUP, {"desert_arid": SUP}, "desert_environments", " | ".join(prop), sorted(set(src)), "OR(Koppen BW >= 0.5% or BS >= 10%, NE desert region, UNESCO desert property, GLC-SHARE bare+sparse >= 25%)", att
        if k and k[0]["B"] == 0 and k[0]["E"] == 0 and bs < 5:
            return NOT, {"desert_arid": NOT}, "desert_environments", f"No Koppen-Geiger arid (BW/BS) or polar (E) cell in the territory (classes: {fmt(k[0])}); no Natural Earth desert region; no UNESCO desert property; FAO GLC-SHARE bare soil + sparse vegetation only {bs:.1f}%", ["KG2023", "NE", "UNESCO_WHL", "GLC_SHARE"], "Koppen B and E absent AND NE desert absent AND UNESCO desert absent AND GLC-SHARE bare+sparse < 5%", att
        att.append(f"Beck 2023 Koppen-Geiger: arid group B present but below the support thresholds (BW {k[0]['BW']*100:.2f}% < 0.5%, BS {k[0]['BS']*100:.2f}% < 10%) or polar E present" if k else "no classified cell"); att.append(f"Natural Earth desert regions: none; UNESCO WHL: none; FAO GLC-SHARE bare+sparse {bs:.1f}% (< 25%)")
        return UNR, {"desert_arid": UNR}, "desert_environments", "", [], "", att
    if cat == "snow_arctic":
        if k and (k[0]["D"] + k[0]["E"]) >= PRESENT:
            prop.append(f"Koppen-Geiger snow/polar groups D+E cover {(k[0]['D']+k[0]['E'])*100:.1f}% of the territory (D {k[0]['D']*100:.1f}%, E {k[0]['E']*100:.1f}%)"); src += ["KG2023"]
        if v["glacier_n"]:
            prop.append(f"Natural Earth glaciated areas: {v['glacier_n']} intersect"); src += ["NE"]
        if v["tundra_ne"]:
            prop.append("Natural Earth tundra region(s): " + ", ".join(v["tundra_ne"])); src += ["NE"]
        if un.get("snow_arctic"):
            h = un["snow_arctic"][0]; prop.append(f"UNESCO World Heritage property '{h[1]}' (id {h[0]}) describes {h[2]}"); src += ["UNESCO_WHL"]
        sg = GL[code]["snow"][0] or 0
        if sg >= 0.1:
            prop.append(f"FAO GLC-SHARE v1.0: snow and glaciers cover {sg:.2f}% of the territory"); src += ["GLC_SHARE"]
        if prop:
            return SUP, {"snow_arctic": SUP}, "snow_environments", " | ".join(prop), sorted(set(src)), "OR(Koppen D+E >= 0.5%, NE glaciated/tundra, UNESCO ice/snow property, GLC-SHARE snow >= 0.1%)", att
        if k and k[0]["A"] >= 0.999:
            return NOT, {"snow_arctic": NOT}, "snow_environments", f"Every classified cell is tropical (Koppen group A: coldest month >= 18 C): snow is not a climatic possibility ({fmt(k[0])}); no glaciated area, tundra region or UNESCO ice property", ["KG2023", "NE", "UNESCO_WHL"], "Koppen A >= 99.9% AND no glacier/tundra/UNESCO ice", att
        att.append("Beck 2023 Koppen-Geiger: D+E below 0.5% and not purely tropical" if k else "no classified cell"); att.append("Natural Earth glaciated/tundra: none; UNESCO WHL: none")
        return UNR, {"snow_arctic": UNR}, "snow_environments", "", [], "", att
    if cat == "mountains_alpine":
        if v["range_ne"]:
            prop.append("Natural Earth mountain range region(s): " + ", ".join(v["range_ne"][:4])); src += ["NE"]
        if v["peak_max"] and v["peak_max"] >= 1500:
            pk = v["peaks"][0]; prop.append(f"Natural Earth elevation point: {pk[0] or 'peak'} {int(pk[1])} m (>= 1,500 m)"); src += ["NE"]
        if un.get("mountains_alpine"):
            h = [x for x in un["mountains_alpine"]][0]; prop.append(f"UNESCO World Heritage property '{h[1]}' (id {h[0]})"); src += ["UNESCO_WHL"]
        if prop:
            return SUP, {"mountains_alpine": SUP}, "mountain_environments", " | ".join(prop), sorted(set(src)), "OR(NE Range/mtn region, NE peak >= 1,500 m, UNESCO mountain property)", att
        att.append(f"Natural Earth ranges/peaks: none >= 1,500 m (highest recorded {v['peak_max']} m)"); att.append("UNESCO WHL: none")
        return UNR, {"mountains_alpine": UNR}, "mountain_environments", "", [], "", att
    if cat == "urban_major_city":
        if nat and t.get("wup"):
            w = t["wup"]
            if w["Cities"] >= 200:
                return SUP, {"urban_major_city": SUP}, "urban_environments", f"UN DESA WUP 2025 (Degree of Urbanisation, 2025): {w['Cities']:.0f} thousand people live in cities ({w['Cities']/w['Total']*100:.1f}% of {w['Total']:.0f} thousand)", ["WUP2025"], "WUP Cities >= 200 thousand", att
            att.append(f"UN WUP 2025: cities population {w['Cities']:.0f} thousand (< 200 thousand)")
        elif nat:
            att.append("UN WUP 2025 F01: no row for this jurisdiction")
        if v["n_cities300k"]:
            cs = v["cities300k"]
            return SUP, {"urban_major_city": SUP}, "urban_environments", "Natural Earth populated places with population >= 300,000 inside the territory: " + ", ".join(f"{n} ({p:,})" for n, p in cs), ["NE_PP"], "NE populated place POP_MAX >= 300,000", att
        att.append("Natural Earth populated places: no place >= 300,000 in territory")
        return UNR, {"urban_major_city": UNR}, "urban_environments", "", [], "", att
    if cat == "small_town_suburban":
        if nat and t.get("wup"):
            w = t["wup"]
            if w["Towns"] >= 100 and w["Towns"] / w["Total"] >= 0.03:
                return SUP, {"small_town_suburban": SUP}, "small_town_environments", f"UN DESA WUP 2025 (Degree of Urbanisation, 2025): {w['Towns']:.0f} thousand people live in towns and suburbs ({w['Towns']/w['Total']*100:.1f}% of national population)", ["WUP2025"], "WUP Towns >= 100 thousand AND >= 3%", att
            att.append(f"UN WUP 2025: towns and suburbs {w['Towns']:.0f} thousand ({w['Towns']/w['Total']*100:.1f}%)")
        elif nat:
            att.append("UN WUP 2025 F01: no row for this jurisdiction")
        if (not nat) and v["n_towns"] >= 3:
            return SUP, {"small_town_suburban": SUP}, "small_town_environments", f"Natural Earth populated places of 10,000-300,000 inhabitants inside the territory: {v['n_towns']} (e.g. " + ", ".join(f"{n} ({p:,})" for n, p in v["towns_sample"]) + ")", ["NE_PP"], "NE places 10,000-300,000 >= 3", att
        if not nat:
            att.append(f"Natural Earth populated places: {v['n_towns']} places of 10,000-300,000 (< 3)")
        return UNR, {"small_town_suburban": UNR}, "small_town_environments", "", [], "", att
    if cat == "rural_countryside":
        if nat and t.get("wup"):
            w = t["wup"]
            if w["Rural"] >= 100:
                return SUP, {"rural_countryside": SUP}, "rural_environments", f"UN DESA WUP 2025 (Degree of Urbanisation, 2025): {w['Rural']:.0f} thousand people live in rural areas ({w['Rural']/w['Total']*100:.1f}%)", ["WUP2025"], "WUP Rural >= 100 thousand", att
            att.append(f"UN WUP 2025: rural population {w['Rural']:.0f} thousand (< 100 thousand)")
        elif nat:
            att.append("UN WUP 2025 F01: no row for this jurisdiction")
        ag = (GL[code]["crop"][0] or 0) + (GL[code]["grass"][0] or 0)
        if ag >= 10:
            return SUP, {"rural_countryside": SUP}, "rural_environments", f"FAO GLC-SHARE v1.0: cropland + grassland cover {ag:.0f}% of the territory", ["GLC_SHARE"], "GLC-SHARE crop+grass >= 10%", att
        att.append(f"FAO GLC-SHARE v1.0: cropland + grassland {ag:.1f}% (< 10%)")
        return UNR, {"rural_countryside": UNR}, "rural_environments", "", [], "", att
    if cat == "forest_woodland":
        prop = []
        wb = t.get("wb", {}).get("AG.LND.FRST.ZS") if nat else None
        if wb and wb[0] >= 5:
            prop.append(f"FAO Global Forest Resources Assessment via World Bank WDI AG.LND.FRST.ZS: forest area {wb[0]:.1f}% of land area ({wb[1]})"); src += ["WB_FRST"]
        elif nat:
            att.append(f"World Bank WDI/FAO forest area: {wb[0]:.2f}% ({wb[1]}) < 5%" if wb else "World Bank WDI/FAO forest area: no value for this jurisdiction")
        tr = GL[code]["trees"][0] or 0
        if tr >= 5:
            prop.append(f"FAO GLC-SHARE v1.0: tree-covered area {tr:.1f}% of the territory"); src += ["GLC_SHARE"]
        if un.get("forest_woodland"):
            h = un["forest_woodland"][0]; prop.append(f"UNESCO World Heritage property '{h[1]}' (id {h[0]}) describes forests"); src += ["UNESCO_WHL"]
        if prop:
            return SUP, {"forest_woodland": SUP}, "forest_environments", " | ".join(prop), sorted(set(src)), "OR(FAO GLC-SHARE tree cover >= 5%, FAO FRA forest area >= 5%, UNESCO forest property)", att
        wbv = wb[0] if wb else None
        if tr < 0.1 and (wbv is None or wbv < 0.1) and not un.get("forest_woodland"):
            return NOT, {"forest_woodland": NOT}, "forest_environments", f"FAO GLC-SHARE v1.0 tree-covered area {tr:.2f}% of the territory" + (f" and FAO FRA forest area {wbv:.1f}% of land (World Bank WDI)" if wbv is not None else "") + "; no UNESCO forest property", ["GLC_SHARE"] + (["WB_FRST"] if wbv is not None else []), "GLC-SHARE tree cover < 0.1% AND FAO FRA forest < 0.1%", att
        att.append(f"FAO GLC-SHARE v1.0: tree-covered area {tr:.2f}% (< 5%)"); att.append("UNESCO WHL: no forest property")
        return UNR, {"forest_woodland": UNR}, "forest_environments", "", [], "", att
    if cat == "historic_old_world":
        if un.get("historic_old_world"):
            hs = un["historic_old_world"][:3]
            return SUP, {"historic_old_world": SUP}, "historic_architecture", "UNESCO World Heritage cultural properties: " + "; ".join(f"{n} (id {i})" for i, n in hs), ["UNESCO_WHL"], "UNESCO cultural/mixed property with historic-urban name", att
        att.append("UNESCO WHL: no cultural property with a historic-centre/old-town/medina/castle name")
        if code == "US":
            n = sum(NRHP.values())
            return SUP, {"historic_old_world": SUP}, "historic_architecture", f"US National Park Service National Register of Historic Places (Cultural Resources GIS): {n:,} listed historic districts", ["NRHP"], "NRHP historic districts >= 5", att
        if code in US_NAME:
            n = NRHP.get(US_NAME[code], 0)
            if n >= 5:
                return SUP, {"historic_old_world": SUP}, "historic_architecture", f"US National Park Service National Register of Historic Places (Cultural Resources GIS): {n} listed historic districts in {US_NAME[code]}", ["NRHP"], "NRHP historic districts >= 5", att
            att.append(f"US NPS National Register of Historic Places: {n} listed districts (< 5)")
        if code in AU_STATE:
            if code == "AU":
                n = sum(len(v) for v in AU_HIST.values())
            else:
                n = len(AU_HIST.get(AU_STATE[code], []))
            if n >= 1:
                return SUP, {"historic_old_world": SUP}, "historic_architecture", f"Australian National Heritage List (DCCEEW spatial database, updated 2026-02-25): {n} listed historic places" + ("" if code == "AU" else f" in {AU_STATE[code]}"), ["AU_NHL"], "NHL class Historic >= 1", att
            att.append("Australian National Heritage List: no historic place")
        if code.startswith("CA-") or code == "CA":
            att.append("Parks Canada Places FeatureServer (open.canada.ca): only 2 national-historic-site polygons published; open.canada.ca search found no province-level historic register dataset")
        return UNR, {"historic_old_world": UNR}, "historic_architecture", "", [], "", att


R = {}
for code in V:
    for cat in CATS:
        R[(code, cat)] = cell(code, cat)
pickle.dump(R, open("derived.pkl", "wb"))
cnt = collections.Counter((cat, r[0]) for (code, cat), r in R.items())
for cat in CATS:
    print(f"{cat:22s}", {s: cnt[(cat, s)] for s in (SUP, NOT, UNR)})
print(collections.Counter(r[0] for r in R.values()))
