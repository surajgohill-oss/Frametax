"use client";

import { cn } from "@/lib/utils";

/**
 * Single row template for every Current Market panel (Active hero, Watchlist,
 * Event Detail). Fixed grid guarantees identical column positions on all rows:
 *
 *   [Label] [Baseline] [→] [Current] [Abs Delta] [% Chip / note]
 *
 * Typography is locked here so Median/Low/High/Inventory/Dup % can never drift:
 * label 12px slate-400 · baseline 15px slate-400 · current 22px bold ·
 * abs 15px medium · tail (chip 13px via DeltaChip, or 13px italic note).
 */
export default function MarketRow({
  label,
  baseline,
  current,
  currentCls,
  delta,
  deltaCls,
  tail,
  last = false,
}: {
  label: string;
  baseline?: string | null;
  current: string;
  currentCls?: string;
  delta?: string | null;
  deltaCls?: string;
  tail?: React.ReactNode;
  last?: boolean;
}) {
  return (
    <div
      className={cn(
        "grid items-baseline py-2 tabular-nums",
        "grid-cols-[4rem_3.9rem_0.8rem_5.1rem_4.1rem_minmax(0,1fr)]",
        !last && "border-b border-white/[0.04]",
      )}
    >
      <span className="text-[12px] font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      <span className="text-[15px] text-slate-400 text-right pr-1">{baseline ?? ""}</span>
      <span className="text-[15px] text-slate-500">{baseline != null ? "→" : ""}</span>
      <span className={cn("text-[22px] font-bold leading-none", currentCls ?? "text-white")}>{current}</span>
      <span className={cn("text-[15px] font-semibold", deltaCls ?? "text-slate-500")}>{delta ?? ""}</span>
      {/* overflow-hidden keeps the chip inside this panel at narrow widths */}
      <span className="min-w-0 overflow-hidden">{tail ?? null}</span>
    </div>
  );
}
