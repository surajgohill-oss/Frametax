"use client";
import { useState, useEffect, useCallback, useRef } from "react";

export type ArtistFollowScope = "next3" | "next5" | "next10" | "all_future";
export type TeamFollowScope   = "home" | "away" | "both" | "next5" | "next10" | "season";

export interface ArtistFollow {
  type: "artist";
  key: string;
  displayName: string;
  scope: ArtistFollowScope;
  since: string;
  id?: number;   // backend row id (absent for optimistic entries)
}

export interface TeamFollow {
  type: "team";
  key: string;
  displayName: string;
  scope: TeamFollowScope;
  since: string;
  id?: number;
}

export type FollowEntry = ArtistFollow | TeamFollow;

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "https://backend-production-509f.up.railway.app";

// ── localStorage fallback key (used only when API is unreachable) ─────────────
const LS_KEY = "awr_follows";

function lsLoad(): FollowEntry[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? (JSON.parse(raw) as FollowEntry[]) : [];
  } catch { return []; }
}

// ── API helpers ───────────────────────────────────────────────────────────────

interface BackendFollow {
  id: number;
  entity_type: string;
  entity_key: string;
  display_name: string;
  scope_type: string;
  scope_anchor: string;
  status: string;
  created_at: string;
}

function backendToEntry(f: BackendFollow): FollowEntry {
  const base = {
    key: f.entity_key,
    displayName: f.display_name,
    since: f.scope_anchor,
    id: f.id,
  };
  if (f.entity_type === "artist") {
    return { type: "artist", ...base, scope: f.scope_type as ArtistFollowScope };
  }
  return { type: "team", ...base, scope: f.scope_type as TeamFollowScope };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useFollowArtist() {
  const [follows, setFollows] = useState<FollowEntry[]>([]);
  const [mounted, setMounted] = useState(false);
  // Track backend id by entity key for deletes
  const idMapRef = useRef<Map<string, number>>(new Map());

  // Load follows from backend on mount; fall back to localStorage if unreachable
  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        const data = await apiFetch<BackendFollow[]>("/api/follows");
        if (cancelled) return;
        const entries = data.map(backendToEntry);
        // Rebuild id map
        const newMap = new Map<string, number>();
        data.forEach(f => newMap.set(f.entity_key, f.id));
        idMapRef.current = newMap;
        setFollows(entries);
      } catch {
        // API unreachable — fall back to localStorage
        if (!cancelled) setFollows(lsLoad());
      } finally {
        if (!cancelled) setMounted(true);
      }
    }
    init();
    return () => { cancelled = true; };
  }, []);

  const follow = useCallback((entry: Omit<FollowEntry, "since">) => {
    const key   = entry.key.trim().toLowerCase();
    const since = new Date().toISOString();

    // Optimistic update
    setFollows(prev => {
      const next = prev.filter(f => !(f.key === key && f.type === entry.type));
      next.push({ ...entry, key, since } as FollowEntry);
      return next;
    });

    // Persist to backend
    apiFetch<BackendFollow>("/api/follows", {
      method: "POST",
      body: JSON.stringify({
        entity_type:  entry.type,
        entity_key:   key,
        display_name: entry.displayName,
        scope_type:   entry.scope,
      }),
    })
      .then(saved => {
        idMapRef.current.set(key, saved.id);
        // Sync since from server response (scope_anchor)
        setFollows(prev => prev.map(f =>
          f.key === key && f.type === entry.type
            ? { ...f, since: saved.scope_anchor, id: saved.id }
            : f
        ));
      })
      .catch(() => {
        // Backend write failed — keep localStorage fallback
        try {
          const snap = follows.filter(f => !(f.key === key && f.type === entry.type));
          snap.push({ ...entry, key, since } as FollowEntry);
          localStorage.setItem(LS_KEY, JSON.stringify(snap));
        } catch {}
      });
  }, [follows]);

  const unfollow = useCallback((key: string) => {
    const normKey = key.trim().toLowerCase();

    setFollows(prev => {
      const next = prev.filter(f => f.key !== normKey);
      return next;
    });

    const backendId = idMapRef.current.get(normKey);
    if (backendId !== undefined) {
      apiFetch<void>(`/api/follows/${backendId}`, { method: "DELETE" })
        .then(() => idMapRef.current.delete(normKey))
        .catch(() => {});
    }
  }, []);

  const getFollow = useCallback((key: string): FollowEntry | undefined => {
    return follows.find(f => f.key === key.trim().toLowerCase());
  }, [follows]);

  return { follows, follow, unfollow, getFollow, mounted };
}
