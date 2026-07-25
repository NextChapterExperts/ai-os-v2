"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/platform", label: "Health" },
  { href: "/platform/storage", label: "Speicher" },
  { href: "/platform/kg", label: "Graph" },
  { href: "/platform/capture", label: "Chat-Erfassung" },
] as const;

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div>
      <div className="mb-8 flex gap-5 border-b border-line text-sm">
        {TABS.map((tab) => {
          const active = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className="nav-link pb-3"
              data-active={active ? "true" : "false"}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
      {children}
    </div>
  );
}
