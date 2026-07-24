"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Lagebild" },
  { href: "/search", label: "Suche" },
  { href: "/workflows", label: "Workflows" },
  { href: "/platform", label: "Plattform" },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="shell-bg">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between gap-6 px-5 pt-5 pb-2 sm:px-8">
        <Link href="/" className="brand-mark text-xl text-ink no-underline sm:text-2xl">
          AI-OS
        </Link>
        <nav className="flex flex-wrap items-center gap-5 text-sm sm:gap-7 sm:text-base">
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
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
        <div className="hidden text-right text-xs text-ink-soft sm:block">
          <div className="mono">tenant · nextchapter</div>
          <div className="mono">proj · 1100-AI-OS-V2</div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-5 pb-16 sm:px-8">{children}</main>
    </div>
  );
}
