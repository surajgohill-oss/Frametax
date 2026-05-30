"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CalendarDays, ArrowLeftRight, Map } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/",        label: "My Events",   icon: LayoutDashboard },
  { href: "/events",  label: "All Events",  icon: CalendarDays    },
  { href: "/compare", label: "Compare",     icon: ArrowLeftRight  },
  { href: "/heatmap", label: "Heatmap",     icon: Map             },
];

/**
 * MobileNav — bottom tab bar, visible only on screens below md breakpoint.
 * Mirrors the Sidebar's primary nav items.
 */
export function MobileNav() {
  const path = usePathname();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around px-2 py-2"
      style={{
        background: "rgba(6, 0, 4, 0.96)",
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderTop: "1px solid rgba(255, 255, 255, 0.07)",
      }}
    >
      {navItems.map(({ href, label, icon: Icon }) => {
        const active = path === href || (href !== "/" && path.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-col items-center gap-1 px-4 py-1.5 rounded-xl transition-all duration-150 min-w-0",
              active ? "text-red-400" : "text-slate-600 hover:text-slate-400"
            )}
            style={active ? { background: "rgba(229,9,20,0.10)" } : {}}
          >
            <Icon
              size={18}
              style={active ? { color: "#E50914" } : {}}
            />
            <span className="text-[9px] font-semibold tracking-wide leading-none">
              {label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
