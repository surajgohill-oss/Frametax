"use client";
import { useState, useEffect, useCallback } from "react";

// ── Exclusion record ──────────────────────────────────────────────────────────
// Exclusions are stored in localStorage scoped per event.
// BACKEND DEPENDENCY: exclusions currently only affect the local UI.
// To propagate exclusions into intelligence calculations, inventory counts,
// charts, and section/seller metrics, the backend needs a POST
// /api/events/{id}/exclusions endpoint that accepts { key, reason, timestamp }.
// Until that endpoint exists, excluded sections are visually marked and
// filtered from the local summary modules, but the hero metrics and API
// responses will still reflect the unexcluded data.

export interface ExclusionRecord {
  key: string;        // section display_name (the stable identifier we have)
  reason?: string;    // user-provided or auto (e.g. "parking", "bad_listing")
  timestamp: string;  // ISO 8601
  eventId: number;
}

function lsKey(eventId: number) {
  return `ct_excl_v1_${eventId}`;
}

export function useExclusions(eventId: number) {
  const [items, setItems] = useState<ExclusionRecord[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const raw = localStorage.getItem(lsKey(eventId));
      if (raw) setItems(JSON.parse(raw) as ExclusionRecord[]);
    } catch {}
  }, [eventId]);

  const exclude = useCallback(
    (key: string, reason?: string) => {
      setItems((prev) => {
        if (prev.some((e) => e.key === key)) return prev;
        const next: ExclusionRecord[] = [
          ...prev,
          { key, reason, timestamp: new Date().toISOString(), eventId },
        ];
        try { localStorage.setItem(lsKey(eventId), JSON.stringify(next)); } catch {}
        return next;
      });
    },
    [eventId],
  );

  const restore = useCallback(
    (key: string) => {
      setItems((prev) => {
        const next = prev.filter((e) => e.key !== key);
        try { localStorage.setItem(lsKey(eventId), JSON.stringify(next)); } catch {}
        return next;
      });
    },
    [eventId],
  );

  const isExcluded = useCallback(
    (key: string) => items.some((e) => e.key === key),
    [items],
  );

  return { items, exclude, restore, isExcluded, mounted };
}
