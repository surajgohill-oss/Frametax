import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { patchProject } from "../../api";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, compactScenarioIdentity, normalizeTrivialVariance, flagEmoji } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, structureTier, activeStructure, bestPricedCandidate } from "../../lib/globeData";
import { buildFxItems } from "../../lib/todayCompute";
import QuestionStack from "../../components/QuestionStack";
import RecommendationsList from "../../components/RecommendationsList";
import EconomicsTrace from "../../components/EconomicsTrace";
import QualificationPanel from "../../components/QualificationPanel";
import { InspectorBody } from "../../shell/Inspector";

// Docked-inspector header label per selection kind (frozen artifact
// "Selection · Question" convention).
const INSPECT_KIND_LABEL = {
  question: "Question",
  "allocation-segment": "Segment",
  "allocation-assignment": "Routing",
  "structure-recommendation": "Structure",
  recommendation: "Recommendation",
  candidate: "Candidate",
  jurisdiction: "Jurisdiction",
  account: "Account",
};

// Workspace — the approved artifact "rack" layout
// (reference/artifacts/prototype-v1-updated.html): a collapsible question
// stack on the left, a full-width grid of universal scenario cards in the
// centre (or the Map/Split globe), and a two-group leading-structure strip
// pinned to the bottom. The right-hand Inspector is the app-level overlay
// (openInspector). Every card value is read verbatim from the allocated
// structure — Qualified spend is the backend's own per-segment QPE summed;
// Gross incentive is selected_incentive_usd (best-supported modeled rate);
// NPC is npc_with_adjustments_usd (modeled + normalizations). No client-side
// derivation.

const MODES = [
  { key: "lanes", label: "Lanes" },
  { key: "map", label: "Map" },
  { key: "split", label: "Split" },
];
const CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"];

// The optimizer may compose far more structures than a card rack can
// usefully show at once (every discovery-retained partner — incentive-
// ready AND capability-only — gets a full-relocation and a component
// candidate). Six visible cards, swap-in overflow — the same contract
// Scenarios.jsx uses, over the SAME ordering rule (rank-first, then
// composition order). This is EXISTING optimizer output navigation
// ("Other Scenarios"), not scenario creation — the optimizer already
// generated every one of these; the control only changes which of them
// occupies a visible lane.
const MAX_VISIBLE = 6;
function visibleStructures(structures, rankById, swapId) {
  const ordered = [...structures].sort((a, b) => {
    const ra = rankById.get(a.structure_id)?.rank ?? Infinity;
    const rb = rankById.get(b.structure_id)?.rank ?? Infinity;
    if (ra !== rb) return ra - rb;
    // Workspace Top-6/Data Truthfulness: among structures with no
    // canonical rank (comparable_count can be 0 — the production's own
    // baseline is unpriceable — while real priced candidates still
    // exist), the served array order is arbitrary generation order, not
    // economic order. Tie-break by the SAME real NPC field the canonical
    // comparable ranking already sorts by — grants no rank, no
    // recommendation; it only makes "which 6 show first" deterministic
    // and cost-ordered instead of accidental. Priced structures sort
    // before unpriced ones.
    const an = a.is_fully_priced ? (a.npc_with_adjustments_usd ?? Infinity) : Infinity;
    const bn = b.is_fully_priced ? (b.npc_with_adjustments_usd ?? Infinity) : Infinity;
    return an - bn;
  });
  const base = ordered.slice(0, MAX_VISIBLE);
  const overflow = ordered.slice(MAX_VISIBLE);
  const swapped = swapId ? ordered.find((s) => s.structure_id === swapId) : null;
  const cols = swapped ? [...base.slice(0, MAX_VISIBLE - 1), swapped] : base;
  return { overflow, cols };
}
const pct = (part, whole) => (whole ? Math.max(0, Math.min(100, (part / whole) * 100)) : 0);

// Workspace Display Regression: "Other Scenarios" is a real HTML <select>
// — every option needs its own distinct text, unlike a visible card,
// where the jurisdiction alone is enough because same-jurisdiction
// scenarios rarely land in the same visible 6 at once. A dropdown
// routinely DOES hold several same-jurisdiction options (e.g. several
// distinct Ontario programs) — appends the SAME compact program label
// compactScenarioIdentity already derives (never a second name/ID
// scheme) whenever it exists, so the producer can tell them apart
// without the full legal program name.
function scenarioOptionLabel(structure) {
  const { flags, name, programLabel } = compactScenarioIdentity(structure);
  const label = flags ? `${flags} ${name}` : name;
  return programLabel ? `${label} — ${programLabel}` : label;
}

// Project FX strip — Workspace-only, same component family as Today's
// original FX strip (flag + code, optional 12-month delta chip, both
// quotation directions USD/{code} and {code}/USD, honest-unavailable
// fallback) — reused visually and computationally, not redesigned. The
// fixed EUR/CAD/GBP trio (via the SAME buildFxItems() Today's strip used,
// unchanged) is always present; after that, one cell per DISTINCT local
// currency among the dynamic structure's real participants — one cell for
// a single-jurisdiction structure (SAR), two for a genuine multi-
// jurisdiction one (MUR + SAR), deduplicated so two participants sharing
// a currency (e.g. two Eurozone jurisdictions) never render twice. Never
// a full local-costing breakdown (that stays ENGINE-PENDING). Every rate
// is read verbatim from economics.fx_horizons (the SAME dataset feeding
// the fixed EUR/CAD/GBP trio — no second fetch, no frontend FX math); a
// participant currency with no snapshot entry renders as its own real
// currency code plus an honest "rate unavailable", never a fabricated
// number and never the bare "—" placeholder this used to fall back to.
//
// Workspace/FX Display Regression: `structure` here is deliberately NOT
// always the producer's manually-selected Leading Structure — see its
// caller. When `structure` is null (neither a Leading selection nor a
// Top Priced candidate exists — e.g. a totally unpriced production),
// this returns an empty array; Section 7 of the governing directive is
// explicit that a fake, unresolved "—" block must never render just to
// fill the fourth slot.
function buildLeaderFxItems(economics, structure, label) {
  if (!structure) return [];
  const horizons = economics?.fx_horizons || {};
  const jurisdictionCurrency = economics?.jurisdiction_currency || {};
  // Same participants-or-primary fallback compactScenarioIdentity() uses,
  // so this reads the identical real structure fields, never a second
  // derivation of "which jurisdictions this structure touches."
  const participants = structure?.participants?.length
    ? structure.participants
    : (structure?.primary_jurisdiction ? [structure.primary_jurisdiction] : []);

  const seenCodes = new Set();
  const items = [];
  for (const jurisdiction of participants) {
    const iso2 = jurisdiction.split("-")[0].toUpperCase();
    // Generic chain, no jurisdiction/currency special-cased here:
    // jurisdiction -> ISO2 -> economics.jurisdiction_currency (the SAME
    // canonical registry map served for the fixed trio) -> currency code.
    // No mapping on file: show the jurisdiction's own code rather than
    // silently dropping the cell.
    const code = jurisdictionCurrency[iso2] || iso2;
    if (seenCodes.has(code)) continue; // dedupe — never a repeated currency cell
    seenCodes.add(code);
    const flag = flagEmoji(jurisdiction);
    const h = horizons[code];
    if (!h || h.current == null) {
      items.push({ code, flag, available: false, isLeader: true, leaderLabel: label });
      continue;
    }
    const deltaPct = h["12m"] != null ? ((h["12m"] - h.current) / h.current) * 100 : null;
    // Same 5-decimal display precision buildFxItems() uses for the fixed
    // three, so leader cells never read visually inconsistent with their
    // siblings — reverse is still always 1/current, computed here, never a
    // second stored constant.
    items.push({
      code, flag, isLeader: true, leaderLabel: label, available: true,
      current: Number(h.current.toFixed(5)), reverse: Number((1 / h.current).toFixed(5)), deltaPct,
    });
  }
  return items;
}

function ScenarioCard({ structure, tier, rank, grossBudget, isLeading, onSetLeading, onInspect, onCompare, onSelectSegment }) {
  const priced = structure.is_fully_priced;
  // All four card figures read from THIS scenario's canonical allocated
  // structure — gross from structure.gross_budget_usd (falls back to the
  // production-level prop only if a structure ever omits it), qualified
  // spend from its own per-segment QPE, incentive and NPC from its own
  // priced fields. No production-level or prototype figure is shown.
  const gross = structure.gross_budget_usd ?? grossBudget;
  const qualifiedSpendRaw = structure.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;
  // Segment QPE is summed from the same real leaf accounts the production's
  // Gross budget is drawn from; when a structure excludes nothing, that sum
  // can land a few dollars off the source document's own stated Grand Total
  // (Gross budget) — economically immaterial rounding noise, not additional
  // or double-counted spend. Normalized via the shared global rule rather
  // than surfaced to producers (see normalizeTrivialVariance in lib/format).
  const qualifiedSpend = normalizeTrivialVariance(qualifiedSpendRaw, gross);
  const npc = structure.npc_with_adjustments_usd;

  const laneClass = isLeading ? "anchor" : priced ? "" : "draft";
  // Workspace Top-6/Data Truthfulness: "Set as leading"/LEADING is a
  // PRODUCER SELECTION, never CineGlobe's own ranked recommendation —
  // it must never borrow the "①" glyph, which implies canonical rank #1
  // regardless of the leading structure's real (possibly absent) rank.
  // A priced structure with no real canonical rank (rank?.rank is only
  // ever set for a directly-comparable, recommendation-eligible
  // candidate — see canonical_production_view.py's comparable/
  // review_required split) must never silently default to "①" either;
  // "PRICED" states plainly that real economics exist without
  // asserting an order the doctrine did not establish.
  const badge = isLeading
    ? "◈ LEADING"
    : priced
      ? (rank?.rank ? (CIRCLED[rank.rank - 1] || `#${rank.rank}`) : "PRICED")
      : "DRAFT";

  // Compact card identity (flag + full jurisdiction name + "Up to X%") —
  // the approved Workspace format. See compactScenarioIdentity in
  // lib/format.jsx; detailed program mechanics live in Inspector, not here.
  const { flags, name, subtitle } = compactScenarioIdentity(structure);
  // FX presentation is intentionally hidden here for now: structure.fx_basis
  // is real, sourced exchange-rate provenance (currency/rate/source/date),
  // but under the default economics controls fx_delta_usd is always $0 —
  // "priced at spot, no currency stress modeled" — which reads to a
  // producer as a meaningful adjustment when it isn't one yet. The backend
  // still computes and serves it; a real FX adjustment (applied only to
  // currency-exposed local spend) belongs in the Inspector later, not a
  // prominent card chip.

  // Inspector interaction (Workspace Top-6/Data Truthfulness): the whole
  // card body is inspectable, not only the small "Inspect" button —
  // click or Enter/Space anywhere on the card opens the SAME existing
  // Inspector with this SAME structure. Footer/leading-action buttons
  // stop propagation so Compare/Set-as-leading don't ALSO fire Inspect.
  const openInspect = () => onInspect(structure);
  const handleCardKeyDown = (e) => {
    if (e.target !== e.currentTarget) return; // let inner buttons handle their own keys
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openInspect();
    }
  };

  return (
    <div
      className={`wsx-lane ${laneClass}`}
      role="button"
      tabIndex={0}
      aria-label={`Inspect ${name}`}
      onClick={openInspect}
      onKeyDown={handleCardKeyDown}
    >
      <div className="wsx-lh">
        <div className="wsx-lh-id">
          <div className="wsx-nm">{flags ? `${flags} ${name}` : name}</div>
          <div className="wsx-lb">{subtitle}</div>
        </div>
        <span className="wsx-badge">{badge}</span>
      </div>

      {priced ? (
        <>
          <div className="wsx-rows">
            <div className="wsx-row"><span>Gross budget</span><span><Money value={gross} bare /></span></div>
            <div className="wsx-row"><span>Qualified spend</span><span><Money value={qualifiedSpend} bare /></span></div>
            <div className="wsx-row"><span>Gross incentive</span><span className="incentive"><Money value={structure.selected_incentive_usd} bare /></span></div>
          </div>
          <div className="wsx-row net"><span>Net production cost</span><span><Money value={npc} bare /></span></div>
          <div className="wsx-range">
            <u style={{ left: 0, width: `${pct(qualifiedSpend, gross)}%` }} />
            <i style={{ left: `${pct(qualifiedSpend, gross)}%`, right: 0 }} />
            <b style={{ left: `${pct(npc, gross)}%` }} />
          </div>
        </>
      ) : (
        <div className="wsx-partial">
          <div className="note">Not yet priced — {structure.blockers.length} blocker{structure.blockers.length === 1 ? "" : "s"}.</div>
          {structure.blockers.slice(0, 3).map((b, i) => <p key={i}>{b}</p>)}
          {structure.blockers.length > 3 && <p>+{structure.blockers.length - 3} more — open the recommendation for the full trace.</p>}
        </div>
      )}

      <div className="wsx-foot">
        <button onClick={(e) => { e.stopPropagation(); openInspect(); }}>Inspect</button>
        <button onClick={(e) => { e.stopPropagation(); onCompare(structure); }}>Compare</button>
      </div>
      <div className="wsx-lead-act">
        {isLeading ? (
          <button className="wsx-lead is-leading" disabled>● Current leading structure</button>
        ) : (
          <button className="wsx-lead" onClick={(e) => { e.stopPropagation(); onSetLeading(structure.structure_id); }}>◈ Set as leading</button>
        )}
      </div>
    </div>
  );
}

// Globe chrome — a context HUD only (which production, how many composed
// scenarios, how many routes). The old "Layers" panel was prototype
// scaffolding — two toggles that controlled nothing plus four permanently-
// ghosted "engine pending" rows and a note naming the rendering library — so
// it was removed rather than shipped to producers. Country polygon fill and
// borders are the Globe's primary always-on visualization, never a togglable
// layer.
//
// PHASE 2 CLOSEOUT: the persistent status legend is gone from here too. A
// Globe that needs a colour key to be read is a Globe that hasn't been
// designed; the states are learned by hovering (which names the state) and
// by opening one (which explains it). The HUD stays because it is context
// about the production, not an explanation of the instrument itself.
function GlobeChrome({ productionName, nScenarios, nArcs }) {
  return (
    <div className="wsx-g-hud">
      <b>Project globe · {productionName}</b>
      {nScenarios} scenario{nScenarios === 1 ? "" : "s"} · {nArcs} structure route{nArcs === 1 ? "" : "s"}
    </div>
  );
}

export default function Workspace() {
  const { projectId: routeProjectId } = useParams();
  const { data, error, loading, refetch } = useCineGlobe(routeProjectId);
  const location = useLocation();
  const navTab = location.state?.tab;

  const [mode, setMode] = useState(navTab === "map" || navTab === "split" ? navTab : "lanes");
  const [qOpen, setQOpen] = useState(navTab === "inputs" || navTab === "recommendations");
  const [qTab, setQTab] = useState(navTab === "inputs" || navTab === "recommendations" ? navTab : "questions");
  const [activeGreyArea, setActiveGreyArea] = useState(null);
  const [sortByMoney, setSortByMoney] = useState(true); // artifact "by $ ▾"
  // Which overflow (optimizer-generated, not user-created) structure is
  // swapped into the last visible lane via "Other Scenarios" — selecting,
  // never creating.
  const [swapId, setSwapId] = useState("");
  // Compare identity (Workspace Top-6/Data Truthfulness): the canonical
  // structure_id of whichever card's Compare was last clicked — never a
  // jurisdiction code, so two same-country/different-program structures
  // (e.g. Australia Location Offset vs Australia PDV Offset) are never
  // collapsed into one comparison target.
  const [compareStructureId, setCompareStructureId] = useState(null);
  const [globeMode, setGlobeMode] = useState("jurisdictions"); // "jurisdictions" | "optimizer"
  const [globeHover, setGlobeHover] = useState(null);
  const {
    openInspector, inspector, closeInspector, setDocked,
    leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
  } = useAppState();

  // Phase C write-through for "Set as Leading": persists to the real
  // Project row so the choice survives a reload/restart, in addition to
  // the existing shared AppState update every Workspace view already reads
  // synchronously. Fire-and-forget — never blocks the UI, never triggers
  // the optimizer.
  //
  // Known, deferred gap (NOT a bug — logged here rather than worked around,
  // per Phase C's own scope boundary against touching engine/optimizer
  // code): the optimizer's in-memory structures use their own string
  // identifiers (e.g. "ALLOC-COMPONENT-POST-SA"), not real
  // production_structures.id UUIDs. Only the one structure the Phase C
  // migration persisted (the effective baseline) has a real row. Selecting
  // any other structure 422s on the UUID FK — expected until a later phase
  // persists the optimizer's own generated structures, not a failure.
  const handleSetLeading = useCallback((structureId) => {
    setLeadingStructureId(structureId);
    const projectId = data?.production?.project_id;
    if (projectId) {
      patchProject(projectId, { leading_structure_id: structureId }).catch((err) => {
        if (String(err.message).startsWith("422")) {
          console.info(`[Workspace] leading structure ${structureId} has no persisted backend row yet (optimizer-generated, not yet migrated) — UI selection still applied`);
        } else {
          console.error("[Workspace] failed to persist leading structure to backend:", err);
        }
      });
    }
  }, [setLeadingStructureId, data]);

  // Dock the Inspector into the Workspace right column (frozen-artifact
  // interaction) for as long as this screen is mounted; the app-level
  // floating overlay stands down meanwhile.
  useEffect(() => {
    setDocked(true);
    return () => setDocked(false);
  }, [setDocked]);

  // Honor cross-page navigation intent (Overview "Deal facts → edit",
  // "Project globe") once the location changes.
  useEffect(() => {
    if (navTab === "map" || navTab === "split") setMode(navTab);
    if (navTab === "inputs" || navTab === "recommendations") { setQOpen(true); setQTab(navTab); }
  }, [navTab]);

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: globeMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, legal, economics } = data;
  const openGrey = (legal.grey_areas_current || []).filter((g) => g.status === "open");
  const openCount = (pkg.missing_inputs?.length || 0) + openGrey.length;
  const leadingStructure = activeStructure(allocated, leadingStructureId);
  const leadingId = leadingStructure?.structure_id ?? null;
  const { overflow, cols } = visibleStructures(allocated.structures, rankById, swapId);
  // Workspace/FX Display Regression: Leading (activeStructure, which
  // already carries this project's OWN manual-selection-or-canonical-
  // rank-1 semantics — the same "leading" identity every other Workspace
  // element, e.g. the anchor lane / "Set as leading" toggle, already
  // reads) drives the dynamic FX slot whenever it resolves to a real
  // structure. Only when NEITHER a manual selection nor a canonical
  // rank-1 exists (Lips Like Sugar's own real state — comparable_count:0
  // means no candidate is ever directly-comparable) does the slot fall
  // back to bestPricedCandidate, the SAME real economics the Hero already
  // uses for its own "Top Priced Candidate" state (ProjectHeader.jsx) —
  // never a second, divergent "best" computation.
  const dynamicFxStructure = leadingStructure || bestPricedCandidate(allocated);
  const dynamicFxLabel = leadingStructure ? "LEADING" : (dynamicFxStructure ? "TOP PRICED" : null);
  const fxItems = [...buildFxItems(economics?.fx_horizons), ...buildLeaderFxItems(economics, dynamicFxStructure, dynamicFxLabel)];

  // Collapsed-rail status dots — hot for any money-bearing / blocking item.
  const dots = [
    ...openGrey.map(() => "hot"),
    ...(pkg.missing_inputs || []).map((m) => (m.blocking ? "hot" : "")),
  ].slice(0, 8);

  const contingencyByAccount = allocated?.contingency || {};
  function handleGlobeClick(pt) {
    const code = pt.jurisdictionCode || pt.id;
    setSelectedJurisdiction(code);
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label, contingencyByAccount });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }
  function handleSelectStructure(structure) {
    if (structure.recommendation) openInspector("structure-recommendation", structure.recommendation);
    else if (structure.segments?.[0]) openInspector("allocation-segment", { ...structure.segments[0], structureLabel: structure.label, contingencyByAccount });
  }
  function handleSelectSegment(structure, code) {
    const seg = structure.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: structure.label, contingencyByAccount });
  }

  return (
    <div className="wsx-screen">
      {/* Project FX strip — immediately below the shared production tabs
          (rendered by ProjectHeader, outside this component) and
          immediately above the Lanes/Map/Split mode row. Same component
          family as Today's original FX strip (flag + code, 12-month delta
          chip, both quotation directions, honest-unavailable fallback) —
          reused visually and structurally under a wsx- prefix since Today
          no longer renders FX at all. */}
      <section className="wsx-fxstrip">
        <div className="wsx-fx-row">
          {fxItems.map((it) => (
            <div className={`wsx-fx-item ${it.isLeader ? "leader" : ""}`} key={`${it.code}-${it.isLeader ? "leader" : "fixed"}`}>
              <div className="wsx-fx-head">
                <span className="wsx-fx-flag" aria-hidden="true">{it.flag}</span>
                <span className="wsx-fx-code">{it.code}</span>
                {it.isLeader && it.leaderLabel && <span className="wsx-fx-tag">{it.leaderLabel === "LEADING" ? "Leading" : "Top Priced"}</span>}
                {it.available && it.deltaPct != null && (
                  <span className={`wsx-fx-delta ${it.deltaPct > 0 ? "up" : "down"}`} title={`12-month move on USD/${it.code}`}>
                    {it.deltaPct > 0 ? "▲" : "▼"} {Math.abs(it.deltaPct).toFixed(1)}%
                  </span>
                )}
              </div>
              <div className="wsx-fx-rates">
                <div className="wsx-fx-pair">
                  <span className="l2">USD / {it.code}</span>
                  <span className={`wsx-fx-val mono ${it.available ? "" : "wsx-fx-unavailable"}`}>
                    {it.available ? it.current : "rate unavailable"}
                  </span>
                </div>
                <div className="wsx-fx-pair">
                  <span className="l2">{it.code} / USD</span>
                  <span className={`wsx-fx-val mono ${it.available ? "" : "wsx-fx-unavailable"}`}>
                    {it.available ? it.reverse : "rate unavailable"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="text-tertiary small wsx-fx-note">
          Reference rates (ECB). Reverse pairs derive from the same rate; the optimizer prices at current rates, not forward movement.
        </p>
      </section>

      {/* Grid geometry matches the artifact: 48px | 1fr | 38px collapsed;
          left widens to 220px (stack) / 340px (Recs/Inputs); the right
          column widens from the 38px quiet rail to the 300px docked
          Inspector when something is selected (frozen-artifact layoutWork). */}
      <div
        className="wsx-work"
        style={{
          gridTemplateColumns: `${!qOpen ? "48px" : qTab !== "questions" ? "340px" : "220px"} 1fr ${inspector ? "290px" : "38px"}`,
        }}
      >
        {/* Question stack — collapsible left rail. Collapsed by default per
            the artifact; expands into the full work stack (Questions /
            Recommendations / Inputs) so every backend-wired panel stays
            reachable (QualificationPanel = the real POST /people, /facts). */}
        {qOpen ? (
          <aside className="wsx-qstack wsx-qstack-open">
            <div className="wsx-qh">
              Question Stack · {openCount}
              <button className="wsx-qsort" onClick={() => setSortByMoney((v) => !v)} title="Toggle question ordering">
                {sortByMoney ? "by $ ▾" : "by stack ▾"}
              </button>
              <button className="wsx-qcollapse" onClick={() => setQOpen(false)} aria-label="Collapse question stack">⟨</button>
            </div>
            <div className="wsx-qtabs">
              <button className={qTab === "questions" ? "active" : ""} onClick={() => setQTab("questions")}>Questions</button>
              <button className={qTab === "recommendations" ? "active" : ""} onClick={() => setQTab("recommendations")}>Recs</button>
              <button className={qTab === "inputs" ? "active" : ""} onClick={() => setQTab("inputs")}>Inputs</button>
            </div>
            {qTab === "questions" && (
              <>
                <QuestionStack missingInputs={pkg.missing_inputs} greyAreas={legal.grey_areas_current} sortByMoney={sortByMoney} />
                {openGrey.length > 0 && (
                  <div className="trace-trigger-row">
                    {openGrey.map((g) => (
                      <button key={g.item_id} className={`tag ${activeGreyArea?.item_id === g.item_id ? "active" : ""}`} onClick={() => setActiveGreyArea(g)}>
                        Trace {g.jurisdiction_code} · <Money value={g.amount_usd} /> <ChevronDown size={12} />
                      </button>
                    ))}
                  </div>
                )}
                {activeGreyArea && <EconomicsTrace greyArea={activeGreyArea} legal={legal} />}
              </>
            )}
            {qTab === "recommendations" && (
              <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} />
            )}
            {qTab === "inputs" && (
              <QualificationPanel people={data.people} facts={data.facts} script={pkg.script} refetch={refetch} />
            )}
          </aside>
        ) : (
          <aside className="wsx-qstack collapsed">
            <button className="wsx-qexpand" onClick={() => setQOpen(true)} aria-label="Expand question stack">⟩</button>
            <div className="wsx-qcount">{openCount}</div>
            <div className="wsx-qdots">
              {dots.map((d, i) => <i key={i} className={`wsx-qdot ${d}`} />)}
            </div>
          </aside>
        )}

        {/* Station — card rack or globe. One horizontal control row:
            Lanes/Map/Split stays centered over the scenario-comparison
            region (a fixed left spacer column balances the right-hand
            Other Scenarios column so the tabs never drift off-center
            depending on whether Other Scenarios is present); Other
            Scenarios sits at the right, same baseline, never a second
            row. The Jurisdictions/Optimizer Overlay toggle is secondary
            to the Globe itself and lives docked to the globe pane (see
            wsx-g-modetoggle below), not here. */}
        <div className="wsx-station">
          <div className="wsx-station-head">
            <div className="wsx-station-head-spacer" aria-hidden="true" />
            <div className="wsx-viewtabs">
              {MODES.map((m) => (
                <button key={m.key} className={mode === m.key ? "active" : ""} onClick={() => setMode(m.key)}>
                  {m.label}
                </button>
              ))}
            </div>
            {/* Other Scenarios — navigates among structures the optimizer
                already generated but that don't currently occupy a visible
                lane; it swaps the last lane's contents, it never creates a
                new structure and never reruns the optimizer. */}
            {mode !== "map" && overflow.length > 0 ? (
              <div className="wsx-other-scenarios">
                <label htmlFor="wsx-swap">Other scenarios</label>
                <select
                  id="wsx-swap"
                  className="field-select"
                  value={swapId}
                  onChange={(e) => setSwapId(e.target.value)}
                >
                  <option value="">— {(() => { const last = cols[cols.length - 1]; return last ? scenarioOptionLabel(last) : "—"; })()} —</option>
                  {overflow.map((s) => (
                    <option key={s.structure_id} value={s.structure_id}>{scenarioOptionLabel(s)}</option>
                  ))}
                </select>
              </div>
            ) : <div aria-hidden="true" />}
          </div>

          {mode === "lanes" && (
            <div className="wsx-rack">
              {cols.map((s) => (
                <ScenarioCard
                  key={s.structure_id}
                  structure={s}
                  tier={structureTier(s, rankById)}
                  rank={rankById.get(s.structure_id)}
                  grossBudget={production.gross_budget_usd}
                  isLeading={s.structure_id === leadingId}
                  onSetLeading={handleSetLeading}
                  onInspect={handleSelectStructure}
                  onCompare={(s) => { setCompareStructureId(s.structure_id); setQOpen(true); setQTab("recommendations"); }}
                  onSelectSegment={handleSelectSegment}
                />
              ))}
            </div>
          )}

          {/* Map — side-by-side, NOT a full-width globe: left is the
              current scenario's own economics (the Leading structure — the
              same "current scenario" concept Set as Leading already
              establishes elsewhere in Workspace), right is the geographic
              view. Distinct from Split (which shows the full comparison
              rack beside the globe) — Map shows exactly one scenario in
              geographic context. Reuses the existing ScenarioCard and the
              same shared Globe3D usage, unmodified. */}
          {mode === "map" && (
            <div className="wsx-mapv">
              <div className="lcol wsx-map-econ">
                {leadingStructure && (
                  <ScenarioCard
                    key={leadingStructure.structure_id}
                    structure={leadingStructure}
                    tier={structureTier(leadingStructure, rankById)}
                    rank={rankById.get(leadingStructure.structure_id)}
                    grossBudget={production.gross_budget_usd}
                    isLeading={leadingStructure.structure_id === leadingId}
                    onSetLeading={handleSetLeading}
                    onInspect={handleSelectStructure}
                    onCompare={(s) => { setCompareStructureId(s.structure_id); setQOpen(true); setQTab("recommendations"); }}
                    onSelectSegment={handleSelectSegment}
                  />
                )}
              </div>
              <div className="mcol">
                <div className="wsx-globe dark-panel wsx-globe-chrome">
                  <Globe3D
                    points={points}
                    arcs={arcs}
                    height={460}
                    pointRadius={0.22}
                    polygonColors={polygonColors}
                    selectedIso={selectedIso}
                    hoveredIso={globeHover?.iso ?? null}
                    selectedLat={selectedLat}
                    selectedLng={selectedLng}
                    focusLat={focusLat}
                    focusLng={focusLng}
                    focusDistance={focusDistance}
                    onPointClick={handleGlobeClick}
                    onPointHover={setGlobeHover}
                  />
                  <GlobeChrome productionName={production.production_name} nScenarios={allocated.structures.length} nArcs={arcs.length} />
                  <div className="wsx-g-modetoggle" title="Jurisdictions: every jurisdiction this production touches, by what it means for the production. Optimizer Overlay: the recommended structure's own routing chain only.">
                    <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
                    <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
                  </div>
                  {globeHover && (
                    <div className="globe-tooltip">
                      <strong>{globeHover.jurisdictionName}</strong>
                      <div className="text-tertiary small">{globeHover.statusLabel}</div>
                      {globeHover.role && <div className="text-tertiary small">{globeHover.role}</div>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {mode === "split" && (
            <div className="wsx-splitv">
              <div className="lcol">
                <div className="wsx-rack">
                  {cols.map((s) => (
                    <ScenarioCard
                      key={s.structure_id}
                      structure={s}
                      tier={structureTier(s, rankById)}
                      rank={rankById.get(s.structure_id)}
                      grossBudget={production.gross_budget_usd}
                      isLeading={s.structure_id === leadingId}
                      onSetLeading={handleSetLeading}
                      onInspect={handleSelectStructure}
                      onCompare={(s) => { setCompareStructureId(s.structure_id); setQOpen(true); setQTab("recommendations"); }}
                      onSelectSegment={handleSelectSegment}
                    />
                  ))}
                </div>
              </div>
              <div className="mcol">
                <div className="wsx-globe dark-panel wsx-globe-chrome">
                  <Globe3D
                    points={points}
                    arcs={arcs}
                    height={480}
                    pointRadius={0.22}
                    polygonColors={polygonColors}
                    selectedIso={selectedIso}
                    hoveredIso={globeHover?.iso ?? null}
                    selectedLat={selectedLat}
                    selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
                    onPointClick={handleGlobeClick}
                    onPointHover={setGlobeHover}
                  />
                  <GlobeChrome productionName={production.production_name} nScenarios={allocated.structures.length} nArcs={arcs.length} />
                  <div className="wsx-g-modetoggle" title="Jurisdictions: every jurisdiction this production touches, by what it means for the production. Optimizer Overlay: the recommended structure's own routing chain only.">
                    <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
                    <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
                  </div>
                  {globeHover && (
                    <div className="globe-tooltip">
                      <strong>{globeHover.jurisdictionName}</strong>
                      <div className="text-tertiary small">{globeHover.statusLabel}</div>
                      {globeHover.role && <div className="text-tertiary small">{globeHover.role}</div>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Inspector — docked into the right column per the frozen artifact.
            Populated on selection (question / lane / segment / structure)
            from the shared openInspector state; quiet 38px rail otherwise.
            Same InspectorBody the overlay uses — no forked render, no
            duplicated data. */}
        {inspector ? (
          <aside className="wsx-insp">
            <div className="wsx-insp-inner">
              <div className="wsx-insp-h">
                <span className="kind">Selection · {INSPECT_KIND_LABEL[inspector.kind] || "Detail"}</span>
                <button className="close" onClick={closeInspector} aria-label="Close inspector">✕</button>
              </div>
              <InspectorBody inspector={inspector} />
            </div>
          </aside>
        ) : (
          <div className="wsx-insp-gutter" aria-hidden="true" />
        )}
      </div>
    </div>
  );
}
