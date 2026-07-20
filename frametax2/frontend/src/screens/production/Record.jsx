import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import { buildRecordRows } from "../../lib/recordEvents";

export default function Record() {
  const { data, error, loading } = useCineGlobe();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const rows = buildRecordRows(data);

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
