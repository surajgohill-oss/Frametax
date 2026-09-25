import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import GlobeLegend from "../../components/GlobeLegend";
import GlobeHoverCard from "../../components/GlobeHoverCard";
import { buildGlobeView, structureTier, STATUS_HEX, STATUS_RANK, globeKey, buildCandidateDetail, buildOpportunityDetail, optimizerStructureStatus, OPTIMIZER_STATUS_HEX, OPTIMIZER_FAMILY_LABEL } from "../../lib/globeData";
import { admissibleForMode, MODE_NORMAL, MODE_OPTIMIZER, optimizerProjection } from "../../lib/workspaceScenarioMode";
import { isFixtureActive } from "../../lib/globeVisualFixture";
import { useAppState } from "../../state/AppState";
import { Money, humanizeToken, buildScenarioLabel } from "../../lib/format";
import { loadCategorySnapshot, saveCategorySnapshot, diffCategories } from "../../lib/globeCategoryDiff";

// OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25) — SUPERSEDES the prior
// tier-based grouping below (kept only as history in git, not in this file):
// the previous section boundaries were `practicality_tier`
// (PRACTICAL_HYBRID/FORMAL_COPRODUCTION/ADVANCED_MULTI_JURISDICTION) —
// confirmed live across all four acceptance productions to be a THRESHOLD
// dimension (2 vs 3+ jurisdictions), not a structural family: every single
// real optimizer_scenarios entry in all four productions has the SAME
// `classification` (HYBRID_ANCHOR_COMPONENT); `practicality_tier` only ever
// varies within that one family. Headings like "Advanced Multi-Jurisdiction"
// therefore read as if hundreds of structures were a DIFFERENT, more complex
// family, when they were the identical family at a higher jurisdiction
// count — "do not use family as a substitute for recommendation status" (and
// the inverse: don't use a threshold-tier heading as a substitute for real
// structural family either). The controlling contract is explicit:
// Recommended / Evaluated Alternatives / Needs More Facts are the three
// section boundaries (matching Workspace's own "Other scenarios" dropdown
// sections) — structural family (HYBRID_ANCHOR_COMPONENT -> "Practical
// Hybrid", etc.) is shown per-row instead, via OPTIMIZER_FAMILY_LABEL,
// never as a section heading. Needs More Facts is real, disclosed,
// non-executable content that the PRIOR list never showed here at all
// (visibleStructures excluded optimizer_opportunities_requiring_facts
// entirely) — it now renders as its own trailing section, per the
// controlling contract's "shown separately after executable structures".
const OPTIMIZER_SECTIONS = [
  { key: "recommended", heading: "Recommended" },
  { key: "evaluated", heading: "Evaluated Alternatives" },
];

// Project Globe — this production's structures and their routing on the
// canonical globe. Same live model as the Workspace Map mode, given its own
// full section per the approved artifact nav. Country click opens the
// jurisdiction segment / structure recommendation in the Inspector.
//
// DIVISION OF LABOUR (Phase 2 closeout; hover scope reopened Phase 3A final
// closeout): the Globe VISUALIZES, the Inspector EXPLAINS — that boundary
// still holds for source notes, qualification traces and account-level
// detail, which stay Inspector-only. Hover was explicitly reopened to carry
// "a lightweight economic summary" (jurisdiction, category, base incentive,
// estimated NPC) — see buildHoverLines() below and globeData's
// buildCountryHoverData, which is the sole source for every figure here.
export default function ProjectGlobe() {
  // Restore Final Phase 3B Globe: current-data compatibility adapter, not a
  // frozen-behavior change. The Phase 3B closeout predates project-scoped
  // routing (useCineGlobe() with no args, the single in-memory demo
  // project). The app is now genuinely multi-project
  // (/projects/:projectId/globe) — useCineGlobe already supports a
  // projectId argument for exactly this. Nothing below this line (camera,
  // polygons, borders, elevation, hover, tooltip, interaction state) is
  // touched.
  const { projectId } = useParams();
  const { data, error, loading } = useCineGlobe(projectId);
  const {
    inspector, openInspector, leadingStructureId, setLeadingStructureId, selectedJurisdiction, setSelectedJurisdiction,
    workspaceMode, setWorkspaceMode,
  } = useAppState();
  // GLOBE_SINGLE_AND_OPTIMIZER_WIRING (2026-09-21): reads/writes the SAME
  // shared mode Workspace's six-scenario-card rack uses — previously local
  // state here, so switching mode on Project Globe never moved Workspace and
  // vice versa. MODE_NORMAL === Single Jurisdiction / "Jurisdictions";
  // MODE_OPTIMIZER === "Optimizer Overlay" (labels unchanged, per the
  // approved design — only the underlying state is now shared).
  const globeMode = workspaceMode;
  const setGlobeMode = setWorkspaceMode;
  const [hover, setHover] = useState(null);
  // Viewport-relative box of the hovered marker (see Globe3D's mouseenter),
  // converted to a position relative to canvasRef below at render time.
  const [hoverRect, setHoverRect] = useState(null);
  const canvasRef = useRef(null);
  // PHASE 3B BATCH 2 (objective 6) — one-time "unlock pulse" isos, cleared
  // by its own timeout. A plain ref (not state) tracks the pending timeout
  // so a second genuine transition inside the pulse window replaces rather
  // than stacks it.
  const [pulsingIsos, setPulsingIsos] = useState(null);
  const pulseTimeoutRef = useRef(null);
  // Read once per render: the fixture gate is durable state now, not a URL read.
  const fixtureActive = isFixtureActive();

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode, categoryByIso, sceneSignature } = useMemo(
    () => buildGlobeView(allocated, rankById, {
      mode: globeMode, leadingStructureId, selectedJurisdiction,
      grossBudgetUsd: data?.production?.gross_budget_usd ?? null,
    }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction, data?.production?.gross_budget_usd],
  );
  // FVD_GLOBE_RENDERER_CORRECTION (2026-09-21) — Phase 5 diagnostic contract:
  // exposes the EXACT scene signature computed from the SAME `points`/`arcs`
  // handed to <Globe3D> below (never re-derived), dev-only, so a live
  // browser check can assert what the renderer actually received without
  // reaching into three.js internals. No production behavior depends on
  // this — it is read-only and inert outside DEV.
  useEffect(() => {
    if (import.meta.env.DEV) window.__cineGlobeSceneSignature = sceneSignature;
  }, [sceneSignature]);
  // GLOBE_SINGLE_AND_OPTIMIZER_WIRING (2026-09-21): the "Production
  // structures" card list below the mode toggle must show the SAME
  // candidate set the Globe itself is currently rendering (best_per_
  // jurisdiction winners in Single Jurisdiction mode; the canonical,
  // GD-4-backstopped multi-jurisdiction families in Optimizer mode) —
  // previously it always listed every `allocated.structures` (the bounded
  // general candidate page) regardless of `globeMode`, so the mode toggle
  // changed the Globe's own colouring/routing but never the list beside it.
  const visibleStructures = useMemo(
    () => admissibleForMode(allocated, globeMode),
    [allocated, globeMode],
  );
  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): the SAME shared Optimizer
  // adapter Workspace's own six-slot dropdown reads (never a second,
  // independently-filtered grouping) — recommended/evaluated (both already
  // real, executable, priced) plus opportunities (real, disclosed, never
  // executable, never priced). `visibleStructures` above stays the
  // recommended+evaluated union for the existing empty-state/caption checks;
  // this is the SAME union, just pre-split into its own real sections for
  // the list render below.
  const optimizerProj = useMemo(
    () => (globeMode === MODE_OPTIMIZER ? optimizerProjection(allocated) : null),
    [allocated, globeMode],
  );

  // PHASE 3B BATCH 2 (objective 9): opening the Inspector clears hover
  // (and, transitively, any Co-Production illumination) rather than leaving
  // it stale underneath — the cursor can stay parked on the same marker
  // after a click without the Globe still showing a hover response for a
  // country whose full detail is now in the Inspector.
  useEffect(() => {
    if (inspector) { setHover(null); setHoverRect(null); }
  }, [inspector]);

  // Phase 3B Batch 1 — category-state diff engine. Produces transition
  // information ONLY (console-logged for dev verification, same disclosure
  // pattern as the visual fixture); no animation, no visible UI change.
  // Later Phase 3B batches consume `diffCategories`'s output to drive
  // one-time signals. Runs whenever the engine's own output changes, and
  // persists the new snapshot so a page refresh doesn't read every
  // jurisdiction as "newly changed".
  useEffect(() => {
    if (!categoryByIso || categoryByIso.size === 0) return;
    const productionId = data?.production?.production_id;
    const prevSnapshot = loadCategorySnapshot(productionId);
    const changes = diffCategories(prevSnapshot, categoryByIso);
    if (changes.length > 0 && import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.info("[CineGlobe] Globe category changes since last snapshot:", changes);
    }
    // PHASE 3B BATCH 2 (objective 6) — one-time unlock pulse for a genuine
    // IMPROVING transition only (silver -> amber, amber -> jade, etc. — the
    // same STATUS_RANK the status upsert itself resolves by, never a second
    // ordering). Never fires on first observation (diffCategories already
    // excludes that) or on a downgrade. Respects prefers-reduced-motion by
    // not scheduling any timer at all — the fill still updates to the new
    // category colour on the very same repaint, just without the pulse.
    const improved = changes
      .filter((c) => STATUS_RANK[c.currCategory] > STATUS_RANK[c.prevCategory])
      .map((c) => c.iso);
    const reducedMotion = typeof window !== "undefined"
      && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (improved.length > 0 && !reducedMotion) {
      if (pulseTimeoutRef.current) clearTimeout(pulseTimeoutRef.current);
      setPulsingIsos(improved);
      pulseTimeoutRef.current = setTimeout(() => {
        setPulsingIsos(null);
        pulseTimeoutRef.current = null;
      }, 2400);
    }
    saveCategorySnapshot(productionId, categoryByIso);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryByIso, data?.production?.production_id]);

  // Pulse timeout must not outlive the component (route navigation away
  // from Project Globe mid-pulse).
  useEffect(() => () => { if (pulseTimeoutRef.current) clearTimeout(pulseTimeoutRef.current); }, []);

  // PHASE 3B BATCH 2 (objective 5) — Co-Production Opportunity hover
  // illumination. Only computed (non-null) while hovering an amber
  // jurisdiction with real related codes; every other hover — Recommended,
  // Alternative, Excluded — passes null through and Globe3D's illumination
  // path is a complete no-op for them (see capColorFn/strokeColorFn there).
  // Memoized on the hovered jurisdiction's own code, not on the `hover`
  // object identity, so Globe3D's illumination effect doesn't re-fire on
  // every hover-position update within the same country.
  const { illuminatedIsos, primaryIlluminatedIso } = useMemo(() => {
    if (!hover || hover.status !== "amber" || !hover.relatedCodes?.length) {
      return { illuminatedIsos: null, primaryIlluminatedIso: null };
    }
    return {
      illuminatedIsos: hover.relatedCodes.map(globeKey),
      primaryIlluminatedIso: hover.primaryJurisdictionCode ? globeKey(hover.primaryJurisdictionCode) : null,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hover?.isoA2, hover?.status]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  // PHASE 3B BATCH 1 — CLICK CONTRACT (establish, do not redesign):
  // Globe click -> open Inspector -> select jurisdiction -> the same
  // shared AppState (`selectedJurisdiction`/`leadingStructureId`) Workspace
  // already reads (Workspace.jsx: `activeStructure(allocated,
  // leadingStructureId)`, `selectedJurisdiction` in its own buildGlobeView
  // call) — so a Globe click already "activates the corresponding Workspace
  // scenario family" via existing shared state, no new wiring needed. This
  // function SHALL NOT call any backend endpoint, rerun optimization, or
  // create/modify a scenario — it only sets client-side selection state and
  // opens the (already-computed, already-served) Inspector view for it. See
  // the regression test guarding this exact contract.
  function selectJurisdiction(code) {
    setSelectedJurisdiction(code);
    // SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23): Single Jurisdiction mode
    // resolves the EXACT canonical `best_per_jurisdiction[code]` winner
    // directly — never `structuresByCode.get(code)[0]` (a lookup built by
    // iterating admissibleForMode's pool and indexing by every participant
    // code; for Single Jurisdiction mode's own pool this happens to hold
    // only that one winner per code today, since every best_per_jurisdiction
    // entry's own participants is exactly [code] — but resolving via the
    // shared lookup made the click path depend on that pool-construction
    // detail rather than stating the real canonical contract explicitly).
    // Opens the SAME full structure-level Inspector (buildCandidateDetail /
    // "candidate-structure") every Optimizer card already uses — never the
    // single-segment "allocation-segment" view, which silently showed only
    // the FIRST program of a real same-jurisdiction stack (e.g. Ontario's
    // real OFTTC + OCASE) and omitted structure id/economic identity/total
    // NPC/delta from Current Location entirely.
    if (globeMode === MODE_NORMAL) {
      const winner = allocated?.best_per_jurisdiction?.[code];
      if (!winner) return;
      openInspector("candidate-structure", buildCandidateDetail(winner));
      return;
    }
    // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): every marker currently
    // on screen in Optimizer mode belongs to the SAME ONE selected/leading
    // structure (buildOptimizerPathway renders exactly one structure's own
    // routing chain at a time — "render only the selected structure's
    // markers/arcs at one time"). Clicking ANY of its own markers must
    // re-open THAT SAME structure's Inspector — never
    // `structuresByCode.get(code)[0]`, which indexes the WHOLE admissible
    // pool by participant code and could resolve to a DIFFERENT structure
    // that merely happens to also touch this jurisdiction (the exact
    // "arbitrary structure rather than the exact canonical winner" defect
    // the Single Jurisdiction pass fixed for MODE_NORMAL above — the
    // Optimizer pathway has the identical failure mode). Resolves via the
    // SAME pool/fallback buildOptimizerPathway itself uses, so a marker
    // click can never disagree with what the Globe is already showing.
    const { recommended, evaluated } = optimizerProjection(allocated);
    const optimizerPool = [...recommended, ...evaluated];
    const s = (leadingStructureId && optimizerPool.find((c) => c.structure_id === leadingStructureId)) || optimizerPool[0] || null;
    if (!s) return;
    openInspector("candidate-structure", buildCandidateDetail(s));
  }

  // Candidate cards already have their own exact structure in hand —
  // routing the click through selectJurisdiction()'s structuresByCode
  // lookup was wrong whenever multiple structures share a participant
  // (every "Mauritius + X" component structure shares MU as a
  // participant): structuresByCode.get(code)[0] silently resolved to
  // WHICHEVER structure happens to be first for that code, not the one
  // whose card was actually clicked — clicking the "routed to SA" card
  // could open the baseline structure's Inspector instead. This opens
  // THIS structure's own segment directly, and frames the jurisdiction
  // that makes this specific card distinct: the routed destination for a
  // component/treaty structure, or the primary shoot for a single-country
  // baseline.
  function selectStructure(s) {
    const routedTo = (s.participants || []).find((c) => c !== s.primary_jurisdiction);
    const code = routedTo || s.primary_jurisdiction || s.participants?.[0];
    setSelectedJurisdiction(code);
    // FVD_GLOBE_RENDERER_CORRECTION (2026-09-21): this previously only set
    // selectedJurisdiction, which drives the choropleth's selection
    // highlight/camera-focus but is NEVER read by buildOptimizerPathway —
    // that function resolves the rendered Optimizer scene from
    // leadingStructureId alone. Confirmed live against F#K Valentine's Day:
    // clicking every one of the 36 Optimizer cards left the Globe scene
    // completely unchanged (same blank/default state) because nothing ever
    // set leadingStructureId. Scoped to Optimizer mode only — Single
    // Jurisdiction mode's choropleth already derives its full jurisdiction
    // set from best_per_jurisdiction independent of leadingStructureId, so
    // setting it there would only leak into Workspace's separate "Leading"
    // FX badge with no Globe-rendering benefit.
    if (globeMode === MODE_OPTIMIZER) setLeadingStructureId(s.structure_id);
    // CODEX_FG-002 (2026-09-21): selecting a STRUCTURE (a card) must open
    // that structure's own complete identity — structure ID, economic
    // identity, classification, every participant, the full program stack,
    // and structure-level totals — never an arbitrarily chosen non-primary
    // participant's segment. Confirmed live: an Alabama-primary Optimizer
    // candidate previously opened Manitoba's segment Inspector instead,
    // because `code` above is only used for the choropleth focus/highlight,
    // not for identifying which candidate was actually clicked — the card
    // already has its own exact structure in hand (`s`) and must describe
    // itself via buildCandidateDetail, the one shared structure-level
    // adapter (see globeData.js). Per-jurisdiction marker clicks
    // (selectJurisdiction, below) are unaffected — those stay scoped to a
    // single segment on purpose.
    openInspector("candidate-structure", buildCandidateDetail(s));
  }

  // OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22): one chip renderer for
  // both modes — Card <-> Globe selection sync ("active" when the routed/
  // primary jurisdiction matches selectedJurisdiction) and the click handler
  // are unchanged; only the title text differs by mode (buildScenarioLabel
  // for Optimizer, the backend's own s.label for Single Jurisdiction — see
  // the row-title comment below).
  function renderStructureChip(s) {
    const routedTo = (s.participants || []).find((c) => c !== s.primary_jurisdiction);
    const code = routedTo || s.primary_jurisdiction || s.participants?.[0];
    const active = code && code === selectedJurisdiction;
    return (
      <div
        className={`portfolio-chip${active ? " active" : ""}`}
        key={s.structure_id}
        onClick={() => selectStructure(s)}
      >
        {/* OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): Optimizer rows now
            colour from optimizerStructureStatus (the SAME real
            recommendation-status derivation the Globe's own markers/arcs
            use), never structureTier/STATUS_HEX — that derivation reads
            `rankById`, which is only ever populated for the Single
            Jurisdiction-family overall ranking, so every Optimizer
            structure fell through to a uniform "jade" regardless of its
            real recommendation status. Single Jurisdiction rows are
            unaffected — same structureTier/STATUS_HEX as before. */}
        <span
          className="dot"
          style={{ background: globeMode === MODE_OPTIMIZER ? OPTIMIZER_STATUS_HEX[optimizerStructureStatus(allocated, s)] : STATUS_HEX[structureTier(s, rankById)] }}
        />
        <div>
          {/* OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22) — ROOT
              DEFECT 3/4: `s.label` is the backend's own free-text label,
              which never distinguishes WHICH routed component went where
              (post/music/vfx to the same destination all read
              identically) and, via compactScenarioIdentity elsewhere,
              risked pulling in a non-claiming segment jurisdiction. In
              Optimizer mode every card here IS an optimizer-classified
              structure (visibleStructures already comes from
              admissibleForMode(allocated, MODE_OPTIMIZER)) —
              buildScenarioLabel (the one shared adapter Workspace's own
              scenarioOptionLabel/ScenarioCard now use too) reads
              component_allocations directly, so component-distinct
              scenarios render visibly distinct titles, with its own
              producer-option prefix. Single Jurisdiction mode is
              unaffected — s.label unchanged there. */}
          <div className="row-title small">
            {globeMode === MODE_OPTIMIZER ? buildScenarioLabel(s) : s.label}
          </div>
          <div className="row-sub">
            {/* OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): structural
                family — real classification, shown per-row via
                OPTIMIZER_FAMILY_LABEL, never as the section heading (see
                OPTIMIZER_SECTIONS above) and never a substitute for the
                section's own recommendation-status grouping. */}
            {globeMode === MODE_OPTIMIZER && OPTIMIZER_FAMILY_LABEL[s.classification] && (
              <>{OPTIMIZER_FAMILY_LABEL[s.classification]} · </>
            )}
            {humanizeToken(s.structure_type)} · {s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : `${s.blockers.length} blocker${s.blockers.length === 1 ? "" : "s"}`}
            {globeMode === MODE_OPTIMIZER && s.savings_vs_current_usd != null && (
              <> · {s.recommendation_status === "COSTS_MORE" ? "costs " : "saves "}<Money value={Math.abs(s.savings_vs_current_usd)} bare /></>
            )}
          </div>
        </div>
      </div>
    );
  }

  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): a Needs-More-Facts
  // opportunity is never executable/selectable as the leading structure (the
  // controlling contract is explicit) — clicking one opens its own read-only
  // Inspector (buildOpportunityDetail / "optimizer-opportunity") describing
  // the real treaty/framework and its unresolved facts, and never touches
  // selectedJurisdiction/leadingStructureId/the Globe scene at all.
  function selectOpportunity(s) {
    openInspector("optimizer-opportunity", buildOpportunityDetail(s));
  }

  function renderOpportunityChip(s) {
    return (
      <div className="portfolio-chip" key={s.structure_id} onClick={() => selectOpportunity(s)}>
        <span className="dot" style={{ background: OPTIMIZER_STATUS_HEX.amber }} />
        <div>
          <div className="row-title small">{s.label}</div>
          <div className="row-sub">Needs more facts · not yet executable</div>
        </div>
      </div>
    );
  }

  return (
    <div className="globe-screen">
      <div className="globe-screen-context">
        <p className="screen-eyebrow">Project Globe</p>
        {/* "Candidate jurisdictions" was the previous engine's framing — a
            database of things examined. This production's real unit of
            decision is the production structure, which is also what the list
            below and the Inspector both open onto. */}
        <h1 className="serif" style={{ fontSize: 20 }}>Production structures</h1>
        <p className="text-tertiary small">
          The recommended structure for this production, its optimized alternatives,
          and the opportunities still to unlock.
        </p>
        <div className="wsx-viewtabs" style={{ marginBottom: 10 }}>
          <button className={globeMode === MODE_NORMAL ? "active" : ""} onClick={() => setGlobeMode(MODE_NORMAL)}>Single Jurisdiction</button>
          <button className={globeMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setGlobeMode(MODE_OPTIMIZER)}>Optimizer</button>
        </div>
        {/* DATA-SOURCE LABEL (required). These cards read the PRODUCTION engine
            — `structureTier()` over the live allocated structures and ranking —
            in every mode. The visual fixture only rewrites the Globe's semantic
            map, so in fixture mode the Globe and this list are deliberately
            driven by different sources. That mismatch must never be silent. */}
        {fixtureActive && (
          <p className="globe-cards-source-note">
            Cards below show <strong>production engine</strong> data. The Globe is
            showing fixture states — the two will not agree.
          </p>
        )}
        <div className="sc-jurlist">
          {globeMode === MODE_OPTIMIZER && visibleStructures.length === 0 && (
            <p className="empty-state">No executable optimizer structures for this production yet.</p>
          )}
          {/* OPTIMIZER_NAVIGATION_LABEL_CLOSEOUT (2026-09-22) — ROOT DEFECT 1
              (still applies): `rankById` (built from `allocated.ranking`, the
              SINGLE combined overall ranking, which only the baseline/
              comparable candidates ever populate) has no relationship to the
              Optimizer projection's own ordering — re-sorting by it risks
              silently breaking the recommended-first order the whole point
              of this list is to preserve. Rank-first ordering is still
              correct and unchanged for Single Jurisdiction mode (real
              per-jurisdiction ranks exist there). */}
          {globeMode === MODE_OPTIMIZER ? (
            /* OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): three genuine
               recommendation-status sections, in this exact order, each with
               its own real count, plus a trailing Needs More Facts section —
               never one flattened, undifferentiated list, and never a
               structural-family heading standing in for recommendation
               status (see OPTIMIZER_SECTIONS above for the full root-cause
               narrative). A section with zero real entries renders no header
               at all (never a fabricated empty one). Every executable option
               appears in exactly one of Recommended/Evaluated Alternatives —
               optimizerProj.recommended/evaluated are already disjoint,
               real, backend-served collections (never a second client-side
               filter/re-derivation). */
            <>
              {OPTIMIZER_SECTIONS.map(({ key, heading }) => {
                const sectionStructures = optimizerProj?.[key] || [];
                if (sectionStructures.length === 0) return null;
                return (
                  <div key={key} className="sc-jurlist-section">
                    <p className="inspector-eyebrow" style={{ margin: "10px 0 4px" }}>
                      {heading} ({sectionStructures.length})
                    </p>
                    {sectionStructures.map((s) => renderStructureChip(s))}
                  </div>
                );
              })}
              {optimizerProj?.opportunities?.length > 0 && (
                <div key="opportunities" className="sc-jurlist-section">
                  <p className="inspector-eyebrow" style={{ margin: "10px 0 4px" }}>
                    Needs More Facts ({optimizerProj.opportunities.length})
                  </p>
                  {optimizerProj.opportunities.map((s) => renderOpportunityChip(s))}
                </div>
              )}
            </>
          ) : (
            [...visibleStructures]
              .sort((a, b) => (rankById.get(a.structure_id)?.rank ?? Infinity) - (rankById.get(b.structure_id)?.rank ?? Infinity))
              .map((s) => renderStructureChip(s))
          )}
        </div>
      </div>

      <div className="globe-screen-canvas" style={{ position: "relative" }} ref={canvasRef}>
        <GlobeLegend mode={globeMode} />
        <Globe3D
          points={points}
          arcs={arcs}
          // The stage owns the height (see --globe-stage-* tokens); 560 is now
          // only the floor. Previously a hardcoded 560 regardless of how much
          // vertical space the page actually had.
          autoHeight
          height={560}
          pointRadius={0.22}
          polygonColors={polygonColors}
          selectedIso={selectedIso}
          hoveredIso={hover?.iso ?? null}
          illuminatedIsos={illuminatedIsos}
          primaryIlluminatedIso={primaryIlluminatedIso}
          pulsingIsos={pulsingIsos}
          selectedLat={selectedLat}
          selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
          // Inspector floats over this screen (not docked — see AppState),
          // covering the right var(--inspector-width)=400px of the canvas.
          // Bias camera framing left so a selected country stays clear of it.
          obscuredRightPx={inspector ? 400 : 0}
          onPointClick={(pt) => selectJurisdiction(pt.jurisdictionCode || pt.id)}
          onPointHover={(pt, rect) => { setHover(pt); setHoverRect(pt ? rect : null); }}
        />
        {/* Lightweight economic-summary card (Phase 3A final closeout —
            explicit, user-directed reopening of the Phase 2 "no figures in
            hover" rule). Anchored near the hovered marker via hoverRect
            rather than fixed top-left. Long source notes, the qualification
            trace and account-level detail remain Inspector-only — click
            still opens the Inspector; hover never does. */}
        {hover && (
          <GlobeHoverCard hover={hover} hoverRect={hoverRect} canvasRef={canvasRef} />
        )}
        <p className="globe-caption small" style={{ borderRadius: "0 0 var(--radius-lg) var(--radius-lg)" }}>
          {/* The overlay caption must describe what is actually on screen. It
              previously always promised "production routing", but when the
              recommended structure is single-jurisdiction there is no routing
              to show — the overlay correctly lights one jurisdiction and draws
              no arc, and the caption then read as a rendering failure. */}
          {globeMode === MODE_OPTIMIZER
            ? visibleStructures.length === 0
              ? "No executable optimizer structures for this production yet."
              : arcs.length > 0
              ? "Showing the recommended structure's production routing only."
              : "The recommended structure is single-jurisdiction — no routing to show."
            : arcs.length > 0
              ? "Dashed routes mark this production's real multi-jurisdiction structures."
              : "No multi-jurisdiction structure is currently priced for this production."}
        </p>
      </div>
    </div>
  );
}
