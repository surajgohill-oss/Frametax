"use client";

import {
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { HistoryPoint, HistoryWindow } from "@/lib/types";
import { fmt$$ } from "@/lib/utils";

interface Props {
  series: HistoryPoint[];
  window: HistoryWindow;
  height?: number;
}

function tickFmt(ts: string, win: HistoryWindow) {
  try {
    const d = parseISO(ts);
    return win === "24h" ? format(d, "HH:mm") : format(d, "MM/dd");
  } catch {
    return ts;
  }
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  let dateLabel = label;
  try { dateLabel = format(parseISO(label), "MMM d, HH:mm"); } catch {}

  return (
    <div className="rounded-lg border border-white/8 bg-[#111827] px-3 py-2 text-xs text-slate-200 shadow-xl">
      <div className="text-slate-400 mb-1.5">{dateLabel}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-medium">
            {p.dataKey === "listings" || p.dataKey === "tickets"
              ? (p.value?.toLocaleString() ?? "—")
              : fmt$$(p.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function PriceHistoryChart({ series, window, height = 260 }: Props) {
  if (!series?.length) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-slate-600 text-sm"
      >
        No history data available.
      </div>
    );
  }

  const data = series.map((p) => ({
    ts: p.ts,
    low_ask: p.low_ask,
    median_ask: p.median_ask,
    high_ask: p.high_ask,
    p25_ask: p.p25_ask,
    p75_ask: p.p75_ask,
    listings: p.listings,
  }));

  const maxListings = Math.max(...data.map((d) => d.listings ?? 0), 1);
  const maxPrice = Math.max(...data.map((d) => d.high_ask ?? 0), 1);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />

        {/* Left Y: price */}
        <YAxis
          yAxisId="price"
          orientation="left"
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          tick={{ fill: "#4B5563", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          width={40}
          domain={[0, maxPrice * 1.1]}
        />

        {/* Right Y: listings */}
        <YAxis
          yAxisId="inv"
          orientation="right"
          tick={{ fill: "#4B5563", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          width={36}
          domain={[0, maxListings * 3]}
        />

        <XAxis
          dataKey="ts"
          tickFormatter={(v) => tickFmt(v, window)}
          tick={{ fill: "#4B5563", fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.05)" }}
          interval="preserveStartEnd"
          minTickGap={40}
        />

        <Tooltip content={<CustomTooltip />} />

        {/* Listings bars (background) */}
        <Bar
          yAxisId="inv"
          dataKey="listings"
          name="Listings"
          fill="#334155"
          fillOpacity={0.4}
          radius={[1, 1, 0, 0]}
          maxBarSize={12}
        />

        {/* p25–p75 band */}
        <Area
          yAxisId="price"
          dataKey="p25_ask"
          name="P25"
          stroke="none"
          fill="transparent"
          legendType="none"
        />
        <Area
          yAxisId="price"
          dataKey="p75_ask"
          name="P75 band"
          stroke="none"
          fill="#3b82f6"
          fillOpacity={0.08}
          legendType="none"
        />

        {/* Low ask */}
        <Line
          yAxisId="price"
          dataKey="low_ask"
          name="Low"
          stroke="#34d399"
          strokeWidth={1.5}
          dot={false}
          strokeDasharray="4 3"
          connectNulls
        />

        {/* Median ask */}
        <Line
          yAxisId="price"
          dataKey="median_ask"
          name="Median"
          stroke="#60a5fa"
          strokeWidth={2}
          dot={false}
          connectNulls
        />

        {/* High ask */}
        <Line
          yAxisId="price"
          dataKey="high_ask"
          name="High"
          stroke="#f87171"
          strokeWidth={1.5}
          dot={false}
          strokeDasharray="4 3"
          connectNulls
        />

        <Legend
          wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
          formatter={(v) => <span style={{ color: "#6B7280" }}>{v}</span>}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
