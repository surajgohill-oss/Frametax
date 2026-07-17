import { NavLink, useNavigate } from "react-router-dom";
import { useCineGlobe } from "../lib/useCineGlobe";
import { useProjectStatus } from "../lib/useProjectStatus";
import { Money } from "../lib/format";

// Approved project header (migrated from the frozen design reference):
// back affordance, artwork, production identity with the lifecycle
// selector beneath it, dominant Production Budget group, question count.
// No fixed location in the subtitle — the leading jurisdiction is an
// optimizer outcome shown by the Workspace leading rail, not a permanent
// production identity field.
const PRODUCTION_TABS = [
  { to: "/production/overview", label: "Overview" },
  { to: "/production/workspace", label: "Workspace" },
  { to: "/production/binder", label: "Documents" },
  { to: "/production/knowledge", label: "Knowledge" },
  { to: "/production/record", label: "Record" },
  { to: "/production/settings", label: "Settings" },
];

export default function ProjectHeader() {
  const navigate = useNavigate();
  const { data } = useCineGlobe();

  const production = data?.production;
  const productionId = production?.production_id;
  const { status, setStatus, statuses, meta } = useProjectStatus(productionId);

  const openQuestions =
    (data?.pkg?.missing_inputs?.length || 0) +
    (data?.legal?.grey_areas_current?.filter((g) => g.status === "open").length || 0);

  return (
    <header className="project-header-wrap">
      <div className="project-header">
        <button className="ph-back" onClick={() => navigate("/company/today")}>← Today</button>
        <div className="ph-art" aria-hidden="true" />
        <div className="ph-identity">
          <h1 className="serif ph-title">{production?.production_name || "—"}</h1>
          <p className="ph-sub">Feature{data?.pkg?.confidence ? ` · ${data.pkg.confidence} confidence` : ""}</p>
          <div className="ph-stage">
            <span className="ph-stage-label">Production stage</span>
            <select
              className="ph-stage-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              title={meta.description}
              aria-label="Production stage"
            >
              {statuses.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="ph-budget">
          <span className="ph-budget-label">Production budget</span>
          <span className="ph-budget-value mono">
            {production ? <Money value={production.gross_budget_usd} /> : "—"}
          </span>
        </div>
        {data && (
          <button className="ph-qcount" onClick={() => navigate("/production/workspace")}>
            <i />{openQuestions} question{openQuestions === 1 ? "" : "s"} open
          </button>
        )}
      </div>
      <nav className="project-tabs" aria-label="Production sections">
        {PRODUCTION_TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} className={({ isActive }) => (isActive ? "on" : "")}>
            {tab.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
