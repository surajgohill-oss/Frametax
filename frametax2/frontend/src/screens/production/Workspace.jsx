import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { patchProject } from "../../api";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, compactScenarioIdentity, buildScenarioLabel, normalizeTrivialVariance, hasAdministrativeAllocationRisk } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, structureTier, activeStructure, resolveSegmentDetail, buildCandidateDetail } from "../../lib/globeData";
import { bestPricedCandidate } from "../../lib/bestPricedCandidate";
import { isBaselineStructure } from "../../lib/productionOptions";
import { MODE_NORMAL, MODE_OPTIMIZER, selectSixSlots } from "../../lib/workspaceScenarioMode";
import FXStrip from "../../components/FXStrip";
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
// Scenarios.jsx uses. This is EXISTING optimizer output navigation
// ("Other Scenarios"), not scenario creation — the optimizer already
// generated every one of these; the control only changes which of them
// occupies a visible lane.
//
// Workspace scenario-mode data wiring: the six-slot composition itself
// (Current Location -> top four mode-admissible scenarios -> slot 6) now
// lives in lib/workspaceScenarioMode.js's selectSixSlots(), keyed off the
// backend's own canonical `classification` field for the active Normal/
// Optimizer mode — never a second, independently-maintained selection
// here. See that module's header comment for the exact family mapping.
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
// OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22): the four canonical
// optimizer classifications (structural_classification.py's own
// OPTIMIZER_STRUCTURE_FAMILIES) — a plain inline set rather than a
// cross-module import, since every optimizer-consuming display site here
// only needs to answer one question: "is this structure's identity best
// described by its routed COMPONENTS (buildScenarioLabel) or its plain
// jurisdiction/program (compactScenarioIdentity)?"
const OPTIMIZER_CLASSIFICATIONS = new Set([
  "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
]);

// OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22) — ROOT DEFECT 3/4: this
// used to derive its label from compactScenarioIdentity alone, which (a)
// can append a non-claiming cost-tracking segment jurisdiction to the
// visible text (never real routed-component data) and (b) never surfaces
// WHICH component routed where, so component-distinct scenarios (post vs
// music vs vfx to the same destination) rendered identical dropdown text.
// buildScenarioLabel (lib/format.jsx) is the one canonical producer
// scenario label adapter — every optimizer-classified structure now
// resolves through it (its own Advanced-tier prefix supersedes the
// duplicate prefix this function used to add locally); a non-optimizer
// structure (Single Jurisdiction winner, stacked program) is unaffected,
// unchanged.
function scenarioOptionLabel(structure) {
  if (OPTIMIZER_CLASSIFICATIONS.has(structure.classification)) {
    return buildScenarioLabel(structure);
  }
  const { flags, name, programLabel } = compactScenarioIdentity(structure);
  const label = flags ? `${flags} ${name}` : name;
  return programLabel ? `${label} — ${programLabel}` : label;
}

// Project FX strip — CineGlobe Overview FX Strip + Vertical Scrolling
// closeout extracted this screen's own inline buildLeaderFxItems() (and
// the whole rendered strip below) into the shared components/FXStrip.jsx
// + lib/todayCompute.js buildLeaderFxItems, now used by both Workspace
// and Overview — one FX engine, not two. See FXStrip.jsx's own header
// comment for the full contract.

function ScenarioCard({ structure, tier, rank, grossBudget, isLeading, isBestPriced, onSetLeading, onInspect, onCompare, onSelectSegment }) {
  const priced = structure.is_fully_priced;
  // 2x2 anchor/scenario composition (item 7): the canonical anchor/
  // current-production structure — isBaselineStructure/is_baseline,
  // the SAME field Overview's Card 1 reads, never a second derivation.
  const isAnchor = isBaselineStructure(structure);
  // All four card figures read from THIS scenario's canonical allocated
  // structure — gross from structure.gross_budget_usd (falls back to the
  // production-level prop only if a structure ever omits it), qualified
  // spend from its own per-segment QPE, incentive and NPC from its own
  // priced fields. No production-level or prototype figure is shown.
  const gross = structure.gross_budget_usd ?? grossBudget;
  // LOCAL_GLOBE_WIRING_CLOSEOUT (2026-09-21): every Optimizer-family
  // structure (built by the structural generator) carries segments: [] and
  // only populates component_allocations — confirmed live this silently
  // displayed "Qualified spend $0" on every Optimizer scenario card
  // (Lanes/Split), not a real zero. Sums the same real served field
  // (allocated_usd, the routed/qualified spend per component) this line
  // already sums for segments' qpe_usd — no new derivation, just the other
  // real field name this structure type actually carries.
  const qualifiedSpendRaw = structure.segments?.length
    ? structure.segments.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0)
    : (structure.component_allocations || []).reduce((sum, ca) => sum + (ca.allocated_usd || 0), 0);
  // Segment QPE is summed from the same real leaf accounts the production's
  // Gross budget is drawn from; when a structure excludes nothing, that sum
  // can land a few dollars off the source document's own stated Grand Total
  // (Gross budget) — economically immaterial rounding noise, not additional
  // or double-counted spend. Normalized via the shared global rule rather
  // than surfaced to producers (see normalizeTrivialVariance in lib/format).
  const qualifiedSpend = normalizeTrivialVariance(qualifiedSpendRaw, gross);
  const npc = structure.npc_with_adjustments_usd;

  const laneClass = (isLeading || isAnchor) ? "anchor" : priced ? "" : "draft";
  // Workspace Top-6/Data Truthfulness: "Set as leading"/LEADING is a
  // PRODUCER SELECTION, never CineGlobe's own ranked recommendation —
  // it must never borrow the "①" glyph, which implies canonical rank #1
  // regardless of the leading structure's real (possibly absent) rank.
  // A priced structure with no real canonical rank (rank?.rank is only
  // ever set for a directly-comparable, recommendation-eligible
  // candidate — see canonical_production_view.py's comparable/
  // review_required split) must never silently default to "①" either.
  // 2x2 anchor/scenario composition (item 7): a producer's own manual
  // Leading selection is always surfaced honestly (never silently
  // relabeled) — ANCHOR only shows when this is the canonical baseline
  // AND not also the producer's manual pick.
  //
  // Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 4:
  // ROLE vs QUALIFICATION STATE are two distinct concepts and must never
  // overwrite each other (task doctrine) — "PRICED" is a qualification
  // state, not a role, and using it as the ONLY thing every non-Anchor/
  // Leading/ranked card said was the actual regression: a discretionary/
  // preapproval-gated jurisdiction's genuinely lowest-priced candidate
  // read identically to every other unranked alternative, even though
  // its real conditional STATUS is already shown separately below (⚠ Discretionary /
  // preapproval required — see hasAdministrativeAllocationRisk). A real
  // rank still wins when the doctrine has established one (the circled
  // number); otherwise the single genuinely lowest-NPC unranked
  // candidate reads "BEST PRICED" (bestPricedCandidate — the SAME
  // selection the Hero/BudgetRail already use), and every other priced-
  // but-unranked structure reads "ALTERNATIVE" — never the bare
  // qualification word "PRICED" standing in for a role it isn't.
  const badge = isLeading
    ? "◈ LEADING"
    : isAnchor
      ? "◆ ANCHOR"
      : priced
        ? (rank?.rank ? (CIRCLED[rank.rank - 1] || `#${rank.rank}`) : (isBestPriced ? "BEST PRICED" : "ALTERNATIVE"))
        : "DRAFT";

  // Compact card identity (flag + full jurisdiction name + "Up to X%") —
  // the approved Workspace format. See compactScenarioIdentity in
  // lib/format.jsx; detailed program mechanics live in Inspector, not here.
  // OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22): an optimizer-
  // classified structure's headline name comes from buildScenarioLabel
  // (its own routed-component identity, e.g. "Post → Manitoba") instead —
  // flags/subtitle (rate) still come from compactScenarioIdentity, which
  // remains correct for those; only the jurisdiction-name portion changes.
  const { flags, name: compactName, subtitle } = compactScenarioIdentity(structure);
  const name = OPTIMIZER_CLASSIFICATIONS.has(structure.classification)
    ? buildScenarioLabel(structure)
    : compactName;
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
          {/* F#K item 3: same generic administrative/discretionary
              allocation-risk disclosure as Overview's cards and the Hero
              — a priced structure here can still be gated by award-
              authority discretion, competitive/capacity-limited
              allocation, or a mandatory preapproval step. Cross-page
              consistency (invariant H): reads the SAME warnings-derived
              signal, never a per-page re-derivation. */}
          {hasAdministrativeAllocationRisk(structure) && (
            <div className="wsx-row" style={{ color: "var(--amber)" }}>
              <span>⚠ Discretionary / preapproval required</span>
            </div>
          )}
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
  // Compare identity (Workspace Top-6/Data Truthfulness): the canonical
  // structure_id of whichever card's Compare was last clicked — never a
  // jurisdiction code, so two same-country/different-program structures
  // (e.g. Australia Location Offset vs Australia PDV Offset) are never
  // collapsed into one comparison target.
  const [compareStructureId, setCompareStructureId] = useState(null);
  // GLOBE_SINGLE_AND_OPTIMIZER_WIRING (2026-09-21): the Map/Split embedded
  // Globe previously kept its OWN local "jurisdictions"/"optimizer" mode,
  // entirely independent of the shared `workspaceMode` (destructured below)
  // that already drives the six-scenario-card rack — switching one never
  // moved the other, even though both live on this same screen. The Globe
  // now reads/writes `workspaceMode` directly (MODE_NORMAL === Single
  // Jurisdiction / "Jurisdictions"; MODE_OPTIMIZER === "Optimizer Overlay"),
  // so this is the one project-scoped mode Workspace and Globe share.
  const [globeHover, setGlobeHover] = useState(null);
  const {
    openInspector, inspector, closeInspector, setDocked,
    leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
    workspaceMode, setWorkspaceMode, getSlot6Selection, setSlot6Selection,
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
  // Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 4:
  // restore a meaningful producer-facing ROLE for priced structures that
  // have no canonical direct-comparability rank (rank?.rank absent — a
  // real, common state; see canonical_production_view.py's comparable/
  // review_required split) and are not Anchor/Leading. These used to all
  // collapse to the bare qualification-state word "PRICED", which is not
  // a role and does not distinguish, e.g. a jurisdiction's genuinely
  // lowest-NPC candidate from every other unranked alternative. Reuses
  // the SAME bestPricedCandidate() selection the Hero/BudgetRail already
  // use — never a second, independently-maintained "which one is best
  // priced" computation.
  const bestPricedStructureId = useMemo(
    () => (allocated ? bestPricedCandidate(allocated)?.structure_id ?? null : null),
    [allocated],
  );
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode, sceneSignature } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: workspaceMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, workspaceMode, leadingStructureId, selectedJurisdiction],
  );
  // FVD_GLOBE_RENDERER_CORRECTION (2026-09-21) — same Phase 5 diagnostic
  // contract as ProjectGlobe.jsx, same window key: the embedded Map/Split
  // Globe and the full-page Project Globe must be provably the SAME
  // scene-data contract (buildGlobeView), so this intentionally shares the
  // identical diagnostic global rather than a second, screen-specific one.
  useEffect(() => {
    if (import.meta.env.DEV) window.__cineGlobeSceneSignature = sceneSignature;
  }, [sceneSignature]);
  // Workspace scenario-mode data wiring: slot 6's producer override is
  // stored per (project, mode) in shared AppState so switching modes
  // restores each mode's own prior choice (see AppState.jsx). The six-
  // slot composition itself is selectSixSlots() — Current Location (never
  // mode-filtered) + the top four mode-admissible scenarios + slot 6.
  const projectId = data?.production?.project_id ?? null;
  const slot6Override = getSlot6Selection(projectId, workspaceMode);
  const { cols, dropdownOptions: overflow } = useMemo(
    () => {
      const { slots, dropdownOptions } = selectSixSlots(allocated, workspaceMode, slot6Override);
      return { cols: slots, dropdownOptions };
    },
    [allocated, workspaceMode, slot6Override],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, legal, economics } = data;
  const openGrey = (legal.grey_areas_current || []).filter((g) => g.status === "open");
  const openCount = (pkg.missing_inputs?.length || 0) + openGrey.length;
  const leadingStructure = activeStructure(allocated, leadingStructureId);
  const leadingId = leadingStructure?.structure_id ?? null;
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
  // PROJECT_UI_DATA_INTEGRITY (2026-09-21), fourth FX cell: when NEITHER
  // a manual Leading selection NOR a canonical bestPricedCandidate exists
  // (F#K Valentine's Day's real state — no directly-comparable winner),
  // the cell used to disappear entirely (buildLeaderFxItems(economics,
  // null, ...) returns []). Extends the SAME existing fallback chain,
  // never a fabricated recommendation: (3) the active selected scenario
  // for the current Normal/Optimizer mode — cols[1], the top mode-
  // admissible scenario selectSixSlots() already ranks into slot 2 —
  // then (4) Current Location itself (cols[0], the production's own
  // anchor), which always exists. `dynamicFxStructureKind` distinguishes
  // all four states for FXStrip's own tag text — never re-derived there.
  const bestPriced = bestPricedCandidate(allocated);
  const dynamicFxStructure = leadingStructure || bestPriced || cols[1] || cols[0];
  const dynamicFxIsLeading = !!leadingStructure;
  // True only on the FINAL fallback rung — the production's own Current
  // Location, reached when nothing else (Leading, bestPriced, or an
  // active mode-admissible scenario) resolved to a real structure. Rung
  // tracked explicitly rather than compared by identity afterward, so an
  // anchor that ALSO happens to be the real bestPricedCandidate is still
  // correctly labeled "Top Priced", never miscategorized as a fallback.
  const dynamicFxIsCurrentLocation = !dynamicFxIsLeading && !bestPriced && !cols[1];

  // Collapsed-rail status dots — hot for any money-bearing / blocking item.
  const dots = [
    ...openGrey.map(() => "hot"),
    ...(pkg.missing_inputs || []).map((m) => (m.blocking ? "hot" : "")),
  ].slice(0, 8);

  const contingencyByAccount = allocated?.contingency || {};
  // LOCAL_GLOBE_WIRING_CLOSEOUT (2026-09-21): resolveSegmentDetail falls
  // back to component_allocations for structures the structural generator
  // built (every Optimizer family), which never populate `segments` at all
  // — confirmed live: clicking any Optimizer jurisdiction/structure here
  // previously opened no Inspector (segments empty, recommendation null).
  function handleGlobeClick(pt) {
    const code = pt.jurisdictionCode || pt.id;
    setSelectedJurisdiction(code);
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    const seg = resolveSegmentDetail(s, code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label, contingencyByAccount });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }
  // CODEX_FG-002 (2026-09-21): the card's "Inspect" action opens that whole
  // structure's own complete identity via buildCandidateDetail — the same
  // shared adapter ProjectGlobe.jsx's selectStructure uses — never an
  // arbitrarily chosen first participant's segment. onSelectSegment (below)
  // stays scoped to one row/jurisdiction on purpose.
  function handleSelectStructure(structure) {
    if (structure.recommendation) openInspector("structure-recommendation", structure.recommendation);
    else openInspector("candidate-structure", buildCandidateDetail(structure));
  }
  function handleSelectSegment(structure, code) {
    const seg = resolveSegmentDetail(structure, code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: structure.label, contingencyByAccount });
  }

  return (
    <div className="wsx-screen">
      {/* Project FX strip — immediately below the shared production tabs
          (rendered by ProjectHeader, outside this component) and
          immediately above the Lanes/Map/Split mode row. Now the shared
          components/FXStrip.jsx engine (CineGlobe Overview FX Strip +
          Vertical Scrolling closeout) — Overview mounts the identical
          component. */}
      <FXStrip
        economics={economics} structure={dynamicFxStructure}
        structureIsLeading={dynamicFxIsLeading} structureIsCurrentLocation={dynamicFxIsCurrentLocation}
      />

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

        {/* Station — card rack or globe. Wide station: one control row —
            mode toggle (count stacked beneath it) at left, Lanes/Map/Split
            centered, Other Scenarios at right. Constrained station (narrow
            viewport, or Question Stack/Inspector open shrinking this
            station's own width): two rows — see .wsx-station-head's
            @container rule in screens.css. The Jurisdictions/Optimizer
            Overlay toggle is secondary to the Globe itself and lives
            docked to the globe pane (see wsx-g-modetoggle below), not
            here. */}
        <div className="wsx-station">
          <div className="wsx-station-head">
            {/* Workspace scenario-mode data wiring: smallest functional
                Normal/Optimizer control, reusing the existing .wsx-viewtabs
                button style (Lanes/Map/Split's own) rather than a new
                visual system. */}
            <div className="wsx-station-head-spacer wsx-scenario-mode">
              <div className="wsx-viewtabs">
                <button className={workspaceMode === MODE_NORMAL ? "active" : ""} onClick={() => setWorkspaceMode(MODE_NORMAL)}>Single Jurisdiction</button>
                <button className={workspaceMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setWorkspaceMode(MODE_OPTIMIZER)}>Optimizer</button>
              </div>
            </div>
            {/* PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION (2026-09-22): a
                truthful count of the DISTINCT producer-facing optimizer
                scenarios this mode's rack/dropdown/Globe surfaces draw from
                — `allocated.producer_optimizer_options_total`
                (canonical_production_view.py), never the raw search-
                iteration count (`optimizer_candidates_total`, kept available
                for audit/debug evidence only), the exhaustive canonical
                scenario count (`optimizer_scenarios_total`), or the length of
                whatever happens to render.
                WORKSPACE_RESPONSIVE_CONTROL/RACK_CLOSEOUT (2026-09-23): now
                its own grid item (.wsx-scenario-count, no inline
                whiteSpace:"nowrap") so it lays out on its own row and can
                wrap instead of ever sharing a line with Lanes/Map/Split or
                Other Scenarios. Compact producer copy; the 0-value Formal
                tier is omitted rather than printed as "0 formal". */}
            {workspaceMode === MODE_OPTIMIZER && allocated?.producer_optimizer_options_total != null && (() => {
              const total = allocated.producer_optimizer_options_total;
              return (
                <span className="wsx-scenario-count">
                  {total} practical optimizer option{total === 1 ? "" : "s"} · each saves more than $100K
                </span>
              );
            })()}
            <div className="wsx-viewtabs">
              {MODES.map((m) => (
                <button key={m.key} className={mode === m.key ? "active" : ""} onClick={() => setMode(m.key)}>
                  {m.label}
                </button>
              ))}
            </div>
            {/* Other Scenarios — navigates among structures the optimizer
                already generated but that don't currently occupy a visible
                lane, WITHIN the active scenario mode; it swaps slot 6's
                contents, it never creates a new structure and never
                reruns the optimizer. */}
            {mode !== "map" && overflow.length > 0 ? (
              <div className="wsx-other-scenarios">
                <label htmlFor="wsx-swap">Other scenarios</label>
                <select
                  id="wsx-swap"
                  className="field-select"
                  value={slot6Override ?? ""}
                  onChange={(e) => setSlot6Selection(projectId, workspaceMode, e.target.value)}
                >
                  <option value="">— {(() => { const last = cols[cols.length - 1]; return last ? scenarioOptionLabel(last) : "—"; })()} —</option>
                  {overflow.map((s) => (
                    <option key={s.structure_id} value={s.structure_id}>{scenarioOptionLabel(s)}</option>
                  ))}
                </select>
              </div>
            ) : <div aria-hidden="true" className="wsx-other-scenarios-spacer" />}
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
                  isBestPriced={s.structure_id === bestPricedStructureId}
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
                    isBestPriced={leadingStructure.structure_id === bestPricedStructureId}
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
                    <button className={workspaceMode === MODE_NORMAL ? "active" : ""} onClick={() => setWorkspaceMode(MODE_NORMAL)}>Single Jurisdiction</button>
                    <button className={workspaceMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setWorkspaceMode(MODE_OPTIMIZER)}>Optimizer</button>
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
                      isBestPriced={s.structure_id === bestPricedStructureId}
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
                    <button className={workspaceMode === MODE_NORMAL ? "active" : ""} onClick={() => setWorkspaceMode(MODE_NORMAL)}>Single Jurisdiction</button>
                    <button className={workspaceMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setWorkspaceMode(MODE_OPTIMIZER)}>Optimizer</button>
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
