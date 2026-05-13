import { cn } from "@/lib/utils";

const V = {
  default: "bg-slate-700 text-slate-200",
  secondary: "bg-slate-800 text-slate-400 border border-slate-700",
  success: "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30",
  blue: "bg-blue-600/20 text-blue-400 border border-blue-500/30",
  green: "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30",
  yellow: "bg-yellow-600/20 text-yellow-400 border border-yellow-500/30",
  red: "bg-red-600/20 text-red-400 border border-red-500/30",
  orange: "bg-orange-600/20 text-orange-400 border border-orange-500/30",
};

export function Badge({ variant = "default", className, children }: { variant?: keyof typeof V; className?: string; children: React.ReactNode }) {
  return <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium", V[variant], className)}>{children}</span>;
}
