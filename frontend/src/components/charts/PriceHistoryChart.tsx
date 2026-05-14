"use client";
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format } from "date-fns";
import { api } from "@/lib/api";

const COLORS: Record<string, string> = { stubhub: "#3b82f6", seatgeek: "#10b981" };

export function PriceHistoryChart({ eventId, data: dataProp, height = 280 }: { eventId?: number; data?: any[]; height?: number }) {
  const [data, setData] = useState<any[]>(dataProp ?? []);
  useEffect(() => {
    if (eventId != null) api.analytics.priceHistory(eventId).then(setData).catch(() => {});
  }, [eventId]);

  const byTs: Record<string, any> = {};
  for (const pt of data) {
    if (!byTs[pt.ts]) byTs[pt.ts] = { ts: new Date(pt.ts).getTime() };
    if (pt.lowest_ask != null) byTs[pt.ts][`${pt.marketplace_slug}_price`] = Number(pt.lowest_ask);
  }
  const chartData = Object.values(byTs).sort((a, b) => a.ts - b.ts);
  const mps = [...new Set(data.map((p) => p.marketplace_slug))];
  if (!chartData.length) return <div style={{ height }} className="flex items-center justify-center text-slate-500 text-sm">No history yet — trigger a poll to start.</div>;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a3145" />
        <XAxis dataKey="ts" type="number" scale="time" domain={["dataMin", "dataMax"]} tickFormatter={(v) => format(new Date(v), "MM/dd HH:mm")} tick={{ fill: "#6b7280", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#2a3145" }} />
        <YAxis tickFormatter={(v) => `$${v}`} tick={{ fill: "#6b7280", fontSize: 11 }} tickLine={false} axisLine={false} width={55} />
        <Tooltip contentStyle={{ background: "#1e2535", border: "1px solid #2a3145", borderRadius: "8px", fontSize: "12px", color: "#e2e8f0" }} labelFormatter={(v) => format(new Date(v as number), "MMM d, HH:mm")} formatter={(v: number, name: string) => [`$${v}`, name.replace("_price", "")]} />
        <Legend wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }} />
        {mps.map((mp) => <Line key={mp} type="monotone" dataKey={`${mp}_price`} name={mp} stroke={COLORS[mp] || "#94a3b8"} strokeWidth={2} dot={false} connectNulls />)}
      </LineChart>
    </ResponsiveContainer>
  );
}
