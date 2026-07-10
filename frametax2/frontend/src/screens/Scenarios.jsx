import { useState } from "react";
import { getStructures, postScenario } from "../api";
import { useBackend } from "../hooks";
import { Loading, ErrorBox, Money, Pct } from "../components/Status";

const CASE_ORDER = ["conservative", "base", "optimistic", "risk_adjusted"];

const SCENARIO_KINDS = [
  "move_vfx", "move_post", "move_music", "move_sound",
  "move_payroll", "move_marine", "create_spv", "create_coproduction",
];

function CandidateCard({ c }) {
  return (
    <div className="card">
      <h3>{c.label} <span className="muted small">({c.candidate_id})</span></h3>
      <p className="muted small">
        Jurisdictions: {c.participating_jurisdictions.join(", ")} · Priceable: <Pct value={c.priceable_pct} /> ·
        Fully priced: {String(c.is_fully_priced)}
      </p>
      {Object.keys(c.cases).length > 0 ? (
        <table>
          <thead><tr><th>Case</th><th>Net Production Cost</th><th>Incentive</th><th>Finance cost</th></tr></thead>
          <tbody>
            {CASE_ORDER.filter((k) => c.cases[k]).map((k) => (
              <tr key={k}>
                <td>{k}</td>
                <td><Money value={c.cases[k].net_production_cost_usd} /></td>
                <td><Money value={c.cases[k].incentive_usd} /></td>
                <td><Money value={c.cases[k].finance_cost_usd} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">Unpriced — no qualification register available for this jurisdiction set.</p>
      )}
      {c.constraints.length > 0 && (
        <p className="muted small">{c.constraints.length} open constraint(s).</p>
      )}
    </div>
  );
}

export default function Scenarios() {
  const { data, error, loading } = useBackend(getStructures, []);
  const [kind, setKind] = useState(SCENARIO_KINDS[0]);
  const [target, setTarget] = useState("FR");
  const [scenarioResult, setScenarioResult] = useState(null);
  const [scenarioError, setScenarioError] = useState(null);
  const [running, setRunning] = useState(false);

  const runScenario = async () => {
    setRunning(true);
    setScenarioError(null);
    try {
      const result = await postScenario(kind, target);
      setScenarioResult(result);
    } catch (err) {
      setScenarioError(err.message);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  return (
    <section>
      <h1>Scenarios &amp; Structures</h1>

      <h2>Ranked structures</h2>
      <table>
        <thead><tr><th>#</th><th>Label</th><th>Priceable</th><th>Risk-Adjusted NPC</th></tr></thead>
        <tbody>
          {data.ranking.map((r) => (
            <tr key={r.structure_id}>
              <td>{r.rank}</td>
              <td>{r.label}</td>
              <td>{String(r.is_priceable)}</td>
              <td><Money value={r.risk_adjusted_npc_usd} /></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Composed candidates ({data.candidates.length})</h2>
      <div className="cards">
        {data.candidates.map((c) => <CandidateCard key={c.candidate_id} c={c} />)}
      </div>

      <h2>Run a scenario</h2>
      <p className="muted small">Reuses production_scenario_engine.run_scenario() directly — no client-side calculation.</p>
      <div className="scenario-form">
        <select value={kind} onChange={(e) => setKind(e.target.value)}>
          {SCENARIO_KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="target jurisdiction (e.g. FR)" />
        <button onClick={runScenario} disabled={running}>{running ? "Running…" : "Run scenario"}</button>
      </div>
      {scenarioError && <ErrorBox message={scenarioError} />}
      {scenarioResult && (
        <table className="kv">
          <tbody>
            <tr><th>Scenario</th><td>{scenarioResult.kind}</td></tr>
            <tr><th>Baseline candidate</th><td>{scenarioResult.baseline_candidate_id || "—"}</td></tr>
            <tr><th>Scenario candidate</th><td>{scenarioResult.scenario_candidate_id || "—"}</td></tr>
            <tr><th>Baseline Risk-Adjusted NPC</th><td><Money value={scenarioResult.baseline_risk_adjusted_npc_usd} /></td></tr>
            <tr><th>Scenario Risk-Adjusted NPC</th><td><Money value={scenarioResult.scenario_risk_adjusted_npc_usd} /></td></tr>
            <tr><th>Delta (savings if positive)</th><td><Money value={scenarioResult.delta_usd} /></td></tr>
            <tr><th>Notes</th><td>{scenarioResult.notes || "—"}</td></tr>
          </tbody>
        </table>
      )}
      {scenarioResult && scenarioResult.relevant_structuring_opportunities.length > 0 && (
        <>
          <h3>Relevant structuring opportunities</h3>
          <ul>
            {scenarioResult.relevant_structuring_opportunities.map((o) => (
              <li key={o.opportunity_id}>{o.description} ({o.subtype})</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
