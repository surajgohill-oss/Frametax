"use client";

/**
 * CryptoArenaMap
 * Schematic arena map for Crypto.com Arena (concert config).
 * SVG layout: oval arena, stage at bottom.
 * Rings: Floor (center) → Lower bowl (100s) → Upper bowl (300s)
 * PR sections shown as a strip along the floor perimeter.
 */

import type { VenueSection } from "@/lib/types";
import type { VenueMode } from "./SofiVenueMap";
import { cn } from "@/lib/utils";

// ── Color helpers (shared with other maps) ────────────────────────────────────

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * clamp(t, 0, 1);
}

function modeColor(mode: VenueMode, score: number | null): string {
  if (score == null) return "#1a2535";
  const t = clamp(score, 0, 1);
  switch (mode) {
    case "opportunity": {
      const r = Math.round(lerp(0x1e, 0x10, t));
      const g = Math.round(lerp(0x3a, 0xb9, t));
      const b = Math.round(lerp(0x5f, 0x81, t));
      return `rgb(${r},${g},${b})`;
    }
    case "demand": {
      const r = Math.round(lerp(0x1a, 0xef, t));
      const g = Math.round(lerp(0x1a, 0x44, t));
      const b = Math.round(lerp(0x2e, 0x44, t));
      return `rgb(${r},${g},${b})`;
    }
    case "inventory": {
      const r = Math.round(lerp(0x0f, 0x3b, t));
      const g = Math.round(lerp(0x17, 0x82, t));
      const b = Math.round(lerp(0x2a, 0xf6, t));
      return `rgb(${r},${g},${b})`;
    }
    case "price_trend": {
      if (t < 0.5) {
        const u = t / 0.5;
        return `rgb(${Math.round(lerp(0xef,0x47,u))},${Math.round(lerp(0x44,0x55,u))},${Math.round(lerp(0x44,0x69,u))})`;
      } else {
        const u = (t - 0.5) / 0.5;
        return `rgb(${Math.round(lerp(0x47,0x05,u))},${Math.round(lerp(0x55,0x96,u))},${Math.round(lerp(0x69,0x69,u))})`;
      }
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
      if (pct == null) return 0.5;
      return clamp(0.5 + pct / 40, 0, 1);
    }
  }
}

// ── Section → section_id mapping for the SVG ─────────────────────────────────
// Maps the future_map_key or section_id to a position in the SVG

interface SectionProps {
  section: VenueSection | undefined;
  label: string;
  mode: VenueMode;
  selected: boolean;
  onClick: () => void;
  // SVG position
  x: number;
  y: number;
  width: number;
  height: number;
  rx?: number;
}

function SectionRect({ section, label, mode, selected, onClick, x, y, width, height, rx = 3 }: SectionProps) {
  const score = section ? getModeScore(mode, section) : null;
  const fill = section ? modeColor(mode, score) : "#111827";
  const hasData = section?.metrics != null;

  return (
    <g onClick={onClick} className="cursor-pointer" style={{ userSelect: "none" }}>
      <rect
        x={x} y={y} width={width} height={height} rx={rx}
        fill={fill}
        stroke={selected ? "#fff" : "rgba(255,255,255,0.12)"}
        strokeWidth={selected ? 2 : 0.5}
        opacity={section ? 1 : 0.35}
      />
      {width > 18 && height > 9 && (
        <text
          x={x + width / 2} y={y + height / 2 + 1}
          textAnchor="middle" dominantBaseline="middle"
          fill={hasData ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.3)"}
          fontSize={Math.min(width / label.length * 1.4, 8)}
          fontFamily="monospace"
          fontWeight={selected ? "700" : "400"}
        >
          {label}
        </text>
      )}
    </g>
  );
}

// ── Main map ──────────────────────────────────────────────────────────────────

interface Props {
  sections: VenueSection[];
  mode: VenueMode;
  selectedId: string | null;
  onSelectSection: (id: string) => void;
}

export default function CryptoArenaMap({ sections, mode, selectedId, onSelectSection }: Props) {
  const byId = Object.fromEntries(sections.map((s) => [s.section_id, s]));

  function sec(id: string) {
    return byId[id];
  }

  function toggle(id: string) {
    onSelectSection(id);
  }

  const hasAnyMetrics = sections.some((s) => s.metrics != null);

  // SVG canvas 480 × 440
  // Arena oval centered at (240, 220)
  // Stage at bottom (south)

  return (
    <div className="rounded-xl border border-white/8 bg-[#0c1421] overflow-hidden">
      {!hasAnyMetrics && (
        <div className="px-4 pt-3 pb-0">
          <p className="text-[10px] text-slate-600 text-center">
            Metrics compute as listings are collected · Click a section for detail
          </p>
        </div>
      )}

      <svg viewBox="0 0 480 460" className="w-full" aria-label="Crypto.com Arena seating map">

        {/* ── Background oval — upper bowl outline ── */}
        <ellipse cx={240} cy={218} rx={220} ry={200} fill="#0a1220" stroke="rgba(255,255,255,0.06)" strokeWidth={1} />

        {/* ── Stage at bottom ── */}
        <rect x={190} y={388} width={100} height={28} rx={4}
          fill="#1d2d44" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
        <text x={240} y={405} textAnchor="middle" dominantBaseline="middle"
          fill="rgba(255,255,255,0.5)" fontSize={9} fontFamily="sans-serif" letterSpacing={1.5}>
          STAGE
        </text>

        {/* ════════════════════════════════════════════════
            UPPER BOWL — 300s (outer ring, 13 sections shown)
        ════════════════════════════════════════════════ */}

        {/* Upper stage-side: 301, 303, 333 (bottom arc) */}
        <SectionRect section={sec("301")} label="301" mode={mode} selected={selectedId==="301"} onClick={()=>toggle("301")}
          x={168} y={330} width={42} height={26} />
        <SectionRect section={sec("303")} label="303" mode={mode} selected={selectedId==="303"} onClick={()=>toggle("303")}
          x={216} y={338} width={48} height={26} />
        <SectionRect section={sec("333")} label="333" mode={mode} selected={selectedId==="333"} onClick={()=>toggle("333")}
          x={270} y={330} width={42} height={26} />

        {/* Upper west side: 304, 305, 308 (left arc) */}
        <SectionRect section={sec("304")} label="304" mode={mode} selected={selectedId==="304"} onClick={()=>toggle("304")}
          x={30} y={278} width={42} height={26} />
        <SectionRect section={sec("305")} label="305" mode={mode} selected={selectedId==="305"} onClick={()=>toggle("305")}
          x={22} y={236} width={42} height={28} />
        <SectionRect section={sec("308")} label="308" mode={mode} selected={selectedId==="308"} onClick={()=>toggle("308")}
          x={22} y={192} width={42} height={28} />
        <SectionRect section={sec("315")} label="315" mode={mode} selected={selectedId==="315"} onClick={()=>toggle("315")}
          x={28} y={150} width={42} height={26} />

        {/* Upper north (opposite): 316, 318, 320, 321 (top arc) */}
        <SectionRect section={sec("316")} label="316" mode={mode} selected={selectedId==="316"} onClick={()=>toggle("316")}
          x={96} y={26} width={42} height={24} />
        <SectionRect section={sec("318")} label="318" mode={mode} selected={selectedId==="318"} onClick={()=>toggle("318")}
          x={150} y={18} width={48} height={24} />
        <SectionRect section={sec("320")} label="320" mode={mode} selected={selectedId==="320"} onClick={()=>toggle("320")}
          x={204} y={14} width={48} height={24} />
        <SectionRect section={sec("321")} label="321" mode={mode} selected={selectedId==="321"} onClick={()=>toggle("321")}
          x={258} y={18} width={48} height={24} />

        {/* Upper east side: 331, 332 (right arc) */}
        <SectionRect section={sec("331")} label="331" mode={mode} selected={selectedId==="331"} onClick={()=>toggle("331")}
          x={406} y={192} width={42} height={28} />
        <SectionRect section={sec("332")} label="332" mode={mode} selected={selectedId==="332"} onClick={()=>toggle("332")}
          x={406} y={236} width={42} height={28} />

        {/* ════════════════════════════════════════════════
            LOWER BOWL — 100s (inner ring)
        ════════════════════════════════════════════════ */}

        {/* Lower stage-side: 101-104 (bottom arc) */}
        <SectionRect section={sec("101")} label="101" mode={mode} selected={selectedId==="101"} onClick={()=>toggle("101")}
          x={170} y={284} width={36} height={28} />
        <SectionRect section={sec("102")} label="102" mode={mode} selected={selectedId==="102"} onClick={()=>toggle("102")}
          x={210} y={292} width={40} height={28} />
        <SectionRect section={sec("103")} label="103" mode={mode} selected={selectedId==="103"} onClick={()=>toggle("103")}
          x={254} y={284} width={36} height={28} />

        {/* Lower west side: 105-109 */}
        <SectionRect section={sec("105")} label="105" mode={mode} selected={selectedId==="105"} onClick={()=>toggle("105")}
          x={100} y={278} width={36} height={26} />
        <SectionRect section={sec("106")} label="106" mode={mode} selected={selectedId==="106"} onClick={()=>toggle("106")}
          x={82} y={240} width={36} height={26} />
        <SectionRect section={sec("107")} label="107" mode={mode} selected={selectedId==="107"} onClick={()=>toggle("107")}
          x={82} y={206} width={36} height={26} />
        <SectionRect section={sec("108")} label="108" mode={mode} selected={selectedId==="108"} onClick={()=>toggle("108")}
          x={90} y={172} width={36} height={26} />
        <SectionRect section={sec("109")} label="109" mode={mode} selected={selectedId==="109"} onClick={()=>toggle("109")}
          x={104} y={142} width={36} height={26} />

        {/* Lower north (opposite): 112-115 */}
        <SectionRect section={sec("112")} label="112" mode={mode} selected={selectedId==="112"} onClick={()=>toggle("112")}
          x={152} y={80} width={36} height={26} />
        <SectionRect section={sec("113")} label="113" mode={mode} selected={selectedId==="113"} onClick={()=>toggle("113")}
          x={200} y={70} width={40} height={26} />
        <SectionRect section={sec("114")} label="114" mode={mode} selected={selectedId==="114"} onClick={()=>toggle("114")}
          x={246} y={70} width={40} height={26} />

        {/* Lower east side: 117-119 */}
        <SectionRect section={sec("117")} label="117" mode={mode} selected={selectedId==="117"} onClick={()=>toggle("117")}
          x={340} y={142} width={36} height={26} />
        <SectionRect section={sec("118")} label="118" mode={mode} selected={selectedId==="118"} onClick={()=>toggle("118")}
          x={354} y={172} width={36} height={26} />
        <SectionRect section={sec("119")} label="119" mode={mode} selected={selectedId==="119"} onClick={()=>toggle("119")}
          x={362} y={206} width={36} height={26} />
        <SectionRect section={sec("110")} label="110" mode={mode} selected={selectedId==="110"} onClick={()=>toggle("110")}
          x={362} y={240} width={36} height={26} />
        <SectionRect section={sec("112")} label="112" mode={mode} selected={selectedId==="112"} onClick={()=>toggle("112")}
          x={344} y={278} width={36} height={26} />

        {/* ════════════════════════════════════════════════
            FLOOR sections (center rectangle)
        ════════════════════════════════════════════════ */}
        {/* Floor 4, 5, 6 visible from listings */}
        <SectionRect section={sec("floor-4")} label="FL 4" mode={mode} selected={selectedId==="floor-4"} onClick={()=>toggle("floor-4")}
          x={162} y={214} width={46} height={32} rx={4} />
        <SectionRect section={sec("floor-5")} label="FL 5" mode={mode} selected={selectedId==="floor-5"} onClick={()=>toggle("floor-5")}
          x={214} y={200} width={52} height={32} rx={4} />
        <SectionRect section={sec("floor-6")} label="FL 6" mode={mode} selected={selectedId==="floor-6"} onClick={()=>toggle("floor-6")}
          x={272} y={214} width={46} height={32} rx={4} />

        {/* Floor 1-3 (stage-closest — above stage label) */}
        <SectionRect section={sec("floor-1")} label="FL 1" mode={mode} selected={selectedId==="floor-1"} onClick={()=>toggle("floor-1")}
          x={168} y={260} width={42} height={26} rx={4} />
        <SectionRect section={sec("floor-2")} label="FL 2" mode={mode} selected={selectedId==="floor-2"} onClick={()=>toggle("floor-2")}
          x={216} y={264} width={48} height={26} rx={4} />
        <SectionRect section={sec("floor-3")} label="FL 3" mode={mode} selected={selectedId==="floor-3"} onClick={()=>toggle("floor-3")}
          x={270} y={260} width={42} height={26} rx={4} />

        {/* Floor 7-8 (far from stage) */}
        <SectionRect section={sec("floor-7")} label="FL 7" mode={mode} selected={selectedId==="floor-7"} onClick={()=>toggle("floor-7")}
          x={168} y={176} width={42} height={26} rx={4} />
        <SectionRect section={sec("floor-8")} label="FL 8" mode={mode} selected={selectedId==="floor-8"} onClick={()=>toggle("floor-8")}
          x={270} y={176} width={42} height={26} rx={4} />

        {/* ════════════════════════════════════════════════
            PR (Premium Row) sections — floor-level strip
        ════════════════════════════════════════════════ */}
        <SectionRect section={sec("pr-2")} label="PR 2" mode={mode} selected={selectedId==="pr-2"} onClick={()=>toggle("pr-2")}
          x={130} y={218} width={28} height={18} rx={2} />
        <SectionRect section={sec("pr-15")} label="PR15" mode={mode} selected={selectedId==="pr-15"} onClick={()=>toggle("pr-15")}
          x={322} y={218} width={28} height={18} rx={2} />

        {/* ── Labels ── */}
        <text x={240} y={52} textAnchor="middle" fill="rgba(255,255,255,0.18)" fontSize={8} fontFamily="sans-serif" letterSpacing={1.5}>UPPER BOWL</text>
        <text x={240} y={130} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={7} fontFamily="sans-serif" letterSpacing={1}>LOWER BOWL</text>
        <text x={240} y={198} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={7} fontFamily="sans-serif">FLOOR</text>
      </svg>
    </div>
  );
}
