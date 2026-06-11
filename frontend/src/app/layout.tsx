import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Concert Tracker",
  description: "LA concert ticket market intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0f1117] text-slate-200">
        <header className="sticky top-0 z-50 border-b border-white/5 bg-[#0f1117]/95 backdrop-blur-sm">
          <div className="mx-auto max-w-7xl px-4 h-12 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm font-semibold tracking-wide text-slate-200">Concert Tracker</span>
            <span className="text-xs text-slate-500 ml-1">LA Market Intelligence</span>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
