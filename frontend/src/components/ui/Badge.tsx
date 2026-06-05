import { cn } from "@/lib/utils";

const V = {
  // ── existing ──────────────────────────────────────────────────────────────
  default:    "bg-slate-700 text-slate-200",
  secondary:  "bg-slate-800 text-slate-400 border border-slate-700",
  success:    "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30",
  blue:       "bg-blue-600/20 text-blue-400 border border-blue-500/30",
  indigo:     "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30",
  green:      "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30",
  yellow:     "bg-yellow-600/20 text-yellow-400 border border-yellow-500/30",
  red:        "bg-red-600/20 text-red-400 border border-red-500/30",
  orange:     "bg-orange-600/20 text-orange-400 border border-orange-500/30",
  // ── new cinematic variants ─────────────────────────────────────────────────
  live:        "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30",
  "low-inv":   "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  "last-few":  "bg-rose-600/15 text-rose-400 border border-rose-500/35 animate-pulse",
  "no-listings":"bg-slate-700/40 text-slate-600 border border-slate-700/60",
  inactive:    "bg-slate-800/60 text-slate-600 border border-slate-700/40",
  deferred:    "bg-zinc-800/60 text-zinc-600 border border-zinc-700/40",
  unresolved:  "bg-yellow-900/30 text-yellow-600 border border-yellow-700/30",
  "my-event":  "bg-amber-500/15 text-amber-400 border border-amber-400/30",
  "hero-event":"bg-violet-600/15 text-violet-400 border border-violet-500/30",
  hidden:      "bg-slate-900/60 text-slate-700 border border-slate-800",
  followed:    "bg-purple-600/15 text-purple-400 border border-purple-500/30",
};

export function Badge({ variant = "default", className, children }: { variant?: keyof typeof V; className?: string; children: React.ReactNode }) {
  return <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium", V[variant], className)}>{children}</span>;
}
