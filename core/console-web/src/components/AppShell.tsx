"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserSelector } from "@/components/UserSelector";

const NAV = [
  { href: "/", label: "Lagebild" },
  { href: "/portfolio", label: "Projekte" },
  { href: "/meetings", label: "Meetings" },
  { href: "/agents", label: "Agenten" },
  { href: "/search", label: "Suche" },
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
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 pt-5 pb-2 sm:px-8">
        <div className="relative group/virki">
          <Link href="/" className="brand-mark no-underline flex items-center gap-2">
            <span className="text-xl sm:text-2xl text-signal group-hover/virki:scale-110 transition-transform font-bold" title="Wyrd-Key / Odins Raben">
              ᚢ
            </span>
            <span className="font-mystic text-2xl sm:text-3xl font-extrabold tracking-[0.16em] text-ink uppercase group-hover/virki:text-signal transition-colors">
              VIRKI
            </span>
          </Link>

          {/* Odin's Ravens Story Hover Popover Dropdown */}
          <div className="absolute left-0 top-full mt-2 w-80 sm:w-96 rounded-xl border border-line bg-card/95 p-4 shadow-2xl backdrop-blur-md opacity-0 pointer-events-none group-hover/virki:opacity-100 group-hover/virki:pointer-events-auto transition-all duration-200 z-50">
            <div className="flex items-center gap-2 mb-2 border-b border-line pb-2">
              <span className="text-lg">🦅</span>
              <h4 className="font-bold text-sm text-ink m-0">VIRKI & Die Raben von Odin</h4>
            </div>
            <p className="text-xs text-ink-soft leading-relaxed mb-2">
              Es war einmal Odin, der Gott der Weisheit, der sein Reich von der Festung <strong className="text-ink">VIRKI</strong> aus regierte. An seiner Seite dienten zwei treue Raben:
            </p>
            <ul className="text-xs text-ink-soft space-y-1 pl-1 list-none mb-2">
              <li className="flex items-start gap-1.5">
                <span>🦅</span>
                <span><strong className="text-ink">MUNINN</strong> <em>(Das Gedächtnis)</em>: Fliegt täglich aus, erfasst Mails, Chats & Wissen und bewahrt es unvergesslich auf.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span>🦅</span>
                <span><strong className="text-ink">HUGINN</strong> <em>(Der Gedanke)</em>: Blickt in die Zukunft, durchdenkt Strategien & führt autonome KI-Workflows aus.</span>
              </li>
            </ul>
            <p className="text-[11px] text-muted italic m-0 pt-1 border-t border-line/50">
              VIRKI vereint Gedächtnis, Gedanke & souveräne Kontrolle in Ihrem KI-Betriebssystem.
            </p>
          </div>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm sm:gap-6 sm:text-base">
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
          <div className="hidden lg:block">
            <div className="mono">tenant · nextchapter</div>
            <div className="mono">proj · VIRKI-OS</div>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-5 pb-16 sm:px-8">{children}</main>
    </div>
  );
}
