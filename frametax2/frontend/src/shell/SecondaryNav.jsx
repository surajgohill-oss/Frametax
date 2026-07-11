import { NavLink, useLocation } from "react-router-dom";

const COMPANY_NAV = [
  { to: "/company/today", label: "Today" },
  { to: "/company/globe", label: "Company Globe" },
  { to: "/company/knowledge", label: "Company Knowledge" },
  { to: "/company/reports", label: "Organization Reports" },
];

const PRODUCTION_NAV = [
  { to: "/production/overview", label: "Overview" },
  { to: "/production/workspace", label: "Workspace" },
  { to: "/production/binder", label: "Production Binder" },
  { to: "/production/knowledge", label: "Knowledge" },
  { to: "/production/record", label: "Record" },
  { to: "/production/settings", label: "Settings" },
];

export default function SecondaryNav() {
  const location = useLocation();
  const isProduction = location.pathname.startsWith("/production");
  const items = isProduction ? PRODUCTION_NAV : COMPANY_NAV;

  return (
    <nav className="secondary-nav" aria-label="Section navigation">
      <div className="secondary-nav-heading">
        {isProduction ? (
          <>
            <span className="secondary-nav-eyebrow">Production</span>
            <span className="serif secondary-nav-title">The Little Utopia</span>
          </>
        ) : (
          <>
            <span className="secondary-nav-eyebrow">Company</span>
            <span className="serif secondary-nav-title">CineGlobe</span>
          </>
        )}
      </div>
      <ul>
        {items.map((item) => (
          <li key={item.to}>
            <NavLink to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
