"use client";

/**
 * KiaForumMap
 * Schematic arena map for Kia Forum (concert config).
 * Circular arena, stage at bottom. Floor letters (A-H), lower bowl 100s, upper 200s.
 */

import type { VenueSection } from "@/lib/types";
import type { VenueMode } from "./SofiVenueMap";

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * clamp(t, 0, 1);
}

function modeColor(mode: VenueMode, score: number | null): string {
  if (score == null) return "#1a2535";
  const t = clamp(score, 0, 1);
  switch (mode) {
    case "opportunity": {
      return `rgb(${Math.round(lerp(0x1e,0x10,t))},${Math.round(lerp(0x3a,0xb9,t))},${Math.round(lerp(0x5f,0x81,t))})`;
    }
    case "demand": {
      return `rgb(${Math.round(lerp(0x1a,0xef,t))},${Math.round(lerp(0x1a,0x44,t))},${Math.round(lerp(0x2e,0x44,t))})`;
    }
    case "inventory": {
      return `rgb(${Math.round(lerp(0x0f,0x3b,t))},${Math.round(lerp(0x17,0x82,t))},${Math.round(lerp(0x2a,0xf6,t))})`;
    }
    case "price_trend": {
      if (t < 0.5) {
        const u = t / 0.5;
        return `rgb(${Math.round(lerp(0xef,0x47,u))},${Math.round(lerp(0x44,0x55,u))},${Math.round(lerp(0x44,0x69,u))})`;
      }
      const u = (t - 0.5) / 0.5;
      return `rgb(${Math.round(lerp(0x47,0x05,u))},${Math.round(lerp(0x55,0x96,u))},${Math.round(lerp(0x69,0x69,u))})`;
    }
  }
}

function getModeScore(mode: VenueMode, section: VenueSection): number | null {
  const m = section.metrics;
  if (!m) return null;
  switch (mode) {
    case "opportunity": return m.value_score != null ? m.value_score / 100 : m.deal_score;
    case "demand": return m.demand_score;
    case "inventory": return m.listing_count != null ? clamp(m.listing_count / 30, 0, 1) : null;
    case "price_trend": {
      const pct = m.price_delta_pct_24h;
      return pct == null ? 0.5 : clamp(0.5 + pct / 40, 0, 1);
    }
  }
}

function SecRect({
  section, label, mode, selected, onClick,
  x, y, w, h, rx = 3,
}: {
  section?: VenueSection; label: string; mode: VenueMode;
  selected: boolean; onClick: () => void;
  x: number; y: number; w: number; h: number; rx?: number;
}) {
  const score = section ? getModeScore(mode, section) : null;
  const fill = section ? modeColor(mode, score) : "#111827";
  const hasData = section?.metrics != null;
  const labelLen = label.length;

  return (
    <g onClick={onClick} style={{ cursor: "pointer", userSelect: "none" }}>
      <rect x={x} y={y} width={w} height={h} rx={rx}
        fill={fill}
        stroke={selected ? "#fff" : "rgba(255,255,255,0.1)"}
        strokeWidth={selected ? 2 : 0.5}
        opacity={section ? 1 : 0.3}
      />
      {w > 16 && h > 8 && (
        <text
          x={x + w / 2} y={y + h / 2 + 1}
          textAnchor="middle" dominantBaseline="middle"
          fill={hasData ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.3)"}
          fontSize={Math.min(w / labelLen * 1.3, 8)}
          fontFamily="monospace"
          fontWeight={selected ? "700" : "400"}
        >{label}</text>
      )}
    </g>
  );
}

interface Props {
  sections: VenueSection[];
  mode: VenueMode;
  selectedId: string | null;
  onSelectSection: (id: string) => void;
}

export default function KiaForumMap({ sections, mode, selectedId, onSelectSection }: Props) {
  const byId = Object.fromEntries(sections.map((s) => [s.section_id, s]));
  const S = (id: string) => byId[id];
  const T = (id: string) => () => onSelectSection(id);
  const sel = (id: string) => selectedId === id;
  const hasAnyMetrics = sections.some((s) => s.metrics != null);

  return (
    <div className="rounded-xl border border-white/8 bg-[#0c1421] overflow-hidden">
      {!hasAnyMetrics && (
        <p className="text-[10px] text-slate-600 text-center px-4 pt-3">
          Metrics compute as listings are collected
        </p>
      )}
      <svg viewBox="0 0 480 460" className="w-full" aria-label="Kia Forum seating map">

        {/* Background circle */}
        <circle cx={240} cy={210} r={206} fill="#0a1220" stroke="rgba(255,255,255,0.05)" strokeWidth={1} />

        {/* Stage */}
        <rect x={192} y={376} width={96} height={26} rx={4}
          fill="#1d2d44" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
        <text x={240} y={392} textAnchor="middle" dominantBaseline="middle"
          fill="rgba(255,255,255,0.5)" fontSize={9} fontFamily="sans-serif" letterSpacing={1.5}>STAGE</text>

        {/* ── UPPER BOWL 200s (outer ring) ── */}
        {/* Stage arc (south) */}
        <SecRect section={S("220")} label="220" mode={mode} selected={sel("220")} onClick={T("220")} x={168} y={332} w={40} h={24} />
        <SecRect section={S("219")} label="219" mode={mode} selected={sel("219")} onClick={T("219")} x={214} y={340} w={52} h={24} />
        <SecRect section={S("218")} label="218" mode={mode} selected={sel("218")} onClick={T("218")} x={272} y={332} w={40} h={24} />

        {/* West arc */}
        <SecRect section={S("224")} label="224" mode={mode} selected={sel("224")} onClick={T("224")} x={60} y={298} w={38} h={22} />
        <SecRect section={S("225")} label="225" mode={mode} selected={sel("225")} onClick={T("225")} x={34} y={264} w={38} h={22} />
        <SecRect section={S("208")} label="208" mode={mode} selected={sel("208")} onClick={T("208")} x={22} y={230} w={38} h={24} />
        <SecRect section={S("207")} label="207" mode={mode} selected={sel("207")} onClick={T("207")} x={20} y={196} w={38} h={24} />
        <SecRect section={S("206")} label="206" mode={mode} selected={sel("206")} onClick={T("206")} x={24} y={162} w={38} h={22} />
        <SecRect section={S("205")} label="205" mode={mode} selected={sel("205")} onClick={T("205")} x={38} y={130} w={38} h={22} />

        {/* North arc (opposite stage) */}
        <SecRect section={S("204")} label="204" mode={mode} selected={sel("204")} onClick={T("204")} x={80} y={28} w={38} h={22} />
        <SecRect section={S("210")} label="210" mode={mode} selected={sel("210")} onClick={T("210")} x={130} y={12} w={46} h={22} />
        <SecRect section={S("211")} label="211" mode={mode} selected={sel("211")} onClick={T("211")} x={182} y={8} w={52} h={22} />
        <SecRect section={S("212")} label="212" mode={mode} selected={sel("212")} onClick={T("212")} x={240} y={8} w={52} h={22} />
        <SecRect section={S("213")} label="213" mode={mode} selected={sel("213")} onClick={T("213")} x={298} y={12} w={46} h={22} />

        {/* East arc */}
        <SecRect section={S("215")} label="215" mode={mode} selected={sel("215")} onClick={T("215")} x={362} y={130} w={38} h={22} />
        <SecRect section={S("216")} label="216" mode={mode} selected={sel("216")} onClick={T("216")} x={418} y={162} w={38} h={22} />
        <SecRect section={S("217")} label="217" mode={mode} selected={sel("217")} onClick={T("217")} x={422} y={196} w={38} h={24} />
        <SecRect section={S("229")} label="229" mode={mode} selected={sel("229")} onClick={T("229")} x={420} y={230} w={38} h={24} />
        <SecRect section={S("232")} label="232" mode={mode} selected={sel("232")} onClick={T("232")} x={408} y={264} w={38} h={22} />
        <SecRect section={S("233")} label="233" mode={mode} selected={sel("233")} onClick={T("233")} x={382} y={298} w={38} h={22} />

        {/* ── LOWER BOWL 100s (inner ring) ── */}
        {/* Stage arc */}
        <SecRect section={S("119")} label="119" mode={mode} selected={sel("119")} onClick={T("119")} x={172} y={290} w={36} h={24} />
        <SecRect section={S("120")} label="120" mode={mode} selected={sel("120")} onClick={T("120")} x={214} y={298} w={52} h={24} />
        <SecRect section={S("118")} label="118" mode={mode} selected={sel("118")} onClick={T("118")} x={272} y={290} w={36} h={24} />

        {/* West arc */}
        <SecRect section={S("126")} label="126" mode={mode} selected={sel("126")} onClick={T("126")} x={108} y={274} w={32} h={22} />
        <SecRect section={S("125")} label="125" mode={mode} selected={sel("125")} onClick={T("125")} x={86} y={246} w={32} h={22} />
        <SecRect section={S("124")} label="124" mode={mode} selected={sel("124")} onClick={T("124")} x={78} y={214} w={32} h={22} />
        <SecRect section={S("104")} label="104" mode={mode} selected={sel("104")} onClick={T("104")} x={82} y={182} w={32} h={22} />
        <SecRect section={S("107")} label="107" mode={mode} selected={sel("107")} onClick={T("107")} x={96} y={150} w={32} h={22} />

        {/* North arc */}
        <SecRect section={S("112")} label="112" mode={mode} selected={sel("112")} onClick={T("112")} x={148} y={82} w={34} h={22} />
        <SecRect section={S("113")} label="113" mode={mode} selected={sel("113")} onClick={T("113")} x={196} y={72} w={44} h={22} />
        <SecRect section={S("114")} label="114" mode={mode} selected={sel("114")} onClick={T("114")} x={248} y={72} w={44} h={22} />

        {/* East arc */}
        <SecRect section={S("113")} label="113" mode={mode} selected={sel("113")} onClick={T("113")} x={296} y={82} w={34} h={22} />
        <SecRect section={S("128")} label="128" mode={mode} selected={sel("128")} onClick={T("128")} x={352} y={150} w={32} h={22} />
        <SecRect section={S("129")} label="129" mode={mode} selected={sel("129")} onClick={T("129")} x={370} y={182} w={32} h={22} />
        <SecRect section={S("130")} label="130" mode={mode} selected={sel("130")} onClick={T("130")} x={370} y={214} w={32} h={22} />

        {/* ── FLOOR letter sections (center) ── */}
        <SecRect section={S("floor-a")} label="A" mode={mode} selected={sel("floor-a")} onClick={T("floor-a")} x={212} y={260} w={56} h={24} rx={4} />
        <SecRect section={S("floor-b")} label="B" mode={mode} selected={sel("floor-b")} onClick={T("floor-b")} x={162} y={242} w={40} h={22} rx={4} />
        <SecRect section={S("floor-c")} label="C" mode={mode} selected={sel("floor-c")} onClick={T("floor-c")} x={212} y={234} w={56} h={22} rx={4} />
        <SecRect section={S("floor-d")} label="D" mode={mode} selected={sel("floor-d")} onClick={T("floor-d")} x={278} y={242} w={40} h={22} rx={4} />
        <SecRect section={S("floor-e")} label="E" mode={mode} selected={sel("floor-e")} onClick={T("floor-e")} x={162} y={210} w={40} h={22} rx={4} />
        <SecRect section={S("floor-f")} label="F" mode={mode} selected={sel("floor-f")} onClick={T("floor-f")} x={212} y={208} w={56} h={22} rx={4} />
        <SecRect section={S("floor-g")} label="G" mode={mode} selected={sel("floor-g")} onClick={T("floor-g")} x={278} y={210} w={40} h={22} rx={4} />
        <SecRect section={S("floor-h")} label="H" mode={mode} selected={sel("floor-h")} onClick={T("floor-h")} x={212} y={184} w={56} h={22} rx={4} />

        {/* ── Special sections ── */}
        <SecRect section={S("lower-bowl-vip")} label="LB VIP" mode={mode} selected={sel("lower-bowl-vip")} onClick={T("lower-bowl-vip")} x={144} y={302} w={40} h={18} rx={3} />
        <SecRect section={S("upper-bowl-hot-seat")} label="HOT SEAT" mode={mode} selected={sel("upper-bowl-hot-seat")} onClick={T("upper-bowl-hot-seat")} x={196} y={356} w={88} h={18} rx={3} />

        {/* ── Zone labels ── */}
        <text x={240} y={38} textAnchor="middle" fill="rgba(255,255,255,0.15)" fontSize={8} fontFamily="sans-serif" letterSpacing={1.5}>UPPER BOWL</text>
        <text x={240} y={128} textAnchor="middle" fill="rgba(255,255,255,0.1)" fontSize={7} fontFamily="sans-serif">LOWER BOWL</text>
        <text x={240} y={220} textAnchor="middle" fill="rgba(255,255,255,0.1)" fontSize={7} fontFamily="sans-serif">FLOOR</text>
      </svg>
    </div>
  );
}
