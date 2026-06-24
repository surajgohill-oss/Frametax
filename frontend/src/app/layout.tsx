import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Concert Tracker",
  description: "LA concert ticket market intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen text-slate-200">
        <NavBar />
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
