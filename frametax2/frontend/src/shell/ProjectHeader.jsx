import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";
import { getTheme, toggleTheme } from "../lib/theme";
import ProductionHero from "../components/ProductionHero";

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

export default function ProjectHeader() {
  const navigate = useNavigate();
  // PHASE: Production Shell closeout. The cinematic hero is the production
  // identity header for every production route, not an Overview-specific
  // treatment — one ProductionHero instance, one shared `.project-tabs`
  // nav below it, rendered identically regardless of which production
  // route is active. The former per-route compact `.project-header` bar
  // has been retired; its markup/CSS classes are left in shell.css
  // unused rather than deleted, since removing CSS carries its own
  // regression risk and no other component references them.
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

  // Recommended Structure (hero only) — the SAME rank-1 resolution
  // Overview.jsx's own `structure`/`snapshot` derivation uses
  // (allocated.ranking, rank === 1), read here without importing Overview's
  // internals so this component has no dependency on a screen file.
  const allocated = data?.structures?.allocated_structures;
  const topRank = allocated?.ranking?.find((r) => r.rank === 1);
  const topStructure = topRank
    ? allocated?.structures?.find((s) => s.structure_id === topRank.structure_id)
    : null;

  // Shared stage control — identical markup/behavior in both the hero and
  // the compact bar, so the lifecycle dropdown is provably the same
  // component either way, not a second implementation.
  const stageControl = (
    <div className="ph-stage">
      <span className="ph-stage-label">Production stage</span>
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
  );

  // Header action icons — IDENTICAL markup/handlers to the compact bar's
  // `.ph-hactions` (upload document, AI analyst placeholder, theme toggle).
  // Extracted so the hero can't silently drop this functionality — it did,
  // in an earlier pass of this batch, caught by runtime verification before
  // completion, not by inspection.
  const headerActions = (
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
  );

  return (
    <header className="project-header-wrap">
      <ProductionHero
        production={production}
        topStructure={topStructure}
        stageControl={stageControl}
        openQuestions={openQuestions}
        swing={swing}
        onBack={() => navigate("/company/today")}
        headerActions={headerActions}
      />
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
