import { useCallback, useEffect, useState } from "react";
import { Money } from "../lib/format";
import { getContingencyDeployments, postContingencyDeployments } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import { RetainedSaveNote } from "./EvaluationStatus";

// Producer-stated deployment of the contingency reserve into real destination categories (planning input; never rewrites the budget gross or the reserve). Unknown is kept distinct from
// stated: until the producer states a plan the state is NOT_STATED, and "Clear" returns to it. Save writes the one project fact then runs the real evaluation; Cancel discards only the draft.
// The destination category is read from the budget by the server; this control only picks the account and the amount.
function readableError(err) {
  const raw = String(err?.message || err);
  const json = raw.slice(raw.indexOf("{"));
  try {
    const detail = JSON.parse(json).detail;
    if (Array.isArray(detail?.errors)) return detail.errors.join("; ");
    if (typeof detail === "string") return detail;
    if (detail?.message) return detail.message;
  } catch { /* fall through */ }
  return raw;
}

const toDraft = (plan) => Object.fromEntries((plan?.accounts || []).map((a) => [a.account_code, a.deployments.map((d) => ({ account: d.destination_account_code, amount: String(d.amount_usd) }))]));

export default function ContingencyDeployments({ projectId, onSaved, evaluateOnSave = true }) {
  const run = useEvaluationRun(projectId);
  const [plan, setPlan] = useState(null);
  const [draft, setDraft] = useState({});
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);

  const load = useCallback(async () => {
    try {
      const next = await getContingencyDeployments(projectId);
      setPlan(next);
      setDraft(toDraft(next));
      setError(null);
    } catch (err) {
      setError(readableError(err));
    }
  }, [projectId]);

  useEffect(() => { if (projectId) load(); }, [projectId, load]);

  if (!projectId || !plan || plan.accounts.length === 0) return error ? <p className="text-tertiary small" data-contingency-deployments="error">{error}</p> : null;

  const reserveOf = (code) => plan.accounts.find((a) => a.account_code === code)?.reserve_usd || 0;
  const totalOf = (code) => (draft[code] || []).reduce((sum, row) => sum + (Number(row.amount) || 0), 0);
  const rowsValid = (code) => (draft[code] || []).every((row) => row.account && Number.isFinite(Number(row.amount)) && Number(row.amount) > 0);
  const overReserve = plan.accounts.some((a) => totalOf(a.account_code) > a.reserve_usd + 0.005);
  const valid = plan.accounts.every((a) => rowsValid(a.account_code)) && !overReserve;
  const dirty = JSON.stringify(draft) !== JSON.stringify(toDraft(plan));

  const setRow = (code, index, patch) => setDraft((d) => ({ ...d, [code]: d[code].map((row, i) => (i === index ? { ...row, ...patch } : row)) }));
  const addRow = (code) => setDraft((d) => ({ ...d, [code]: [...(d[code] || []), { account: plan.destinations[0]?.account_code || "", amount: "" }] }));
  const removeRow = (code, index) => setDraft((d) => ({ ...d, [code]: d[code].filter((_, i) => i !== index) }));

  async function submit(payload) {
    if (busy || run.running) return;
    setBusy(true);
    setError(null);
    try {
      const next = await postContingencyDeployments(projectId, payload);
      setPlan(next);
      setDraft(toDraft(next));
      if (evaluateOnSave) await runEvaluation(projectId);
      else setSavedNotEvaluated(true);
      onSaved?.();
      await load();
    } catch (err) {
      setError(readableError(err));
    } finally {
      setBusy(false);
    }
  }

  const save = () => {
    const payload = {};
    for (const a of plan.accounts) {
      const rows = (draft[a.account_code] || []).map((row) => ({ destination_account_code: row.account, amount_usd: Number(row.amount) }));
      if (rows.length) payload[a.account_code] = rows;
    }
    return submit(Object.keys(payload).length ? payload : null);
  };

  const locked = busy || run.running;
  return (
    <div className="brail-block" data-contingency-deployments={plan.state}>
      <div className="brail-header brail-static brail-contingency-row">
        <span style={{ width: 13 }} />
        <button type="button" className="ghost-action" aria-expanded={open} onClick={() => setOpen((v) => !v)} data-contingency-deployments-toggle>
          {plan.state === "STATED" ? "Reserve deployment (stated)" : "Deploy reserve into a category (not stated)"}
        </button>
      </div>
      {open && (
        <div style={{ padding: "4px 0 8px 18px" }}>
          <p className="text-tertiary small" style={{ margin: "0 0 6px" }}>
            A deployment prices the destination account's own jurisdiction rules (qualifying spend); it never changes the budget, the reserve or the planned cost, which the Use % above sets.
            Not stated means no reserve is assumed spent in any category.
          </p>
          {plan.accounts.map((a) => (
            <div key={a.account_code} data-deployment-account={a.account_code}>
              <div className="row-sub">{a.description} · reserve <Money value={a.reserve_usd} bare /> · deployed <Money value={totalOf(a.account_code)} bare /> · undeployed <Money value={Math.max(0, a.reserve_usd - totalOf(a.account_code))} bare /></div>
              {(draft[a.account_code] || []).map((row, i) => (
                <div key={i} style={{ display: "flex", gap: 6, margin: "4px 0" }} data-deployment-row>
                  <select className="brail-contingency-select" value={row.account} disabled={locked} onChange={(e) => setRow(a.account_code, i, { account: e.target.value })} aria-label="Destination account">
                    {plan.destinations.map((d) => <option key={d.account_code} value={d.account_code}>{d.account_code} · {d.description} ({d.spend_category})</option>)}
                  </select>
                  <input type="number" min="0" step="1" value={row.amount} disabled={locked} onChange={(e) => setRow(a.account_code, i, { amount: e.target.value })} aria-label="Amount (USD)" style={{ width: 110 }} />
                  <button type="button" className="ghost-action" disabled={locked} onClick={() => removeRow(a.account_code, i)}>Remove</button>
                </div>
              ))}
              <button type="button" className="ghost-action" disabled={locked || plan.destinations.length === 0} onClick={() => addRow(a.account_code)} data-add-deployment>+ Add deployment</button>
              {totalOf(a.account_code) > reserveOf(a.account_code) + 0.005 && <p className="text-secondary small" role="alert">Deployments exceed the {reserveOf(a.account_code).toLocaleString()} reserve.</p>}
            </div>
          ))}
          <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
            <button type="button" className="hero-action primary" disabled={locked || !dirty || !valid} onClick={save} data-save-deployments>{locked ? "Saving…" : "Save"}</button>
            <button type="button" className="ghost-action" disabled={locked || !dirty} onClick={() => setDraft(toDraft(plan))} data-cancel-deployments>Cancel</button>
            <button type="button" className="ghost-action" disabled={locked || plan.state !== "STATED"} onClick={() => submit(null)} data-clear-deployments>Clear (not stated)</button>
          </div>
        </div>
      )}
      {savedNotEvaluated && <RetainedSaveNote />}
      {error && <p className="text-secondary small" role="alert" data-contingency-deployments-error>{error}</p>}
    </div>
  );
}
