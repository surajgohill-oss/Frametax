"use client";

export default function OpportunityMeter({ score }: { score: number | null | undefined }) {
  // API returns 0–1 range; normalize to 0–100
  const raw = score ?? 0;
  const pct = Math.max(0, Math.min(100, raw > 1 ? raw : raw * 100));
  const color =
    pct >= 75 ? "#f87171" :
    pct >= 50 ? "#fb923c" :
    pct >= 25 ? "#facc15" :
    "#34d399";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-[11px] tabular-nums text-slate-400 w-8 text-right">{Math.round(pct)}</span>
    </div>
  );
}
