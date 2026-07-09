"use client";

import { useState, useEffect, useCallback } from "react";

const KEY = "awr_watchlist_events";

export function useWatchlist() {
  const [watched, setWatched] = useState<Set<number>>(new Set());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setWatched(new Set(JSON.parse(raw) as number[]));
    } catch {}
    setMounted(true);
  }, []);

  const toggle = useCallback((id: number) => {
    setWatched((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  const add = useCallback((id: number) => {
    setWatched((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  const remove = useCallback((id: number) => {
    setWatched((prev) => {
      if (!prev.has(id)) return prev;
      const next = new Set(prev);
      next.delete(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  return { watched, toggle, add, remove, mounted };
}
