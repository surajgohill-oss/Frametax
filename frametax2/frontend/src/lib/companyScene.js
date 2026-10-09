// Company Globe scene: ONE pure function from the resolved portfolio rows to the Globe's markers, routes, labels and territory
// colours. The side list and the Globe both consume the same `rows` array, so they cannot disagree on the project count.
import { JURISDICTION_COORDS } from "./jurisdictions.js";
import { globeKey } from "./globeKey.js";
import { participantsOf, structureArcs, structureRouteLabels } from "./globeStructure.js";
import { readIncentivePotential } from "./incentivePotential.js";
import { libraryStageKey } from "./libraryStatus.js";

// The globe body is dark glass in both app themes, but the day stage tokens are dark inks (#2C5580 blue); a territory painted in
// the raw token disappears into the graphite land. Territories take the stage hue lifted toward white so they read in both themes.
export function liftHex(hex, amount = 0.42) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex || "").trim());
  if (!m) return hex;
  const n = parseInt(m[1], 16);
  const mix = (c) => Math.round(c + (255 - c) * amount);
  return `#${[(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => mix(c).toString(16).padStart(2, "0")).join("")}`;
}

export function buildCompanyScene(rows, hexOf) {
  const points = [];
  const arcs = [];
  const routeLabels = [];
  // Each project's participating territories are painted in its stage colour (principal first, so it wins a shared country).
  const polygonColors = new Map();
  for (const { project, structure, principal, homeCode } of rows || []) {
    const hex = hexOf(project);
    const codes = structure ? participantsOf(structure) : [principal];
    for (const code of new Set([principal, ...codes].filter(Boolean))) {
      if (!polygonColors.has(globeKey(code))) polygonColors.set(globeKey(code), liftHex(hex));
      const coord = JURISDICTION_COORDS[code] || JURISDICTION_COORDS[String(code).split("-")[0]];
      if (!coord) continue;
      points.push({
        lat: coord.lat, lng: coord.lng, tier: libraryStageKey(project), color: hex,
        name: project.title, id: `${project.id}:${code}`, iso: globeKey(code), projectId: project.id, code, principal: code === principal,
        pot: readIncentivePotential(structure),
      });
    }
    if (structure) {
      arcs.push(...structureArcs(structure, { color: hex, homeCode }));
      routeLabels.push(...structureRouteLabels(structure, { homeCode }).map((l) => ({ ...l, key: `${project.id}:${l.key}` })));
    }
  }
  return { points, arcs, routeLabels, polygonColors };
}
