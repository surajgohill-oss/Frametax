import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, CompactMoney } from "../../lib/format";
import { useProjectStatus } from "../../lib/useProjectStatus";
import { buildRecordRows } from "../../lib/recordEvents";
import { buildHeroStages, buildFxItems } from "../../lib/todayCompute";

// Today — the company operating system. Approved blueprint (frozen), page
// order fixed: State of the Studio (hero) -> FX strip -> Production Slate
// (one row per production, every operational fact attached to the
// production it belongs to, ordered by executive importance) -> Company
// Intelligence (compact, cross-production only, jurisdiction facts). No
// separate issue queue exists anywhere on this page — an issue is always
// an attribute of the production row it belongs to, never its own object.
//
// Built entirely from Overview's established visual language (.ovx-sec
// cards, .oh headers, .row-list/.row-item rows, .dot tiers, .ovx-stats
// .l2/.v2 typography) — no new dashboard aesthetic. The backend serves
// exactly one real production (little_utopia_state.py); every
// computation below runs generically over a `productions` array so nothing
// here needs to change when a second production exists, but nothing is
// padded to look busier than the real slate is today.
//
// Hero stage buckets and FX-item building are pure functions in
// lib/todayCompute.js (no React/DOM), independently regression-tested via
// plain `node scripts/test_today_compute.mjs` — this frontend has no test
// runner installed, and none is introduced here.

const NEW_PRODUCTION_REASON = "Production intake — engine pending";

// Momentum taxonomy, in the approved rank order (lower rank = more
// urgent, sorts first): Blocked, Stalled, Advanced, Milestone, Healthy.
// Reuses the app's existing 6-tier dot-color vocabulary — no new colors.
const MOMENTUM = {
  blocked: { key: "blocked", glyph: "⚠", label: "Blocked", tier: "red", rank: 0 },
  stalled: { key: "stalled", glyph: "▼", label: "Stalled", tier: "amber", rank: 1 },
  advanced: { key: "advanced", glyph: "▲", label: "Advanced", tier: "gold", rank: 2 },
  milestone: { key: "milestone", glyph: "✓", label: "Milestone", tier: "jade", rank: 3 },
  healthy: { key: "healthy", glyph: "●", label: "Healthy", tier: "silver", rank: 4 },
};

// A production's momentum is computed from real, already-served signals
// only — never a fabricated "days idle" figure the backend has no
// timestamp for. Categories are exclusive; the first match wins, in the
// approved rank order.
function classifyMomentum({ hasOpenBlocker, hasFreshActivity, hasResolvedItem, isSettled }) {
  if (hasOpenBlocker) return MOMENTUM.blocked;
  if (!hasFreshActivity && !isSettled && !hasResolvedItem) return MOMENTUM.stalled;
  if (hasFreshActivity) return MOMENTUM.advanced;
  if (hasResolvedItem) return MOMENTUM.milestone;
  return MOMENTUM.healthy;
}

export default function Today() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  const { meta: statusMeta, statuses } = useProjectStatus(data?.production?.production_id);
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal, recommendations, production, structures, economics } = data;
  const openGrey = legal.grey_areas_current.filter((g) => g.status === "open");
  const resolvedGrey = legal.grey_areas_current.filter((g) => g.status !== "open");
  const swingTotal = openGrey.reduce((s, g) => s + (g.amount_usd || 0), 0);

  // Canonical allocated_structures ranking — the SAME source Overview/
  // Workspace/Scenarios read. structures.ranking (top-level) is the
  // older, narrower STRUCT-* pair; deliberately not read here.
  const allocated = structures.allocated_structures;
  const structById = new Map((allocated?.structures || []).map((s) => [s.structure_id, s]));
  const bestRank = (allocated?.ranking || []).find((r) => r.rank === 1);
  const best = bestRank ? structById.get(bestRank.structure_id) : null;
  const topRec = recommendations.by_category.financial
    .filter((r) => r.estimated_value_usd)
    .sort((a, b) => (b.estimated_value_usd || 0) - (a.estimated_value_usd || 0))[0];
  const activity = buildRecordRows(data);

  // ── The production slate, as a genuinely generic array. Length is 1
  // today (the only production this backend serves) — every downstream
  // computation reads from this array, never a single-production literal. ──
  const momentum = classifyMomentum({
    hasOpenBlocker: openGrey.length > 0,
    hasFreshActivity: activity.length > 1,
    hasResolvedItem: resolvedGrey.length > 0,
    isSettled: !!best?.is_fully_priced,
  });
  const impactUsd = swingTotal || topRec?.estimated_value_usd || 0;
  const headline = openGrey.length
    ? `${openGrey[0].resolving_evidence} — ±$${Math.round(openGrey[0].amount_usd).toLocaleString()}`
    : topRec
      ? `${topRec.title} — $${Math.round(topRec.estimated_value_usd).toLocaleString()} estimated value`
      : "No action needed";
  const delta = activity.length > 1 ? activity[activity.length - 1].event : null;

  const productions = [
    {
      id: production.production_id,
      name: production.production_name,
      stageMeta: statusMeta,
      budget: production.gross_budget_usd,
      npc: best?.is_fully_priced ? best.npc_with_adjustments_usd : null,
      headline,
      delta,
      momentum,
      impactUsd,
      route: "/production/overview",
    },
  ];

  // ── Ordering: momentum rank first (Blocked -> Stalled -> Advanced ->
  // Milestone -> Healthy, the approved order), then financial impact
  // descending within a rank, then budget descending as a final tiebreak. ──
  const orderedProductions = [...productions].sort((a, b) =>
    a.momentum.rank - b.momentum.rank || b.impactUsd - a.impactUsd || b.budget - a.budget
  );

  // ── Hero: State of the Studio ──────────────────────────────────────
  const activeProductions = productions.filter((p) => p.stageMeta.key !== "archived");
  const totalActiveBudget = activeProductions.reduce((s, p) => s + (p.budget || 0), 0);
  const attentionCount = productions.filter((p) => p.momentum.rank <= 1).length; // Blocked or Stalled

  // Exactly Evaluation / Development / Production, in that fixed order —
  // no rollup groupings, no alternative labels. See lib/todayCompute.js.
  const heroStages = buildHeroStages(statuses, productions);

  // ── FX strip: EUR / CAD / GBP, sourced from economics.fx_horizons
  // (production_normalization.py's FX_RATE_SNAPSHOTS — a real, sourced
  // table; EUR/GBP have live snapshots, CAD has none anywhere in this
  // codebase — rendered as an honest unavailable state, never invented). ──
  const fxItems = buildFxItems(economics.fx_horizons);

  // ── Company Intelligence: compact, cross-production signals only —
  // never a production-level event (those belong on the slate row), and
  // FX no longer duplicated here now that it has its own strip. Sourced
  // from real, already-served jurisdiction data. ─────────────────────
  const intel = (production.rate_resolution?.unverified_claims || []).map((claim) => ({
    tier: "amber",
    label: `${production.jurisdiction_code} — unverified requirement`,
    text: claim.claim,
    detail: claim.verification_status,
  }));

  return (
    <div className="screen tdy-screen">
      {/* ── HERO — State of the Studio ─────────────────────────────── */}
      <section className="ovx-sec tdy-hero">
        <div className="oh">
          <b>State of the Studio</b>
        </div>

        <div className="tdy-hero-top">
          <div className="tdy-hn tdy-hn-primary">
            <span className="l2">Active Productions</span>
            <span className="v2 tdy-hn-xl">{activeProductions.length}</span>
          </div>
          <div className="tdy-hn">
            <span className="l2">Total Active Budget</span>
            <span className="v2 tdy-hn-big"><Money value={totalActiveBudget} /></span>
          </div>
          <div className={`tdy-attention ${attentionCount ? "hot" : "calm"}`}>
            {attentionCount} Production{attentionCount === 1 ? "" : "s"} {attentionCount === 1 ? "Requires" : "Require"} Immediate Attention
          </div>
        </div>

        <div className="tdy-pipeline">
          <div className="l2 tdy-pipeline-label">Production Summary</div>
          <div className="ovx-stats tdy-ladder">
            {heroStages.map((s) => (
              <div className={`st ${s.count ? "" : "zero"}`} key={s.key}>
                <div className="l2">{s.label}</div>
                <div className="v2 tdy-stage-val">{s.count} · <CompactMoney value={s.budget} /></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FX STRIP — company-level, beneath the hero, above the Slate.
          Each currency is one compact unit carrying BOTH quotation
          directions (USD/{code} the canonical stored rate, {code}/USD
          computed as 1/rate — see buildFxItems) so the relationship
          reads together, not as two unrelated cards. ─────────────── */}
      <section className="ovx-sec tdy-fxstrip">
        <div className="oh"><b>FX</b></div>
        <div className="tdy-fx-row">
          {fxItems.map((it) => (
            <div className="tdy-fx-item" key={it.code}>
              <div className="tdy-fx-head">
                <span className="tdy-fx-flag" aria-hidden="true">{it.flag}</span>
                <span className="tdy-fx-code">{it.code}</span>
              </div>
              {it.available ? (
                <>
                  <div className="tdy-fx-pair">
                    <span className="l2">USD / {it.code}</span>
                    <span className="v2 mono">{it.current}</span>
                  </div>
                  <div className="tdy-fx-pair">
                    <span className="l2">{it.code} / USD</span>
                    <span className="v2 mono">{it.reverse}</span>
                  </div>
                  {it.deltaPct != null && (
                    <span className={`tdy-fx-delta ${it.deltaPct > 0 ? "up" : "down"}`}>
                      {it.deltaPct > 0 ? "▲" : "▼"} {Math.abs(it.deltaPct).toFixed(1)}% / 12m on USD/{it.code}
                    </span>
                  )}
                </>
              ) : (
                <>
                  <div className="tdy-fx-pair">
                    <span className="l2">USD / {it.code}</span>
                    <span className="v2 text-tertiary tdy-fx-unavailable">Rate not yet loaded</span>
                  </div>
                  <div className="tdy-fx-pair">
                    <span className="l2">{it.code} / USD</span>
                    <span className="v2 text-tertiary tdy-fx-unavailable">Rate not yet loaded</span>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
        <p className="text-tertiary small tdy-fx-note">
          Reverse pairs are calculated from the same stored rate. Commentary only — the optimizer prices at current rates, not forwards.
        </p>
      </section>

      {/* ── PRODUCTION SLATE ────────────────────────────────────────── */}
      <section className="ovx-sec tdy-slate">
        <div className="oh">
          <b>Production Slate</b><span className="n">{productions.length}</span>
          <button className="hero-action primary tdy-newprod" disabled title={NEW_PRODUCTION_REASON}>
            ＋ New Production
          </button>
        </div>
        <div className="row-list">
          {orderedProductions.map((p) => (
            <div className="row-item tdy-slate-row" key={p.id} onClick={() => navigate(p.route)}>
              <span className="tdx-art" aria-hidden="true" />
              <div className="row-main">
                <div className="row-title">
                  <i className="serif">{p.name}</i> <span className="tdy-stage">{p.stageMeta.label}</span>
                </div>
                <div className="row-sub">{p.headline}</div>
                {p.delta && <div className="row-sub tdy-delta">Since last visit: {p.delta}</div>}
              </div>
              <div className="tdy-slate-figs">
                <span className="tdy-fig"><span className="l2">Budget</span><Money value={p.budget} /></span>
                <span className="tdy-fig"><span className="l2">Net cost</span>{p.npc != null ? <Money value={p.npc} /> : "—"}</span>
              </div>
              <span className={`dot ${p.momentum.tier} tdy-momentum`} title={p.momentum.label}>{p.momentum.glyph}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── COMPANY INTELLIGENCE ────────────────────────────────────── */}
      <section className="ovx-sec tdy-intel">
        <div className="oh"><b>Company Intelligence</b></div>
        {intel.length ? (
          <div className="row-list">
            {intel.map((it, i) => (
              <div className="row-item tdy-intel-row" key={i} style={{ cursor: "default" }}>
                <span className={`dot ${it.tier}`} />
                <div className="row-main">
                  <div className="row-title small">{it.label}</div>
                  <div className="row-sub">{it.text}</div>
                  <div className="row-sub text-tertiary">{it.detail}</div>
                </div>
              </div>
            ))}
          </div>
        ) : <div className="empty-state">No cross-production signals right now.</div>}
      </section>
    </div>
  );
}
