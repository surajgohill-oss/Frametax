"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Plus, CheckCircle2, BarChart2 } from "lucide-react";
import AddEventModal from "./AddEventModal";

export default function NavBar() {
  const pathname = usePathname();
  const [showAdd, setShowAdd] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#0f1117]/95 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 h-12 flex items-center gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm font-semibold tracking-wide text-slate-200">Concert Tracker</span>
          </Link>
          <span className="text-xs text-slate-500 hidden sm:block">LA Market Intelligence</span>

          {/* Nav links */}
          <nav className="flex items-center gap-1 ml-2">
            <NavLink href="/" active={pathname === "/"}>
              <BarChart2 size={13} />
              <span>Active</span>
            </NavLink>
            <NavLink href="/completed" active={pathname === "/completed"}>
              <CheckCircle2 size={13} />
              <span>Completed</span>
            </NavLink>
          </nav>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Add event */}
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-1.5 text-xs font-medium text-white/70 hover:text-white bg-white/6 hover:bg-white/10 border border-white/8 hover:border-white/15 rounded-lg px-3 py-1.5 transition-all"
          >
            <Plus size={13} />
            <span className="hidden sm:inline">Add Event</span>
          </button>
        </div>
      </header>

      {showAdd && <AddEventModal onClose={() => setShowAdd(false)} />}
    </>
  );
}

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md transition-all ${
        active
          ? "text-white bg-white/8 font-medium"
          : "text-slate-500 hover:text-slate-300 hover:bg-white/4"
      }`}
    >
      {children}
    </Link>
  );
}
