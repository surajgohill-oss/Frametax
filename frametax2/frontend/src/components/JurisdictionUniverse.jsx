import { useState } from "react";
import { Money } from "../lib/format";
import {
  accountedRowFor, coproductionNeedsFactsLabel, coproductionRows, executableFor, groupUniverse, jurisdictionLabel,
  policySuppressedLabel, policySuppressedRows,
} from "../lib/jurisdictionUniverse";
import { buildCandidateDetail, buildOpportunityDetail, buildRejectedDetail } from "../lib/globeData";

// Complete served jurisdiction universe (Single-Jurisdiction mode) + the co-production-opportunities-need-facts list.
// Reads ONLY the served contract (lib/jurisdictionUniverse.js); opens the same Inspector every other surface opens.

const usd = (v) => (v == null ? "—" : <Money value={v} bare />);

export function openUniverseRecord(allocated, rec, openInspector, onSelect) {
  onSelect?.(rec.jurisdiction_code);
  const exec = rec.disposition === "EXECUTABLE" ? executableFor(allocated, rec) : null;
  if (exec) return openInspector("candidate-structure", buildCandidateDetail(exec));
  const row = accountedRowFor(allocated, rec);
  if (!row) return null;
  return rec.disposition === "HARD_BLOCK"
    ? openInspector("optimizer-rejection", buildRejectedDetail(row))
    : openInspector("optimizer-opportunity", buildOpportunityDetail(row));
}

function UniverseRow({ rec, onOpen }) {
  const conditional = rec.category === "CONDITIONAL_ALTERNATIVE" && rec.disposition !== "EXECUTABLE";
  const missing = rec.missing_conditions || [];
  return (
    <div className="portfolio-chip" data-universe-row={rec.jurisdiction_code} data-universe-category={rec.category} onClick={() => onOpen(rec)} style={{ display: "block" }}>
      <div className="row-title small">{jurisdictionLabel(rec)}{rec.program_name ? ` — ${rec.program_name}` : ""}</div>
      {rec.disposition === "EXECUTABLE" && (
        <div className="row-sub">
          Confirmed incentive {usd(rec.confirmed_incentive_usd)} · NPC {usd(rec.confirmed_npc_usd)}
          {rec.potential_incentive_usd != null && rec.potential_incentive_usd > (rec.confirmed_incentive_usd ?? 0) && <> · maximum potential {usd(rec.potential_incentive_usd)} (not guaranteed)</>}
          {rec.economic_certainty ? ` · ${String(rec.economic_certainty).toLowerCase()}` : ""}
        </div>
      )}
      {conditional && (
        <div className="row-sub" data-universe-conditional>
          Confirmed floor {usd(rec.confirmed_incentive_usd ?? 0)} · maximum potential {usd(rec.potential_incentive_usd)} (not guaranteed) · potential NPC {usd(rec.potential_npc_usd)}
          {rec.stated_ceiling_rate != null ? ` · ceiling up to ${Math.round(rec.stated_ceiling_rate * 100)}%` : ""}
        </div>
      )}
      {(conditional || rec.category === "NOT_SUITABLE_FOR_THIS_PRODUCTION" || rec.disposition === "HARD_BLOCK" || rec.disposition === "DATA_INCOMPLETE") && (rec.headline || rec.hard_failure_reason) && (
        <div className="row-sub">{rec.hard_failure_reason || rec.headline}</div>
      )}
      {missing.length > 0 && (
        <details onClick={(e) => e.stopPropagation()} data-universe-missing>
          <summary className="row-sub" style={{ cursor: "pointer" }}>{missing.length} exact missing fact{missing.length === 1 ? "" : "s"}</summary>
          <ul className="row-sub" style={{ margin: "4px 0 0 16px" }}>{missing.map((m, i) => <li key={i}>{m}</li>)}</ul>
        </details>
      )}
    </div>
  );
}

export function JurisdictionUniversePanel({ allocated, openInspector, onSelect }) {
  const { groups, unknown, total, winners } = groupUniverse(allocated);
  const [open, setOpen] = useState(false);
  if (!total) return null;
  const onOpen = (rec) => openUniverseRecord(allocated, rec, openInspector, onSelect);
  const counts = groups.filter((g) => g.items.length).map((g) => `${g.items.length} ${g.label.toLowerCase()}`).join(" · ");
  return (
    <div className="wsx-universe" data-testid="jurisdiction-universe" style={{ margin: "6px 0 10px" }}>
      <button type="button" className="field-select" data-testid="jurisdiction-universe-toggle" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        {open ? "Hide" : "Show"} all {total} served jurisdictions
      </button>
      <span className="text-tertiary small" data-testid="jurisdiction-winner-stat" style={{ marginLeft: 8 }}>
        {winners} jurisdiction winner{winners === 1 ? "" : "s"} (executable, one per jurisdiction) · {counts}
      </span>
      {open && (
        <div data-testid="jurisdiction-universe-groups">
          {groups.map((g) => (
            <details key={g.key} data-universe-group={g.key} open={g.items.length > 0 && g.items.length <= 30 && g.key !== "REFERENCE_ALTERNATIVE"}>
              <summary className="inspector-eyebrow" style={{ cursor: "pointer", margin: "8px 0 4px" }}>{g.label} ({g.items.length})</summary>
              {g.items.length === 0 && <p className="text-tertiary small" style={{ margin: "2px 0 6px" }}>None established for this production.</p>}
              {g.items.map((rec) => <UniverseRow key={rec.jurisdiction_code} rec={rec} onOpen={onOpen} />)}
            </details>
          ))}
          {unknown.length > 0 && (
            <details data-universe-group="UNCLASSIFIED"><summary className="inspector-eyebrow">Unclassified ({unknown.length})</summary>
              {unknown.map((rec) => <UniverseRow key={rec.jurisdiction_code} rec={rec} onOpen={onOpen} />)}
            </details>
          )}
        </div>
      )}
    </div>
  );
}

// "N co-production opportunities need facts" -- a real button that expands the complete list (never program rows).
export function CoproductionFactsList({ allocated, openInspector }) {
  const rows = coproductionRows(allocated);
  const [open, setOpen] = useState(false);
  if (!rows.length) return null;
  return (
    <div className="wsx-copro-facts" data-testid="copro-facts" style={{ margin: "4px 0 8px" }}>
      <button type="button" className="field-select" data-testid="copro-facts-toggle" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        {coproductionNeedsFactsLabel(rows.length)}
      </button>
      {open && (
        <div data-testid="copro-facts-list">
          {rows.map((r) => (
            <div key={r.id} className="portfolio-chip" data-copro-row={r.id} style={{ display: "block" }}
              onClick={() => openInspector("optimizer-opportunity", buildOpportunityDetail(r.structure))}>
              <div className="row-title small">{r.pairing}</div>
              <div className="row-sub">
                {String(r.classification).replace(/_/g, " ").toLowerCase()}{r.resolutionState ? ` · ${String(r.resolutionState).replace(/_/g, " ").toLowerCase()}` : ""}
                {" · confirmed floor "}{r.confirmedFloor == null ? "not established" : usd(r.confirmedFloor)}
                {" · maximum potential "}{r.maximumPotential == null ? "not calculable (no priced program)" : usd(r.maximumPotential)}
              </div>
              <div className="row-sub">Why it cannot be confirmed: {r.why}</div>
              {r.missingFacts.length > 0 && (
                <details onClick={(e) => e.stopPropagation()}>
                  <summary className="row-sub" style={{ cursor: "pointer" }}>{r.missingFacts.length} exact missing fact{r.missingFacts.length === 1 ? "" : "s"}</summary>
                  <ul className="row-sub" style={{ margin: "4px 0 0 16px" }}>{r.missingFacts.map((m, i) => <li key={i}>{m}</li>)}</ul>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Policy-suppressed reference structures (music carve-out): a collapsed, secondary list -- never primary cards,
// never Leading/Strong. Every row opens the same candidate Inspector, which shows the suppression explanation.
export function PolicySuppressedReferences({ allocated, openInspector }) {
  const rows = policySuppressedRows(allocated);
  const [open, setOpen] = useState(false);
  if (!rows.length) return null;
  return (
    <div className="wsx-policy-suppressed" data-testid="policy-suppressed" style={{ margin: "4px 0 8px" }}>
      <button type="button" className="field-select" data-testid="policy-suppressed-toggle" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        {policySuppressedLabel(rows.length)}
      </button>
      {open && (
        <div data-testid="policy-suppressed-list">
          <p className="text-tertiary small" style={{ margin: "4px 0 6px" }}>
            Calculated and priced, but excluded from preferred presentation by the music carve-out policy: Music is routed
            separately only when that saves at least the policy threshold against the bundled counterpart.
          </p>
          {rows.map((r) => (
            <div key={r.id} className="portfolio-chip" data-policy-suppressed-row={r.id} style={{ display: "block" }}
              onClick={() => openInspector("candidate-structure", buildCandidateDetail(r.structure))}>
              <div className="row-title small">{r.route}</div>
              <div className="row-sub">
                Music destination {r.musicDestination || "—"} · bundled comparison: {r.bundledRoute}
                {r.bundledNpc != null && <> (NPC {usd(r.bundledNpc)})</>}
              </div>
              <div className="row-sub">
                NPC {usd(r.npc)} · NPC benefit of splitting Music {r.delta == null ? "not established" : usd(r.delta)} · policy threshold {usd(r.threshold)}
              </div>
              <div className="row-sub">{r.reason}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
