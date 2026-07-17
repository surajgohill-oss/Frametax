import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Money } from "../lib/format";
import { buildAccountBlocks } from "../lib/budgetBlocks";

// Production Budget rail — approved Overview right column. Categories and
// line items come verbatim from the real parsed budget register
// (pkg.register via buildAccountBlocks); nothing is recalculated here.
// Finance Costs default to zero when absent — no assumed rates or periods.
function RailBlock({ block, onSelectAccount }) {
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
          {block.lines.map((l) => (
            <button className="brail-line" key={l.key} onClick={() => onSelectAccount?.(l)}>
              <span className="brail-line-name">{l.label}</span>
              <span className="mono"><Money value={l.amount} /></span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function BudgetRail({ production, register, onSelectAccount }) {
  const blocks = useMemo(() => buildAccountBlocks(register || []), [register]);
  const hasFinance = blocks.some((b) => /finance/i.test(b.label));

  return (
    <section className="brail-panel">
      <div className="pd-section-label">Production budget</div>
      {blocks.map((block) => (
        <RailBlock key={block.key} block={block} onSelectAccount={onSelectAccount} />
      ))}
      {!hasFinance && (
        <div className="brail-block">
          <div className="brail-header brail-static">
            <span style={{ width: 13 }} />
            <span className="brail-name">Finance costs</span>
            <span className="brail-amount mono"><Money value={0} /></span>
          </div>
        </div>
      )}
      <div className="brail-total">
        <span>Total budget</span>
        <span className="mono brail-total-value"><Money value={production?.gross_budget_usd} /></span>
      </div>
    </section>
  );
}
