import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/ui/Sidebar";
import { MobileNav } from "@/components/ui/MobileNav";

export const metadata: Metadata = { title: "LA Concert Watchlist" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0f1117] text-slate-200">
        <div className="flex min-h-screen">
          {/* Sidebar: desktop only */}
          <Sidebar />
          {/* Main: full-width on mobile, offset by sidebar on desktop */}
          <main className="flex-1 md:ml-56 p-4 sm:p-6 overflow-auto pb-24 md:pb-6">
            {children}
          </main>
        </div>
        {/* Mobile bottom nav */}
        <MobileNav />
      </body>
    </html>
  );
}
