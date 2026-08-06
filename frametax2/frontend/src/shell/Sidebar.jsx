import { NavLink, useLocation, useNavigate } from "react-router-dom";
import CompactSidebarGlobe from "../components/CompactSidebarGlobe";
import ErrorBoundary from "./ErrorBoundary";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";

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
  const { data } = useCineGlobe();

  const production = data?.production;
  const productionId = production?.production_id;
  const { meta } = useProjectStatus(productionId, {
    projectId: production?.project_id,
    backendLifecycle: production?.lifecycle,
  });
  const onProduction = location.pathname.startsWith("/production");

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
      <button
        className={`cg-navlink cg-prodrow ${onProduction ? "on" : ""}`}
        onClick={() => navigate("/production/overview")}
      >
        <span className={`dot ${meta.tier}`} />
        <span className="cg-prodtext">
          <span className="cg-pname">{production?.production_name || "The Little Utopia"}</span>
          <span className="cg-stage">{meta.label}</span>
        </span>
      </button>

      {/* Frozen-artifact "＋ New production" affordance. No create-production
          backend exists yet (documents router only ingests files), so the
          control is presented ghosted per the artifact's own engine-pending
          convention rather than wired to an invented mutation. */}
      <button className="cg-navlink cg-newprod ghosted" title="Production intake — engine pending" disabled>
        ＋ New production
      </button>

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
