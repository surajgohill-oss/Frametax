import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { commitLeadingStructure } from "../../lib/leadingSelection";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, compactScenarioIdentity, buildScenarioLabel, buildRouteOptionDetail, hasAdministrativeAllocationRisk } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import { CoproductionFactsList, JurisdictionUniversePanel, PolicySuppressedReferences } from "../../components/JurisdictionUniverse";
import { coproductionNeedsFactsLabel } from "../../lib/jurisdictionUniverse";
import Globe3D from "../../components/Globe3D";
import GlobeHoverCard from "../../components/GlobeHoverCard";
import { alternativeLabel, fitTag, structureStatusDetail } from "../../lib/alternativeLabels";
import { buildGlobeView, structureTier, activeStructure, resolveSegmentDetail, buildCandidateDetail, buildOpportunityDetail, buildRejectedDetail, OPTIMIZER_FAMILY_LABEL, PRACTICALITY_TIER_LABEL } from "../../lib/globeData";
import { bestPricedCandidate } from "../../lib/bestPricedCandidate";
import { readIncentivePotential } from "../../lib/incentivePotential";
import EconomicWell from "../../components/EconomicWell";
import { isBaselineStructure, qpeOf, classifyRouteTies } from "../../lib/productionOptions";
import { MODE_NORMAL, MODE_OPTIMIZER, optimizerProjection, resolveRequestedWorkspaceMode, selectSixSlots } from "../../lib/workspaceScenarioMode";
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
  "optimizer-opportunity": "Opportunity",
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
    // GW-OI-004: the dropdown specifically (never the card headline, which
    // keeps buildScenarioLabel's existing compact form) also discloses the
    // real practicality tier and each leg's allocated amount — hundreds of
    // routes previously read as indistinguishable permutations with no way
    // to see why each additional jurisdiction/component is present.
    const tier = PRACTICALITY_TIER_LABEL[structure.practicality_tier];
    const detail = buildRouteOptionDetail(structure);
    return tier && structure.practicality_tier !== "ADVANCED_MULTI_JURISDICTION" ? `${tier} · ${detail}` : detail;
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

function ScenarioCard({ structure, tier, rank, grossBudget, isLeading, isBestPriced, optimizerLeadingId = null, onSetLeading, onInspect, onCompare, onSelectSegment }) {
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
  // GW-OI-001: qualifiedSpend now renders the exact result of the shared
  // qpeOf() adapter (productionOptions.js) — the same segment-first/
  // component-allocation-fallback precedence Overview's IncentiveIntelligence
  // uses. Previously this was computed locally (a duplicate of qpeOf's own
  // logic) and then passed through normalizeTrivialVariance(qualifiedSpendRaw,
  // gross), which silently collapsed a canonical QPE within $5 of gross to
  // gross itself — for Little Utopia this replaced the real, correct
  // component-allocation sum $4,364,395 with $4,364,393, while Overview and
  // Inspector (which never normalized) correctly showed $4,364,395. A $2
  // source-authored variance between allocated QPE and declared gross is
  // real canonical data, not rounding noise to be hidden — never normalized
  // away here.
  const qualifiedSpend = qpeOf(structure);
  const npc = structure.npc_with_adjustments_usd;
  // MAXIMUM-POTENTIAL INCENTIVE CONTRACT (2026-10-01): confirmed vs. maximum-supported
  // economics are backend-served fields (services/incentive_potential.py), read verbatim
  // through the one shared reader the Inspector also uses -- nothing is computed here.
  const pot = readIncentivePotential(structure);

  // CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 8:
  // an Evaluated Alternative shown in a six-card slot (backfilled when its tier
  // has fewer than two Recommended candidates) is a real, producer-selectable
  // reference structure -- visually muted (existing `.reference` styling token),
  // never conflated with "not yet priced" (`.draft`) or Leading/Anchor.
  const isReference = priced && !isLeading && !isAnchor && structure.recommendation_status === "EVALUATED_ALTERNATIVE";
  const laneClass = (isLeading || isAnchor) ? "anchor" : isReference ? "reference" : priced ? "" : "draft";
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
  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): an Optimizer-family
  // structure (identified the same way the savings-delta row below already
  // does — recommendation_status is only ever present on optimizer_scenarios
  // entries, never on a Jurisdictions-layer best_per_jurisdiction winner)
  // now reads its badge from the real recommendation_status field, never
  // from rank/position. This card can now legitimately hold an Evaluated
  // Alternative in a leading/slot-6 position (selectSixSlots backfills slots
  // 2-6 from evaluated alternatives once real recommended options run out —
  // see workspaceScenarioMode.js) — the controlling contract is explicit:
  // "Never make an evaluated alternative appear recommended." Before this,
  // EVERY Optimizer card fell through to the generic rank/BEST PRICED/
  // ALTERNATIVE badge (rank is only ever populated for the Single
  // Jurisdiction-family overall ranking, so every Optimizer card read
  // "ALTERNATIVE" regardless of its real recommendation status) — a real
  // conflation between Single Jurisdiction's generic priced-but-unranked
  // badge and Optimizer's own recommendation-status vocabulary. Single
  // Jurisdiction cards (recommendation_status always absent) are completely
  // unaffected — same rank/BEST PRICED/ALTERNATIVE/DRAFT badge as before.
  // CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 8:
  // a reference card's BADGE stays short (matching the existing RECOMMENDED/
  // ALTERNATIVE/BEST PRICED badge-length convention -- card dimensions are never
  // changed by this pass) while the applicable specific reason (below the
  // recommendation hurdle, dominated by a simpler structure, or an added
  // jurisdiction's marginal shortfall) renders as its own explanatory row further
  // down the card (see referenceExplanationText below) -- never the bare,
  // ambiguous "EVALUATED ALTERNATIVE" this previously showed, and never silently
  // reading as Recommended/Leading.
  const referenceExplanationText = (reason) => {
    if (reason === "DOMINATED_BY_LOWER_COMPLEXITY_STRUCTURE") return "Dominated by a simpler structure";
    if (typeof reason === "string" && reason.startsWith("JURISDICTION_") && reason.endsWith("_MARGINAL_BENEFIT_BELOW_THRESHOLD")) {
      return "Added jurisdiction below the $100,000 marginal hurdle";
    }
    if (typeof reason === "string" && reason.startsWith("JURISDICTION_") && reason.endsWith("_MARGINAL_BENEFIT_BELOW_THRESHOLD_PROVEN_UPPER_BOUND")) {
      return "Added jurisdiction proven below the $100,000 marginal hurdle (upper bound)";
    }
    if (typeof reason === "string" && reason.startsWith("JURISDICTION_") && reason.endsWith("_MARGINAL_BENEFIT_UNCOMPUTED")) {
      return "Marginal benefit unverified — exact comparison could not be computed";
    }
    if (typeof reason === "string" && reason.startsWith("NO_PRICED_PARENT_WITHOUT_")) {
      return "Marginal benefit unverified — no priced comparison available";
    }
    return "Reference alternative — below the leading-alternative hurdle";
  };
  const badge = isLeading
    ? "◈ LEADING"
    : isAnchor
      ? "◆ ANCHOR"
      : priced
        ? (structure.recommendation_status
            ? alternativeLabel(structure, optimizerLeadingId)
            : (rank?.rank ? (CIRCLED[rank.rank - 1] || `#${rank.rank}`) : (isBestPriced ? "BEST PRICED" : "ALTERNATIVE")))
        : "DRAFT";
  // Structural family — real backend `classification`, never a substitute
  // for the recommendation-status badge above. Only ever present on an
  // Optimizer-family structure (OPTIMIZER_FAMILY_LABEL has no Single
  // Jurisdiction entries), so this renders nothing extra for those cards.
  // GW-OI-002: practicality tier is a SEPARATE real backend field
  // (practicality_tier) — always shown alongside family, never implied by
  // it (family "Hybrid Anchor + Component" says nothing about whether this
  // specific scenario is Practical/Formal/Advanced tier).
  const familyLabel = OPTIMIZER_FAMILY_LABEL[structure.classification] ?? null;
  const tierLabel = PRACTICALITY_TIER_LABEL[structure.practicality_tier] ?? null;

  // Compact card identity (flag + full jurisdiction name + "Up to X%") —
  // the approved Workspace format. See compactScenarioIdentity in
  // lib/format.jsx; detailed program mechanics live in Inspector, not here.
  // OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22): an optimizer-
  // classified structure's headline name comes from buildScenarioLabel
  // (its own routed-component identity, e.g. "Post → Manitoba") instead —
  // flags/subtitle (rate) still come from compactScenarioIdentity, which
  // remains correct for those; only the jurisdiction-name portion changes.
  const { flags, name: compactName } = compactScenarioIdentity(structure);
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
          {/* Title: up to two lines, full title (and the real family / tier for an optimizer structure) in the tooltip.
              No rate or percentage on the card face -- those stay in the Inspector. */}
          <div
            className="wsx-nm"
            title={[flags ? `${flags} ${name}` : name, familyLabel ? [familyLabel, tierLabel].filter(Boolean).join(" · ") : null].filter(Boolean).join(" — ")}
          >{flags ? `${flags} ${name}` : name}</div>
          <span className="wsx-badge" title={isReference ? referenceExplanationText(structure.recommendation_reason) : undefined}>{badge}</span>
        </div>
      </div>

      {priced ? (
        <>
          {pot ? (
            <>
              {/* ECONOMIC WELL v2: shared with Overview's cards (components/EconomicWell.jsx). Gross budget is not
                  repeated here; qualified spend is quiet subordinate context below the well, never before NPC. */}
              <EconomicWell pot={pot} awardRisk={hasAdministrativeAllocationRisk(structure)} />
              <div className="wsx-qs"><span>Qualified spend</span><span><Money value={qualifiedSpend} bare /></span></div>
            </>
          ) : (
            <div className="wsx-rows">
              <div className="wsx-row"><span>Qualified spend</span><span><Money value={qualifiedSpend} bare /></span></div>
              <div className="wsx-row"><span>Gross incentive</span><span className="incentive"><Money value={structure.selected_incentive_usd} bare /></span></div>
              <div className="wsx-row net"><span>Net production cost</span><span><Money value={npc} bare /></span></div>
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
          <button className="wsx-lead" onClick={(e) => { e.stopPropagation(); onSetLeading(structure); }}>◈ Set as leading</button>
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
// Canonical-totals fix (2026-09-30): this HUD used to report
// `allocated.structures.length` (the bounded ~100-row RETAINED detail page,
// per PROJECT_RULES' PERSISTENCE CARDINALITY RULE -- never the true total)
// as "N scenarios", and the CURRENTLY SELECTED route's own leg count as if
// it were the number of available structure routes ("N structure routes").
// `nScenarios` is now the real canonical total for the active mode
// (Optimizer: optimizerProjection(allocated).executableTotal; Single
// Jurisdiction: the count of real priced best_per_jurisdiction winners).
// `nArcsInRoute` keeps its real meaning but is labeled unambiguously as
// belonging to the one selected route on screen, never the total universe.
function GlobeChrome({ productionName, nScenarios, nMarkers, nArcsInRoute }) {
  return (
    <div className="wsx-g-hud">
      <b>Project globe · {productionName}</b>
      {nScenarios} executable structure{nScenarios === 1 ? "" : "s"} total · {nMarkers} jurisdiction marker{nMarkers === 1 ? "" : "s"} shown · selected route: {nArcsInRoute} leg{nArcsInRoute === 1 ? "" : "s"}
    </div>
  );
}

export default function Workspace() {
  const { projectId: routeProjectId } = useParams();
  const { data, error, loading, refetch } = useCineGlobe(routeProjectId);
  const location = useLocation();
  const navTab = location.state?.tab;
  // "See all N" mode preservation (Overview.jsx's OptimizerCategorySummary
  // onOpenComplete): a URL query param, not navigation state, specifically
  // so a direct reload/bookmark of this exact URL also restores the
  // requested Single Jurisdiction / Optimizer mode — never silently
  // reverting to whatever workspaceMode last happened to be in memory.
  const requestedMode = resolveRequestedWorkspaceMode(location.search);

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
  // Shared-hover-card fix (2026-09-30): Map/Split used to render their own
  // shallow ad-hoc tooltip (jurisdictionName/statusLabel/role only) instead
  // of the same GlobeHoverCard Overview.jsx and ProjectGlobe.jsx already
  // use — same pattern as those two screens: hoverRect anchors the card
  // near the hovered marker, canvasRef is the nearest positioned ancestor.
  const [globeHoverRect, setGlobeHoverRect] = useState(null);
  const globeCanvasRef = useRef(null);
  const {
    openInspector, inspector, closeInspector, setDocked,
    leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
    workspaceMode, setWorkspaceMode, getSlot6Selection, setSlot6Selection,
  } = useAppState();

  // "See all N" mode preservation: apply the requested mode from the URL
  // once (on mount / whenever the param itself changes — e.g. following a
  // second "See all" link without unmounting Workspace). Never applied
  // when the param is absent, so a plain /workspace visit or a manual
  // Single Jurisdiction / Optimizer click is never overridden.
  useEffect(() => {
    if (requestedMode) setWorkspaceMode(requestedMode);
  }, [requestedMode, setWorkspaceMode]);

  // "Set as Leading": the shared AppState selection plus the project-scoped persisted commit (lib/leadingSelection.js),
  // which every Globe surface reads. Presentation/portfolio state only -- never an evaluation.
  const handleSetLeading = useCallback((structure) => {
    setLeadingStructureId(structure.structure_id);
    commitLeadingStructure(data?.production?.project_id, structure);
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
  const { cols, dropdownOptions: overflow, dropdownEvaluatedAlternatives, dropdownOpportunities, tiedStructureIds } = useMemo(
    () => {
      const { slots, dropdownOptions, dropdownEvaluatedAlternatives: evalAlts, dropdownOpportunities: opps, tiedStructureIds: ties } =
        selectSixSlots(allocated, workspaceMode, slot6Override);
      return { cols: slots, dropdownOptions, dropdownEvaluatedAlternatives: evalAlts, dropdownOpportunities: opps, tiedStructureIds: ties || {} };
    },
    [allocated, workspaceMode, slot6Override],
  );

  // GW-OI-005: the Evaluated Alternatives dropdown group is where hundreds
  // of routes sharing an exact-NPC coincidence live — classifyRouteTies
  // (productionOptions.js) groups them honestly: a group that shares every
  // real economic figure (not just NPC) collapses to one representative
  // option + "N equivalent route variants" rather than N visually
  // indistinguishable rows; a group that merely ties on NPC while differing
  // in QPE/incentive/status stays fully separate, each labeled "NPC tie" —
  // never silently merged. Every real route/economic_identity remains
  // selectable; nothing is deleted from the underlying list.
  const dropdownEvaluatedAlternativesGrouped = useMemo(() => {
    const list = dropdownEvaluatedAlternatives || [];
    const tieGroups = classifyRouteTies(list);
    const collapsedIds = new Set();
    const entries = [];
    for (const g of tieGroups) {
      if (g.type === "EQUIVALENT_ROUTE_VARIANTS") {
        for (const m of g.members) collapsedIds.add(m.structure_id);
        entries.push({ structure: g.representative, suffix: g.members.length > 1 ? ` (+${g.members.length - 1} equivalent route variant${g.members.length - 1 === 1 ? "" : "s"})` : "" });
      } else {
        for (const v of g.variants) {
          for (const m of v.members) collapsedIds.add(m.structure_id);
          const equivSuffix = v.equivalentCount > 1 ? ` +${v.equivalentCount - 1} equivalent` : "";
          entries.push({ structure: v.representative, suffix: ` (NPC tie${equivSuffix})` });
        }
      }
    }
    for (const s of list) {
      if (!collapsedIds.has(s.structure_id)) entries.push({ structure: s, suffix: "" });
    }
    // Fit-aware presentation order, read from the SERVED fit_priority (stable sort): grouping
    // by route tie must not push weak / unconfirmed references above fit-confirmed ones.
    entries.sort((a, b) => (a.structure.fit_priority ?? 2) - (b.structure.fit_priority ?? 2));
    return entries;
  }, [dropdownEvaluatedAlternatives]);

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
  // Canonical Globe/HUD scenario total for the active mode — never the
  // bounded allocated.structures.length retained-page count (see
  // GlobeChrome's own comment above).
  // First canonical RECOMMENDED option (null when none passes the hurdle) -- drives LEADING vs STRONG ALTERNATIVE.
  const optimizerLeadingId = optimizerProjection(allocated).recommended[0]?.structure_id ?? null;
  const canonicalScenarioTotal = workspaceMode === MODE_OPTIMIZER
    ? optimizerProjection(allocated).executableTotal
    : Object.keys(allocated?.best_per_jurisdiction || {}).length;
  // Truthful HUD (2026-09-30): `points` mixes the full categorized-universe
  // markers (one per real jurisdiction, aggregated status) with the
  // selected route's own exact-structure markers (sourceStructure set) —
  // confirmed live, e.g. Little Utopia renders 99 universe markers
  // alongside its 2-node selected route. Reporting only `canonicalScenarioTotal`
  // ("168 scenarios") on a canvas showing 99 dots plus one 2-leg route
  // implied every structure had its own marker. Counted separately so the
  // HUD never conflates "how many executable structures exist" with "how
  // many markers are actually drawn."
  // Every point (universe AND exact-route) carries `sourceStructure` (see
  // globeData.js's buildCountryPoints), so that field alone can't
  // distinguish them -- `isAggregatedUniverseMarker` is the real signal.
  // In Single Jurisdiction mode there is no route/universe split at all, so
  // every point is correctly counted as a marker.
  const globeMarkerCount = workspaceMode === MODE_OPTIMIZER
    ? points.length // every Optimizer marker is a jurisdiction marker (route jurisdictions keep their own marker)
    : points.length;

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
    // SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23): Single Jurisdiction mode
    // (Map/Split's embedded globe, same contract as ProjectGlobe.jsx's own
    // selectJurisdiction) resolves the EXACT canonical
    // best_per_jurisdiction[code] winner directly, opening the same full
    // structure-level Inspector every Optimizer card already uses — never
    // structuresByCode[0], and never the single-segment view that silently
    // dropped every program past the first in a real same-jurisdiction stack.
    if (workspaceMode === MODE_NORMAL) {
      const winner = allocated?.best_per_jurisdiction?.[code];
      if (!winner) return;
      openInspector("candidate-structure", buildCandidateDetail(winner));
      return;
    }
    // EXACT-IDENTITY FIX (2026-09-30): `structuresByCode.get(code)[0]` picks
    // the FIRST structure touching this jurisdiction across the whole
    // production — not necessarily the ONE structure whose routing is
    // actually rendered on screen right now (buildOptimizerPathway draws
    // exactly one structure's pathway at a time). Every point belonging to
    // that exact rendered route now carries `sourceStructure` directly
    // (globeData.js) — the SAME field name/shape ProjectGlobe.jsx's own
    // click handler resolves exact identity from, so the two screens can
    // never disagree about which structure a click on the displayed route
    // opens. A universe/aggregated-jurisdiction marker carries no
    // `sourceStructure` and correctly falls back to the jurisdiction-level
    // winner below.
    const s = pt.sourceStructure || (structuresByCode.get(code) || [])[0];
    if (!s) return;
    // GLOBE_WIRING_REMEDIATION (2026-10-01): a Needs-More-Facts / blocked
    // jurisdiction marker opens ITS OWN canonical row (opportunity /
    // blocked-with-reason Inspector), never an empty/foreign segment view.
    // AMBER now also marks an EXECUTABLE alternative that is conditional on missing location-capability data; that is
    // a structure (candidate Inspector), never a "co-production opportunity".
    if (pt.tier === "amber") {
      if (s.is_fully_priced) openInspector("candidate-structure", buildCandidateDetail(s));
      else openInspector("optimizer-opportunity", buildOpportunityDetail(s));
      return;
    }
    if (pt.tier === "red") { openInspector("optimizer-rejection", buildRejectedDetail(s)); return; }
    const seg = resolveSegmentDetail(s, code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label, ...structureStatusDetail(s, optimizerLeadingId), contingencyByAccount });
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
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: structure.label, ...structureStatusDetail(structure, optimizerLeadingId), contingencyByAccount });
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
              <QualificationPanel people={data.people} facts={data.facts} script={pkg.script} refetch={refetch} projectId={projectId} />
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
            {/* GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22):
                CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md found the
                prior "N practical optimizer options · each saves more than
                $100K" copy read `producer_optimizer_options_total` ALONE —
                which was 0 for all four real productions once that field
                became a hard filter, so this disclosure silently vanished
                (`!= null` still passed, `total` was just 0) everywhere. The
                complete, never-filtered executable total is shown first,
                with recommended/evaluated-alternative counts as sub-detail
                so a truthful "0 recommended" is still legible next to a
                real, nonzero executable total — never the reverse.
                WORKSPACE_RESPONSIVE_CONTROL/RACK_CLOSEOUT (2026-09-23): its
                own grid item (.wsx-scenario-count, no inline
                whiteSpace:"nowrap") so it lays out on its own row and can
                wrap instead of ever sharing a line with Lanes/Map/Split or
                Other Scenarios. */}
            {/* GW-OI-003: "Showing N of M" — the six-card rack is a compact
                FEATURED working set, never the complete optimizer/
                jurisdiction universe; this makes that explicit for both
                modes (previously Single Jurisdiction mode showed no count
                at all, and Optimizer mode's own count line never stated
                how many of the total were actually visible in the rack). */}
            {workspaceMode === MODE_OPTIMIZER && allocated?.optimizer_executable_total != null && (() => {
              const executableTotal = allocated.optimizer_executable_total;
              const recommendedTotal = allocated.recommended_optimizer_options_total ?? 0;
              const evaluatedTotal = allocated.evaluated_optimizer_alternatives_total ?? 0;
              const opportunitiesTotal = allocated.optimizer_opportunities_requiring_facts_total ?? 0;
              const fitCounts = allocated.optimizer_production_fit_counts ?? null;
              const shownCount = cols.length;
              return (
                <span className="wsx-scenario-count">
                  Showing {shownCount} of {executableTotal} executable option{executableTotal === 1 ? "" : "s"} · {recommendedTotal} leading/strong alternative{recommendedTotal === 1 ? "" : "s"} · {evaluatedTotal} reference alternative{evaluatedTotal === 1 ? "" : "s"}
                  {opportunitiesTotal > 0 ? ` · ${coproductionNeedsFactsLabel(opportunitiesTotal)}` : ""}
                  {/* PRODUCTION-FIT (2026-10-01): exact counts served by the backend
                      (optimizer_production_fit_counts); never recomputed here. */}
                  {fitCounts ? ` · location fit: ${fitCounts.fit_confirmed} confirmed · ${fitCounts.fit_unconfirmed} unconfirmed · ${fitCounts.weak_fit} low-fit` : ""}
                </span>
              );
            })()}
            {workspaceMode === MODE_NORMAL && allocated?.best_per_jurisdiction && (() => {
              const winnerTotal = Object.values(allocated.best_per_jurisdiction).filter(Boolean).length;
              const shownCount = cols.length;
              return (
                <span className="wsx-scenario-count">
                  Showing {shownCount} of {winnerTotal} jurisdiction winner{winnerTotal === 1 ? "" : "s"}
                </span>
              );
            })()}
            {workspaceMode === MODE_OPTIMIZER && (
              <>
                <CoproductionFactsList allocated={allocated} openInspector={openInspector} />
                <PolicySuppressedReferences allocated={allocated} openInspector={openInspector} />
              </>
            )}
            {workspaceMode === MODE_NORMAL && (
              <JurisdictionUniversePanel allocated={allocated} openInspector={openInspector} onSelect={setSelectedJurisdiction} />
            )}
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
                reruns the optimizer.
                GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22): in
                Optimizer mode, remaining recommended options, evaluated
                alternatives, and Needs-More-Facts opportunities are three
                separately labeled <optgroup> sections — never merged into
                one undifferentiated list, and Needs More Facts options are
                rendered disabled (never selectable as slot 6 / leading —
                see selectSixSlots' own slot6Candidates, which already
                excludes them; disabled here is belt-and-suspenders so a
                stray option can never be chosen even if this markup is
                ever copied elsewhere). */}
            {mode !== "map" && (overflow.length > 0 || (dropdownEvaluatedAlternatives?.length > 0) || (dropdownOpportunities?.length > 0)) ? (
              <div className="wsx-other-scenarios">
                <label htmlFor="wsx-swap">Other scenarios</label>
                <select
                  id="wsx-swap"
                  className="field-select"
                  value={slot6Override ?? ""}
                  onChange={(e) => setSlot6Selection(projectId, workspaceMode, e.target.value)}
                >
                  <option value="">— {(() => { const last = cols[cols.length - 1]; return last ? scenarioOptionLabel(last) : "—"; })()} —</option>
                  {overflow.length > 0 && (
                    <optgroup label={workspaceMode === MODE_OPTIMIZER ? "Leading / Strong Alternatives" : "Other scenarios"}>
                      {overflow.map((s) => (
                        <option key={s.structure_id} value={s.structure_id}>{scenarioOptionLabel(s)}</option>
                      ))}
                    </optgroup>
                  )}
                  {workspaceMode === MODE_OPTIMIZER && dropdownEvaluatedAlternativesGrouped.length > 0 && (
                    <optgroup label="Reference Alternatives">
                      {dropdownEvaluatedAlternativesGrouped.map(({ structure: s, suffix }) => (
                        <option key={s.structure_id} value={s.structure_id}>{scenarioOptionLabel(s)}{suffix}{fitTag(s)}</option>
                      ))}
                    </optgroup>
                  )}
                  {workspaceMode === MODE_OPTIMIZER && dropdownOpportunities?.length > 0 && (
                    // Never routed through scenarioOptionLabel/buildScenarioLabel — both are
                    // built for PRICED, component-routed structures; an unresolved co-production/
                    // multilateral opportunity has no component_allocations. The backend's own
                    // already-humanized `label` (e.g. "Greece — Eurimages multilateral
                    // co-production opportunity") is the real, accurate producer-facing text.
                    <optgroup label="Needs More Facts">
                      {dropdownOpportunities.map((s) => (
                        <option key={s.structure_id} value="" disabled>{s.label || "Needs more facts"}</option>
                      ))}
                    </optgroup>
                  )}
                </select>
              </div>
            ) : <div aria-hidden="true" className="wsx-other-scenarios-spacer" />}
          </div>

          {mode === "lanes" && (
            <div className="wsx-rack">
              {cols.map((s) => (
                <ScenarioCard
                  optimizerLeadingId={optimizerLeadingId}
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
                {/* BLANK-MAP-PANEL FIX (2026-09-30): this rendered nothing
                    at all whenever no producer-set Leading structure
                    existed — the common default case — leaving the fixed
                    360/300px economics column empty beside the Globe.
                    Falls back to the SAME canonical, already-computed
                    dynamicFxStructure chain the FX strip above uses
                    (Leading -> bestPriced -> top mode-admissible scenario
                    -> Current Location) — never a second, independently
                    reranked selection, and never blank while any real
                    structure exists. */}
                {dynamicFxStructure && (
                  <ScenarioCard
                  optimizerLeadingId={optimizerLeadingId}
                    key={dynamicFxStructure.structure_id}
                    structure={dynamicFxStructure}
                    tier={structureTier(dynamicFxStructure, rankById)}
                    rank={rankById.get(dynamicFxStructure.structure_id)}
                    grossBudget={production.gross_budget_usd}
                    isLeading={dynamicFxStructure.structure_id === leadingId}
                    isBestPriced={dynamicFxStructure.structure_id === bestPricedStructureId}
                    onSetLeading={handleSetLeading}
                    onInspect={handleSelectStructure}
                    onCompare={(s) => { setCompareStructureId(s.structure_id); setQOpen(true); setQTab("recommendations"); }}
                    onSelectSegment={handleSelectSegment}
                  />
                )}
              </div>
              <div className="mcol">
                <div className="wsx-globe dark-panel wsx-globe-chrome" ref={globeCanvasRef}>
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
                    onPointHover={(pt, rect) => { setGlobeHover(pt); setGlobeHoverRect(pt ? rect : null); }}
                  />
                  <GlobeChrome productionName={production.production_name} nScenarios={canonicalScenarioTotal} nMarkers={globeMarkerCount} nArcsInRoute={arcs.length} />
                  <div className="wsx-g-modetoggle" title="Jurisdictions: every jurisdiction this production touches, by what it means for the production. Optimizer Overlay: the recommended structure's own routing chain only.">
                    <button className={workspaceMode === MODE_NORMAL ? "active" : ""} onClick={() => setWorkspaceMode(MODE_NORMAL)}>Single Jurisdiction</button>
                    <button className={workspaceMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setWorkspaceMode(MODE_OPTIMIZER)}>Optimizer</button>
                  </div>
                  {globeHover && (
                    <GlobeHoverCard hover={globeHover} hoverRect={globeHoverRect} canvasRef={globeCanvasRef} />
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
                  optimizerLeadingId={optimizerLeadingId}
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
                <div className="wsx-globe dark-panel wsx-globe-chrome" ref={globeCanvasRef}>
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
                    onPointHover={(pt, rect) => { setGlobeHover(pt); setGlobeHoverRect(pt ? rect : null); }}
                  />
                  <GlobeChrome productionName={production.production_name} nScenarios={canonicalScenarioTotal} nMarkers={globeMarkerCount} nArcsInRoute={arcs.length} />
                  <div className="wsx-g-modetoggle" title="Jurisdictions: every jurisdiction this production touches, by what it means for the production. Optimizer Overlay: the recommended structure's own routing chain only.">
                    <button className={workspaceMode === MODE_NORMAL ? "active" : ""} onClick={() => setWorkspaceMode(MODE_NORMAL)}>Single Jurisdiction</button>
                    <button className={workspaceMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setWorkspaceMode(MODE_OPTIMIZER)}>Optimizer</button>
                  </div>
                  {globeHover && (
                    <GlobeHoverCard hover={globeHover} hoverRect={globeHoverRect} canvasRef={globeCanvasRef} />
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
