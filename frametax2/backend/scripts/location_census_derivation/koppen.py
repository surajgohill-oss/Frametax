import sys, pickle, math, collections
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.features import geometry_mask
from shapely import wkb
from shapely.geometry import mapping

TIF = sys.argv[1]
G = {c: wkb.loads(w) for c, (w, s) in pickle.load(open("geoms.pkl", "rb")).items()}
src = rasterio.open(TIF)
print(src.shape, src.res, src.crs, src.dtypes, src.nodata)
res = {}
for code, g in G.items():
    parts = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    cnt = collections.Counter()
    for p in parts:
        minx, miny, maxx, maxy = p.bounds
        win = from_bounds(minx, miny, maxx, maxy, src.transform).round_offsets().round_lengths()
        win = Window(max(0, win.col_off), max(0, win.row_off), max(1, min(win.width + 1, src.width - win.col_off)), max(1, min(win.height + 1, src.height - win.row_off)))
        arr = src.read(1, window=win)
        tr = src.window_transform(win)
        m = geometry_mask([mapping(p)], out_shape=arr.shape, transform=tr, invert=True, all_touched=True)
        if not m.any():   # polygon smaller than a cell: take the cell containing the centroid
            continue
        rows_ = np.arange(arr.shape[0])
        lat = tr.f + (rows_ + 0.5) * tr.e
        w_ = np.cos(np.radians(lat))[:, None] * np.ones((1, arr.shape[1]))
        vals = arr[m]; wt = w_[m]
        for v in np.unique(vals):
            cnt[int(v)] += float(wt[vals == v].sum())
    res[code] = dict(cnt)
    tot = sum(res[code].values()) or 1
    print(code, {k: round(v / tot, 3) for k, v in sorted(res[code].items(), key=lambda kv: -kv[1])[:5]}, flush=True)
pickle.dump(res, open("facts_kg.pkl", "wb"))
