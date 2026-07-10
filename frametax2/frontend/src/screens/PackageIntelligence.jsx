import { getPackage } from "../api";
import { useBackend } from "../hooks";
import { Loading, ErrorBox, Money } from "../components/Status";

export default function PackageIntelligence() {
  const { data, error, loading } = useBackend(getPackage, []);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  return (
    <section>
      <h1>Package Intelligence</h1>
      <p className="muted">
        Overall confidence: <strong>{data.confidence}</strong> — ready for downstream
        engines: <strong>{String(data.is_ready_for_downstream_engines)}</strong>
      </p>

      <h2>Budget Intelligence</h2>
      <table className="kv">
        <tbody>
          <tr><th>Known</th><td>{String(data.budget.known)}</td></tr>
          <tr><th>Line items</th><td>{data.budget.line_item_count}</td></tr>
          <tr><th>ATL total</th><td><Money value={data.budget.atl_total_usd} /></td></tr>
          <tr><th>BTL total</th><td><Money value={data.budget.btl_total_usd} /></td></tr>
          <tr><th>POST total</th><td><Money value={data.budget.post_total_usd} /></td></tr>
          <tr><th>Other total</th><td><Money value={data.budget.other_total_usd} /></td></tr>
          <tr><th>Labor spend</th><td><Money value={data.budget.labor_usd} /></td></tr>
        </tbody>
      </table>

      <h3>Spend by category</h3>
      <table>
        <thead><tr><th>Category</th><th>Amount</th></tr></thead>
        <tbody>
          {Object.entries(data.budget.totals_by_spend_category_usd).map(([cat, amt]) => (
            <tr key={cat}><td>{cat}</td><td><Money value={amt} /></td></tr>
          ))}
        </tbody>
      </table>

      <h3>Opportunity hints ({data.budget.opportunity_hints.length})</h3>
      <ul>
        {data.budget.opportunity_hints.map((h) => (
          <li key={h.hint_id}><strong>{h.category}:</strong> {h.description}</li>
        ))}
      </ul>

      <h2>Script Intelligence</h2>
      <p>Known: <strong>{String(data.script.known)}</strong>
        {!data.script.known && " — no screenplay on file for this production."}
      </p>
      {data.script.known && (
        <>
          <p>Locations mentioned: {data.script.locations_mentioned.join(", ") || "none"}</p>
        </>
      )}

      <h2>Missing Inputs (Question Engine) — {data.missing_inputs.length}</h2>
      <table>
        <thead>
          <tr><th>Blocking</th><th>Question</th><th>Why it matters</th><th>Downstream engines</th></tr>
        </thead>
        <tbody>
          {data.missing_inputs.map((m) => (
            <tr key={m.identifier} className={m.blocking ? "blocking" : ""}>
              <td>{m.blocking ? "YES" : "no"}</td>
              <td>{m.question}</td>
              <td>{m.why_it_matters}</td>
              <td>{m.downstream_engines.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
