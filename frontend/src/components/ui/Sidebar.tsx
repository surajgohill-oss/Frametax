"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CalendarDays, Map, ArrowLeftRight, Bug, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const primaryNav = [
  { href: "/",        label: "My Events",  icon: LayoutDashboard },
  { href: "/events",  label: "All Events", icon: CalendarDays    },
  { href: "/compare", label: "Compare",    icon: ArrowLeftRight  },
  { href: "/heatmap", label: "Heatmap",    icon: Map             },
];

const secondaryNav = [
  { href: "/debug", label: "Debug", icon: Bug },
];

export function Sidebar() {
  const path = usePathname();

  const NavLink = ({ href, label, icon: Icon, dim = false }: {
    href: string; label: string; icon: any; dim?: boolean;
  }) => {
    const active = path === href || (href !== "/" && path.startsWith(href));
    return (
      <Link
        href={href}
        className={cn(
          "flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-150",
          active
            ? "text-white"
            : dim
              ? "text-[#3A3A3A] hover:text-[#666] hover:bg-white/[0.03]"
              : "text-[#666] hover:text-[#aaa] hover:bg-white/[0.04]"
        )}
        style={active ? {
          background: "rgba(229,9,20,0.15)",
          border: "1px solid rgba(229,9,20,0.28)",
          boxShadow: "inset 0 0 12px rgba(229,9,20,0.06)",
        } : { border: "1px solid transparent" }}
      >
        <Icon
          size={14}
          style={active ? { color: "#FF2020" } : dim ? { color: "#333" } : { color: "#555" }}
        />
        {label}
      </Link>
    );
  };

  return (
    <aside
      className="hidden md:flex fixed left-0 top-0 h-screen w-56 flex-col z-10"
      style={{
        background: "rgba(10,10,12,0.98)",
        backdropFilter: "blur(32px)",
        WebkitBackdropFilter: "blur(32px)",
        borderRight: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      {/* Brand */}
      <div
        className="flex items-center gap-3 px-4 py-5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{
            background: "rgba(229,9,20,0.2)",
            border: "1px solid rgba(229,9,20,0.4)",
            boxShadow: "0 0 12px rgba(229,9,20,0.15)",
          }}
        >
          <Zap style={{ color: "#FF2020" }} size={14} />
        </div>
        <div>
          <p className="text-[13px] font-bold leading-tight text-white tracking-tight">Event Intel</p>
          <p className="text-[10px] leading-tight mt-0.5 uppercase tracking-widest" style={{ color: "#444" }}>Live Market</p>
        </div>
      </div>

      {/* Primary nav */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {primaryNav.map(item => <NavLink key={item.href} {...item} />)}

        <div className="my-3" style={{ height: "1px", background: "rgba(255,255,255,0.04)" }} />

        {secondaryNav.map(item => <NavLink key={item.href} {...item} dim />)}
      </nav>

      {/* Footer */}
      <div
        className="px-4 py-3"
        style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
      >
        <p className="text-[10px] uppercase tracking-widest" style={{ color: "#333" }}>Los Angeles</p>
      </div>
    </aside>
  );
}
