import { useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import { useProjectStatus } from "../../lib/useProjectStatus";

export default function Settings() {
  const { projectId } = useParams();
  const { data, error, loading } = useCineGlobe(projectId);
  const { status, setStatus, statuses } = useProjectStatus(data?.production?.production_id, {
    projectId: data?.production?.project_id,
    backendLifecycle: data?.production?.lifecycle,
  });
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;
  const { production } = data;

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Settings</p>
        <h1 className="screen-title">Production configuration</h1>
      </header>

      <section className="region">
        <div className="region-title">Production identity</div>
        <dl className="kv-list">
          <div><dt>Production ID</dt><dd className="mono">{production.production_id}</dd></div>
          <div><dt>Baseline jurisdiction</dt><dd>{production.jurisdiction_code}</dd></div>
          <div><dt>Gross budget</dt><dd><Money value={production.gross_budget_usd} /></dd></div>
          <div><dt>Incentive rate</dt><dd className="mono">{production.rate != null ? `${(production.rate * 100).toFixed(0)}%` : "—"}</dd></div>
        </dl>
      </section>

      <section className="region">
        <div className="region-title">Company workflow status</div>
        <p className="text-tertiary small" style={{ marginBottom: 12 }}>
          Where this production stands in the company's own process — separate from any optimizer or calculation
          state. Stored locally in this browser (no backend field exists yet for this status).
        </p>
        <div className="tag-row">
          {statuses.map((s) => (
            <button
              key={s.key}
              className={`tag ${status === s.key ? "active" : ""}`}
              onClick={() => setStatus(s.key)}
              title={s.description}
            >
              <span className={`dot ${s.tier}`} /> {s.label}
            </button>
          ))}
        </div>
      </section>

      <section className="region">
        <div className="region-title">Not yet available</div>
        <div className="row-list">
          {["Team & permissions", "Connector configuration", "Notification preferences", "Export destinations"].map((s) => (
            <div className="row-item" key={s}>
              <span className="dot charcoal" />
              <div className="row-main"><div className="row-title text-tertiary">{s}</div></div>
              <span className="ghost-action small">Configure</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
