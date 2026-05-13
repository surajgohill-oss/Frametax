import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/ui/Sidebar";

export const metadata: Metadata = { title: "LA Concert Watchlist" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0f1117] text-slate-200">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 ml-56 p-6 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
