import sys, pickle, glob, os
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.features import geometry_mask
from shapely import wkb
from shapely.geometry import mapping

G = {c: wkb.loads(w) for c, (w, s) in pickle.load(open("geoms.pkl", "rb")).items()}
LAYERS = {"artificial": "01", "crop": "02", "grass": "03", "trees": "04", "sparse": "08", "bare": "09", "snow": "10"}
out = {c: {} for c in G}
for name, n in LAYERS.items():
    tifs = glob.glob(f"glc/x{n}/**/*.[Tt][Ii][Ff]", recursive=True)
    if not tifs:
        print("no tif for", name); continue
    src = rasterio.open(tifs[0])
    print(name, tifs[0], src.shape, src.res, src.dtypes, src.nodata, flush=True)
    for code, g in G.items():
        parts = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        tot = 0.0; acc = 0.0; hi = 0.0
        for p in parts:
            minx, miny, maxx, maxy = p.bounds
            win = from_bounds(minx, miny, maxx, maxy, src.transform).round_offsets().round_lengths()
            win = Window(max(0, win.col_off), max(0, win.row_off), max(1, min(win.width + 1, src.width - win.col_off)), max(1, min(win.height + 1, src.height - win.row_off)))
            arr = src.read(1, window=win).astype("float32")
            tr = src.window_transform(win)
            m = geometry_mask([mapping(p)], out_shape=arr.shape, transform=tr, invert=True, all_touched=True)
            if not m.any():
                continue
            lat = tr.f + (np.arange(arr.shape[0]) + 0.5) * tr.e
            w_ = (np.cos(np.radians(lat))[:, None] * np.ones((1, arr.shape[1])))[m]
            v = arr[m]
            ok = (v >= 0) & (v <= 100)
            tot += float(w_[ok].sum()); acc += float((w_[ok] * v[ok]).sum()); hi += float(w_[ok & (v >= 50)].sum())
        out[code][name] = (acc / tot if tot else None, hi / tot * 100 if tot else None)
    pickle.dump(out, open("facts_glc.pkl", "wb"))
for c in ("QA", "AT", "US-WA", "SG", "CA-NB", "US-AZ", "CH"):
    print(c, {k: (round(v[0], 1) if v[0] is not None else None) for k, v in out[c].items()})
