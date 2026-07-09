"use client";

// Marketplace brand config — real brand colors, text-only logos until SVG assets arrive
export const MP_BRAND: Record<string, {
  label: string;
  short: string;
  fullName: string;
  color: string;       // primary brand color
  bg: string;          // tinted background
  border: string;      // tinted border
  textColor: string;   // readable text on dark bg
}> = {
  stubhub: {
    label: "StubHub", short: "SH", fullName: "StubHub",
    color: "#e05c2a",
    bg: "rgba(224,92,42,0.08)",
    border: "rgba(224,92,42,0.25)",
    textColor: "#f0844a",
  },
  tickpick: {
    label: "TickPick", short: "TP", fullName: "TickPick",
    color: "#2563eb",
    bg: "rgba(37,99,235,0.08)",
    border: "rgba(37,99,235,0.25)",
    textColor: "#60a5fa",
  },
  gametime: {
    label: "Gametime", short: "GT", fullName: "Gametime",
    color: "#16a34a",
    bg: "rgba(22,163,74,0.08)",
    border: "rgba(22,163,74,0.25)",
    textColor: "#4ade80",
  },
  vividseats: {
    label: "Vivid Seats", short: "VS", fullName: "Vivid Seats",
    color: "#7c3aed",
    bg: "rgba(124,58,237,0.08)",
    border: "rgba(124,58,237,0.25)",
    textColor: "#a78bfa",
  },
};

export function fallbackBrand(slug: string) {
  return {
    label: slug, short: slug.slice(0, 2).toUpperCase(), fullName: slug,
    color: "#60a5fa", bg: "rgba(96,165,250,0.08)",
    border: "rgba(96,165,250,0.2)", textColor: "#60a5fa",
  };
}

export function getBrand(slug: string) {
  return MP_BRAND[slug] ?? fallbackBrand(slug);
}

interface Props {
  slug: string;
  size?: "sm" | "md";
  /** If true, show full name; otherwise abbreviation */
  full?: boolean;
}

/** Inline branded marketplace pill */
export default function MarketplaceBadge({ slug, size = "sm", full = false }: Props) {
  const b = getBrand(slug);
  const label = full ? b.label : b.short;

  if (size === "md") {
    return (
      <span
        className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md border tracking-wide"
        style={{ color: b.textColor, background: b.bg, borderColor: b.border }}
      >
        <span
          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
          style={{ background: b.color }}
        />
        {label}
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center text-[8px] font-bold px-1.5 py-0.5 rounded border tracking-wider uppercase"
      style={{ color: b.textColor, background: b.bg, borderColor: b.border }}
    >
      {label}
    </span>
  );
}
