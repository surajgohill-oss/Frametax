import { cn } from "@/lib/utils";

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("bg-[#161b27] border border-[#2a3145] rounded-xl p-5", className)}>{children}</div>;
}

export function StatCard({ label, value, sub, accent }: { label: string; value: string | number; sub?: string; accent?: boolean }) {
  return (
    <Card className="flex flex-col gap-1">
      <p className="text-xs text-slate-400 uppercase tracking-wider">{label}</p>
      <p className={cn("text-2xl font-semibold", accent ? "text-blue-400" : "text-slate-100")}>{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </Card>
  );
}
