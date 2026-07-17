import { JURISDICTION_COORDS } from "./jurisdictions";

export const TIER_RANK = { gold: 4, jade: 3, amber: 2, silver: 1 };

// Tier is derived entirely from the allocated structure's own real
// fields (allocated_structures.ranking + is_fully_priced + blockers) —
// never a client-side re-derivation of pricing.
export function structureTier(structure, rankById) {
  const rank = rankById.get(structure.structure_id);
  if (rank?.rank === 1) return "gold";
  if (structure.is_fully_priced) return "jade";
  if (structure.blockers?.length > 0) return "amber";
  return "silver";
}

// Builds globe points/arcs from the SAME allocated_structures payload the
// Lane Rack renders — one live production model feeding Overview's globe,
// Workspace Map, and Split alike. structuresByCode (best-tier-first per
// jurisdiction) also drives globe click → Inspector.
export function buildGlobeData(allocated, rankById) {
  if (!allocated) return { points: [], arcs: [], structuresByCode: new Map() };
  const tierByCode = new Map();
  const byCode = new Map();
  const arcList = [];
  for (const s of allocated.structures) {
    const tier = structureTier(s, rankById);
    for (const code of s.participants) {
      if (!JURISDICTION_COORDS[code]) continue;
      const list = byCode.get(code) || [];
      list.push(s);
      byCode.set(code, list);
      const existingTier = tierByCode.get(code);
      if (!existingTier || TIER_RANK[tier] > TIER_RANK[existingTier]) tierByCode.set(code, tier);
    }
    if (s.treaty_slug && s.participants.length === 2) {
      const [a, b] = s.participants;
      const ca = JURISDICTION_COORDS[a];
      const cb = JURISDICTION_COORDS[b];
      if (ca && cb) arcList.push({ startLat: ca.lat, startLng: ca.lng, endLat: cb.lat, endLng: cb.lng, tier });
    }
  }
  for (const list of byCode.values()) {
    list.sort((x, y) => TIER_RANK[structureTier(y, rankById)] - TIER_RANK[structureTier(x, rankById)]);
  }
  const points = [...tierByCode.entries()].map(([code, tier]) => ({
    lat: JURISDICTION_COORDS[code].lat, lng: JURISDICTION_COORDS[code].lng, tier, name: code, id: code,
  }));
  return { points, arcs: arcList, structuresByCode: byCode };
}
