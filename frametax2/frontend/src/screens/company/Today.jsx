import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, recommendationHeadline } from "../../lib/format";
import { useProjectStatus } from "../../lib/useProjectStatus";
import { buildRecordRows } from "../../lib/recordEvents";
import { UPLOAD_BLOCKED_REASON } from "../../lib/ingestion";

// Today — the company operations home (approved artifact: topbar hero +
// two-column board — decision queue / blocked / watching on the left,
// production portfolio + recent activity on the right). This is NOT an
// incentive-tracking dashboard: every tile answers a portfolio-operations
// question (what's active, what needs me, what changed), never a
// marketing metric. The backend currently serves exactly one real
// production (little_utopia_state.py) — every section below is written
// generically over a `productions` array so a second production requires
// no changes here, but nothing is padded or fabricated to look larger
// than the real portfolio.

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

const NEW_PRODUCTION_REASON = "Production intake — engine pending";

export default function Today() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  const { meta: statusMeta, statuses } = useProjectStatus(data?.production?.production_id);
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

  // ── The production portfolio, as a generic array. Length is 1 today
  // (the only production this backend serves) — every row/stat below
  // reads from this array, never a hardcoded single-production literal,
  // so the portfolio genuinely scales when a second production exists. ──
  const productions = [
    {
      id: production.production_id,
      name: production.production_name,
      stageMeta: statusMeta,
      openCount,
      budget: production.gross_budget_usd,
      npc: best?.conservative_npc_usd,
      route: "/production/overview",
    },
  ];
  const needingAction = productions.filter((p) => p.openCount > 0);
  const stageCounts = statuses.map((s) => ({
    ...s,
    count: productions.filter((p) => p.stageMeta.key === s.key).length,
  }));

  const activity = buildRecordRows(data);

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
        <div className="tdx-stat">
          <div className="l">Portfolio budget</div>
          <div className="v"><Money value={productions.reduce((s, p) => s + (p.budget || 0), 0)} /></div>
        </div>
        {swingTotal > 0 && (
          <button className="tdx-alert" onClick={goWorkspace}><i />In-kind FMV ruling awaited</button>
        )}
        <button
          className="tdx-btn p tdx-newprod"
          disabled
          title={NEW_PRODUCTION_REASON}
        >
          ＋ New Production
        </button>
        <button className="tdx-ico" disabled title="Global search is not wired to a backend index yet">⌕</button>
      </header>

      {/* Lifecycle stage strip — every canonical stage (useProjectStatus's
          own PROJECT_STATUSES, the same taxonomy the header/sidebar stage
          selector uses), counted across the real productions array. With
          one production this shows 1 in whichever stage it's actually in
          and 0 elsewhere — an honest single-production portfolio view,
          not a padded fake one. */}
      <div className="tdx-stages">
        {stageCounts.map((s) => (
          <span key={s.key} className={`tdx-stage-chip ${s.count ? "" : "zero"}`} title={s.description}>
            <span className={`dot ${s.tier}`} />{s.label} <b>{s.count}</b>
          </span>
        ))}
      </div>

      {/* Quick actions — real navigations to existing pages, or the same
          honest disabled affordances already established elsewhere
          (Binder.jsx's Upload budget/script, the sidebar's New Production)
          — never a new upload/create flow invented here. */}
      <div className="tdx-qact">
        <button className="hero-action primary" disabled title={NEW_PRODUCTION_REASON}>＋ New Production</button>
        <button className="hero-action" onClick={goWorkspace}>Continue Production</button>
        <button className="hero-action" disabled title={UPLOAD_BLOCKED_REASON}>Upload Budget</button>
        <button className="hero-action" disabled title={UPLOAD_BLOCKED_REASON}>Upload Script</button>
        <button className="hero-action" onClick={() => navigate("/production/reports")}>Generate Report</button>
      </div>

      <main className="tdx-board">
        {/* Column 1 — operational attention */}
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
                <div className="acts2">
                  <button className="tdx-btn p" onClick={goWorkspace}>Review</button>
                  <button className="tdx-btn g" onClick={goWorkspace}>Open →</button>
                </div>
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

        {/* Column 2 — production portfolio + recent activity */}
        <div>
          <div className="tdx-sec-h">
            <h2>Productions needing action</h2><span className="n">{needingAction.length} of {productions.length}</span>
            <button className="all" disabled title={NEW_PRODUCTION_REASON}>＋ New production</button>
          </div>
          <div className="tdx-flat">
            {productions.map((p) => (
              <div className="tdx-prow" key={p.id} onClick={() => navigate(p.route)}>
                <div className="tdx-art" />
                <span className="nm2">{p.name}</span>
                <span className="ph2">{p.stageMeta.label}</span>
                {p.openCount > 0 ? (
                  <span className="need2">{p.openCount} question{p.openCount === 1 ? "" : "s"} open</span>
                ) : (
                  <span className="need2 calm">No action needed</span>
                )}
                <span className="bud2"><Money value={p.budget} /> budget</span>
                <span className="cost2">{p.npc != null ? <Money value={p.npc} /> : "—"}</span>
              </div>
            ))}
          </div>

          <div className="tdx-sec-h" style={{ marginTop: 26 }}><h2>Since your last visit</h2><span className="n">{activity.length}</span></div>
          <div className="tdx-flat">
            {activity.length ? activity.map((a, i) => (
              <div className="tdx-fi" key={i}>
                <span className="tdx-tm">{a.date}</span>
                <span className="tdx-ic">{a.value != null ? "✓" : "▤"}</span>
                <span className="tdx-tx">
                  <b>{a.event}</b> — <span className="tdx-obj" onClick={() => navigate("/production/record")}>{a.detail}</span>
                  {a.value != null && <span className="mono" style={{ marginLeft: 6, color: "var(--jade)" }}><Money value={a.value} /></span>}
                </span>
              </div>
            )) : <div className="tdx-empty">Nothing recorded yet.</div>}
            <button className="link-more" onClick={() => navigate("/production/record")}>Full record →</button>
          </div>
        </div>
      </main>
    </div>
  );
}
