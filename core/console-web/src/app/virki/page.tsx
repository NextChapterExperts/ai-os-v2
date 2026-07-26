"use client";

import Image from "next/image";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";

export default function VirkiProductPage() {
  return (
    <AppShell activeTab="platform">
      <div className="mx-auto max-w-5xl space-y-8 p-6">
        {/* Hero Banner */}
        <header className="rounded-2xl border border-sky-500/30 bg-slate-900 p-8 shadow-xl">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-3 md:max-w-2xl">
              <span className="inline-block rounded-full bg-sky-500/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-sky-300 border border-sky-500/30">
                Souveränes Enterprise KI-Betriebssystem
              </span>
              <h1 className="text-3xl font-extrabold text-white md:text-4xl">
                VIRKI — Ein System. Zwei Raben. Volle Souveränität.
              </h1>
              <p className="text-base text-slate-300 leading-relaxed">
                Das schlüsselfertige KI-Betriebssystem auf Ihren eigenen Servern (Platform-VM). 
                Keine Datenlecks, kein Hype — entwickelt für die 10 realen Herausforderungen von Enterprise-KI.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row md:flex-col">
              <Link
                href="/search"
                className="rounded-lg bg-sky-500 px-5 py-3 text-center text-sm font-bold text-white transition hover:bg-sky-400 shadow-md"
              >
                🔎 Unified Search testen
              </Link>
              <Link
                href="/platform"
                className="rounded-lg border border-slate-700 bg-slate-800 px-5 py-3 text-center text-sm font-semibold text-slate-200 transition hover:bg-slate-700"
              >
                📊 Platform Health
              </Link>
            </div>
          </div>
        </header>

        {/* Blueprint Sketchbook Artwork */}
        <section className="rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-xl">
          <h2 className="text-xl font-bold text-slate-100 mb-2">
            🏛️ VIRKI / Sovereign Norse Citadel (Architectural Blueprint)
          </h2>
          <p className="text-xs text-slate-400 mb-4">
            Druckoptimierte Architektur-Skizze mit Odin als Orchestrator, Huginn (Gedanke) & Muninn (Gedächtnis).
          </p>
          <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-amber-50/10 p-2">
            <img
              src="/assets/virki_odin_sketchbook_bright.png"
              alt="VIRKI Blueprint Artwork"
              className="w-full rounded-lg object-contain"
            />
          </div>
        </section>

        {/* 4 Pillars Grid */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold text-white">
            ⚔️ Die 4 Säulen des VIRKI-Systems
          </h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div className="rounded-xl border border-sky-500/30 bg-slate-900/80 p-6 shadow">
              <h3 className="text-lg font-bold text-sky-400">🏰 VIRKI Platform-VM</h3>
              <div className="mt-1 text-xs font-medium uppercase tracking-wider text-slate-400">
                Die feuerfeste Festung (Appliance)
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                100 % In-House / On-Premise (P19). Logische & physische Mandantentrennung. Kein einziges Datum verlässt unkontrolliert Ihr Unternehmen.
              </p>
            </div>

            <div className="rounded-xl border border-amber-500/30 bg-slate-900/80 p-6 shadow">
              <h3 className="text-lg font-bold text-amber-400">🦅 MUNINN Memory Engine</h3>
              <div className="mt-1 text-xs font-medium uppercase tracking-wider text-slate-400">
                Das unbestechliche Gedächtnis
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                GraphRAG (Knowledge Graph <code className="text-amber-300">org:*</code>), Qdrant Vector Engine & FTS5. Chat Capture aus Cursor/Antigravity/Gemini. Krypto-Audit-Trail für den Prüfer.
              </p>
            </div>

            <div className="rounded-xl border border-blue-500/30 bg-slate-900/80 p-6 shadow">
              <h3 className="text-lg font-bold text-blue-400">🦅 HUGINN Agent Engine</h3>
              <div className="mt-1 text-xs font-medium uppercase tracking-wider text-slate-400">
                Der scharfsinnige Gedanke
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                LangGraph Workflows & autonome Agenten-Flotte. 80–90 % lokale LLM-Inference via Ollama (€0 Token-Kosten). Strikte Pydantic Schema-Hülle gegen Halluzinationen.
              </p>
            </div>

            <div className="rounded-xl border border-emerald-500/30 bg-slate-900/80 p-6 shadow">
              <h3 className="text-lg font-bold text-emerald-400">👑 ODIN Orchestrator & UI</h3>
              <div className="mt-1 text-xs font-medium uppercase tracking-wider text-slate-400">
                Der Mensch auf dem Hochsitz
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                Ebene 1 Lagebild für tägliche Führung. Sie behalten die volle Kontrolle – und die Raben arbeiten für Sie. Volle Multi-User Sichtbarkeits-Steuerung.
              </p>
            </div>
          </div>
        </section>

        {/* 10 Solved Challenges */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
          <h2 className="text-xl font-bold text-white">
            🛡️ Wie VIRKI die 10 Realitätsfallen von Enterprise-KI meistert
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h4 className="font-bold text-slate-200 text-sm">1. Failing Silently (Stumme Falschbuchung)</h4>
              <p className="mt-1 text-xs text-rose-400">⚠️ KI rät probabilistisch ohne Fehlermeldung ins ERP.</p>
              <p className="mt-1 text-xs font-medium text-emerald-400">✔ Huginn Pydantic Schema-Validierung + HITL-Freigabe.</p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h4 className="font-bold text-slate-200 text-sm">2. Context- & RAG-Drift (Datenmüll)</h4>
              <p className="mt-1 text-xs text-rose-400">⚠️ Vektorsuche zieht veraltete Verträge.</p>
              <p className="mt-1 text-xs font-medium text-emerald-400">✔ Muninn GraphRAG sucht im echten Beziehungsnetz.</p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h4 className="font-bold text-slate-200 text-sm">3. Reasoning Loops (Endlos-Schleifen)</h4>
              <p className="mt-1 text-xs text-rose-400">⚠️ Agent wiederholt API-Calls 40x in 2 Minuten.</p>
              <p className="mt-1 text-xs font-medium text-emerald-400">✔ State-Machine Checkpoints & Max-Try-Limits.</p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h4 className="font-bold text-slate-200 text-sm">4. Privacy & DSGVO-Lecks</h4>
              <p className="mt-1 text-xs text-rose-400">⚠️ Kundendaten fließen unbemerkt an Cloud-LLMs.</p>
              <p className="mt-1 text-xs font-medium text-emerald-400">✔ Lokale VM-Anonymisierung & Re-Enrichment.</p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h4 className="font-bold text-slate-200 text-sm">5. Model- & Prompt-Drift</h4>
              <p className="mt-1 text-xs text-rose-400">⚠️ Stilles Cloud-Update bricht JSON-Formate.</p>
              <p className="mt-1 text-xs font-medium text-emerald-400">✔ Automatische Golden-Dataset Regression.</p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <h4 className="font-bold text-slate-200 text-sm">6. GoBD / SOX Audit-Lineage</h4>
              <p className="mt-1 text-xs text-rose-400">⚠️ Prüfer fragt warum gebucht wurde – ERP zeigt nur System-User.</p>
              <p className="mt-1 text-xs font-medium text-emerald-400">✔ Krypto-Lineage mit Prompt-Hash & RAG-Quellen.</p>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
