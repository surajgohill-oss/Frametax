"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CalendarDays, Map, ArrowLeftRight, Bug, Music2 } from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Feed", icon: LayoutDashboard },
  { href: "/events", label: "Events", icon: CalendarDays },
  { href: "/heatmap", label: "Heatmap", icon: Map },
  { href: "/compare", label: "Compare", icon: ArrowLeftRight },
  { href: "/debug", label: "Debug", icon: Bug },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-[#161b27] border-r border-[#2a3145] flex flex-col z-10">
      <div className="flex items-center gap-2 px-4 py-5 border-b border-[#2a3145]">
        <Music2 className="text-blue-500 shrink-0" size={20} />
        <div><p className="text-sm font-semibold leading-tight text-slate-100">LA Concert</p><p className="text-xs text-slate-400 leading-tight">Watchlist Tracker</p></div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} className={cn("flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors", path === href || (href !== "/" && path.startsWith(href)) ? "bg-blue-600/20 text-blue-400 font-medium" : "text-slate-400 hover:text-slate-200 hover:bg-[#1e2535]")}>
            <Icon size={16} />{label}
          </Link>
        ))}
      </nav>
      <div className="p-3 border-t border-[#2a3145] text-xs text-slate-500 px-4"><p>Personal use · LA only</p></div>
    </aside>
  );
}
