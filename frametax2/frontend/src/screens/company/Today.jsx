import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, recommendationHeadline } from "../../lib/format";
import { useProjectStatus } from "../../lib/useProjectStatus";

// Today — the approved artifact company dashboard: a sticky metric topbar
// over a two-column board (the decision queue on the left; productions and
// recent activity on the right). The artifact is a four-production demo;
// this backend serves one production (little_utopia_state.py), so the same
// layout is populated with the single real production and its live queue.
// Every value is read verbatim from useCineGlobe.

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export default function Today() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  const { meta: statusMeta } = useProjectStatus(data?.production?.production_id);
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { pkg, legal, recommendations, production, structures } = data;
  const openGrey = legal.grey_areas_current.filter((g) => g.status === "open");
  const blockingQuestions = pkg.missing_inputs.filter((m) => m.blocking);
  const watching = pkg.missing_inputs.filter((m) => !m.blocking);
  const decisions = recommendations.by_category.financial
    .filter((r) => r.estimated_value_usd)
    .sort((a, b) => (b.estimated_value_usd || 0) - (a.estimated_value_usd || 0))
    .slice(0, 3);

  const swingTotal = openGrey.reduce((s, g) => s + (g.amount_usd || 0), 0);
  const openCount = pkg.missing_inputs.length + openGrey.length;
  const blockingCount = blockingQuestions.length + openGrey.length;
  const best = (structures.ranking || []).find((r) => r.is_priceable);

  const now = new Date();
  const goWorkspace = () => navigate("/production/workspace");

  return (
    <div className="tdx-screen">
      <header className="tdx-topbar">
        <div className="tdx-today">
          <span>Today · {WEEKDAYS[now.getDay()]}</span>
          <b>{now.getDate()} {MONTHS[now.getMonth()]} {now.getFullYear()}</b>
        </div>
        <div className="tdx-stat">
          <div className="l">Decisions waiting on you</div>
          <div className="v gold">{openCount} <em>{swingTotal ? `±$${Math.round(swingTotal).toLocaleString()} at stake` : "in queue"}</em></div>
        </div>
        <div className="tdx-stat">
          <div className="l">Optimization in play</div>
          <div className="v">{swingTotal ? `$${Math.round(swingTotal).toLocaleString()}` : "—"}</div>
        </div>
        <div className="tdx-stat">
          <div className="l">Blocking rulings</div>
          <div className="v" style={{ color: blockingCount ? "var(--red)" : "var(--jade)" }}>
            {blockingCount}{blockingCount ? " " : ""}<em>{blockingCount ? "authority pending" : "none"}</em>
          </div>
        </div>
        {swingTotal > 0 && (
          <button className="tdx-alert" onClick={goWorkspace}><i />In-kind FMV ruling awaited</button>
        )}
      </header>

      <main className="tdx-board">
        {/* Column 1 — the decision queue */}
        <div>
          <div className="tdx-sec-h"><h2>Requires your decision</h2><span className="n">{decisions.length}</span></div>
          <div className="tdx-flat">
            {decisions.length ? decisions.map((r) => (
              <div className="tdx-trow" key={r.recommendation_id}>
                <span className="bar dec" />
                <div className="tt2">
                  <b><i>{production.production_name}</i> — {recommendationHeadline(r)}</b>
                  <div className="m2">{r.requires_counsel_approval ? "Counsel approval" : "Producer approval"} · <span className="mono" style={{ color: "var(--jade)" }}><Money value={r.estimated_value_usd} /></span> estimated value</div>
                </div>
                <div className="acts2"><button className="tdx-btn g" onClick={goWorkspace}>Open →</button></div>
              </div>
            )) : <div className="tdx-empty">No decisions pending — every priced structure is settled.</div>}
          </div>

          <div className="tdx-sec-h" style={{ marginTop: 26 }}><h2>Blocked</h2><span className="n">{blockingCount}</span></div>
          <div className="tdx-flat">
            {blockingCount ? (
              <>
                {openGrey.map((g) => (
                  <div className="tdx-trow" key={g.item_id}>
                    <span className="bar blk" />
                    <div className="tt2">
                      <b>{g.resolving_evidence}</b>
                      <div className="m2">{g.authority_to_ask} · <span className="mono">±<Money value={g.amount_usd} bare /></span> at stake · {g.jurisdiction_code}</div>
                    </div>
                    <div className="acts2"><button className="tdx-btn s" onClick={goWorkspace}>Open →</button></div>
                  </div>
                ))}
                {blockingQuestions.map((q) => (
                  <div className="tdx-trow" key={q.identifier}>
                    <span className="bar blk" />
                    <div className="tt2"><b>{q.question}</b><div className="m2">{q.why_it_matters}</div></div>
                    <div className="acts2"><button className="tdx-btn s" onClick={goWorkspace}>Open →</button></div>
                  </div>
                ))}
              </>
            ) : <div className="tdx-empty">Nothing is blocked right now.</div>}
          </div>

          <div className="tdx-sec-h" style={{ marginTop: 26 }}><h2>Watching — no action needed</h2><span className="n">{watching.length}</span></div>
          <div className="tdx-flat">
            {watching.length ? watching.map((q) => (
              <div className="tdx-trow" key={q.identifier}>
                <span className="bar wat" />
                <div className="tt2"><div className="m2"><b style={{ color: "var(--text-primary)" }}>{q.question}</b> · {q.optimizer_value} priority</div></div>
              </div>
            )) : <div className="tdx-empty">Nothing open to watch.</div>}
          </div>
        </div>

        {/* Column 2 — productions + activity */}
        <div>
          <div className="tdx-sec-h">
            <h2>Productions needing action</h2><span className="n">1</span>
            <button className="all" disabled title="POST /api/v1/projects exists but no screen reads the projects table yet — every screen is wired to the single cached Little Utopia state.">＋ New production</button>
          </div>
          <div className="tdx-flat">
            <div className="tdx-prow" onClick={() => navigate("/production/overview")}>
              <div className="tdx-art" />
              <span className="nm2">{production.production_name}</span>
              <span className="ph2">{statusMeta.label}</span>
              <span className="need2">{openCount} question{openCount === 1 ? "" : "s"} open</span>
              <span className="bud2"><Money value={production.gross_budget_usd} /> budget</span>
              <span className="cost2">{best ? <Money value={best.conservative_npc_usd} /> : "—"}</span>
            </div>
          </div>

          <div className="tdx-sec-h" style={{ marginTop: 26 }}><h2>Since your last visit</h2></div>
          <div className="tdx-flat">
            <div className="tdx-empty">
              Activity feed is served by the ingestion/event engine, which is not wired to this cached
              production state yet — the Record page carries the production's append-only history.
              <div style={{ marginTop: 8 }}>
                <button className="tdx-btn g" onClick={() => navigate("/production/record")}>Open Record →</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
