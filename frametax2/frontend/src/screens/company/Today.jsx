import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, CompactMoney } from "../../lib/format";
import { useProjectStatus } from "../../lib/useProjectStatus";
import { buildRecordRows } from "../../lib/recordEvents";
import { buildHeroStages } from "../../lib/todayCompute";
import { getTheme, toggleTheme } from "../../lib/theme";
import heroArt from "../../assets/production-art/little-utopia-hero-clean.png";

// Today — the company command center. Answers: what's active, what needs
// attention, what questions are unresolved, and a fast path to ask
// CineGlobe about the slate. NOT another Workspace — no scenario
// comparison, no FX intelligence (that is project-specific and lives in
// the production screens), no research notebook. Page order: toolbar
// (theme + New Production) -> State of the Studio (compact executive
// summary) -> Questions / Ask CineGlobe (side by side) -> Production
// Slate (collapsible Evaluation -> Development -> Production groups).
//
// Built from the same visual language as the rest of the app (.ovx-sec
// cards, .oh headers, .row-list/.row-item rows, .dot tiers, .l2/.v2
// typography, .tag chips, .field-input, .ph-ico) — no new dashboard
// aesthetic introduced. The backend serves exactly one real production
// (little_utopia_state.py); every computation below runs generically
// over a `productions` array so nothing here needs to change when a
// second production exists, but nothing is padded to look busier than
// the real slate is today.

const NEW_PRODUCTION_REASON = "Production intake — engine pending";
const ASK_REASON = "AI query engine — engine pending";
const ASK_EXAMPLES = [
  "Why is Mauritius the recommended structure?",
  "What happens if I move post to the UK?",
  "What is this budget in Mauritian Rupees?",
  "Can Mauritius and Saudi Arabia be combined?",
  "What happens to NPC if the euro weakens 5%?",
];
const TOP_ATTENTION = 5;
const ATTENTION_TIER_RANK = { red: 0, amber: 1, silver: 2, charcoal: 3 };

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
  const { meta: statusMeta, statuses } = useProjectStatus(data?.production?.production_id, {
    projectId: data?.production?.project_id,
    backendLifecycle: data?.production?.lifecycle,
  });
  // Local mirror of the theme purely so the button's icon re-renders —
  // same pattern as ProjectHeader's own toggle. The authoritative state
  // is the `data-theme` attribute on <html> (lib/theme.js), never React
  // state, so nothing here can cause a remount elsewhere in the app.
  // Today has no ProjectHeader (Company routes render no production
  // chrome), so this is its own trigger for the SAME canonical theme
  // module — not a second theme implementation.
  const [theme, setThemeState] = useState(getTheme);
  const [askText, setAskText] = useState("");
  const [expandedStages, setExpandedStages] = useState(null); // null = use the data-derived default

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal, recommendations, production, structures, pkg } = data;
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

  const productions = [
    {
      id: production.production_id,
      name: production.production_name,
      stageMeta: statusMeta,
      budget: production.gross_budget_usd,
      npc: best?.is_fully_priced ? best.npc_with_adjustments_usd : null,
      headline,
      momentum,
      impactUsd,
      route: "/production/overview",
    },
  ];

  // ── State of the Studio: compact executive summary (4 figures), no
  // stage ladder here — the lifecycle breakdown lives in the Production
  // Slate's own collapsible groups below, so it isn't shown twice. ────
  const activeProductions = productions.filter((p) => p.stageMeta.key !== "archived");
  const totalActiveBudget = activeProductions.reduce((s, p) => s + (p.budget || 0), 0);
  const totalNpc = activeProductions.reduce((s, p) => s + (p.npc || 0), 0);
  const attentionCount = productions.filter((p) => p.momentum.rank <= 1).length; // Blocked or Stalled

  // Exactly Evaluation / Development / Production, in that fixed order,
  // each carrying its own aggregate count/budget/npc/attention — see
  // lib/todayCompute.js.
  const heroStages = buildHeroStages(statuses, productions);
  const defaultExpandedStages = new Set(heroStages.filter((s) => s.count > 0).map((s) => s.key));
  const openStages = expandedStages ?? defaultExpandedStages;
  function toggleStage(key) {
    setExpandedStages((cur) => {
      const next = new Set(cur ?? defaultExpandedStages);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }

  // ── Questions Requiring Your Attention — the SAME two real sources
  // QuestionStack reads (Legal Engine open grey areas, Question Engine
  // missing inputs), compacted for the executive view and tagged with
  // the production each belongs to. Status is the only real temporal
  // signal this backend serves — no fabricated age/deadline. ─────────
  const attentionItems = [
    ...openGrey.map((g) => ({
      tier: "red",
      question: g.resolving_evidence,
      productionName: production.production_name,
      status: "Unresolved",
      amount: g.amount_usd,
    })),
    ...(pkg.missing_inputs || []).map((m) => ({
      tier: m.blocking ? "amber" : "silver",
      question: m.question,
      productionName: production.production_name,
      status: "Missing",
      amount: null,
    })),
  ].sort((a, b) => ATTENTION_TIER_RANK[a.tier] - ATTENTION_TIER_RANK[b.tier] || (b.amount || 0) - (a.amount || 0));

  return (
    <div className="screen tdy-screen">
      {/* ── Page toolbar — the existing canonical theme control (no
          Today-specific implementation) plus a prominent New Production
          action, both near the upper right of the Today content. ────── */}
      <div className="tdy-toolbar">
        <button
          className="ph-ico"
          title={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
          aria-label={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
          aria-pressed={theme === "night"}
          onClick={() => setThemeState(toggleTheme())}
        >
          {theme === "night" ? "☾" : "◐"}
        </button>
        <button className="hero-action primary tdy-newprod" disabled title={NEW_PRODUCTION_REASON}>
          ＋ New Production
        </button>
      </div>

      {/* ── HERO — State of the Studio ─────────────────────────────── */}
      <section className="ovx-sec tdy-hero">
        <div className="oh tdy-hero-oh">
          <b>State of the Studio</b>
          <span className={`tdy-attention ${attentionCount ? "hot" : "calm"}`}>
            <i />{attentionCount} Production{attentionCount === 1 ? "" : "s"} {attentionCount === 1 ? "Requires" : "Require"} Attention
          </span>
        </div>
        <div className="tdy-summary4">
          <div className="tdy-hn">
            <span className="l2">Active Productions</span>
            <span className="v2 tdy-hn-xl">{activeProductions.length}</span>
          </div>
          <div className="tdy-hn">
            <span className="l2">Total Estimated Budget</span>
            <span className="v2 tdy-hn-big"><Money value={totalActiveBudget} /></span>
          </div>
          <div className="tdy-hn">
            <span className="l2">Aggregate Net Production Cost</span>
            <span className="v2 tdy-hn-big">{totalNpc ? <Money value={totalNpc} /> : "—"}</span>
          </div>
          <div className="tdy-hn">
            <span className="l2">Requires Attention</span>
            <span className="v2 tdy-hn-xl">{attentionCount}</span>
          </div>
        </div>
      </section>

      <div className="tdy-cols">
        {/* ── QUESTIONS REQUIRING YOUR ATTENTION ─────────────────────── */}
        <section className="ovx-sec tdy-attn">
          <div className="oh">
            <b>Questions Requiring Your Attention</b><span className="n">{attentionItems.length}</span>
            <button className="act" onClick={() => navigate("/production/workspace")}>View all questions →</button>
          </div>
          {attentionItems.length ? (
            <div className="row-list">
              {attentionItems.slice(0, TOP_ATTENTION).map((it, i) => (
                <div className="row-item tdy-attn-row" key={i} style={{ cursor: "default" }}>
                  <span className={`dot ${it.tier}`} />
                  <div className="row-main">
                    <div className="row-title small">{it.question}</div>
                    <div className="row-sub text-tertiary">{it.productionName} · {it.status}</div>
                  </div>
                  {it.amount != null && (
                    <span className="tdy-attn-amt mono">±<Money value={it.amount} bare /></span>
                  )}
                </div>
              ))}
            </div>
          ) : <div className="empty-state">No open questions — every account is either qualified or has a resolved position.</div>}
        </section>

        {/* ── ASK CINEGLOBE — production-aware AI assistance. No backend
            query interface exists yet anywhere in this codebase (traced:
            no /ai, /query, or assistant route on the API; no such
            frontend architecture to reuse) — built honestly, wired to
            nothing, never a canned response. ─────────────────────────── */}
        <section className="ovx-sec tdy-ask">
          <div className="oh"><b>Ask CineGlobe</b></div>
          <p className="text-tertiary small tdy-ask-note">
            Production-aware AI assistance over your structures, incentive rules, scenario comparisons, budgets,
            QPE, FX, and jurisdiction requirements — {ASK_REASON}.
          </p>
          <div className="tdy-ask-examples">
            {ASK_EXAMPLES.map((q) => (
              <button type="button" key={q} className="tag" onClick={() => setAskText(q)}>{q}</button>
            ))}
          </div>
          <form className="tdy-ask-form" onSubmit={(e) => e.preventDefault()}>
            <input
              className="field-input"
              type="text"
              placeholder="Ask about structures, incentives, budgets, FX…"
              value={askText}
              onChange={(e) => setAskText(e.target.value)}
            />
            <button className="hero-action primary" type="submit" disabled title={ASK_REASON}>Ask</button>
          </form>
        </section>
      </div>

      {/* ── PRODUCTION SLATE — Evaluation → Development → Production,
          each a collapsible group with its own aggregate row. ────────── */}
      <section className="ovx-sec tdy-slate">
        <div className="oh"><b>Production Slate</b><span className="n">{productions.length}</span></div>
        {heroStages.map((s) => {
          const isOpen = openStages.has(s.key);
          return (
            <div className="tdy-stagegrp" key={s.key}>
              <button className="tdy-stagehead" onClick={() => toggleStage(s.key)} aria-expanded={isOpen}>
                <span className="tdy-stagecar" aria-hidden="true">{isOpen ? "▼" : "▶"}</span>
                <span className="tdy-stagename">{s.label}</span>
                <span className="tdy-stagemeta">{s.count} production{s.count === 1 ? "" : "s"}</span>
                <span className="tdy-stagemeta mono">{s.count ? <CompactMoney value={s.budget} /> : "$0"} Budget</span>
                <span className="tdy-stagemeta mono">{s.npc ? <CompactMoney value={s.npc} /> : "$0"} NPC</span>
                {s.attention > 0 && <span className="tdy-stagemeta tdy-stage-hot">{s.attention} Attention</span>}
              </button>
              {isOpen && s.productions.length > 0 && (
                <div className="row-list tdy-stagerows">
                  {s.productions
                    .slice()
                    .sort((a, b) => a.momentum.rank - b.momentum.rank || b.impactUsd - a.impactUsd)
                    .map((p) => (
                      <div className="row-item tdy-slate-row" key={p.id} onClick={() => navigate(p.route)}>
                        {/* Canonical project key art (Full-Art Hero Rule asset,
                            same file ProductionHero uses) — object-fit:contain
                            so the complete composition is preserved, never
                            cropped or distorted, at this thumbnail size. */}
                        <img className="tdx-art" src={heroArt} alt="" aria-hidden="true" />
                        <div className="row-main">
                          <div className="row-title">
                            <i className="serif">{p.name}</i> <span className="tdy-stage">{p.stageMeta.label}</span>
                          </div>
                          <div className="row-sub">{p.headline}</div>
                        </div>
                        <div className="tdy-slate-figs">
                          <span className="tdy-fig"><span className="l2">Budget</span><Money value={p.budget} /></span>
                          <span className="tdy-fig tdy-fig-net"><span className="l2">Net cost</span>{p.npc != null ? <Money value={p.npc} /> : "—"}</span>
                        </div>
                        <span className={`dot ${p.momentum.tier} tdy-momentum`} title={p.momentum.label}>{p.momentum.glyph}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
