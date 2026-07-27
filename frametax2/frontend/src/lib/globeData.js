import { JURISDICTION_COORDS } from "./jurisdictions";

export const TIER_RANK = { gold: 4, jade: 3, amber: 2, silver: 1 };

// Tier is derived entirely from the allocated structure's own real
// fields (allocated_structures.ranking + is_fully_priced + blockers) —
// never a client-side re-derivation of pricing. Kept as-is: several
// surfaces (card badges, the Optimizer Overlay) key off this ranking
// tier, distinct from the Globe's jurisdiction-qualification palette.
export function structureTier(structure, rankById) {
  const rank = rankById.get(structure.structure_id);
  if (rank?.rank === 1) return "gold";
  if (structure.is_fully_priced) return "jade";
  if (structure.blockers?.length > 0) return "amber";
  return "silver";
}

// The producer's active/leading structure — the shared selection
// (AppState leadingStructureId) if set, else the optimizer's own rank #1.
export function activeStructure(allocated, leadingStructureId) {
  if (!allocated) return null;
  const byId = new Map(allocated.structures.map((s) => [s.structure_id, s]));
  if (leadingStructureId && byId.has(leadingStructureId)) return byId.get(leadingStructureId);
  const best = allocated.ranking.find((r) => r.rank === 1);
  return best ? byId.get(best.structure_id) : null;
}

// Approved jurisdiction-qualification palette for the Globe's default
// "Jurisdictions" mode (distinct semantic axis from the gold/jade/amber/
// silver structure-ranking tier above — a jurisdiction can be "Viable"
// while its structure isn't the top-ranked one).
//   green  = Recommended       — this jurisdiction's best structure is rank #1
//   yellow = Viable            — a fully-priced, non-leading structure exists
//   orange = Conditional       — allocated but not fully priced (blockers)
//   red    = Not Qualified     — discovery rejected the jurisdiction outright
//   white  = Unused            — no participation signal at all
//   blue   = Currently Selected (overrides all of the above)
export const QUALIFICATION_HEX = {
  green: "#5fae72",
  yellow: "#d8c25a",
  orange: "#c99a4d",
  red: "#b8654f",
  white: "#e7e5df",
  blue: "#5b8fd8",
};

function qualificationState(code, { tierByCode, rejectedCodes }) {
  const tier = tierByCode.get(code);
  if (tier === "gold") return "green";
  if (tier === "jade") return "yellow";
  if (tier === "amber" || tier === "silver") return "orange";
  if (rejectedCodes?.has(code)) return "red";
  return "white";
}

// Builds globe points/arcs from the SAME allocated_structures payload the
// Lane Rack renders — one live production model feeding Overview's globe,
// Workspace Map, and Split alike. structuresByCode (best-tier-first per
// jurisdiction) also drives globe click → Inspector.
//
// mode: "jurisdictions" (default — every participating jurisdiction, colored
// by qualification state) or "optimizer" (only the active structure's own
// chain of participants, in participant order, connected by arcs — the
// "US Parent -> Mauritius Production -> London VFX" overlay). Both modes
// reuse this same engine/points/arcs shape; no second visualization.
export function buildGlobeData(
  allocated, rankById,
  { mode = "jurisdictions", leadingStructureId = null, selectedJurisdiction = null } = {},
) {
  if (!allocated) return { points: [], arcs: [], structuresByCode: new Map() };
  const tierByCode = new Map();
  const byCode = new Map();
  const arcList = [];

  const rejectedCodes = new Set(
    (allocated.discovery?.examinations || [])
      .filter((e) => e.classification === "rejected")
      .map((e) => e.jurisdiction_code),
  );

  if (mode === "optimizer") {
    const active = activeStructure(allocated, leadingStructureId);
    if (!active) return { points: [], arcs: [], structuresByCode: byCode };
    const chain = (active.participants || []).filter((c) => JURISDICTION_COORDS[c]);
    for (const code of chain) {
      byCode.set(code, [active]);
      tierByCode.set(code, "gold");
    }
    for (let i = 0; i < chain.length - 1; i++) {
      const ca = JURISDICTION_COORDS[chain[i]];
      const cb = JURISDICTION_COORDS[chain[i + 1]];
      if (ca && cb) arcList.push({ startLat: ca.lat, startLng: ca.lng, endLat: cb.lat, endLng: cb.lng, tier: "gold" });
    }
    const points = chain.map((code) => ({
      lat: JURISDICTION_COORDS[code].lat, lng: JURISDICTION_COORDS[code].lng,
      tier: "gold", name: code, id: code,
      color: code === selectedJurisdiction ? QUALIFICATION_HEX.blue : QUALIFICATION_HEX.green,
    }));
    return { points, arcs: arcList, structuresByCode: byCode };
  }

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
  const points = [...tierByCode.entries()].map(([code, tier]) => {
    const qual = code === selectedJurisdiction ? "blue" : qualificationState(code, { tierByCode, rejectedCodes });
    return {
      lat: JURISDICTION_COORDS[code].lat, lng: JURISDICTION_COORDS[code].lng,
      tier, name: code, id: code, color: QUALIFICATION_HEX[qual],
    };
  });
  return { points, arcs: arcList, structuresByCode: byCode };
}
