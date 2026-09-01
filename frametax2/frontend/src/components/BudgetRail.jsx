import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Money, jurisdictionName } from "../lib/format";
import { buildAccountBlocks, buildDepartmentBlocks } from "../lib/budgetBlocks";
import { postProjectAssumptions, beginEvaluation } from "../api";

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
                        {/* Producer Display Names closeout: was the raw
                            jurisdiction_code — same canonical helper every
                            other producer-facing surface uses. */}
                        <div><dt>Jurisdiction allocation</dt><dd>{jurisdictionName(alloc.jurisdictionCode)}</dd></div>
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

// Producer Display Names + Budget Rail User Assumptions closeout —
// replaces the old "Original -> Adjustment -> Current" scaffold, which
// had four ALWAYS-editable inputs (Reinvestment, In-kind, Manual labor
// normalization, Manual override) that were explicitly local-only —
// typed values vanished on refresh with no persistence, and the row
// itself said so ("preview — not yet saved"). Audited against the real,
// existing canonical capability (Section 10 of the closeout task):
//   - Reinvestment: no canonical persisted input or NPC/QPE treatment
//     exists anywhere in the backend for a producer-stated reinvestment
//     figure. Classification C (planned, not yet implemented).
//   - In-kind: a real backend figure exists
//     (economics.inkind_post_options.accepted_as_qpe...) but ONLY for
//     Little Utopia's own hand-modeled scenario — the generic canonical
//     path (every other/new project) always serves inkind_post_options
//     as {}, and there is no producer-facing persisted input that feeds
//     it (accepting in-kind as QPE is a qualification-doctrine decision,
//     out of this task's scope — see "DO NOT ALTER ... QPE doctrine").
//     Classification C for the generic case.
//   - Manual labor normalization / Manual override: no canonical
//     persisted input or economic treatment exists for either.
//     Classification C.
// All four are C — no fake editable control is left in the active form.
// Finance Costs (below, FinanceCostLine) is the one row this audit found
// real, already-implemented canonical backend support for
// (allocation_pricing.price_allocated_structure's own financing_cost_usd
// parameter, previously fed 0.0 with no input path) — Classification B,
// now wired end-to-end (persisted ProjectFact -> canonical evaluation
// input -> NPC, same mechanism as Contingency below).
function InkindDisclosure({ economics }) {
  const offBudgetInkindUsd = economics?.inkind_post_options?.accepted_as_qpe?.off_budget_inkind_usd;
  if (offBudgetInkindUsd == null) return null;
  return (
    <div className="brail-block">
      <div className="brail-header brail-static" title="Read-only — accepting in-kind contribution as QPE is a qualification-doctrine decision, not yet a producer-editable assumption.">
        <span style={{ width: 13 }} />
        <span className="brail-name">In-kind (accepted as QPE)</span>
        <span className="brail-amount mono"><Money value={offBudgetInkindUsd} /></span>
      </div>
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
      // Producer Display Names + Budget Rail User Assumptions closeout:
      // GET-side reads (useCineGlobe's refetch, called via onSaved below)
      // serve the LAST PERSISTED evaluation row — they never re-run
      // pricing themselves. contingency_expected_utilization_pct is
      // already part of the evaluation cache fingerprint, so without an
      // explicit re-evaluation here the served NPC/economics would stay
      // stale after a save until some unrelated future evaluation
      // happened to run. beginEvaluation is the SAME existing, generic
      // "Begin Evaluation" entry point (idempotent per fingerprint) —
      // no new economics, no new endpoint.
      await beginEvaluation(projectId);
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

// Producer Display Names + Budget Rail User Assumptions closeout —
// Finance Costs, wired the SAME way ContingencyLine above already is:
// POST /projects/{id}/assumptions (generic ProjectFact write path,
// whitelist-only, USER_OVERRIDE precedence) -> onSaved (refetch) ->
// the canonical evaluation fingerprint picks up the change (financing_
// cost_usd is now part of _compute_fingerprint's payload) -> a fresh
// evaluation prices financing_cost_usd straight into NPC via
// allocation_pricing.price_allocated_structure's existing parameter —
// never QPE, never the imported gross budget. `currentUsd` is read from
// the real persisted fact (facts.answers.financing_cost_usd via
// Overview.jsx), not from local state, so a page refresh always shows
// the true saved value, never a value that silently reverts.
function FinanceCostLine({ projectId, currentUsd, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  function startEdit() {
    setDraft(currentUsd != null ? String(currentUsd) : "");
    setEditing(true);
  }

  async function save() {
    if (saving) return;
    const trimmed = draft.trim();
    const value = trimmed === "" ? null : Number(trimmed);
    if (trimmed !== "" && !Number.isFinite(value)) return;
    setSaving(true);
    try {
      await postProjectAssumptions(projectId, { financing_cost_usd: value });
      // Same reasoning as ContingencyLine above — an explicit
      // re-evaluation is required for the new financing_cost_usd (now
      // part of the fingerprint) to actually produce a fresh NPC, not
      // just a persisted-but-unread fact.
      await beginEvaluation(projectId);
      onSaved?.();
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="brail-block">
      <div className="brail-header brail-static brail-contingency-row" title="Producer-stated financing/bridge cost — added to NPC (allocation_pricing's existing financing_cost_usd parameter), never QPE and never the imported budget.">
        <span style={{ width: 13 }} />
        <span className="brail-name">Finance costs</span>
        {editing ? (
          <>
            <input
              type="number"
              className="brail-adj-input"
              value={draft}
              placeholder="0"
              autoFocus
              disabled={saving}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") setEditing(false); }}
            />
            <button className="ghost-action small" disabled={saving} onClick={save}>
              {saving ? "Saving…" : "Save"}
            </button>
            <button className="ghost-action small" disabled={saving} onClick={() => setEditing(false)}>
              Cancel
            </button>
          </>
        ) : (
          <>
            <span className="brail-amount mono"><Money value={currentUsd ?? 0} /></span>
            <button className="ghost-action small" onClick={startEdit}>Edit</button>
          </>
        )}
      </div>
    </div>
  );
}

export default function BudgetRail({
  production, register, budget, structure, structureIsLeading, economics, onSelectAccount,
  projectId, contingencyPct, onContingencySaved, financingCostUsd, onFinanceCostSaved,
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

      <FinanceCostLine
        projectId={projectId}
        currentUsd={financingCostUsd}
        onSaved={onFinanceCostSaved}
      />

      <InkindDisclosure economics={economics} />

      <div className="brail-total">
        <span>Total budget</span>
        <span className="mono brail-total-value"><Money value={production?.gross_budget_usd} /></span>
      </div>
    </section>
  );
}
