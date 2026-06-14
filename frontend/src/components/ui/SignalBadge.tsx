import type { Signal } from "@/lib/types";
import { cn } from "@/lib/utils";

const CONFIG: Record<Signal, { label: string; classes: string }> = {
  deepening:   { label: "Deepening",   classes: "bg-red-500/15 text-red-400 border-red-500/25" },
  loosening:   { label: "Loosening",   classes: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25" },
  stable:      { label: "Stable",      classes: "bg-slate-500/15 text-slate-400 border-slate-500/25" },
  capitulating:{ label: "Capitulating",classes: "bg-amber-500/15 text-amber-400 border-amber-500/25" },
  mixed:       { label: "Mixed",       classes: "bg-yellow-500/15 text-yellow-400 border-yellow-500/25" },
  tightening:  { label: "Tightening",  classes: "bg-red-500/15 text-red-400 border-red-500/25" },
  unknown:     { label: "Unknown",     classes: "bg-slate-500/15 text-slate-400 border-slate-500/25" },
};

export default function SignalBadge({
  signal,
  className,
}: {
  signal: Signal | string | null | undefined;
  className?: string;
}) {
  const cfg = CONFIG[(signal as Signal) ?? "stable"] ?? CONFIG.stable;
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border",
        cfg.classes,
        className,
      )}
    >
      {cfg.label}
    </span>
  );
}
