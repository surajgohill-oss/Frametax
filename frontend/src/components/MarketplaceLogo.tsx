"use client";

// Real marketplace brand icons, served from local assets in /public/logos.
// Sources (official public brand assets, fetched 2026-07-09):
//   stubhub.png    — https://www.stubhub.com/apple-touch-icon.png (57×57)
//   tickpick.png   — https://www.tickpick.com/favicon.ico (PNG payload, 32×32)
//   gametime.svg   — https://assets.gametime.co/favicon/favicon_6d8ccee6ebffeabb9778.svg
//   vividseats.png — https://www.vividseats.com/apple-touch-icon.png (512×512)
const LOGO_SRC: Record<string, string> = {
  stubhub:    "/logos/stubhub.png",
  tickpick:   "/logos/tickpick.png",
  gametime:   "/logos/gametime.svg",
  vividseats: "/logos/vividseats.png",
};

// Brand color for the fallback tile (unknown marketplaces only).
const FALLBACK_BG = "#334155";

/** Real marketplace logo tile; falls back to a two-letter tile for unknown slugs. */
export default function MarketplaceLogo({ slug, size = 16 }: { slug: string; size?: number }) {
  const src = LOGO_SRC[slug];
  const radius = Math.max(3, Math.round(size * 0.22));

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt={slug}
        role="img"
        aria-label={slug}
        width={size}
        height={size}
        className="flex-shrink-0 object-contain"
        style={{ width: size, height: size, borderRadius: radius }}
        loading="lazy"
      />
    );
  }

  return (
    <span
      role="img"
      aria-label={slug}
      className="flex items-center justify-center flex-shrink-0 font-black text-white uppercase"
      style={{ width: size, height: size, borderRadius: radius, background: FALLBACK_BG, fontSize: Math.round(size * 0.42) }}
    >
      {slug.slice(0, 2)}
    </span>
  );
}
