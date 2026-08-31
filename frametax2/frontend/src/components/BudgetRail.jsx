import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Money } from "../lib/format";
import { buildAccountBlocks, buildDepartmentBlocks } from "../lib/budgetBlocks";
import { postProjectAssumptions } from "../api";

// Production Budget rail — approved Overview right column. Categories and
// line items come verbatim from the real parsed budget register
// (pkg.register via buildAccountBlocks); nothing is recalculated here.
// Finance Costs default to zero when absent — no assumed rates or periods.
//
// `structure` is the Production Workspace's shared active/leading structure
// (see AppState.leadingStructureId / lib/globeData.activeStructure) — the
// SAME selection the Globe and Inspector are synchronized to. It supplies
// the rest of the traceability chain a raw budget line can't answer on its
// own: which jurisdiction the account is allocated to under this structure,
// whether it's included in that jurisdiction's QPE or excluded, its credit
// contribution, and its NPC impact. Every one of those fields is read or
// derived from fields already served on GET /structures — nothing invented,
// and every one still traces back to the account's own imported amount.
function jurisdictionAllocation(line, structure) {
  if (!structure) return null;
  const seg = (structure.segments || []).find((s) => (s.account_codes || []).includes(line.code));
  if (!seg) return null;
  const trace = (seg.qualification_trace || []).find((t) => t.account_code === line.code);
  const state = trace?.state ?? line.state;
  const included = state === "qualifies";
  // Best-supported (canonical, non-floor) effective rate for this segment —
  // consistent with the Phase 5 optimization contract (ranking/NPC use the
  // modeled incentive, never the statutory floor).
  const effRate = seg.claims_incentive && seg.qpe_usd > 0 ? (seg.incentive_ceiling_usd || 0) / seg.qpe_usd : 0;
  const creditContribution = included ? line.amount * effRate : 0;
  return {
    jurisdictionCode: seg.jurisdiction_code,
    claimsIncentive: !!seg.claims_incentive,
    included,
    state,
    creditContributionUsd: creditContribution,
    // A qualifying line reduces NPC by its own credit contribution; an
    // excluded line contributes no reduction (its full amount remains
    // uncompensated cost) — never a fabricated marginal-NPC figure, just
    // the same subtraction the structure-level NPC formula already applies.
    npcImpactUsd: included ? -creditContribution : 0,
  };
}

function RailBlock({ block, structure, onSelectAccount, openLineKey, onToggleLine }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="brail-block">
      <button className="brail-header" onClick={() => setOpen((o) => !o)}>
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        <span className="brail-name">{block.label}</span>
        <span className="brail-amount mono"><Money value={block.amount} /></span>
      </button>
      {open && (
        <div className="brail-lines">
          {block.lines.map((l) => {
            const alloc = jurisdictionAllocation(l, structure);
            const lineOpen = openLineKey === l.key;
            return (
              <div key={l.key} className="brail-line-wrap">
                <button
                  className="brail-line"
                  onClick={() => { onToggleLine(l.key); onSelectAccount?.(l, alloc); }}
                >
                  {lineOpen ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                  <span className="brail-line-name">{l.label}</span>
                  <span className="mono"><Money value={l.amount} /></span>
                </button>
                {lineOpen && (
                  <div className="brail-trace">
                    {/* Jurisdiction Allocation -> Included QPE -> Excluded Costs
                        -> Credit Contribution -> NPC Impact — the rest of the
                        chain, scoped to the active structure. */}
                    {alloc ? (
                      <dl className="brail-trace-kv">
                        <div><dt>Jurisdiction allocation</dt><dd className="mono">{alloc.jurisdictionCode}</dd></div>
                        <div>
                          <dt>{alloc.included ? "Included QPE" : "Excluded costs"}</dt>
                          <dd className="mono"><Money value={l.amount} /></dd>
                        </div>
                        <div><dt>Credit contribution</dt><dd className="mono"><Money value={alloc.creditContributionUsd} /></dd></div>
                        <div><dt>NPC impact</dt><dd className="mono">{alloc.npcImpactUsd < 0 ? "−" : ""}<Money value={Math.abs(alloc.npcImpactUsd)} bare /></dd></div>
                      </dl>
                    ) : (
                      <p className="text-tertiary small" style={{ margin: "4px 0" }}>
                        Not allocated under the active structure — select a leading structure to trace this line's
                        jurisdiction / QPE / credit / NPC chain.
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Original -> Adjustment -> Current scaffold (Workspace Phase 1: design
// only, no persistence — see engineering note below). Original values are
// read from already-served backend fields; Adjustment is local component
// state that is never sent anywhere; Current is the computed sum. The
// later "User Adjustments" phase replaces the local state with a real
// mutation + refetch, without changing this shape.
const ADJUSTMENT_ROWS = [
  { key: "reinvestment", label: "Reinvestment" },
  { key: "inkind", label: "In-kind" },
  { key: "labor", label: "Manual labor normalization" },
  { key: "manual", label: "Manual override" },
];

function AdjustmentsPreview({ economics }) {
  const [open, setOpen] = useState(false);
  const [adjustments, setAdjustments] = useState({ reinvestment: 0, inkind: 0, labor: 0, manual: 0 });
  const originals = {
    reinvestment: 0, // no reinvestment imported for this production
    inkind: economics?.inkind_post_options?.accepted_as_qpe?.off_budget_inkind_usd ?? 0,
    labor: 0,
    manual: 0,
  };
  return (
    <div className="brail-block">
      <button className="brail-header" onClick={() => setOpen((o) => !o)}>
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        <span className="brail-name">Adjustments (preview — not yet saved)</span>
      </button>
      {open && (
        <div className="brail-lines">
          {ADJUSTMENT_ROWS.map((r) => {
            const original = originals[r.key] || 0;
            const adj = adjustments[r.key] || 0;
            const current = original + adj;
            return (
              <div key={r.key} className="brail-adj-row">
                <span className="brail-adj-name">{r.label}</span>
                <span className="brail-adj-v" title="Original (imported/computed)"><Money value={original} bare /></span>
                <input
                  type="number"
                  className="brail-adj-input"
                  value={adj || ""}
                  placeholder="0"
                  title="Adjustment (local preview only — not persisted)"
                  onChange={(e) => setAdjustments((a) => ({ ...a, [r.key]: Number(e.target.value) || 0 }))}
                />
                <span className="brail-adj-v mono" title="Current (original + adjustment)"><Money value={current} bare /></span>
              </div>
            );
          })}
          <p className="text-tertiary small" style={{ margin: "6px 4px 0" }}>
            Original → Adjustment → Current. Adjustment values are a local preview only — nothing here is sent to
            the backend yet; persistence is the later User Adjustments phase.
          </p>
        </div>
      )}
    </div>
  );
}

// Compact Contingency Expected-Utilization control — Production Overview +
// Project Globe UI regression repair, Section 5: lives INSIDE the Budget
// Rail (never a standalone module) as a single line — reserve amount, then a
// short dropdown, matching the rest of this rail's density. Same real,
// already-implemented persistence/API this control has used since it was
// first built (POST /projects/{id}/assumptions) — this batch only moves
// where it renders, never what it does or how it's stored.
const CONTINGENCY_OPTIONS = [0, 25, 50, 75, 100];

function ContingencyLine({ projectId, reserveUsd, currentPct, onSaved }) {
  const [saving, setSaving] = useState(false);
  if (!reserveUsd) return null;

  async function choose(e) {
    const pct = e.target.value === "" ? null : Number(e.target.value);
    if (saving) return;
    setSaving(true);
    try {
      await postProjectAssumptions(projectId, { contingency_expected_utilization_pct: pct });
      onSaved?.();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="brail-block">
      <div className="brail-header brail-static brail-contingency-row" title="Expected use of contingency.">
        <span style={{ width: 13 }} />
        <span className="brail-name">Contingency</span>
        <span className="mono brail-amount">
          <Money value={reserveUsd} bare />
        </span>
        <span className="brail-contingency-use">
          <span className="text-tertiary">Use</span>
          <select
            className="brail-contingency-select"
            value={currentPct ?? ""}
            disabled={saving}
            onChange={choose}
          >
            <option value="">—</option>
            {CONTINGENCY_OPTIONS.map((pct) => (
              <option key={pct} value={pct}>{pct}%</option>
            ))}
          </select>
        </span>
      </div>
    </div>
  );
}

export default function BudgetRail({
  production, register, budget, structure, structureIsLeading, economics, onSelectAccount,
  projectId, contingencyPct, onContingencySaved,
}) {
  // Production Overview + Project Globe UI regression repair, Section 3/4:
  // ONE canonical budget surface. pkg.register (jurisdiction-pricing-
  // derived) is used when it's populated; a project whose own base
  // jurisdiction never priced (register genuinely empty — Lips Like Sugar,
  // Bad Hombres) falls back to the SAME generic, jurisdiction-agnostic
  // pkg.budget.line_items every project already has, grouped by the
  // document's own real department sections. Never a second, competing
  // budget presentation — the same RailBlock renders either source.
  const blocks = useMemo(() => {
    const accountBlocks = buildAccountBlocks(register || []);
    if (accountBlocks.length > 0) {
      // The dedicated "Contingency" account block (BLOCK_DEFS) and the
      // compact ContingencyLine row below both show the SAME reserve total
      // — never both. The compact row is the canonical presentation now
      // (Section 5); drop the block rather than showing the figure twice.
      return accountBlocks.filter((b) => b.key !== "contingency");
    }
    return buildDepartmentBlocks(budget?.line_items || []);
  }, [register, budget]);
  const hasFinance = blocks.some((b) => /finance/i.test(b.label));
  const [openLineKey, setOpenLineKey] = useState(null);
  const onToggleLine = (key) => setOpenLineKey((cur) => (cur === key ? null : key));
  const contingencyReserveUsd = budget?.totals_by_spend_category_usd?.contingency ?? 0;

  // Bad Hombres Overview Truthfulness: Credit/NPC describe WHICHEVER
  // structure the caller passed as `structure` — a producer-selected
  // Leading structure when one exists, otherwise the Hero's own real Top
  // Priced candidate (never a silent, unlabeled "—" while the Hero shows
  // a real number for a different structure). Self-contained label so
  // this card can never be read as contradicting the Hero.
  const stateLabel = !structure ? null : (structureIsLeading ? "Leading" : "Top Priced");

  return (
    <section className="brail-panel">
      <div className="pd-section-label">
        Production budget
        {stateLabel && <span className="text-tertiary" style={{ textTransform: "none", fontWeight: 400 }}> · {stateLabel}</span>}
      </div>

      {/* Collapsed presentation: Total Budget, Credit, NPC — the three
          headline figures, all read verbatim from the active structure
          (falls back to "—" when no structure is fully priced yet). */}
      <div className="brail-headline">
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Total budget</span>
          <span className="mono brail-headline-v"><Money value={production?.gross_budget_usd} /></span>
        </div>
        <div className="brail-headline-cell">
          <span className="brail-headline-k">Credit</span>
          <span className="mono brail-headline-v">
            {structure?.is_fully_priced ? <Money value={structure.selected_incentive_usd} /> : "—"}
          </span>
        </div>
        <div className="brail-headline-cell">
          <span className="brail-headline-k">NPC</span>
          <span className="mono brail-headline-v">
            {structure?.is_fully_priced ? <Money value={structure.npc_with_adjustments_usd} /> : "—"}
          </span>
        </div>
      </div>

      {blocks.map((block) => (
        <RailBlock
          key={block.key}
          block={block}
          structure={structure}
          onSelectAccount={onSelectAccount}
          openLineKey={openLineKey}
          onToggleLine={onToggleLine}
        />
      ))}
      <ContingencyLine
        projectId={projectId}
        reserveUsd={contingencyReserveUsd}
        currentPct={contingencyPct}
        onSaved={onContingencySaved}
      />

      {!hasFinance && (
        <div className="brail-block">
          <div className="brail-header brail-static">
            <span style={{ width: 13 }} />
            <span className="brail-name">Finance costs</span>
            <span className="brail-amount mono"><Money value={0} /></span>
          </div>
        </div>
      )}

      <AdjustmentsPreview economics={economics} />

      <div className="brail-total">
        <span>Total budget</span>
        <span className="mono brail-total-value"><Money value={production?.gross_budget_usd} /></span>
      </div>
    </section>
  );
}
