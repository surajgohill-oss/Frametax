import pickle, json, math, re, csv, io, collections
import shapefile
from shapely import wkb
from shapely.geometry import shape, Point, box
from shapely.strtree import STRtree
from shapely.ops import unary_union
from shapely import make_valid

G = {c: wkb.loads(w) for c, (w, s) in pickle.load(open("geoms.pkl", "rb")).items()}
SRC = {c: s for c, (w, s) in pickle.load(open("geoms.pkl", "rb")).items()}


def read(name, kind):
    r = shapefile.Reader(f"ne/{name}/{name}")
    recs = [x.as_dict() for x in r.records()]
    shps = r.shapes()
    return recs, shps


facts = {c: {} for c in G}

# ---- islands: ne_10m_land + minor islands; continents = the 4 largest landmasses (Afro-Eurasia, Americas, Antarctica, Australia)
recs, shps = read("ne_10m_land", "land")
land = [make_valid(shape(s.__geo_interface__)) for s in shps]
polys = []
for g in land:
    polys.extend(list(g.geoms) if g.geom_type == "MultiPolygon" else [g])
polys.sort(key=lambda p: -p.area)
continental = polys[:4]   # sorted by planar area: Afro-Eurasia, Americas, Antarctica, Australia (check below)
print("largest landmass areas", [round(p.area) for p in polys[:7]])
islands = [p for p in polys[4:] if p.area > 1e-4]
rec2, shp2 = read("ne_10m_minor_islands", "mi")
for s in shp2:
    g = make_valid(shape(s.__geo_interface__))
    islands.extend(list(g.geoms) if g.geom_type == "MultiPolygon" else [g])
isl_tree = STRtree(islands)
land_tree = STRtree(polys)
for c, g in G.items():
    idx = [i for i in isl_tree.query(g, predicate="intersects")]
    big = sorted((islands[i].area for i in idx), reverse=True)
    facts[c]["island_n"] = len(idx)
    facts[c]["island_area_deg2_top"] = round(big[0], 3) if big else 0
    # coast: does the territory border open water within ~2 km (0.02 deg)?
    buf = g.buffer(0.02)
    near = [polys[i] for i in land_tree.query(buf, predicate="intersects")]
    covered = unary_union(near) if near else None
    ocean = buf.difference(covered) if covered is not None else buf
    facts[c]["coast"] = ocean.area > 1e-5

# ---- desert / range / tundra regions (NE geography regions)
rr, rs = read("ne_10m_geography_regions_polys", "reg")
regs = [(r["FEATURECLA"], r["NAME"], make_valid(shape(s.__geo_interface__))) for r, s in zip(rr, rs)]
for cls, key in (("Desert", "desert_ne"), ("Range/mtn", "range_ne"), ("Tundra", "tundra_ne")):
    sel = [(n, g) for c_, n, g in regs if c_ == cls]
    tree = STRtree([g for n, g in sel])
    for c, g in G.items():
        hits = [sel[i][0] for i in tree.query(g, predicate="intersects") if g.intersection(sel[i][1]).area > 1e-3]
        facts[c][key] = sorted(set(h for h in hits if h))

# Codex EVD-002 (2026-10-07): a subnational jurisdiction takes a point (peak, populated place) only when that point's
# ONE admin-1 unit -- the containing polygon, else the nearest within 0.05 degrees -- is the jurisdiction; national
# jurisdictions keep the 0.05 degree tolerance (international border summits genuinely belong to both states).
from geoms import NAT, SUB
_a1r = shapefile.Reader(NE + "ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces") if "NE" in globals() else shapefile.Reader("ne/ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces")
A1 = [(rec.as_dict()["iso_3166_2"], make_valid(shape(shp.__geo_interface__))) for rec, shp in zip(_a1r.records(), _a1r.shapes())]
A1_TREE = STRtree([g for _, g in A1])
_a1c = {}
def admin1_of(pt):
    k = (pt.x, pt.y)
    if k not in _a1c:
        inside = [i for i in A1_TREE.query(pt) if A1[i][1].intersects(pt)]
        if inside:
            _a1c[k] = A1[inside[0]][0]
        else:
            i = A1_TREE.nearest(pt)
            _a1c[k] = A1[i][0] if A1[i][1].distance(pt) <= 0.05 else None
    return _a1c[k]
def point_hits(tree, items, ptof, c, g):
    cand = [items[i] for i in tree.query(g.buffer(0.05), predicate="intersects")]
    if c in NAT:
        return cand
    return [x for x in cand if admin1_of(ptof(x)) == SUB.get(c, c)]

# ---- elevation points (peaks)
er, es = read("ne_10m_geography_regions_elevation_points", "el")
pts = [(r["name"], r["elevation"], Point(s.points[0])) for r, s in zip(er, es) if r["elevation"]]
ptree = STRtree([p for n, e, p in pts])
for c, g in G.items():
    hit = point_hits(ptree, pts, lambda x: x[2], c, g)
    hit.sort(key=lambda x: -x[1])
    facts[c]["peaks"] = [(n, e) for n, e, p in hit[:3]]
    facts[c]["peak_max"] = hit[0][1] if hit else None

# ---- glaciated areas
gr, gs = read("ne_10m_glaciated_areas", "gl")
gl = [make_valid(shape(s.__geo_interface__)) for s in gs]
gtree = STRtree(gl)
for c, g in G.items():
    facts[c]["glacier_n"] = len(gtree.query(g, predicate="intersects"))

# ---- urban areas share (NE urban extents) ; equirectangular area weighting
ur, us = read("ne_10m_urban_areas", "ua")
ug = [make_valid(shape(s.__geo_interface__)) for s in us]
utree = STRtree(ug)


def wa(g):  # cos-lat weighted planar area
    if g.is_empty:
        return 0.0
    return g.area * math.cos(math.radians(g.centroid.y))


for c, g in G.items():
    parts = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    tot = sum(wa(p) for p in parts) or 1e-9
    urb = 0.0
    for p in parts:
        hits = [ug[i] for i in utree.query(p, predicate="intersects")]
        if hits:
            urb += wa(unary_union(hits).intersection(p))
    facts[c]["urban_share"] = min(1.0, urb / tot)

# ---- populated places
pr_, ps_ = read("ne_10m_populated_places", "pp")
pp = [(r["NAME"], r["POP_MAX"] or 0, r["ADM0CAP"], Point(s.points[0])) for r, s in zip(pr_, ps_)]
pptree = STRtree([p[3] for p in pp])
for c, g in G.items():
    hit = point_hits(pptree, pp, lambda x: x[3], c, g)
    big = sorted([h for h in hit if h[1] >= 300000], key=lambda h: -h[1])
    town = [h for h in hit if 10000 <= h[1] < 300000]
    facts[c]["cities300k"] = [(h[0], int(h[1])) for h in big[:3]]
    facts[c]["n_cities300k"] = len(big)
    facts[c]["n_towns"] = len(town)
    facts[c]["towns_sample"] = [(h[0], int(h[1])) for h in sorted(town, key=lambda h: -h[1])[:3]]
pickle.dump(facts, open("facts_vec.pkl", "wb"))
for c in ("QA", "SG", "AT", "US-HI", "US-NY", "CA-MB", "LU", "MT", "AU", "US", "KZ"):
    f = facts[c]
    print(c, {k: f[k] for k in ("island_n", "coast", "desert_ne", "range_ne", "glacier_n", "urban_share", "n_cities300k", "n_towns")}, f["peaks"][:1])
