import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";
import { Money } from "../lib/format";
import { getTheme, toggleTheme } from "../lib/theme";

// Approved project header (migrated from the frozen design reference):
// back affordance, artwork, production identity with the lifecycle
// selector beneath it, dominant Production Budget group, question count.
// No fixed location in the subtitle — the leading jurisdiction is an
// optimizer outcome shown by the Workspace leading rail, not a permanent
// production identity field.
// Production sections — the approved artifact tab set (SECTIONS in
// reference/artifacts/prototype-v1-updated.html). Settings is a SYSTEM
// destination in the sidebar, not a production section.
const PRODUCTION_TABS = [
  { to: "/production/overview", label: "Overview" },
  { to: "/production/workspace", label: "Workspace" },
  { to: "/production/scenarios", label: "Scenarios" },
  { to: "/production/globe", label: "Project Globe" },
  { to: "/production/binder", label: "Documents" },
  { to: "/production/record", label: "Record" },
  { to: "/production/knowledge", label: "Knowledge" },
  { to: "/production/reports", label: "Reports" },
];

const JUR_NAMES = { MU: "Mauritius", ES: "Spain", GB: "United Kingdom", US: "United States", IE: "Ireland", MT: "Malta", FJ: "Fiji", GR: "Greece" };

export default function ProjectHeader() {
  const navigate = useNavigate();
  const { data } = useCineGlobe();
  // Local mirror of the theme purely so the button's icon and aria-pressed
  // re-render. The authoritative state is the `data-theme` attribute on
  // <html> (see lib/theme.js) — deliberately NOT React state, so a theme
  // switch cannot remount the Globe's WebGL context.
  const [theme, setThemeState] = useState(getTheme);

  const production = data?.production;
  const productionId = production?.production_id;
  const { status, setStatus, statuses, meta } = useProjectStatus(productionId);

  const openGrey = data?.legal?.grey_areas_current?.filter((g) => g.status === "open") || [];
  const openQuestions = (data?.pkg?.missing_inputs?.length || 0) + openGrey.length;
  const swing = openGrey.reduce((s, g) => s + (g.amount_usd || 0), 0);
  const jur = production?.jurisdiction_code ? (JUR_NAMES[production.jurisdiction_code] || production.jurisdiction_code) : null;

  return (
    <header className="project-header-wrap">
      <div className="project-header">
        <button className="ph-back" onClick={() => navigate("/company/today")}>← Today</button>
        <div className="ph-art" aria-hidden="true" />
        <div className="ph-identity">
          <h1 className="serif ph-title">{production?.production_name || "—"}</h1>
          {/* Identity facts only — the package-confidence grade was stale
              workflow status here; it lives in the working surfaces, not
              the production's identity line. */}
          <p className="ph-sub">Feature{jur ? ` · ${jur}` : ""}</p>
          <div className="ph-stage">
            <span className="ph-stage-label">Production stage</span>
            {/* Frozen-artifact stage control (.stage-dd): a details/summary
                dropdown with a styled menu — same live setStatus wiring the
                native select carried, one canonical lifecycle store. */}
            <details className="ph-stage-dd" title={meta.description}>
              <summary className="ph-stage-val" aria-label="Production stage">
                {meta.label} <span className="car">▾</span>
              </summary>
              <div className="ph-stage-menu">
                {statuses.map((s) => (
                  <button
                    key={s.key}
                    className={s.key === status ? "on" : ""}
                    onClick={(e) => { setStatus(s.key); e.currentTarget.closest("details").removeAttribute("open"); }}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </details>
          </div>
        </div>
        <div className="ph-budget">
          <span className="ph-budget-value mono">
            {production ? <Money value={production.gross_budget_usd} /> : "—"}
          </span>
          <span className="ph-budget-label">production budget</span>
        </div>
        {data && (
          <button className="ph-qcount" onClick={() => navigate("/production/workspace")}>
            <i />{openQuestions} question{openQuestions === 1 ? "" : "s"} open{swing ? ` · ±$${Math.round(swing).toLocaleString()}` : ""}
          </button>
        )}
        <div className="ph-hactions">
          <button className="ph-ico" title="Upload document" onClick={() => navigate("/production/binder")}>⇪</button>
          <button className="ph-ico ghosted" title="AI analyst — engine pending" disabled>◈</button>
          <button
            className="ph-ico"
            title={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
            aria-label={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
            aria-pressed={theme === "night"}
            onClick={() => setThemeState(toggleTheme())}
          >
            {theme === "night" ? "☾" : "◐"}
          </button>
        </div>
      </div>
      <nav className="project-tabs" aria-label="Production sections">
        {PRODUCTION_TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} className={({ isActive }) => (isActive ? "on" : "")}>
            {tab.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
