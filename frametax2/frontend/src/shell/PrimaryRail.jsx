import { useLocation, useNavigate } from "react-router-dom";

const LEVELS = [
  { key: "company", to: "/company/today", label: "Company" },
  { key: "production", to: "/production/overview", label: "Little Utopia" },
];

export default function PrimaryRail() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeLevel = location.pathname.startsWith("/production") ? "production" : "company";

  return (
    <nav className="primary-rail" aria-label="Application level">
      {LEVELS.map((level) => (
        <button
          key={level.key}
          className={`rail-item ${activeLevel === level.key ? "active" : ""}`}
          onClick={() => navigate(level.to)}
          title={level.label}
          aria-label={level.label}
        >
          {level.key === "company" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <rect x="4" y="3" width="16" height="18" rx="1" stroke="currentColor" strokeWidth="1.3" />
              <path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
            </svg>
          ) : (
            <span className="rail-badge">LU</span>
          )}
        </button>
      ))}
    </nav>
  );
}
