"use client";
import { useState, useEffect, useCallback } from "react";

const KEY = "hero_event_id";

export function useHeroEvent() {
  const [heroEventId, setHeroEventId] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const raw = localStorage.getItem(KEY);
      setHeroEventId(raw ? parseInt(raw, 10) : null);
    } catch {}
  }, []);

  const setHero = useCallback((id: number) => {
    setHeroEventId((prev) => {
      const next = prev === id ? null : id;
      try {
        if (next !== null) localStorage.setItem(KEY, String(next));
        else localStorage.removeItem(KEY);
      } catch {}
      return next;
    });
  }, []);

  const clearHero = useCallback(() => {
    setHeroEventId(null);
    try { localStorage.removeItem(KEY); } catch {}
  }, []);

  return { heroEventId, setHero, clearHero, mounted };
}
