import { NavLink, useLocation, useNavigate } from "react-router-dom";
import Globe3D from "../components/Globe3D";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";

// Approved CineGlobe sidebar (migrated from the frozen design reference):
// warm-graphite panel, serif wordmark, identity-globe boundary, then
// COMPANY / PRODUCTIONS / SYSTEM sections. Replaces the previous
// PrimaryRail + SecondaryNav pair; all navigation still goes through the
// real react-router routes those components used.
const COMPANY_NAV = [
  { to: "/company/today", label: "Today" },
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
  const { meta } = useProjectStatus(productionId);
  const onProduction = location.pathname.startsWith("/production");

  return (
    <nav className="cg-sidebar" aria-label="Application navigation">
      <div className="cg-wordmark serif">Cine<i>Globe</i></div>

      {/* Identity globe — reuses the real Globe3D component as a stable
          boundary; final identity-preset art direction is the next phase. */}
      <div className="cg-identity-globe" aria-hidden="true">
        <Globe3D points={[]} arcs={[]} height={76} />
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

      <div className="cg-group">System</div>
      <NavLink
        to="/production/settings"
        className={({ isActive }) => `cg-navlink cg-navlink-co ${isActive ? "on" : ""}`}
      >
        Settings
      </NavLink>

      <div className="cg-foot">
        <span className="cg-avatar">SG</span>
        <span className="cg-foot-text">
          <b>Suraj Gohill</b>
          <span>Executive Producer</span>
        </span>
      </div>
    </nav>
  );
}
