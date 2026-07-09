import { cn } from "@/lib/utils";
import type { FreshnessStatus } from "@/lib/types";

export type MarketplaceSlug = "stubhub" | "gametime" | "tickpick" | "vividseats";

interface Props {
  marketplace: string;
  size?: "sm" | "md" | "lg";
  variant?: "badge" | "icon" | "text" | "full";
}

// Lightweight local SVG marks in each marketplace's brand palette.
// Self-contained (no remote assets) so they render offline and in mock mode.
const MARKS: Record<MarketplaceSlug, { name: string; color: string; textClass: string; svg: (px: number) => React.ReactNode }> = {
  stubhub: {
    name: "StubHub",
    color: "#6236ff",
    textClass: "text-violet-400",
    // ticket silhouette with notches — StubHub violet
    svg: (px) => (
      <svg width={px} height={px} viewBox="0 0 24 24" aria-label="StubHub">
        <rect x="2" y="6" width="20" height="12" rx="2.5" fill="#6236ff" />
        <circle cx="2" cy="12" r="2.2" fill="#0f1117" />
        <circle cx="22" cy="12" r="2.2" fill="#0f1117" />
        <text x="12" y="15.5" textAnchor="middle" fontSize="9" fontWeight="800" fill="#fff" fontFamily="system-ui">S</text>
      </svg>
    ),
  },
  tickpick: {
    name: "TickPick",
    color: "#2f7cf6",
    textClass: "text-blue-400",
    // blue roundel with check — TickPick blue
    svg: (px) => (
      <svg width={px} height={px} viewBox="0 0 24 24" aria-label="TickPick">
        <circle cx="12" cy="12" r="10" fill="#2f7cf6" />
        <path d="M7 12.4l3.2 3.2L17 8.8" stroke="#fff" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  gametime: {
    name: "Gametime",
    color: "#19cf85",
    textClass: "text-emerald-400",
    // green play-bolt — Gametime green
    svg: (px) => (
      <svg width={px} height={px} viewBox="0 0 24 24" aria-label="Gametime">
        <rect x="2" y="2" width="20" height="20" rx="5" fill="#19cf85" />
        <path d="M13.8 4.5L7.5 13.2h3.6l-.9 6.3 6.3-8.7h-3.6l.9-6.3z" fill="#04331f" />
      </svg>
    ),
  },
  vividseats: {
    name: "Vivid Seats",
    color: "#e4002b",
    textClass: "text-red-400",
    // red seat-V mark — Vivid Seats red
    svg: (px) => (
      <svg width={px} height={px} viewBox="0 0 24 24" aria-label="Vivid Seats">
        <circle cx="12" cy="12" r="10" fill="#e4002b" />
        <path d="M7 7l5 10 5-10h-2.8L12 11.8 9.8 7z" fill="#fff" />
      </svg>
    ),
  },
};

const PX = { sm: 14, md: 18, lg: 24 };

export function marketplaceDisplayName(slug: string): string {
  return MARKS[slug as MarketplaceSlug]?.name ?? slug;
}

export function MarketplaceLogo({ marketplace, size = "md", variant = "full" }: Props) {
  const mark = MARKS[marketplace as MarketplaceSlug];
  if (!mark) return <span className="text-slate-400 text-xs">{marketplace}</span>;
  const px = PX[size];

  if (variant === "icon") return <span className="inline-flex flex-shrink-0">{mark.svg(px)}</span>;

  if (variant === "text") {
    return <span className={cn("font-semibold", mark.textClass, size === "sm" ? "text-xs" : "text-sm")}>{mark.name}</span>;
  }

  // "full" (default) and legacy "badge": logo mark + name
  return (
    <span className="inline-flex items-center gap-1.5">
      {mark.svg(px)}
      <span className={cn("font-semibold text-slate-200", size === "sm" ? "text-xs" : "text-sm")}>{mark.name}</span>
    </span>
  );
}

// ── Freshness chip ────────────────────────────────────────────────────────────
// Single source of truth for feed-health colors:
//   fresh = green · late = amber · stale = red · dead = deep red
export const FRESHNESS_STYLES: Record<FreshnessStatus, { dot: string; text: string; bg: string; label: string }> = {
  fresh: { dot: "bg-emerald-400", text: "text-emerald-400", bg: "bg-emerald-500/10", label: "Fresh" },
  late:  { dot: "bg-amber-400",   text: "text-amber-400",   bg: "bg-amber-500/10",   label: "Late" },
  stale: { dot: "bg-red-400",     text: "text-red-400",     bg: "bg-red-500/10",     label: "Stale" },
  dead:  { dot: "bg-red-600",     text: "text-red-500",     bg: "bg-red-500/15",     label: "Dead" },
};

export function freshnessAgeLabel(ageMinutes: number | null | undefined): string | null {
  if (ageMinutes == null) return null;
  if (ageMinutes < 60) return `${Math.round(ageMinutes)}m ago`;
  if (ageMinutes < 48 * 60) return `${Math.round(ageMinutes / 60)}h ago`;
  return `${Math.round(ageMinutes / 1440)}d ago`;
}

export function MarketplaceFreshnessChip({
  marketplace,
  status,
  ageMinutes,
  size = "sm",
}: {
  marketplace: string;
  status: FreshnessStatus;
  ageMinutes?: number | null;
  size?: "sm" | "md";
}) {
  const s = FRESHNESS_STYLES[status] ?? FRESHNESS_STYLES.stale;
  const age = freshnessAgeLabel(ageMinutes);
  const unhealthy = status === "stale" || status === "dead";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5",
        s.bg,
        unhealthy ? "border-red-500/25" : "border-white/8",
      )}
      title={`${marketplaceDisplayName(marketplace)} — ${s.label}${age ? ` · ${age}` : ""}`}
    >
      <MarketplaceLogo marketplace={marketplace} size="sm" variant="icon" />
      <span className={cn("rounded-full flex-shrink-0", s.dot, size === "sm" ? "w-1.5 h-1.5" : "w-2 h-2")} />
      {size === "md" && (
        <span className={cn("text-[10px] font-semibold", s.text)}>
          {s.label}
          {age && unhealthy ? ` ${age}` : ""}
        </span>
      )}
    </span>
  );
}
