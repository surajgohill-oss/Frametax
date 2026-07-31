import { useMemo, useRef, useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import GlobeLegend from "../../components/GlobeLegend";
import { buildGlobeView, structureTier, STATUS_HEX } from "../../lib/globeData";
import { isFixtureActive } from "../../lib/globeVisualFixture";
import { useAppState } from "../../state/AppState";
import { Money, CompactMoney, humanizeToken } from "../../lib/format";

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
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: globeMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

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

// The base-incentive line: read verbatim from buildCountryHoverData's
// `baseIncentive` (program + rate, the same fields Inspector.jsx's
// AllocationSegmentInspector renders) or `excludedReason` (the backend's own
// real discovery-examination sentence). Never a fabricated percentage or
// reason — an honest fallback string when the engine hasn't supplied one.
function baseIncentiveLine(hover) {
  // `hover.status` is the colour-slot key ("gold"/"jade"/"amber"/"silver"),
  // NOT `semanticState` ("recommended"/"alternative"/"unlockable"/
  // "additional") — an earlier draft of this function checked the wrong
  // field (`=== "additional"`), which silently never matched, so Excluded
  // jurisdictions with an actual (if unpriceable) structure attached fell
  // through to the generic "Base incentive · Not available" branch instead
  // of surfacing their real exclusion reason. Caught in runtime
  // verification (Hungary), not by a test — see the test added below.
  if (hover.status === "silver") {
    return hover.excludedReason || "Current production constraints";
  }
  if (hover.baseIncentive) {
    const { programLabel, ratePct, rateCeilingPct } = hover.baseIncentive;
    if (ratePct == null) return programLabel;
    const ceiling = rateCeilingPct != null ? ` (up to ${rateCeilingPct}%)` : "";
    return `${programLabel} · ${ratePct}%${ceiling}`;
  }
  return "Base incentive · Not available";
}

// The NPC line's fallback text depends on WHY there's no number — an
// honest distinction, not one generic dash: Co-Production Opportunities are
// blocked-but-priceable ("not currently priced"), Excluded jurisdictions
// have no structure to price at all ("not viable"). Never a client-computed
// NPC — `hover.npcUsd` is the same `structure.npc_with_adjustments_usd` the
// Inspector and every structure card already read.
function npcFallback(hover) {
  if (hover.status === "amber") return "Not currently priced";
  if (hover.status === "silver") return "Not viable";
  return "Not priced";
}

// Anchors the hover card near the hovered marker's own on-screen box
// (Globe3D passes it through unmodified from the CSS2D hit-target's
// getBoundingClientRect()) rather than a fixed panel corner. Clamped to stay
// inside the canvas panel on every edge — no floating-ui/popper dependency;
// a fixed approximate card width is enough for a compact, single-purpose
// card that never wraps to more than a few short lines.
const HOVER_CARD_W = 220;
const HOVER_CARD_MARGIN = 10;
function hoverCardStyle(hoverRect, canvasEl) {
  if (!hoverRect || !canvasEl) return { display: "none" };
  const box = canvasEl.getBoundingClientRect();
  let left = hoverRect.left - box.left + hoverRect.width / 2 + HOVER_CARD_MARGIN;
  let top = hoverRect.top - box.top - 8;
  left = Math.max(HOVER_CARD_MARGIN, Math.min(left, box.width - HOVER_CARD_W - HOVER_CARD_MARGIN));
  top = Math.max(HOVER_CARD_MARGIN, Math.min(top, box.height - 96));
  return { left, top, width: HOVER_CARD_W };
}

function GlobeHoverCard({ hover, hoverRect, canvasRef }) {
  return (
    <div className="globe-tooltip" style={hoverCardStyle(hoverRect, canvasRef.current)}>
      <strong>{hover.jurisdictionName}</strong>
      <div className="text-tertiary small">{hover.fullStatusLabel}</div>
      <div className="text-secondary small" style={{ marginTop: 4 }}>{baseIncentiveLine(hover)}</div>
      <div className="text-secondary small">
        Estimated NPC · {hover.npcUsd != null ? <CompactMoney value={hover.npcUsd} /> : npcFallback(hover)}
      </div>
    </div>
  );
}
