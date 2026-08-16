import { NavLink } from "react-router-dom";
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
          <CompactSidebarGlobe size={80} />
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
