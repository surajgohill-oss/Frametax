import { useState } from "react";
import { Money, scenarioDisplay, compactIncentiveRate, confidenceStatusLabel, confidenceStatusTone, hasAdministrativeAllocationRisk, flagEmoji, jurisdictionName } from "../lib/format";
import { classifyStructure, selectAnchorLeadingOptimized, cardStatus, qpeOf, isBaselineStructure } from "../lib/productionOptions";
import { postJurisdictionPreference, beginEvaluation } from "../api";

// Batched producer-control closeout (2026-09-03), Batch 6: the fact_key
// prefix must match canonical_evaluation.py's own
// JURISDICTION_PREFERENCE_FACT_PREFIX exactly — never a second,
// independently-maintained constant.
const JURISDICTION_PREFERENCE_FACT_PREFIX = "jurisdiction_preference:";

// Overview center-column, directly beneath Project Globe — the approved
// 2x2 anchor/scenario decision surface (history-based restoration,
// 2026-09-03, root authority: commit ec283e5's real "Incentive
// Intelligence 2x2 grid" — the only genuine 2-row/2-column grid this
// surface has ever used; its category semantics were Recommended/
// Alternatives/Co-Production Opportunities/Excluded, reinterpreted here
// against the canonical anchor/current-production data model
// (isBaselineStructure/is_baseline) rather than inventing a second
// concept). Selection lives in lib/productionOptions.js's
// selectAnchorLeadingOptimized (unit-tested there); this file only
// formats and renders, reusing the existing .ii-* card vocabulary
// (CardShell-style accent bar + metrics grid) unchanged in geometry.
//
// Card 1 — ANCHOR (the production's real current/base structure).
// Cards 2-3 — LEADING (the two highest-ranked alternatives, Anchor
// excluded).
// Card 4 — OPTIMIZED (the strongest legitimate optimization opportunity
// not already shown, or the canonical next-best alternative when none
// exists — never fabricated).

function OptionCard({ structure, cardIndex, baseNpc, onClick, projectId, onPreferenceSaved }) {
  const classification = classifyStructure(structure);
  const { title } = scenarioDisplay(structure);
  // Batched producer-control closeout (2026-09-03), item 2: Top
  // Structures' country/jurisdiction flags were dropped when this
  // 2x2 grid was rebuilt on scenarioDisplay (which returns a plain
  // title string, no flags) — Workspace's own cards never lost them
  // because they use the separate compactScenarioIdentity helper.
  // Restored via the same flagEmoji/participants derivation
  // compactScenarioIdentity already uses (lib/format.jsx) — no new
  // flag mapping, no change to jurisdiction name/status/economics/
  // click behavior, which all still come from scenarioDisplay/
  // cardStatus/structure fields exactly as before.
  const codes = (structure.participants && structure.participants.length)
    ? structure.participants
    : (structure.primary_jurisdiction ? [structure.primary_jurisdiction] : []);
  const flags = codes.map(flagEmoji).filter(Boolean).join(" ");
  const status = cardStatus(structure, cardIndex);
  const isOpportunity = !!structure.__isOpportunity;
  // Opportunity cards (Card 4 when it represents a real disclosed
  // fund/treaty pathway, not yet-earned economics) must never format
  // their figure through compactIncentiveRate — that function only ever
  // describes a structure's OWN resolved rate_floor/rate_ceiling, and
  // applying it here would misrepresent a disclosed cap as an earned
  // rate. F#K Valentine's Day economic/semantic regression fix
  // (2026-09-03): this used to sum every disclosed fund's own
  // documented_cap_usd and show "Potential up to $X" — for a real
  // production this summed five unrelated national funds' own per-
  // project ceilings (sized for productions much larger than this one)
  // into a figure ($16.1M) that exceeded the production's entire $4.5M
  // source budget by more than 3x. A program's own cap is real and
  // disclosable but is never this project's calculated potential (item
  // 5.C/5.D) — disclose the real fund COUNT/NAMES instead, never a
  // fabricated or summed dollar figure.
  const rateLine = isOpportunity
    ? (structure.__fundCount
        ? `${structure.__fundCount} discretionary fund${structure.__fundCount === 1 ? "" : "s"} available — not a guaranteed or project-scaled figure`
        : "Potential — not yet modeled")
    : compactIncentiveRate(structure);
  const npc = structure.npc_with_adjustments_usd;
  const diff = npc != null && baseNpc != null && !isBaselineStructure(structure) ? npc - baseNpc : null;
  const clickable = !!onClick;

  // Batched producer-control closeout (2026-09-03), Batch 6: a compact,
  // generic PROJECT-LEVEL candidate-jurisdiction inclusion/exclusion
  // control. Surfaced only where a jurisdiction's discretionary/
  // preapproval status is ALREADY disclosed — the exact place a producer
  // would want to decide whether to keep modeling it — never a
  // jurisdiction-specific control — the same button appears for any
  // structure that carries this real disclosure. The anchor/current-base
  // structure is
  // never excludable (its own jurisdiction can't be removed from its own
  // candidate universe — enforced generically at the backend too), so
  // the control never renders there.
  const hasRisk = hasAdministrativeAllocationRisk(structure);
  const canExclude = hasRisk && !isBaselineStructure(structure) && projectId && structure.primary_jurisdiction;
  const [savingPreference, setSavingPreference] = useState(false);

  async function excludeJurisdiction() {
    if (savingPreference || !structure.primary_jurisdiction) return;
    setSavingPreference(true);
    try {
      await postJurisdictionPreference(projectId, structure.primary_jurisdiction, false);
      // Same reasoning as BudgetRail's ContingencyLine/FinanceCostLine —
      // an explicit re-evaluation is required for the new exclusion
      // (now part of the fingerprint) to actually recompute the
      // candidate universe, not just persist a fact nothing reads yet.
      await beginEvaluation(projectId);
      onPreferenceSaved?.();
    } finally {
      setSavingPreference(false);
    }
  }

  // Batched producer-control closeout (2026-09-03), Batch 6: a real
  // <button> can never validly contain another <button> (invalid HTML —
  // confirmed live via a React hydration-error console warning once the
  // Exclude/Include controls were added inside it, and clicks landing
  // unpredictably despite stopPropagation). Switched to the SAME
  // role="button" div pattern Workspace's own ScenarioCard already uses
  // for exactly this reason (its own nested Inspect/Compare/Set-as-
  // leading buttons) — never a second, differently-built clickable-card
  // convention.
  const handleCardKeyDown = (e) => {
    if (!clickable || e.target !== e.currentTarget) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={`ii-card ii-${classification.accent}${clickable ? " ii-clickable" : ""}`}
      onClick={clickable ? onClick : undefined}
      onKeyDown={handleCardKeyDown}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
    >
      <div className="ii-card-accent" aria-hidden="true" />
      <div className="ii-card-body">
        <div className="ii-country">
          <span className="ii-country-name">{flags ? `${flags} ${title}` : title}</span>
        </div>
        <div className="ii-status">{status}</div>
        {rateLine && <div className="ii-structure">{rateLine}</div>}

        <div className="ii-metrics">
          <div className="ii-metric">
            <span className="ii-metric-label">Gross Budget</span>
            <span className="ii-metric-value mono">
              {structure.gross_budget_usd != null ? <Money value={structure.gross_budget_usd} bare /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Qualified Spend</span>
            <span className="ii-metric-value mono">
              {structure.is_fully_priced ? <Money value={qpeOf(structure)} bare /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Incentive</span>
            <span className="ii-metric-value mono">
              {structure.selected_incentive_usd != null ? <Money value={structure.selected_incentive_usd} bare /> : "—"}
            </span>
          </div>
          <div className="ii-metric">
            <span className="ii-metric-label">Net Production Cost</span>
            <span className="ii-metric-value mono">
              {npc != null ? <Money value={npc} bare /> : "Not priced"}
            </span>
          </div>
        </div>

        {diff != null && (
          <div className="ii-related">
            <span className="ii-related-label">Vs. current / base</span>
            <span className="ii-related-list">
              {diff > 0 ? "+" : ""}<Money value={diff} />
            </span>
          </div>
        )}

        {structure.confidence_status && (
          <div className="ii-program">
            <span className={`badge ${confidenceStatusTone(structure.confidence_status)}`}>
              {confidenceStatusLabel(structure.confidence_status)}
            </span>
          </div>
        )}

        {/* F#K item 3: real, backend-disclosed administrative/discretionary
            allocation risk (award-authority discretion, competitive/
            capacity-limited allocation, or a mandatory preapproval step).
            A structure carrying this must never present as a clean,
            unconditional deterministic winner — generic across every
            jurisdiction/program, see hasAdministrativeAllocationRisk. */}
        {hasRisk && (
          <div className="ii-program">
            <span className="badge amber">⚠ Discretionary / preapproval required</span>
          </div>
        )}
        {canExclude && (
          <div className="ii-program">
            <button
              className="ghost-action small"
              disabled={savingPreference}
              onClick={(e) => { e.stopPropagation(); excludeJurisdiction(); }}
              title={`Remove ${title} from this project's candidate/ranking universe — a producer modeling preference, never a change to its real discretionary/preapproval requirement.`}
            >
              {savingPreference ? "Excluding…" : `Exclude ${title} from candidates`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Batched producer-control closeout (2026-09-03), Batch 6: the restore
// side of the same generic control — jurisdictions currently excluded
// from this project's candidate universe have no card to attach an
// "Include" button to (they no longer appear anywhere in `allocated`),
// so this reads the real ProjectFact rows directly (already generically
// served on `facts.answers` — no new read path) and offers to restore
// each one. Renders nothing when no jurisdiction is excluded.
function ExcludedJurisdictions({ facts, projectId, onPreferenceSaved }) {
  const [savingCode, setSavingCode] = useState(null);
  const answers = facts?.answers || {};
  const excludedCodes = Object.entries(answers)
    .filter(([key, value]) => key.startsWith(JURISDICTION_PREFERENCE_FACT_PREFIX) && value === "excluded")
    .map(([key]) => key.slice(JURISDICTION_PREFERENCE_FACT_PREFIX.length));
  if (excludedCodes.length === 0) return null;

  async function includeJurisdiction(code) {
    if (savingCode || !projectId) return;
    setSavingCode(code);
    try {
      await postJurisdictionPreference(projectId, code, true);
      await beginEvaluation(projectId);
      onPreferenceSaved?.();
    } finally {
      setSavingCode(null);
    }
  }

  return (
    <div className="ii-excluded">
      <span className="ii-excluded-label">Excluded from this project's candidates:</span>
      {excludedCodes.map((code) => (
        <button
          key={code}
          className="ghost-action small"
          disabled={savingCode === code}
          onClick={() => includeJurisdiction(code)}
          title="Restore this jurisdiction to the candidate/ranking universe — its real discretionary/preapproval requirements, if any, are unchanged."
        >
          {savingCode === code ? "Including…" : `Include ${jurisdictionName(code)}`}
        </button>
      ))}
    </div>
  );
}

export default function IncentiveIntelligence({ allocated, onSelect, projectId, onPreferenceSaved, facts }) {
  const options = selectAnchorLeadingOptimized(allocated);
  const baseline = allocated?.structures?.find(isBaselineStructure);
  const baseNpc = baseline?.npc_with_adjustments_usd ?? null;

  return (
    <section className="ovx-sec ii-section">
      <div className="oh"><b>Top Structures</b><span className="n">{options.length}</span></div>
      {options.length === 0 ? (
        <p className="empty-state">No priced production structures available yet for this production.</p>
      ) : (
        <div className="ii-grid">
          {options.map((s, i) => (
            <OptionCard
              key={s.structure_id}
              structure={s}
              cardIndex={i}
              baseNpc={baseNpc}
              onClick={onSelect ? () => onSelect(s) : undefined}
              projectId={projectId}
              onPreferenceSaved={onPreferenceSaved}
            />
          ))}
        </div>
      )}
      <ExcludedJurisdictions facts={facts} projectId={projectId} onPreferenceSaved={onPreferenceSaved} />
    </section>
  );
}
