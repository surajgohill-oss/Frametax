import { getProduction } from "../api";
import { useBackend } from "../hooks";
import { Loading, ErrorBox, Money, Pct } from "../components/Status";

export default function Production() {
  const { data, error, loading } = useBackend(getProduction, []);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  return (
    <section>
      <h1>{data.production_name}</h1>
      <p className="muted">The single canonical production this CineGlobe instance serves.</p>
      <table className="kv">
        <tbody>
          <tr><th>Production ID</th><td>{data.production_id}</td></tr>
          <tr><th>Baseline jurisdiction</th><td>{data.jurisdiction_code}</td></tr>
          <tr><th>Gross budget</th><td><Money value={data.gross_budget_usd} /></td></tr>
          <tr><th>Incentive rate</th><td><Pct value={data.rate} /></td></tr>
          <tr><th>As of</th><td>{data.as_of_date}</td></tr>
        </tbody>
      </table>
    </section>
  );
}
