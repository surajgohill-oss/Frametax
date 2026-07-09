"use client";
import { useState, useEffect } from "react";
import { getStaticArtUrl } from "@/lib/entityimages";

// Manual overrides for artists where Wikipedia title differs from display name
// or where we want a specific Wikipedia page
const WIKI_OVERRIDES: Record<string, string> = {
  "bts":                 "BTS_(band)",
  "bts world tour":      "BTS_(band)",
  "nfl":                 "National_Football_League",
  "san francisco 49ers": "San_Francisco_49ers",
  "49ers":               "San_Francisco_49ers",
  "la philharmonic":     "Los_Angeles_Philharmonic",
  "morgan jay":          "Morgan_Jay", // LA comedian — try Wikipedia, fall to gradient on miss
  "fifa world cup":      "FIFA_World_Cup",
};

// Module-level cache — persists across re-renders and component remounts
const _cache = new Map<string, string | null>();

function wikiTitle(artistKey: string): string | null {
  if (WIKI_OVERRIDES[artistKey] === "") return null; // explicitly no page
  if (WIKI_OVERRIDES[artistKey]) return WIKI_OVERRIDES[artistKey];
  // Convert display name to Wikipedia title format
  return artistKey.split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join("_");
}

/**
 * Fetches an artist/team photo from Wikipedia's public REST API (no key required, CORS-enabled).
 * Falls back to null → caller should use gradient.
 * Results are cached module-level so subsequent renders are instant.
 */
export function useArtistImage(
  artist: string | null | undefined,
  title?: string | null,
): string | null {
  const rawKey = ((artist ?? title) ?? "").toLowerCase().trim();
  // Strip tour names / event suffixes to get the core artist key
  const artistKey = rawKey
    .replace(/:\s*.+$/, "")   // "ariana grande: eternal sunshine tour" → "ariana grande"
    .replace(/\s+world\s+tour.*$/, "") // strip "world tour..."
    .trim();

  const [url, setUrl] = useState<string | null>(() => {
    // Return static art immediately (no fetch latency) if available
    const staticUrl = getStaticArtUrl(artistKey, title ?? "");
    if (staticUrl) return staticUrl;
    const cached = _cache.get(artistKey);
    return cached !== undefined ? cached : null;
  });

  useEffect(() => {
    if (!artistKey) return;
    // If cache already has this key (e.g. populated by another page), update state directly
    if (_cache.has(artistKey)) {
      setUrl(_cache.get(artistKey) ?? null);
      return;
    }

    const title = wikiTitle(artistKey);
    if (!title) {
      _cache.set(artistKey, null);
      return;
    }

    const controller = new AbortController();
    fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`,
      { signal: controller.signal },
    )
      .then(r => (r.ok ? r.json() : null))
      .then((data: { thumbnail?: { source: string } } | null) => {
        const imgUrl = data?.thumbnail?.source ?? null;
        _cache.set(artistKey, imgUrl);
        setUrl(imgUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) _cache.set(artistKey, null);
      });

    return () => controller.abort();
  }, [artistKey]);

  return url;
}
