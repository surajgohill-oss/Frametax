import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import CompactSidebarGlobe from "../components/CompactSidebarGlobe";
import ErrorBoundary from "./ErrorBoundary";
import { getProjects } from "../api";
import { PROJECT_STATUSES } from "../lib/useProjectStatus";

const STATUS_BY_KEY = Object.fromEntries(PROJECT_STATUSES.map((s) => [s.key, s]));
function statusMetaForLifecycle(lifecycle) {
  const key = (lifecycle || "evaluation").toLowerCase();
  return STATUS_BY_KEY[key] || PROJECT_STATUSES[0];
}

// Approved CineGlobe sidebar (migrated from the frozen design reference):
// warm-graphite panel, serif wordmark, identity-globe boundary, then
// COMPANY / PRODUCTIONS / SYSTEM sections. Replaces the previous
// PrimaryRail + SecondaryNav pair; all navigation still goes through the
// real react-router routes those components used.
const COMPANY_NAV = [
  { to: "/company/today", label: "Today" },
  { to: "/company/library", label: "Project Library" },
  { to: "/company/globe", label: "Company Globe" },
  { to: "/company/knowledge", label: "Company Knowledge" },
  { to: "/company/reports", label: "Organization Reports" },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [productions, setProductions] = useState([]);

  // Productions row: every real Project (existing Company Library source,
  // getProjects() -- no second registry) that has actually entered the
  // mature evaluated flow. leading_structure_id is set by
  // canonical_evaluation.py once a top structure exists, so it's the
  // existing signal that distinguishes an active production (Little
  // Utopia, FVD) from the ~50 untouched Project Library intake records
  // that have never been evaluated.
  useEffect(() => {
    let cancelled = false;
    getProjects()
      .then((projects) => {
        if (cancelled) return;
        setProductions(projects.filter((p) => p.leading_structure_id));
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

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

      <div className="cg-group">Productions</div>
      {productions.map((p) => {
        const meta = statusMetaForLifecycle(p.lifecycle);
        const active = location.pathname.startsWith(`/projects/${p.id}/`) && !location.pathname.endsWith("/summary");
        return (
          <button
            key={p.id}
            className={`cg-navlink cg-prodrow ${active ? "on" : ""}`}
            onClick={() => navigate(`/projects/${p.id}/overview`)}
          >
            <span className={`dot ${meta.tier}`} />
            <span className="cg-prodtext">
              <span className="cg-pname">{p.title}</span>
              <span className="cg-stage">{meta.label}</span>
            </span>
          </button>
        );
      })}

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
