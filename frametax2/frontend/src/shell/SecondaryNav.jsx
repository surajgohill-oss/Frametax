import { NavLink, useLocation } from "react-router-dom";
import { Clapperboard, Globe2, BookOpen, FileBarChart, LayoutDashboard, FolderOpen, History, Settings, Building2 } from "lucide-react";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";

const COMPANY_NAV = [
  { to: "/company/today", label: "Today", icon: LayoutDashboard },
  { to: "/company/globe", label: "Company Globe", icon: Globe2 },
  { to: "/company/knowledge", label: "Company Knowledge", icon: BookOpen },
  { to: "/company/reports", label: "Organization Reports", icon: FileBarChart },
];

const PRODUCTION_NAV = [
  { to: "/production/overview", label: "Overview", icon: Clapperboard },
  { to: "/production/workspace", label: "Workspace", icon: LayoutDashboard },
  { to: "/production/binder", label: "Production Binder", icon: FolderOpen },
  { to: "/production/knowledge", label: "Knowledge", icon: BookOpen },
  { to: "/production/record", label: "Record", icon: History },
  { to: "/production/settings", label: "Settings", icon: Settings },
];

export default function SecondaryNav() {
  const location = useLocation();
  const isProduction = location.pathname.startsWith("/production");
  const items = isProduction ? PRODUCTION_NAV : COMPANY_NAV;

  // Company workflow status (in_development / in_evaluation / in_production)
  // is production-scoped, frontend-local (see useProjectStatus.js) — shown
  // here read-only; Settings hosts the editable control.
  const { data } = useCineGlobe();
  const productionId = isProduction ? data?.production?.production_id : null;
  const { meta } = useProjectStatus(productionId);

  return (
    <nav className="secondary-nav" aria-label="Section navigation">
      <div className="secondary-nav-heading">
        <span className={`secondary-nav-mark ${isProduction ? "" : "company"}`}>
          {isProduction ? <Clapperboard size={15} strokeWidth={2} /> : <Building2 size={17} strokeWidth={1.6} />}
        </span>
        <div className="secondary-nav-text">
          <span className="secondary-nav-eyebrow">{isProduction ? "Production" : "Company"}</span>
          <span className="serif secondary-nav-title">{isProduction ? "The Little Utopia" : "CineGlobe"}</span>
        </div>
      </div>
      {productionId && (
        <span className={`badge ${meta.tier}`} style={{ margin: "-6px 0 12px" }} title={meta.description}>
          {meta.label}
        </span>
      )}
      <ul>
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.to}>
              <NavLink to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
                <Icon size={15} strokeWidth={1.7} />
                {item.label}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
