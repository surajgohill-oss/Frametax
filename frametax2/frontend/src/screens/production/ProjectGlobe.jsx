import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import GlobeLegend from "../../components/GlobeLegend";
import GlobeHoverCard from "../../components/GlobeHoverCard";
import { buildGlobeView, structureTier, STATUS_HEX, STATUS_RANK, globeKey, resolveSegmentDetail, buildCandidateDetail } from "../../lib/globeData";
import { admissibleForMode, MODE_NORMAL, MODE_OPTIMIZER } from "../../lib/workspaceScenarioMode";
import { isFixtureActive } from "../../lib/globeVisualFixture";
import { useAppState } from "../../state/AppState";
import { Money, humanizeToken } from "../../lib/format";
import { loadCategorySnapshot, saveCategorySnapshot, diffCategories } from "../../lib/globeCategoryDiff";

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
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    // LOCAL_GLOBE_WIRING_CLOSEOUT (2026-09-21): resolveSegmentDetail falls
    // back to component_allocations for the generic structural generator's
    // families (every Optimizer candidate), which never populate `segments`
    // at all — confirmed live: this previously opened NO Inspector for any
    // Optimizer jurisdiction (segments empty AND recommendation null).
    const seg = resolveSegmentDetail(s, code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
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
          <button className={globeMode === MODE_NORMAL ? "active" : ""} onClick={() => setGlobeMode(MODE_NORMAL)}>Jurisdictions</button>
          <button className={globeMode === MODE_OPTIMIZER ? "active" : ""} onClick={() => setGlobeMode(MODE_OPTIMIZER)}>Optimizer Overlay</button>
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
          {/* Rank-first ordering — mirrors Workspace/Scenarios (visibleStructures),
              so a producer scanning this list sees the leading option first
              instead of raw generation order. Unranked candidates keep their
              original order after every ranked one. */}
          {[...visibleStructures]
            .sort((a, b) => (rankById.get(a.structure_id)?.rank ?? Infinity) - (rankById.get(b.structure_id)?.rank ?? Infinity))
            .map((s) => {
              // Card <-> Globe selection sync: a card is "active" when the
              // jurisdiction that makes IT distinct (its routed destination,
              // or its primary shoot for a single-country baseline — same
              // rule selectStructure() uses) is the currently selected
              // jurisdiction, so the mapping is symmetric in both directions.
              const routedTo = (s.participants || []).find((c) => c !== s.primary_jurisdiction);
              const code = routedTo || s.primary_jurisdiction || s.participants?.[0];
              const active = code && code === selectedJurisdiction;
              return (
                <div
                  className={`portfolio-chip${active ? " active" : ""}`}
                  key={s.structure_id}
                  onClick={() => selectStructure(s)}
                >
                  {/* Inline colour from the Globe's own STATUS_HEX, not the
                      ".dot" CSS class — that class pulls from unrelated
                      app-wide --gold/--jade/--silver/--amber tokens (a
                      different palette used by every other tier dot in the
                      app), which meant this card's dot and the Globe's own
                      fill for the same jurisdiction never actually matched
                      colours despite sharing a category name. */}
                  <span className="dot" style={{ background: STATUS_HEX[structureTier(s, rankById)] }} />
                  <div>
                    <div className="row-title small">{s.label}</div>
                    <div className="row-sub">
                      {humanizeToken(s.structure_type)} · {s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : `${s.blockers.length} blocker${s.blockers.length === 1 ? "" : "s"}`}
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      <div className="globe-screen-canvas" style={{ position: "relative" }} ref={canvasRef}>
        <GlobeLegend />
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
            ? arcs.length > 0
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

