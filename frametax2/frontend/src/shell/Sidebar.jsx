import { useEffect, useMemo } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { getLeadingSelection, getPortfolio, loadPortfolio, useLeadingSelection, usePortfolio, useLeadingSelectionsVersion } from "../lib/leadingSelection";
import { buildPortfolioAccent } from "../lib/companyScene";
import { portfolioRows } from "../lib/portfolioRows";
import { stageOf } from "../lib/companyStage";
import { JURISDICTION_COORDS } from "../lib/jurisdictions";
import { miniGlobeOverlay } from "../lib/globeStructure";
import CompactSidebarGlobe from "../components/CompactSidebarGlobe";
import ErrorBoundary from "./ErrorBoundary";

// Approved CineGlobe sidebar (migrated from the frozen design reference):
// warm-graphite panel, serif wordmark, identity-globe boundary, then a
// COMPANY nav section. Replaces the previous PrimaryRail + SecondaryNav
// pair; all navigation still goes through the real react-router routes
// those components used.
//
// Overview UI contract: individual project/production rows were removed
// from here entirely -- this panel is company-level navigation, not a
// project selector. Project Library (already in COMPANY_NAV below) is the
// one project selector; every project reaches its own mature Overview by
// clicking its card there (see ProjectLibrary.jsx), not from this rail.
const COMPANY_NAV = [
  { to: "/company/today", label: "Today" },
  { to: "/company/library", label: "Project Library" },
  { to: "/company/globe", label: "Company Globe" },
  { to: "/company/knowledge", label: "Company Knowledge" },
  { to: "/company/reports", label: "Organization Reports" },
];

export default function Sidebar() {
  // On a project route the identity globe shows that project's leading structure (the shared selection every Globe
  // surface reads; no request of its own). Elsewhere, or with no evaluated structure, it stays the neutral emblem.
  const projectId = useLocation().pathname.match(/^\/projects\/([^/]+)/)?.[1] || null;
  const selection = useLeadingSelection(projectId);
  // Company-level routes (Company Globe and the rest of COMPANY nav) show the whole active portfolio from the SAME aggregate
  // payload; project routes keep the selected project's own structure.
  const companyLevel = !projectId;
  const portfolio = usePortfolio();
  const leadingVersion = useLeadingSelectionsVersion();
  // The one aggregate portfolio read (shared single-flight with Company Globe), once per session -- never a full /state.
  useEffect(() => {
    if (!getPortfolio()) loadPortfolio().catch(() => {});
  }, [projectId]);
  const overlay = useMemo(() => {
    if (companyLevel) return portfolio ? buildPortfolioAccent(portfolioRows(portfolio, getLeadingSelection), stageOf) : null;
    // Project routes: the same decorative Earth turned to the principal, with one quiet glow there (no topology).
    const mini = miniGlobeOverlay(selection?.structure, { homeCode: selection?.homeCode, ...(selection?.routeColor ? { color: selection.routeColor } : {}) });
    const principal = mini?.markers.find((m) => m.principal) || mini?.markers[0];
    if (principal) return { key: mini.key, principalCode: principal.code, focus: { lat: principal.lat, lng: principal.lng }, pulse: { lat: principal.lat, lng: principal.lng, color: principal.color } };
    // No explicit "Set as Leading": the project sits at its anchor (Current Location), the same rule Company Globe applies.
    const base = selection?.baselineCode ? (JURISDICTION_COORDS[selection.baselineCode] || JURISDICTION_COORDS[String(selection.baselineCode).split("-")[0]]) : null;
    return base ? { key: `anchor|${selection.baselineCode}`, principalCode: selection.baselineCode, focus: { lat: base.lat, lng: base.lng }, pulse: { lat: base.lat, lng: base.lng, color: "#ffffff" } } : null;
    // leadingVersion is the store's change signal for saved-leader commits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyLevel, portfolio, leadingVersion, selection]);
  return (
    <nav className="cg-sidebar" aria-label="Application navigation">
      <div className="cg-wordmark serif">Cine<i>Globe</i></div>

      {/* Identity mark — a fully decoupled, non-interactive compact globe
          (CompactSidebarGlobe), not the production Globe3D engine. Scoped in
          its own error boundary: this is a WebGL renderer mounted on every
          route, so a context/init failure must degrade to the CSS
          placeholder rather than blank the entire application shell. */}
      <div className="cg-identity-globe" aria-hidden="true">
        <ErrorBoundary label="sidebar-globe" fallback={null}>
          <CompactSidebarGlobe size={92} overlay={overlay} />
        </ErrorBoundary>
      </div>
      <div className="cg-tagline mono">The Production Atlas</div>

      <div className="cg-group">Company</div>
      {COMPANY_NAV.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => `cg-navlink cg-navlink-co ${isActive ? "on" : ""}`}
        >
          {item.label}
        </NavLink>
      ))}

      <div className="cg-group">System</div>
      <NavLink
        to="/production/settings"
        className={({ isActive }) => `cg-navlink cg-navlink-co ${isActive ? "on" : ""}`}
      >
        Settings
      </NavLink>
    </nav>
  );
}
