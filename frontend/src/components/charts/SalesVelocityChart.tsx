"use client";
/**
 * SalesVelocityChart
 * Shows estimated sales (likely_sold) per snapshot window over time.
 * Especially useful for pre-event velocity windows (24h, 12h, 6h, 3h, 1h, 30m).
 */
import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { format, differenceInMinutes } from "date-fns";

interface VelocityPoint {
  window: string;
  ts: number;
  sold_estimated: number;
  relisted: number;
  minutesToEvent?: number;
}

export default function SalesVelocityChart({
  transitions,
  eventDate,
  height = 200,
}: {
  transitions: any[] | null | undefined;
  /** ISO event date for time-before-event labels */
  eventDate?: string;
  height?: number;
}) {
  const chartData: VelocityPoint[] = useMemo(() => {
    if (!transitions?.length) return [];
    const byWindow: Record<string, { sold: number; relisted: number }> = {};
    for (const t of transitions) {
      const w = t.window_prev ?? t.window_curr;
      if (!w) continue;
      if (!byWindow[w]) byWindow[w] = { sold: 0, relisted: 0 };
      if (t.classification === "likely_sold" || t.classification === "disappeared" || t.classification === "withdrawn") {
        byWindow[w].sold++;
      } else if (t.classification === "likely_relisted") {
        byWindow[w].relisted++;
      }
    }
    const evDate = eventDate ? new Date(eventDate) : null;
    return Object.entries(byWindow)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([window, counts]) => {
        const ts = new Date(window).getTime();
        const minutesToEvent = evDate ? differenceInMinutes(evDate, new Date(window)) : undefined;
        return {
          window,
          ts,
          sold_estimated: counts.sold,
          relisted: counts.relisted,
          minutesToEvent,
        };
      });
  }, [transitions, eventDate]);

  if (!chartData.length) {
    return (
      <div style={{ height }} className="flex items-center justify-center text-slate-600 text-sm">
        No sales velocity data available.
      </div>
    );
  }

  const total = chartData.reduce((s, p) => s + p.sold_estimated, 0);

  const tickFmt = (v: string) => {
    try { return format(new Date(v), "MM/dd HH:mm"); } catch { return v; }
  };

  // Pre-event velocity markers
  const evDate = eventDate ? new Date(eventDate) : null;
  const velocityMarkers = evDate
    ? [
        { mins: 1440, label: "24h" },
        { mins: 720,  label: "12h" },
        { mins: 360,  label: "6h"  },
        { mins: 180,  label: "3h"  },
        { mins: 90,   label: "90m" },
        { mins: 60,   label: "60m" },
        { mins: 30,   label: "30m" },
      ].map(({ mins, label }) => ({
        ts: evDate.getTime() - mins * 60_000,
        label,
      }))
    : [];

  return (
    <div>
      <div className="flex items-center justify-between px-4 pb-2">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-[11px]" style={{ color: "#F87171" }}>
            <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "#F87171", opacity: 0.8 }} />
            Sold (est.)
          </span>
          <span className="flex items-center gap-1 text-[11px]" style={{ color: "#60A5FA" }}>
            <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "#60A5FA", opacity: 0.8 }} />
            Relisted
          </span>
        </div>
        <span className="text-[10px] text-slate-500">Total est. sold: {total.toLocaleString()}</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }} barSize={8}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="window"
            tickFormatter={tickFmt}
            tick={{ fill: "#4B5563", fontSize: 9 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.05)" }}
          />
          <YAxis
            tick={{ fill: "#4B5563", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={30}
          />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "12px", color: "#e2e8f0" }}
            labelFormatter={(v) => { try { return format(new Date(v as string), "MMM d, HH:mm"); } catch { return v; } }}
            formatter={(v: number, name: string) => [v, name === "sold_estimated" ? "Sold (est.)" : "Relisted"]}
          />
          {velocityMarkers.map(m => (
            <ReferenceLine
              key={m.label}
              x={new Date(m.ts).toISOString()}
              stroke="#374151"
              strokeDasharray="3 3"
              label={{ value: m.label, position: "top", fill: "#4B5563", fontSize: 8 }}
            />
          ))}
          <Bar dataKey="sold_estimated" name="sold_estimated" fill="#F87171" fillOpacity={0.8} radius={[2, 2, 0, 0]} stackId="a" />
          <Bar dataKey="relisted"       name="relisted"       fill="#60A5FA" fillOpacity={0.8} radius={[2, 2, 0, 0]} stackId="a" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
