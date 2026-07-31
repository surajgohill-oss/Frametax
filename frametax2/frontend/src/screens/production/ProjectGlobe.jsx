import { useEffect, useMemo, useRef, useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import GlobeLegend from "../../components/GlobeLegend";
import { buildGlobeView, structureTier, STATUS_HEX } from "../../lib/globeData";
import { isFixtureActive } from "../../lib/globeVisualFixture";
import { useAppState } from "../../state/AppState";
import { Money, humanizeToken, jurisdictionName } from "../../lib/format";
import { formatFullUsd, incentivePctOfGross, presentExclusionReason, relatedJurisdictions } from "../../lib/globeHoverFormat";
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
  const { data, error, loading } = useCineGlobe();
  const { inspector, openInspector, leadingStructureId, selectedJurisdiction, setSelectedJurisdiction } = useAppState();
  const [globeMode, setGlobeMode] = useState("jurisdictions");
  const [hover, setHover] = useState(null);
  // Viewport-relative box of the hovered marker (see Globe3D's mouseenter),
  // converted to a position relative to canvasRef below at render time.
  const [hoverRect, setHoverRect] = useState(null);
  const canvasRef = useRef(null);
  // Read once per render: the fixture gate is durable state now, not a URL read.
  const fixtureActive = isFixtureActive();

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode, categoryByIso } = useMemo(
    () => buildGlobeView(allocated, rankById, {
      mode: globeMode, leadingStructureId, selectedJurisdiction,
      grossBudgetUsd: data?.production?.gross_budget_usd ?? null,
    }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction, data?.production?.gross_budget_usd],
  );

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
    saveCategorySnapshot(productionId, categoryByIso);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryByIso, data?.production?.production_id]);

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
    const seg = s.segments.find((sg) => sg.jurisdiction_code === code);
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
    const seg = s.segments?.find((sg) => sg.jurisdiction_code === code) || s.segments?.[0];
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
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
          <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
          <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
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
          {[...allocated.structures]
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
          {globeMode === "optimizer"
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

// Anchors the hover card near the hovered marker's own on-screen box
// (Globe3D passes it through unmodified from the CSS2D hit-target's
// getBoundingClientRect()) rather than a fixed panel corner. Clamped to stay
// inside the canvas panel on every edge — no floating-ui/popper dependency;
// a fixed approximate card width is enough for a compact, single-purpose
// card that never wraps to more than a few short lines.
const HOVER_CARD_W = 260;
const HOVER_CARD_MARGIN = 10;
function hoverCardStyle(hoverRect, canvasEl) {
  if (!hoverRect || !canvasEl) return { display: "none" };
  const box = canvasEl.getBoundingClientRect();
  let left = hoverRect.left - box.left + hoverRect.width / 2 + HOVER_CARD_MARGIN;
  let top = hoverRect.top - box.top - 8;
  left = Math.max(HOVER_CARD_MARGIN, Math.min(left, box.width - HOVER_CARD_W - HOVER_CARD_MARGIN));
  top = Math.max(HOVER_CARD_MARGIN, Math.min(top, box.height - 168));
  return { left, top, width: HOVER_CARD_W };
}

// PHASE 3B BATCH 1 — canonical hover template, three variants by category.
// Every figure is read straight off `hover` (built in globeData.js's
// buildCountryHoverData from real structure/segment/discovery fields — see
// that function's own comments for exactly which backend field each one
// is). Full, non-abbreviated currency throughout (formatFullUsd) per this
// batch's explicit "no MM/K abbreviations" instruction — the previously
// used compact-currency formatter must not appear anywhere in this file.

// Recommended / Alternatives: program, modeled rate, this jurisdiction's own
// segment incentive (at the modeled rate) + its share of gross budget, and
// the structure's NPC.
function RecommendedOrAlternativeBody({ hover }) {
  const b = hover.baseIncentive;
  const pctOfGross = incentivePctOfGross(hover.segmentIncentiveUsd, hover.grossBudgetUsd);
  return (
    <>
      <div className="hover-field">
        <div className="text-tertiary small">Program</div>
        <div className="small">
          {b ? `${b.programLabel}${b.isBandCeiling ? ` · Up to ${b.ratePct}%` : ` · ${b.ratePct}%`}` : "Not available"}
        </div>
      </div>
      {b?.isBandCeiling && (
        <div className="hover-field">
          <div className="text-tertiary small">Modeled Rate</div>
          <div className="small">{b.ratePct}%{b.floorPct != null ? ` (guaranteed floor ${b.floorPct}%)` : ""}</div>
        </div>
      )}
      <div className="hover-field">
        <div className="text-tertiary small">Estimated Incentive</div>
        <div className="small">
          {hover.segmentIncentiveUsd != null ? formatFullUsd(hover.segmentIncentiveUsd) : "Not available"}
          {pctOfGross && <div className="text-tertiary small">{pctOfGross} of Gross Budget</div>}
        </div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">NPC</div>
        <div className="small">{hover.npcUsd != null ? formatFullUsd(hover.npcUsd) : "Not priced"}</div>
      </div>
    </>
  );
}

// Co-Production Opportunity: program (if one resolved despite the block),
// the structure's own real related jurisdictions, and an explicit,
// undisguised "not available" for the two figures this data model does not
// yet support (see the Batch 1 report's missing-contract note) — never a
// fabricated uplift or NPC.
function CoProductionBody({ hover }) {
  const b = hover.baseIncentive;
  const related = relatedJurisdictions({ participants: [hover.jurisdictionCode, ...hover.relatedCodes] }, hover.jurisdictionCode, jurisdictionName);
  return (
    <>
      <div className="hover-field">
        <div className="text-tertiary small">Program</div>
        <div className="small">
          {b ? `${b.programLabel}${b.ratePct != null ? (b.isBandCeiling ? ` · Up to ${b.ratePct}%` : ` · ${b.ratePct}%`) : ""}` : "Not available"}
        </div>
      </div>
      {related.length > 0 && (
        <div className="hover-field">
          <div className="text-tertiary small">Co-Production With</div>
          <div className="small">{related.map((r) => r.name).join(", ")}</div>
        </div>
      )}
      {/* MISSING BACKEND CONTRACT (see Batch 1 report): no field anywhere
          expresses a forward-looking "potential uplift" or "best modeled
          NPC" for a BLOCKED structure — blocked structures are, by
          definition, not fully priced, so there is no real number to show.
          Stated honestly rather than fabricated. */}
      <div className="hover-field">
        <div className="text-tertiary small">Potential Uplift</div>
        <div className="small">Not modeled yet</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">Best Modeled NPC</div>
        <div className="small">Not priced — structure is blocked</div>
      </div>
    </>
  );
}

// Excluded: one line answering "why isn't this an option" — the backend's
// own real discovery-examination reason, truncated to its first sentence
// and stripped of raw snake_case tokens (see globeHoverFormat.js's
// presentExclusionReason for exactly what transform is applied and why it
// is NOT a fabricated category enum).
function ExcludedBody({ hover }) {
  const reason = presentExclusionReason(hover.excludedReason) || "Current production constraints";
  return (
    <div className="hover-field">
      <div className="text-tertiary small">Reason</div>
      <div className="small">{reason}</div>
    </div>
  );
}

function GlobeHoverCard({ hover, hoverRect, canvasRef }) {
  return (
    <div className="globe-tooltip" style={hoverCardStyle(hoverRect, canvasRef.current)}>
      <strong>{hover.jurisdictionName}</strong>
      <div className="text-tertiary small" style={{ marginBottom: 6 }}>{hover.fullStatusLabel}</div>
      {hover.status === "silver" ? (
        <ExcludedBody hover={hover} />
      ) : hover.status === "amber" ? (
        <CoProductionBody hover={hover} />
      ) : (
        <RecommendedOrAlternativeBody hover={hover} />
      )}
    </div>
  );
}
