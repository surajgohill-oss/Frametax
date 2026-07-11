import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";

export default function Settings() {
  const { data, error, loading } = useCineGlobe();
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
          <div><dt>Incentive rate</dt><dd className="mono">{(production.rate * 100).toFixed(0)}%</dd></div>
        </dl>
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
