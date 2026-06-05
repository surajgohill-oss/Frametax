// All requests go to the Next.js server via relative paths.
// next.config.js rewrites /api/* → BACKEND_URL/api/* server-side,
// so the browser never makes cross-origin calls to the backend directly.
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function listEvents(): Promise<any[]> {
  const data = await req<any[]>("/events/");
  if (typeof window !== "undefined") {
    (window as any).__EVENT_TRACE__ = data.map((e: any) => e.__trace).filter(Boolean);
  }
  return data;
}

export const api = {
  events: {
    list: (opts?: { include_completed?: boolean }) => {
      if (opts?.include_completed) {
        return req<any[]>("/events/?include_completed=true").then((data) => {
          if (typeof window !== "undefined")
            (window as any).__EVENT_TRACE__ = data.map((e: any) => e.__trace).filter(Boolean);
          return data;
        });
      }
      return listEvents();
    },
    get: (id: number) => req<any>(`/events/${id}`),
    create: (d: any) => req<any>("/events/", { method: "POST", body: JSON.stringify(d) }),
    update: (id: number, d: any) => req<any>(`/events/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
    delete: (id: number) => req<void>(`/events/${id}`, { method: "DELETE" }),
  },
  venues: {
    list: () => req<any[]>("/venues/"),
    get: (slug: string) => req<any>(`/venues/${slug}`),
    sections: (slug?: string) => slug ? req<any[]>(`/venues/${slug}/sections`) : Promise.resolve([]),
  },
  listings: {
    byEvent: (id: number, mp?: string) => req<any[]>(`/listings/events/${id}${mp ? `?marketplace=${mp}` : ""}`),
    byEventPaged: (id: number, opts: { marketplace?: string; after_id?: number; limit?: number } = {}) => {
      const p = new URLSearchParams();
      if (opts.marketplace) p.set("marketplace", opts.marketplace);
      if (opts.after_id != null) p.set("after_id", String(opts.after_id));
      if (opts.limit != null) p.set("limit", String(opts.limit));
      const qs = p.toString();
      return req<any[]>(`/listings/events/${id}${qs ? "?" + qs : ""}`);
    },
    /** Walk all cursor pages and return the complete listing set (no LIMIT 500 cap). */
    byEventAll: async (id: number, marketplace?: string): Promise<any[]> => {
      const PAGE = 500;
      let all: any[] = [];
      let afterId: number | undefined;
      while (true) {
        const p = new URLSearchParams({ limit: String(PAGE) });
        if (marketplace) p.set("marketplace", marketplace);
        if (afterId != null) p.set("after_id", String(afterId));
        const page: any[] = await req<any[]>(`/listings/events/${id}?${p.toString()}`);
        all = all.concat(page);
        if (page.length < PAGE) break;
        afterId = page[page.length - 1].id;
      }
      return all;
    },
    byEventFiltered: (
      id: number,
      opts: {
        marketplace?: string;
        section_id?: string;
        row?: string;
        minPrice?: string;
        maxPrice?: string;
        minQuantity?: string;
        sort?: string;
      } = {}
    ) => {
      const p = new URLSearchParams();
      if (opts.marketplace)  p.set("marketplace",  opts.marketplace);
      if (opts.section_id)   p.set("section_id",   opts.section_id);
      if (opts.row)          p.set("row",           opts.row);
      if (opts.minPrice)     p.set("min_price",     opts.minPrice);
      if (opts.maxPrice)     p.set("max_price",     opts.maxPrice);
      if (opts.minQuantity)  p.set("min_quantity",  opts.minQuantity);
      if (opts.sort)         p.set("sort",          opts.sort);
      const qs = p.toString();
      return req<any[]>(`/listings/events/${id}${qs ? "?" + qs : ""}`);
    },
  },
  analytics: {
    summary: () => req<any>("/analytics/summary"),
    eventSummary: (id: number, mp?: string) => req<any[]>(`/analytics/events/${id}/summary${mp ? `?marketplace=${mp}` : ""}`),
    priceHistory: (id: number, hours = 168, mp?: string) => req<any[]>(`/analytics/events/${id}/price-history?hours=${hours}${mp ? `&marketplace=${mp}` : ""}`),
    heatmap: (id: number) => req<any[]>(`/analytics/events/${id}/heatmap`),
    compare: (id: number) => req<any[]>(`/analytics/events/${id}/compare`),
    inventorySummary: (id: number) => req<any>(`/analytics/events/${id}/inventory-summary`),
    inventoryAccounting: (id: number) => req<any>(`/analytics/events/${id}/inventory-accounting`),
    canonicalInventory: (id: number) => req<any>(`/analytics/events/${id}/canonical-inventory`),
    canonicalHistory: (id: number, limit = 48) => req<any>(`/analytics/events/${id}/canonical-history?limit=${limit}`),
    sectionLiquidity: (id: number) => req<any>(`/analytics/events/${id}/section-liquidity`),
    marketIntelligence: (id: number) => req<any>(`/analytics/events/${id}/market-intelligence`),
    inventoryMovement: (id: number) => req<any>(`/analytics/events/${id}/inventory-movement`),
    baseline: (id: number) => req<any>(`/analytics/events/${id}/baseline`),
    attribution: (id: number) => req<any>(`/analytics/events/${id}/attribution`),
    blockLifecycle: (eventId: number, blockId: string) => req<any>(`/analytics/events/${eventId}/blocks/${blockId}/lifecycle`),
  },
  poll: {
    trigger: (id: number) => req<any>(`/poll/events/${id}/trigger`, { method: "POST" }),
    runs: (id: number) => req<any[]>(`/poll/events/${id}/runs`),
  },
  debug: {
    errors: (mp?: string, type?: string) => req<any[]>(`/debug/errors?limit=100${mp ? `&marketplace=${mp}` : ""}${type ? `&error_type=${type}` : ""}`),
    errorSummary: () => req<any[]>("/debug/errors/summary"),
    memory: (mp?: string) => req<any[]>(`/debug/memory${mp ? `?marketplace=${mp}` : ""}`),
    deleteMemory: (id: number) => req<void>(`/debug/memory/${id}`, { method: "DELETE" }),
    clearMemory: (mp?: string) => req<void>(`/debug/memory${mp ? `?marketplace=${mp}` : ""}`, { method: "DELETE" }),
    testCollect: (marketplace: string, url: string) =>
      req<any>("/debug/test-collect", { method: "POST", body: JSON.stringify({ marketplace, url }) }),
    runtime: () => req<any>("/debug/runtime"),
  },
};
