// JURISDICTION_POLYGON_INTERACTION (2026-10-01): pure geometry for resolving a
// globe coordinate to the jurisdiction polygon that contains it, so hover and
// click work across a country/state/province's whole surface instead of a small
// coordinate marker. Marker hit-boxes remain ONLY as a fallback for represented
// jurisdictions that have no usable polygon (islands/city-states the 110m set
// omits, Australian states, national "CA"/"US" entries whose national polygon is
// replaced by admin-1 provinces/states) -- see markerNeedsFallback.

function ringContains(ring, lng, lat) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
    if ((yi > lat) !== (yj > lat) && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function polygonContains(rings, lng, lat) {
  if (!rings.length || !ringContains(rings[0], lng, lat)) return false;
  for (let k = 1; k < rings.length; k++) if (ringContains(rings[k], lng, lat)) return false; // hole
  return true;
}

function bboxOf(polys) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const rings of polys) for (const [x, y] of rings[0] || []) {
    if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
  }
  return { minX, minY, maxX, maxY };
}

// features: GeoJSON Polygon/MultiPolygon features; isoOf(feature) -> canonical globe key.
export function buildPolygonIndex(features, isoOf) {
  const index = [];
  for (const f of features || []) {
    const iso = isoOf(f);
    const g = f?.geometry;
    if (!iso || !g) continue;
    const polys = g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : null;
    if (!polys) continue;
    const bbox = bboxOf(polys);
    index.push({ iso, polys, bbox, area: (bbox.maxX - bbox.minX) * (bbox.maxY - bbox.minY) });
  }
  return index;
}

// The jurisdiction whose polygon contains (lat, lng); the smallest containing
// bounding box wins so a state/province always beats any enclosing feature.
export function pickIsoAt(index, lat, lng) {
  let best = null;
  for (const e of index) {
    const b = e.bbox;
    if (lng < b.minX || lng > b.maxX || lat < b.minY || lat > b.maxY) continue;
    if (best && e.area >= best.area) continue;
    for (const rings of e.polys) {
      if (polygonContains(rings, lng, lat)) { best = e; break; }
    }
  }
  return best ? best.iso : null;
}

export function polygonIsoSet(index) {
  return new Set(index.map((e) => e.iso));
}

// A marker stays pointer-interactive only when its jurisdiction has no polygon
// geometry to interact with. (Keyboard focus/Enter is always available.)
export function markerNeedsFallback(point, isoSet) {
  if (!isoSet) return true;
  return !isoSet.has(point?.iso);
}

// The datum a pointer-over-polygon resolves to: that jurisdiction's own marker
// record, or null when the jurisdiction is not represented for this production.
export function resolvePolygonTarget(index, lat, lng, pointByIso) {
  const iso = pickIsoAt(index, lat, lng);
  if (!iso) return null;
  return pointByIso.get(iso) || null;
}
