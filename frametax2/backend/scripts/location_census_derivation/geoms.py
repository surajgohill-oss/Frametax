"""Territory geometries for the 114 census jurisdictions from Natural Earth 1:10m admin layers (shared by the derivation steps)."""
import sys, json, pickle
sys.path.insert(0, __import__("os").environ.get("CINEGLOBE_BACKEND", "."))
import shapefile
from shapely.geometry import shape, box
from shapely.ops import unary_union
from shapely import make_valid

NE = "ne/"
# national code -> ADM0_A3 (Natural Earth); ISO2 for most
NAT = {"AL":"ALB","AT":"AUT","AU":"AUS","BE":"BEL","BG":"BGR","CA":"CAN","CH":"CHE","CL":"CHL","CO":"COL","CR":"CRI","CY":"CYP","CZ":"CZE","DE":"DEU",
 "DK":"DNK","DO":"DOM","EE":"EST","EG":"EGY","ES":"ESP","FI":"FIN","FJ":"FJI","FR":"FRA","GB":"GBR","GE":"GEO","GH":"GHA","GR":"GRC","HR":"HRV","HU":"HUN",
 "IE":"IRL","IL":"ISR","IN":"IND","IS":"ISL","IT":"ITA","JO":"JOR","JP":"JPN","KR":"KOR","KZ":"KAZ","LT":"LTU","LU":"LUX","LV":"LVA","MA":"MAR","ME":"MNE",
 "MK":"MKD","MN":"MNG","MT":"MLT","MU":"MUS","MX":"MEX","MY":"MYS","NL":"NLD","NO":"NOR","NZ":"NZL","PA":"PAN","PE":"PER","PH":"PHL","PL":"POL","PT":"PRT",
 "QA":"QAT","RO":"ROU","RS":"SRB","SA":"SAU","SE":"SWE","SG":"SGP","SI":"SVN","SK":"SVK","TH":"THA","TT":"TTO","TW":"TWN","UA":"UKR","US":"USA","UY":"URY",
 "UZ":"UZB","ZA":"ZAF"}
# subnational: Natural Earth admin-1 iso_3166_2
SUB = {"AE-AD":"AE-AZ","AE-DXB":"AE-DU"}
CLIP = {"FR": box(-6, 41, 10, 52), "NL": box(3, 50, 8, 54)}   # metropolitan France (+Corsica); European Netherlands (overseas parts excluded)


def build(profile_codes):
    out = {}
    r0 = shapefile.Reader(NE + "ne_10m_admin_0_countries/ne_10m_admin_0_countries")
    by_a3 = {rec["ADM0_A3"]: sr for rec, sr in zip((x.as_dict() for x in r0.records()), r0.shapes())}
    r1 = shapefile.Reader(NE + "ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces")
    by_iso2 = {}
    for rec, shp in zip((x.as_dict() for x in r1.records()), r1.shapes()):
        by_iso2.setdefault(rec["iso_3166_2"], []).append(shp)
    for code in profile_codes:
        if code in NAT:
            g = make_valid(shape(by_a3[NAT[code]].__geo_interface__))
            if code in CLIP:
                g = make_valid(g.intersection(CLIP[code]))
            out[code] = (g, f"Natural Earth 1:10m admin-0 {NAT[code]}")
        else:
            key = SUB.get(code, code)
            shps = by_iso2.get(key)
            assert shps, code
            g = make_valid(unary_union([make_valid(shape(s.__geo_interface__)) for s in shps]))
            out[code] = (g, f"Natural Earth 1:10m admin-1 {key}")
    return out


if __name__ == "__main__":
    from app.calculators import jurisdiction_comparison as jc
    codes = jc.location_census_jurisdictions()
    G = build(codes)
    pickle.dump({c: (g.wkb, s) for c, (g, s) in G.items()}, open("geoms.pkl", "wb"))
    print(len(G), "ok")
    for c in ("FR", "NL", "US", "AE-AD", "US-PR", "AU-NSW", "TW"):
        print(c, G[c][0].geom_type, round(G[c][0].area, 2), G[c][0].bounds)
