"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserSelector } from "@/components/UserSelector";

const NAV = [
  { href: "/", label: "Lagebild" },
  { href: "/virki", label: "🏰 VIRKI Produkt" },
  { href: "/meetings", label: "Meetings" },
  { href: "/search", label: "Suche" },
  { href: "/workflows", label: "Workflows" },
  { href: "/platform", label: "Plattform" },
] as const;

function matchLength(pathname: string, href: string): number {
  if (href === "/") return pathname === "/" ? 1 : 0;
  if (pathname === href || pathname.startsWith(`${href}/`)) return href.length;
  return 0;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // Bei ueberlappenden Praefixen (z.B. /platform vs. /platform/kg) gewinnt
  // die spezifischste Route, damit nicht beide Nav-Items gleichzeitig aktiv sind.
  const bestMatch = NAV.reduce(
    (best, item) => {
      const len = matchLength(pathname, item.href);
      return len > best.len ? { href: item.href, len } : best;
    },
    { href: "", len: 0 },
  );

  return (
    <div className="shell-bg">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between gap-6 px-5 pt-5 pb-2 sm:px-8">
        <Link href="/" className="brand-mark text-xl text-ink no-underline sm:text-2xl">
          AI-OS
        </Link>
        <nav className="flex flex-wrap items-center gap-5 text-sm sm:gap-7 sm:text-base">
          {NAV.map((item) => {
            const active = bestMatch.len > 0 && item.href === bestMatch.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="nav-link"
                data-active={active ? "true" : "false"}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-3 text-right text-xs text-ink-soft">
          <UserSelector />
          <div className="hidden sm:block">
            <div className="mono">tenant · nextchapter</div>
            <div className="mono">proj · 1100-AI-OS-V2</div>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-5 pb-16 sm:px-8">{children}</main>
    </div>
  );
}
