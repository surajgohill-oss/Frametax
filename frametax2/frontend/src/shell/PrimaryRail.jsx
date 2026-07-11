import { useLocation, useNavigate } from "react-router-dom";
import { Building2, Clapperboard } from "lucide-react";

const LEVELS = [
  { key: "company", to: "/company/today", label: "Company", icon: Building2 },
  { key: "production", to: "/production/overview", label: "The Little Utopia", icon: Clapperboard, mark: true },
];

export default function PrimaryRail() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeLevel = location.pathname.startsWith("/production") ? "production" : "company";

  return (
    <nav className="primary-rail" aria-label="Application level">
      {LEVELS.map((level) => {
        const Icon = level.icon;
        const isActive = activeLevel === level.key;
        return (
          <button
            key={level.key}
            className={`rail-item ${level.mark ? "production-mark" : ""} ${isActive ? "active" : ""}`}
            onClick={() => navigate(level.to)}
            title={level.label}
            aria-label={level.label}
          >
            {level.mark && isActive ? (
              <span className="rail-badge"><Icon size={14} strokeWidth={2} /></span>
            ) : (
              <Icon size={19} strokeWidth={1.6} />
            )}
          </button>
        );
      })}
    </nav>
  );
}
