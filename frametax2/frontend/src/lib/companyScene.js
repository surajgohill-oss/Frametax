// Company Globe scene: ONE pure function from the resolved portfolio rows to the Globe's markers, routes, labels, territory
// fills/boundaries and the stage legend. Colour is the project's PRODUCTION STAGE (stageOf(project) -> {key,label,hex}); the side
// list, legend and Globe all consume the same `rows`, so they cannot disagree.
// A project's contribution is derived only from its own row, so replacing its leader replaces its geography outright.
import { JURISDICTION_COORDS } from "./jurisdictions.js";
import { globeKey } from "./globeKey.js";
import { participantsOf, structureArcs, structureRouteLabels } from "./globeStructure.js";
import { readIncentivePotential } from "./incentivePotential.js";

const channels = (hex) => { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const mixHex = (a, b, t) => {
  const [ar, ag, ab] = channels(a); const [br, bg, bb] = channels(b);
  const m = (x, y) => Math.round(x + (y - x) * t).toString(16).padStart(2, "0");
  return `#${m(ar, br)}${m(ag, bg)}${m(ab, bb)}`;
};

const LAND = "#5d7a7e"; // inactive graphite land (GRAPHITE_HEX)

// rows: [{ project:{id,title}, structure, principal, homeCode }]; focusedId optional.
const DEFAULT_STAGE = () => ({ key: "evaluation", label: "Evaluation", hex: "#6FA0D6" });
export function buildCompanyScene(rows, { stageOf = DEFAULT_STAGE, focusedId = null } = {}) {
  const points = [];
  const arcs = [];
  const routeLabels = [];
  const polygonColors = new Map();
  const polygonBorders = new Map();
  const stageCounts = new Map();
  const colors = new Map(); // project id -> stage entry (the same entry the side list uses)
  // Territories: a principal always wins a shared country over a participant; otherwise the first project keeps it.
  const claimed = new Map(); // key -> { principal, projectId }
  for (const { project, structure, principal, homeCode } of rows || []) {
    const stage = stageOf(project);
    const { hex } = stage;
    colors.set(String(project.id), stage);
    stageCounts.set(stage.key, (stageCounts.get(stage.key) || 0) + 1);
    const focused = focusedId === project.id;
    const codes = [...new Set([principal, ...(structure ? participantsOf(structure) : [])].filter(Boolean))];
    for (const code of codes) {
      const key = globeKey(code);
      const isPrincipal = code === principal;
      const prev = claimed.get(key);
      if (!prev || (isPrincipal && !prev.principal)) {
        claimed.set(key, { principal: isPrincipal, projectId: project.id });
        // Secondary participants sit a step toward the land colour so the principal reads as the anchor.
        polygonColors.set(key, isPrincipal ? hex : mixHex(hex, LAND, 0.28));
        polygonBorders.set(key, mixHex(hex, "#ffffff", isPrincipal ? 0.72 : focused ? 0.62 : 0.45)); // same stage token, lightened
      }
      const coord = JURISDICTION_COORDS[code] || JURISDICTION_COORDS[String(code).split("-")[0]];
      if (!coord) continue;
      points.push({
        lat: coord.lat, lng: coord.lng, tier: "company", color: hex,
        name: project.title, id: `${project.id}:${code}`, iso: key, projectId: project.id, code, principal: isPrincipal,
        pot: readIncentivePotential(structure),
      });
    }
    if (structure) {
      arcs.push(...structureArcs(structure, { color: hex, homeCode }));
      routeLabels.push(...structureRouteLabels(structure, { homeCode }).map((l) => ({ ...l, key: `${project.id}:${l.key}`, color: hex })));
    }
  }
  return { points, arcs, routeLabels, polygonColors, polygonBorders, stageCounts, colors };
}

// The decorative 80px sidebar globe does not plot projects. On company routes it receives only a faint aggregate accent: the stage
// colour of the most common active stage (same token as the Company Globe), plus the active-project count for accessibility.
export function buildPortfolioAccent(rows, stageOf = DEFAULT_STAGE) {
  if (!rows || !rows.length) return null;
  const counts = new Map();
  for (const { project } of rows) {
    const st = stageOf(project);
    const e = counts.get(st.key) || { hex: st.hex, n: 0 };
    e.n += 1;
    counts.set(st.key, e);
  }
  const [key, top] = [...counts.entries()].sort((a, b) => b[1].n - a[1].n || a[0].localeCompare(b[0]))[0];
  return { key: `portfolio|${key}|${top.hex}|${rows.length}`, portfolio: true, projects: rows.length, accent: top.hex };
}
