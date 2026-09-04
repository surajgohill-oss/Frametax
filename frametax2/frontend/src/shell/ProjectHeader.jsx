import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";
import { getTheme, toggleTheme } from "../lib/theme";
import { activeStructure } from "../lib/globeData";
import { useAppState } from "../state/AppState";
import ProductionHero from "../components/ProductionHero";

// Production sections — the approved artifact tab set (SECTIONS in
// reference/artifacts/prototype-v1-updated.html). Settings is a SYSTEM
// destination in the sidebar, not a production section. Mature UI
// restoration: every tab is now project_id-scoped (was a fixed legacy
// production path reachable by only one production) — same tab set,
// same order, same labels, just parameterized.
function productionTabs(projectId) {
  const base = `/projects/${projectId}`;
  return [
    { to: `${base}/overview`, label: "Overview" },
    { to: `${base}/workspace`, label: "Workspace" },
    { to: `${base}/scenarios`, label: "Scenarios" },
    { to: `${base}/globe`, label: "Project Globe" },
    { to: `${base}/binder`, label: "Documents" },
    { to: `${base}/record`, label: "Record" },
    { to: `${base}/knowledge`, label: "Knowledge" },
    { to: `${base}/reports`, label: "Reports" },
  ];
}

export default function ProjectHeader() {
  const navigate = useNavigate();
  // ProjectHeader is rendered by AppShell as a SIBLING of the routed page
  // (AppShell wraps <Routes>, ProjectHeader is not inside any <Route
  // element>), so useParams() has no route context here and always
  // returns {} — confirmed live (every tab href rendered
  // "/projects/undefined/..."). Extracted from the URL directly instead,
  // the same technique AppShell's own MATURE_PROJECT_ROUTE test already
  // uses for exactly this reason.
  const { pathname } = useLocation();
  const projectId = pathname.match(/^\/projects\/([^/]+)\//)?.[1];
  // PHASE: Production Shell closeout. The cinematic hero is the production
  // identity header for every production route, not an Overview-specific
  // treatment — one ProductionHero instance, one shared `.project-tabs`
  // nav below it, rendered identically regardless of which production
  // route is active. The former per-route compact `.project-header` bar
  // has been retired; its markup/CSS classes are left in shell.css
  // unused rather than deleted, since removing CSS carries its own
  // regression risk and no other component references them.
  const { data } = useCineGlobe(projectId);
  // Local mirror of the theme purely so the button's icon and aria-pressed
  // re-render. The authoritative state is the `data-theme` attribute on
  // <html> (see lib/theme.js) — deliberately NOT React state, so a theme
  // switch cannot remount the Globe's WebGL context.
  const [theme, setThemeState] = useState(getTheme);

  const production = data?.production;
  const productionId = production?.production_id;
  const { status, setStatus, statuses, meta } = useProjectStatus(productionId, {
    projectId: production?.project_id,
    backendLifecycle: production?.lifecycle,
  });

  // ROOT CAUSE (traced live, not assumed): `.ph-hero` is `overflow: hidden`
  // — required for the Hero art/scrim treatment, frozen, never touched —
  // which clips ANY descendant that visually extends past the Hero's
  // 242px box, regardless of the descendant's own position:absolute/fixed.
  // The stage dropdown's native <details>/<summary> menu lived inside the
  // Hero and needed ~270px, so it opened correctly (verified: `open`
  // attribute set, state/persistence all fine) but was invisible — clipped
  // by the Hero, not broken logic. Fixed by portaling the menu to
  // document.body with position:fixed computed from the trigger's own
  // on-screen rect, which escapes the Hero's clip entirely. Nothing about
  // the Hero itself changes.
  const [stageOpen, setStageOpen] = useState(false);
  const [stageMenuPos, setStageMenuPos] = useState({ top: 0, left: 0 });
  const stageTriggerRef = useRef(null);

  useEffect(() => {
    if (!stageOpen) return;
    function handleOutside(e) {
      if (stageTriggerRef.current?.contains(e.target)) return;
      if (e.target.closest?.(".ph-stage-menu")) return;
      setStageOpen(false);
    }
    function handleKey(e) {
      if (e.key === "Escape") setStageOpen(false);
    }
    document.addEventListener("mousedown", handleOutside);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleOutside);
      document.removeEventListener("keydown", handleKey);
    };
  }, [stageOpen]);

  function toggleStageMenu() {
    if (!stageOpen && stageTriggerRef.current) {
      const r = stageTriggerRef.current.getBoundingClientRect();
      setStageMenuPos({ top: r.bottom + 6, left: r.left });
    }
    setStageOpen((v) => !v);
  }

  const openGrey = data?.legal?.grey_areas_current?.filter((g) => g.status === "open") || [];
  const openQuestions = (data?.pkg?.missing_inputs?.length || 0) + openGrey.length;
  const swing = openGrey.reduce((s, g) => s + (g.amount_usd || 0), 0);

  // Recommended Structure (hero) — the SAME shared selection every other
  // screen uses (lib/globeData.js::activeStructure): the producer's own
  // explicitly selected/leading structure (AppState.leadingStructureId,
  // written by Scenarios.jsx's Scenario Manager and persisted to the
  // project's leading_structure_id) when one is set, else the optimizer's
  // own rank #1 — never rank #1 unconditionally. This is the SAME helper
  // Overview.jsx/Workspace.jsx/ProjectGlobe.jsx already call, so the hero
  // can never disagree with the scenario cards about which structure is
  // "the" leading one (Task 4, canonical pricing path + discovery repair).
  const { leadingStructureId } = useAppState();
  const allocated = data?.structures?.allocated_structures;
  const topStructure = activeStructure(allocated, leadingStructureId);
  // Workspace/Overview Truthfulness — "Set as leading" is a PRODUCER
  // SELECTION, never CineGlobe's own ranked recommendation (Section 12).
  // activeStructure() intentionally prioritizes the manual leadingStructureId
  // for every OTHER consumer (Globe view, BudgetRail's active structure,
  // Workspace's anchor lane — all correctly want "whichever structure the
  // producer is currently focused on"), so that behavior stays unchanged
  // here too. But the Hero's "Recommended Structure" label specifically
  // must be reserved for a GENUINE canonical recommendation — the same
  // rank-#1 pick activeStructure(allocated, null) resolves when no manual
  // override is in play. If the producer manually leads a structure that
  // is not that genuine rank-#1 pick, the Hero must say so as a manual
  // selection, never imply CineGlobe endorsed it.
  const canonicalTop = activeStructure(allocated, null);
  const isGenuineRecommendation = !!(
    topStructure && canonicalTop && topStructure.structure_id === canonicalTop.structure_id
  );
  // Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 1:
  // the Hero no longer renders any recommendation/best-priced fallback
  // (see ProductionHero.jsx's own header comment), so bestPricedCandidate
  // is no longer computed here. Overview's own BudgetRail already calls
  // bestPricedCandidate directly for its own fallback (see
  // production-overview-truthfulness.test.mjs) — this was never a second,
  // independently-maintained copy of that logic.

  // Shared stage control. The menu itself is portaled to document.body
  // (see the effect above) so it always escapes the Hero's overflow clip,
  // regardless of which route/context renders this control.
  const stageControl = (
    <div className="ph-stage">
      <span className="ph-stage-label">Production stage</span>
      <div className="ph-stage-dd" title={meta.description}>
        <button
          type="button"
          ref={stageTriggerRef}
          className="ph-stage-val"
          aria-label="Production stage"
          aria-haspopup="listbox"
          aria-expanded={stageOpen}
          onClick={toggleStageMenu}
        >
          {meta.label} <span className="car">▾</span>
        </button>
        {stageOpen && createPortal(
          <div className="ph-stage-menu" role="listbox" style={{ position: "fixed", top: stageMenuPos.top, left: stageMenuPos.left }}>
            {statuses.map((s) => (
              <button
                key={s.key}
                role="option"
                aria-selected={s.key === status}
                className={s.key === status ? "on" : ""}
                onClick={() => { setStatus(s.key); setStageOpen(false); }}
              >
                {s.label}
              </button>
            ))}
          </div>,
          document.body,
        )}
      </div>
    </div>
  );

  // Header action icons — IDENTICAL markup/handlers to the compact bar's
  // `.ph-hactions` (upload document, AI analyst placeholder, theme toggle).
  // Extracted so the hero can't silently drop this functionality — it did,
  // in an earlier pass of this batch, caught by runtime verification before
  // completion, not by inspection.
  const headerActions = (
    <div className="ph-hactions">
      <button className="ph-ico" title="Upload document" onClick={() => navigate(`/projects/${projectId}/binder`)}>⇪</button>
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
      {/* Consolidated UI/ingestion/permission closeout (2026-09-03),
          Batch 1: the Hero is budget-only now (see ProductionHero.jsx's
          own header comment) — topStructure/isGenuineRecommendation/
          bestPriced are still computed above (other consumers read
          `allocated`/`topStructure`'s underlying activeStructure() call,
          and a regression test pins ProjectHeader's own
          isGenuineRecommendation derivation), but no longer passed into
          the Hero. */}
      <ProductionHero
        production={production}
        stageControl={stageControl}
        openQuestions={openQuestions}
        swing={swing}
        onBack={() => navigate("/company/today")}
        headerActions={headerActions}
      />
      <nav className="project-tabs" aria-label="Production sections">
        {productionTabs(projectId).map((tab) => (
          <NavLink key={tab.to} to={tab.to} className={({ isActive }) => (isActive ? "on" : "")}>
            {tab.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
