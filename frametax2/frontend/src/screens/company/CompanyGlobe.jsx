import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { buildCompanyScene } from "../../lib/companyScene";
import { portfolioRows } from "../../lib/portfolioRows";
import { participantsOf } from "../../lib/globeStructure";
import { ACTIVE_STAGES, stageOf } from "../../lib/companyStage";
import { getLeadingSelection, getPortfolio, loadPortfolio, usePortfolio, useLeadingSelectionsVersion } from "../../lib/leadingSelection";
import { Money, jurisdictionName } from "../../lib/format";

// COMPANY GLOBE (2026-10-08): every ALL ACTIVE project (Evaluation and later; Submitted and Archived excluded, the same
// predicate the Project Library uses), each drawn from its own persisted leading structure (Project.leading_structure_id,
// else the optimizer's rank #1 exactly as the Project Globe resolves it) with the proven topology: principal marker,
// every participant, relocation / hybrid / co-production routes. Colour is the project's PRODUCTION STAGE (PROJECT_STATUSES
// tiers via lib/companyStage.js: evaluation blue, development silver, production gold, completed jade); the stage is also written text.
// ONE request (GET /cineglobe/portfolio/globe, shared with the sidebar mini-globe through lib/leadingSelection.js) feeds the
// side list and the Globe from the same atomic payload; there is no per-project /state fan-out and it never evaluates.
// The structure each project shows is read from the shared leading selection (the producer's saved choice, else the
// canonical leader, else baseline only when no evaluated structure exists), so a "Set as Leading" anywhere replaces that
// one project's markers, routes and Inspector at once.
const stageLabel = (project) => stageOf(project).label;

export default function CompanyGlobe() {
  const navigate = useNavigate();
  const portfolio = usePortfolio();
  const leadingVersion = useLeadingSelectionsVersion();
  // leadingVersion is the store's change signal: portfolioRows() reads the store, so it must re-run on every change.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const rows = useMemo(() => (portfolio ? portfolioRows(portfolio, getLeadingSelection) : null), [portfolio, leadingVersion]);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [focusedId, setFocusedId] = useState(null);

  // Revalidates on every mount (the cached portfolio, if any, renders at once), so a leading structure saved elsewhere
  // replaces its prior route/territory state here.
  useEffect(() => {
    let alive = true;
    loadPortfolio({ force: !!getPortfolio() }).catch((e) => alive && setError(e.message || String(e)));
    return () => { alive = false; };
  }, []);

  const scene = useMemo(() => buildCompanyScene(rows, { stageOf, focusedId }), [rows, focusedId]);

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
          <div
            key={project.id}
            className={`portfolio-chip ${focusedId === project.id ? "active" : ""}`}
            style={focusedId === project.id ? { borderColor: stageOf(project).hex, boxShadow: `inset 3px 0 0 ${stageOf(project).hex}` } : undefined}
            onClick={() => setFocusedId(project.id)}
          >
            <span className="dot" data-project-color={stageOf(project).hex} style={{ background: stageOf(project).hex }} />
            <div>
              <div className="row-title">{project.title}</div>
              <div className="row-sub">
                {stageLabel(project)}
                {principal ? ` · ${jurisdictionName(principal)}${structure ? "" : " (baseline)"}` : ""}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="globe-screen-canvas">
        <Globe3D
          points={scene.points}
          polygonColors={scene.polygonColors}
          polygonBorders={scene.polygonBorders}
          pointRadius={(d) => (d.principal ? 0.7 : 0.45)}
          arcs={scene.arcs}
          routeLabels={scene.routeLabels}
          height={560}
          autoHeight
          // .globe-screen-inspector is 320px wide, absolutely positioned over the right edge of this canvas.
          obscuredRightPx={focused ? 320 : 0}
          onPointHover={(pt) => setPreview(pt)}
          onPointClick={(pt) => {
            if (pt?.projectId && pt.projectId === focusedId) openProject(pt.projectId);
            else if (pt?.projectId) setFocusedId(pt.projectId);
          }}
        />
        <div className="company-legend" role="list" aria-label="Production stage">
          <div className="company-legend-head">Production stage</div>
          {ACTIVE_STAGES.map((st) => (
            <div key={st.key} role="listitem" className={`company-legend-row${scene.stageCounts.get(st.key) ? "" : " empty"}`} data-legend-stage={st.key}>
              <span className="company-legend-swatch" style={{ background: st.hex }} />
              <span className="company-legend-title">{st.label}</span>
              <span className="company-legend-stage">{scene.stageCounts.get(st.key) || ""}</span>
            </div>
          ))}
          <div className="company-legend-key">White edge, large marker: principal · muted fill: participant</div>
        </div>
        {preview && (
          <div className="globe-tooltip">
            <strong>{preview.name}</strong>
            <div className="text-tertiary small">{jurisdictionName(preview.code)}{preview.principal ? " · principal" : ""}</div>
            {preview.pot && (
              <div className="text-tertiary small">
                Max-potential NPC <Money value={preview.pot.potentialNpc} /> · Confirmed NPC <Money value={preview.pot.confirmedNpc} />
              </div>
            )}
            <div className="text-tertiary small">Click to focus · click again to open</div>
          </div>
        )}
      </div>

      {focused && (
        <div className="globe-screen-inspector">
          <p className="inspector-eyebrow">Production preview</p>
          <h3>{focused.project.title}</h3>
          <dl className="kv-list">
            <div><dt>Stage</dt><dd>{stageLabel(focused.project)}</dd></div>
            <div><dt>{focused.structure ? "Principal jurisdiction" : "Baseline jurisdiction"}</dt><dd>{jurisdictionName(focused.principal)}</dd></div>
            {focused.structure && <div><dt>Participants</dt><dd>{participantsOf(focused.structure).map(jurisdictionName).join(", ")}</dd></div>}
            {focused.selectionKnown && <div><dt>Leading</dt><dd>{focused.unavailable ? "Your selection is no longer available — canonical leader shown" : focused.userSelected ? "Your selection" : focused.structure ? "Canonical leader" : "No evaluated structure"}</dd></div>}
            <div><dt>Gross budget</dt><dd><Money value={focused.grossBudgetUsd} /></dd></div>
          </dl>
          <button className="primary-action" onClick={() => openProject(focused.project.id)}>Open production →</button>
        </div>
      )}
    </div>
  );
}
