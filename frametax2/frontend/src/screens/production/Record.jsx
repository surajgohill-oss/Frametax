import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";

export default function Record() {
  const { data, error, loading } = useCineGlobe();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal, production } = data;
  const rows = [];
  rows.push({ date: production.as_of_date, event: "Baseline register established", detail: `${production.jurisdiction_code} qualification register` });
  for (const g of legal.grey_areas_current) {
    if (g.status !== "open") {
      rows.push({
        date: production.as_of_date,
        event: `${g.jurisdiction_code} authority decision received`,
        detail: `${g.resolving_evidence} — Authority Score ${legal.authority_scores[g.graph_rule_id]?.composite ?? "—"} (${legal.authority_scores[g.graph_rule_id]?.confidence ?? ""})`,
        value: g.amount_usd,
      });
    }
  }

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Record</p>
        <h1 className="screen-title">Versioned history</h1>
      </header>
      <div className="region">
        <table className="record-table">
          <thead>
            <tr><th>Date</th><th>Event</th><th>Detail</th><th>Value</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td className="mono small">{r.date}</td>
                <td>{r.event}</td>
                <td className="text-secondary small">{r.detail}</td>
                <td className="mono"><Money value={r.value} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-tertiary small" style={{ marginTop: 12 }}>
          No realized incentive / final tax credit has been recorded — this production has not been filed.
        </p>
      </div>
    </div>
  );
}
