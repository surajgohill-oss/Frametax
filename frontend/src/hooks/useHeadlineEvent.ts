"use client";
import { useState, useEffect } from "react";

const KEY = "awr_headline_event";

/**
 * localStorage-based pinned headline event.
 * Falls back to best-opportunity event when nothing is pinned.
 */
export function useHeadlineEvent() {
  const [pinnedId, setPinnedId] = useState<number | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(KEY);
    if (stored) {
      const parsed = parseInt(stored, 10);
      if (!isNaN(parsed)) setPinnedId(parsed);
    }
    setMounted(true);
  }, []);

  function pin(id: number) {
    localStorage.setItem(KEY, String(id));
    setPinnedId(id);
  }

  function clear() {
    localStorage.removeItem(KEY);
    setPinnedId(null);
  }

  function toggle(id: number) {
    if (pinnedId === id) clear();
    else pin(id);
  }

  return {
    pinnedId: mounted ? pinnedId : null,
    isPinned: (id: number) => mounted && pinnedId === id,
    pin,
    clear,
    toggle,
    mounted,
  };
}
