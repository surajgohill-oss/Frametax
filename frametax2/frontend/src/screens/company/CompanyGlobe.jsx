import { useEffect, useMemo, useState } from "react";

import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { buildCompanyScene } from "../../lib/companyScene";
import { portfolioRows } from "../../lib/portfolioRows";
import { participantsOf } from "../../lib/globeStructure";
import { activeStages, stageOf } from "../../lib/companyStage";
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
          preview, click it to enter the production.
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
                {stageLabel(project)}{stageOf(project).check ? " ✓" : ""}
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
            if (pt?.projectId) openProject(pt.projectId);
          }}
        />
        {/* Chrome-free, exactly like the Project Globe legend (.globe-legend-vertical): dots and labels over the stage, no plate. */}
        <div className="globe-legend-vertical company-stage-legend" role="note" aria-label="Production stage key">
          <span className="glv-heading">Production stage</span>
          {activeStages().map((st) => (
            <span key={st.key} className="glv-item" data-legend-stage={st.key} style={scene.stageCounts.get(st.key) ? undefined : { opacity: 0.85 }}>
              <span className="glv-dot" style={{ background: st.hex }} aria-hidden="true" />
              {st.label}{st.check && <span className="glv-check" aria-hidden="true">✓</span>}
              {scene.stageCounts.get(st.key) ? <span className="glv-count">{scene.stageCounts.get(st.key)}</span> : null}
            </span>
          ))}
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
            <div className="text-tertiary small">Click to open</div>
          </div>
        )}
      </div>

      {focused && (
        <div className="globe-screen-inspector">
          <button className="inspector-close" onClick={() => setFocusedId(null)} aria-label="Close preview">
            <X size={16} />
          </button>
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
