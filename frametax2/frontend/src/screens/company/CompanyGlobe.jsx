import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentOrganization, getProjects, getProjectState } from "../../api";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { JURISDICTION_COORDS } from "../../lib/jurisdictions";
import { activeStructure, buildSelectedStructureRoute } from "../../lib/globeData";
import { participantsOf, principalOf } from "../../lib/globeStructure";
import { isActiveProject, libraryStageKey } from "../../lib/libraryStatus";
import { PROJECT_STATUSES } from "../../lib/useProjectStatus";
import { Money, jurisdictionName } from "../../lib/format";

// COMPANY GLOBE (2026-10-08): every ALL ACTIVE project (Evaluation and later; Submitted and Archived excluded, the same
// predicate the Project Library uses), each drawn from its own persisted leading structure (Project.leading_structure_id,
// else the optimizer's rank #1 exactly as the Project Globe resolves it) with the proven topology: principal marker,
// every participant, relocation / hybrid / co-production routes. Colour is the established project-STAGE tier
// (PROJECT_STATUSES.tier -> the same CSS tokens the Library's stage dot uses), not the Project Globe's jurisdiction status.
// Read-only: it fetches /state for served projects only (a current generation already exists) and never evaluates.
const TIER_TOKEN = { blue: "--blue", silver: "--silver", gold: "--gold", jade: "--jade", charcoal: "--charcoal" };
const stageHex = (stageKey) => {
  const tier = PROJECT_STATUSES.find((s) => s.key === stageKey)?.tier || "blue";
  const css = getComputedStyle(document.documentElement).getPropertyValue(TIER_TOKEN[tier]).trim();
  return css || "#8c96a4";
};

async function loadActiveProjects() {
  const org = await getCurrentOrganization();
  const active = (await getProjects(org?.id)).filter(isActiveProject);
  return Promise.all(active.map(async (p) => {
    const state = await getProjectState(p.id);
    const allocated = state?.structures?.allocated_structures;
    const leadingId = state?.production?.leading_structure_id || p.leading_structure_id || null;
    const structure = activeStructure(allocated, leadingId);
    // No saved leading structure and no canonical selection: show the production's baseline jurisdiction only.
    const principal = structure ? principalOf(structure) : state?.production?.jurisdiction_code;
    return { project: p, production: state?.production, allocated, structure, principal };
  }));
}

export default function CompanyGlobe() {
  const navigate = useNavigate();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [focusedId, setFocusedId] = useState(null);

  // Fresh read on every mount, so a leading structure saved elsewhere replaces its prior route/territory state here.
  useEffect(() => {
    let alive = true;
    loadActiveProjects().then((r) => alive && setRows(r)).catch((e) => alive && setError(e.message || String(e)));
    return () => { alive = false; };
  }, []);

  const scene = useMemo(() => {
    const points = [];
    const arcs = [];
    const routeLabels = [];
    for (const { project, allocated, structure, principal } of rows || []) {
      const hex = stageHex(libraryStageKey(project));
      const codes = structure ? participantsOf(structure) : [principal];
      for (const code of new Set([principal, ...codes].filter(Boolean))) {
        const coord = JURISDICTION_COORDS[code] || JURISDICTION_COORDS[String(code).split("-")[0]];
        if (!coord) continue;
        points.push({
          lat: coord.lat, lng: coord.lng, tier: libraryStageKey(project), color: hex,
          name: project.title, id: `${project.id}:${code}`, projectId: project.id, code, principal: code === principal,
        });
      }
      const route = buildSelectedStructureRoute(allocated, structure);
      arcs.push(...route.arcs.map((a) => ({ ...a, color: [hex, hex] })));
      routeLabels.push(...route.labels.map((l) => ({ ...l, key: `${project.id}:${l.key}` })));
    }
    return { points, arcs, routeLabels };
  }, [rows]);

  if (error) return <div className="screen"><ErrorBox message={error} /></div>;
  if (!rows) return <div className="screen"><Loading /></div>;

  const focused = rows.find((r) => r.project.id === focusedId) || null;
  const openProject = (id) => navigate(`/projects/${id}/overview`);

  return (
    <div className="globe-screen">
      <div className="globe-screen-context">
        <p className="screen-eyebrow">Company Globe</p>
        <h1 className="serif" style={{ fontSize: 20 }}>Portfolio</h1>
        <p className="text-tertiary small">
          {rows.length} active {rows.length === 1 ? "project" : "projects"}, each at its leading structure. Hover a marker for a
          preview, click to focus, click again (or Open) to enter the production.
        </p>
        {rows.map(({ project, structure, principal }) => (
          <div key={project.id} className={`portfolio-chip ${focusedId === project.id ? "active" : ""}`} onClick={() => setFocusedId(project.id)}>
            <span className="dot" style={{ background: stageHex(libraryStageKey(project)) }} />
            <div>
              <div className="row-title">{project.title}</div>
              <div className="row-sub">
                {PROJECT_STATUSES.find((s) => s.key === libraryStageKey(project))?.label}
                {principal ? ` · ${jurisdictionName(principal)}${structure ? "" : " (baseline)"}` : ""}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="globe-screen-canvas">
        <Globe3D
          points={scene.points}
          arcs={scene.arcs}
          routeLabels={scene.routeLabels}
          height={560}
          // .globe-screen-inspector is 320px wide, absolutely positioned over the right edge of this canvas.
          obscuredRightPx={focused ? 320 : 0}
          onPointHover={(pt) => setPreview(pt)}
          onPointClick={(pt) => {
            if (pt?.projectId && pt.projectId === focusedId) openProject(pt.projectId);
            else if (pt?.projectId) setFocusedId(pt.projectId);
          }}
        />
        {preview && (
          <div className="globe-tooltip">
            <strong>{preview.name}</strong>
            <div className="text-tertiary small">{jurisdictionName(preview.code)}{preview.principal ? " · principal" : ""}</div>
            <div className="text-tertiary small">Click to focus · click again to open</div>
          </div>
        )}
      </div>

      {focused && (
        <div className="globe-screen-inspector">
          <p className="inspector-eyebrow">Production preview</p>
          <h3>{focused.project.title}</h3>
          <dl className="kv-list">
            <div><dt>Stage</dt><dd>{PROJECT_STATUSES.find((s) => s.key === libraryStageKey(focused.project))?.label}</dd></div>
            <div><dt>{focused.structure ? "Principal jurisdiction" : "Baseline jurisdiction"}</dt><dd>{jurisdictionName(focused.principal)}</dd></div>
            {focused.structure && <div><dt>Participants</dt><dd>{participantsOf(focused.structure).map(jurisdictionName).join(", ")}</dd></div>}
            <div><dt>Gross budget</dt><dd><Money value={focused.production?.gross_budget_usd ?? focused.project.total_budget_usd} /></dd></div>
          </dl>
          <button className="primary-action" onClick={() => openProject(focused.project.id)}>Open production →</button>
        </div>
      )}
    </div>
  );
}
