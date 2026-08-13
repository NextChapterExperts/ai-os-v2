"use client";

import React, { useEffect, useState } from "react";
import { getStoredAuth, AuthUser } from "@/lib/auth";
import PrototypeStartPage from "./prototype/page";
import { MemorySearch } from "@/components/MemorySearch";
import { LagebildRibbon } from "@/components/LagebildRibbon";
import { ComputeModePanel } from "@/components/ComputeModePanel";

function formatToday() {
  return new Intl.DateTimeFormat("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());
}

export default function MainPage() {
  const [auth, setAuth] = useState<AuthUser | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setAuth(getStoredAuth());
    setMounted(true);

    const handleAuthChange = () => {
      setAuth(getStoredAuth());
    };

    window.addEventListener("aios-auth-changed", handleAuthChange);
    return () => window.removeEventListener("aios-auth-changed", handleAuthChange);
  }, []);

  if (!mounted) {
    return <div className="p-8 muted font-mono text-xs">Lade AI-OS...</div>;
  }

  // WENN peter (Endanwender) ODER nicht eingeloggt -> Zeige Navigationsrad & Search Agent
  if (!auth || auth.role === "user") {
    return <PrototypeStartPage />;
  }

  // WENN admin (Administrator) -> Zeige bisheriges Plattform- & Entwickler-Lagebild
  return (
    <>
      <LagebildRibbon />

      <section className="lagebild-top rise pt-6">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">
              {formatToday()}
            </p>
            <h1 className="section-title m-0">Administrator Lagebild</h1>
            <p className="muted mt-1 mb-0 max-w-xl text-sm">
              Eingeloggt als <strong className="text-[var(--ink)]">{auth.name}</strong> (Administrator) · Vollzugriff auf Plattform-Infrastruktur, Memory Storage & MCP Gateway
            </p>
          </div>
        </div>

        <MemorySearch autofocus />
      </section>

      <section className="rise rise-delay-1 mt-8">
        <ComputeModePanel />
      </section>

      <section className="rise rise-delay-1 mt-10 grid gap-10 border-t border-line pt-8 lg:grid-cols-2">
        <div>
          <h2 className="section-title">Briefing & System-Orchestrator</h2>
          <p className="m-0 text-ink-soft leading-relaxed">
            Im Admin-Modus steuert das Suchfeld oben den <span className="mono text-ink">Orchestrator</span> direkt an (Intent → Engagements / Memory / Mail-Stub).
          </p>
        </div>
        <div>
          <h2 className="section-title">Infrastruktur & Modul-Status</h2>
          <div className="p-4 rounded-xl border border-[var(--line)] bg-white space-y-2 text-xs mono">
            <div className="flex items-center justify-between">
              <span>Orchestrator FastAPI Server</span>
              <span className="text-[var(--signal)] font-bold">● Online (Port 8091)</span>
            </div>
            <div className="flex items-center justify-between">
              <span>MCP Gateway & Tool Catalog</span>
              <span className="text-[var(--signal)] font-bold">● 8 Tools Aktiv</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Ollama Souveräner LLM Egress</span>
              <span className="text-[var(--signal)] font-bold">● Qwen 2.5 Coder 14B</span>
            </div>
            <div className="flex items-center justify-between">
              <span>SearXNG Anonymer Web Search Egress</span>
              <span className="text-[var(--signal)] font-bold">● Active Proxy</span>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
