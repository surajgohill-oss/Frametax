"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { fmt$ } from "@/lib/utils";

export default function SectionPriceBar({ sections, height = 280 }: { sections: any[]; height?: number }) {
  const sorted = [...sections].sort((a, b) => (a.lowest_ask ?? 0) - (b.lowest_ask ?? 0));
  const min = Math.min(...sorted.map((s) => s.lowest_ask ?? 0));
  const max = Math.max(...sorted.map((s) => s.lowest_ask ?? 0));
  if (!sorted.length) return <div style={{ height }} className="flex items-center justify-center text-slate-500 text-sm">No section data.</div>;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={sorted} margin={{ top: 5, right: 10, bottom: 60, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a3145" vertical={false} />
        <XAxis dataKey="display_name" tick={{ fill: "#6b7280", fontSize: 10 }} tickLine={false} axisLine={{ stroke: "#2a3145" }} angle={-45} textAnchor="end" interval={0} />
        <YAxis tickFormatter={(v) => `$${v}`} tick={{ fill: "#6b7280", fontSize: 11 }} tickLine={false} axisLine={false} width={55} />
        <Tooltip contentStyle={{ background: "#1e2535", border: "1px solid #2a3145", borderRadius: "8px", fontSize: "12px", color: "#e2e8f0" }} formatter={(v: number) => [fmt$(v), "Lowest Ask"]} />
        <Bar dataKey="lowest_ask" radius={[3, 3, 0, 0]} maxBarSize={32}>
          {sorted.map((_, i) => { const t = max === min ? 0.5 : ((sorted[i].lowest_ask ?? 0) - min) / (max - min); return <Cell key={i} fill={`rgb(${Math.round(t * 220)},${Math.round((1 - t) * 180)},60)`} />; })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
