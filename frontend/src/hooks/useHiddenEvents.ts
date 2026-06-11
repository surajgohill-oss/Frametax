"use client";
import { useState, useEffect, useCallback } from "react";

const KEY = "hidden_events";

export function useHiddenEvents() {
  const [hiddenEvents, setHiddenEvents] = useState<Set<number>>(new Set());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setHiddenEvents(new Set(JSON.parse(raw) as number[]));
    } catch {}
  }, []);

  const hide = useCallback((id: number) => {
    setHiddenEvents((prev) => {
      const next = new Set(prev);
      next.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  const unhide = useCallback((id: number) => {
    setHiddenEvents((prev) => {
      const next = new Set(prev);
      next.delete(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  const toggle = useCallback((id: number) => {
    setHiddenEvents((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  return { hiddenEvents, hide, unhide, toggle, mounted };
}
