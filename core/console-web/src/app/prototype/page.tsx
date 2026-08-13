"use client";

import React, { useState } from "react";
import Link from "next/link";
import { RadialNavigationWheel, RADIAL_AGENTS } from "@/components/RadialNavigationWheel";
import { ResearchAgentWorkspace } from "@/components/ResearchAgentWorkspace";
import { DynamicDataProductForm } from "@/components/DynamicDataProductForm";
import { FileUploadDropzone } from "@/components/FileUploadDropzone";
import { DataProductViewer } from "@/components/DataProductViewer";
import {
  IconSearch,
  IconShieldCheck,
  IconShieldOff,
  IconTool,
  IconEdit,
  IconCalendar,
  IconFileText,
  IconSettings,
  IconUserCheck,
  IconCpu,
  IconArrowLeft,
  IconSparkles,
  IconTerminal,
  IconDatabase,
} from "@tabler/icons-react";

export default function PrototypeStartPage() {
  // Mode State: 'user' (Anwendermodus - Default) vs. 'admin' (Admin-Modus)
  const [mode, setMode] = useState<"user" | "admin">("user");

  // Active Agent State for Radial Wheel Navigation
  const [activeAgentId, setActiveAgentId] = useState<string>("research");

  // Search input state for intent detection
  const [searchQuery, setSearchQuery] = useState("");

  // Sample Output for Fachagenten
  const [lastOutput, setLastOutput] = useState<any>(null);

  // Intent Auto-Suggest Detection
  const detectSuggestedAgent = (query: string): string | null => {
    const q = query.toLowerCase().trim();
    if (!q) return null;
    if (q.includes("angebot") || q.includes("maler") || q.includes("fassade") || q.includes("kalkulat")) {
      return "handwerker";
    }
    if (q.includes("blog") || q.includes("artikel") || q.includes("post") || q.includes("news")) {
      return "blog";
    }
    if (q.includes("meeting") || q.includes("termin") || q.includes("kalender") || q.includes("sync")) {
      return "meetings";
    }
    if (q.includes("rechnung") || q.includes("pdf") || q.includes("beleg") || q.includes("upload")) {
      return "email";
    }
    return null;
  };

  const suggestedAgentId = detectSuggestedAgent(searchQuery);

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)] font-sans">
      {/* 1. TOP HEADER & MODE SWITCHER */}
      <header className="border-b border-[var(--line)] bg-[color-mix(in_oklab,white_80%,transparent)] backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Brand Logo & Back to Main Link */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="btn-ghost text-xs inline-flex items-center gap-1.5 muted hover:text-[var(--ink)]"
              title="Zurück zur aktuellen Console"
            >
              <IconArrowLeft size={14} />
              <span>Zurück zur Konsole</span>
            </Link>
            <div className="h-4 w-px bg-[var(--line)]" />
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-[var(--ink)]">
                AI-OS <span className="text-[var(--signal)]">Virki</span>
              </span>
              <span className="badge" data-variant="graph">
                Prototyp V2
              </span>
            </div>
          </div>

          {/* DUAL MODE SWITCHER (Anwendermodus vs. Admin-Modus) */}
          <div className="flex items-center gap-2 bg-[color-mix(in_oklab,white_90%,var(--ink))] p-1 rounded-xl border border-[var(--line)] shadow-xs">
            <button
              type="button"
              onClick={() => setMode("user")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5 cursor-pointer ${
                mode === "user"
                  ? "bg-white text-[var(--ink)] shadow-sm ring-1 ring-[var(--line)]"
                  : "text-[var(--ink-soft)] hover:text-[var(--ink)]"
              }`}
            >
              <IconUserCheck size={15} className={mode === "user" ? "text-[var(--signal)]" : ""} />
              <span>Anwendermodus</span>
            </button>

            <button
              type="button"
              onClick={() => setMode("admin")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5 cursor-pointer ${
                mode === "admin"
                  ? "bg-slate-900 text-white shadow-sm ring-1 ring-slate-700"
                  : "text-[var(--ink-soft)] hover:text-[var(--ink)]"
              }`}
            >
              <IconSettings size={15} className={mode === "admin" ? "text-indigo-400" : ""} />
              <span>Admin-Modus</span>
            </button>
          </div>
        </div>
      </header>

      {/* 2. ADMIN-MODUS SUB-HEADER BANNER (Nur sichtbar im Admin-Modus) */}
      {mode === "admin" && (
        <div className="bg-slate-900 text-slate-200 border-b border-slate-800 px-6 py-3 text-xs animate-in slide-in-from-top duration-200">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2 font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="font-bold text-white uppercase tracking-wider">
                Plattform & Dev Lagebild Aktiv
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-300">
              <Link href="/platform" className="hover:text-white underline flex items-center gap-1">
                <IconCpu size={13} />
                <span>Services Status</span>
              </Link>
              <Link href="/platform" className="hover:text-white underline flex items-center gap-1">
                <IconTerminal size={13} />
                <span>MCP Gateway (8 Tools)</span>
              </Link>
              <Link href="/platform" className="hover:text-white underline flex items-center gap-1">
                <IconDatabase size={13} />
                <span>Knowledge Graph & Storage</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* 3. MAIN WORKSPACE CONTAINER */}
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-10">
        {/* RADIAL NAVIGATION WHEEL & CENTRAL SEARCH AGENT */}
        <section className="space-y-4">
          <RadialNavigationWheel
            activeAgentId={activeAgentId}
            suggestedAgentId={suggestedAgentId}
            onSelectAgent={(id) => {
              setActiveAgentId(id);
              setLastOutput(null);
            }}
          >
            {/* Zentrale Suchkarte */}
            <div className="p-6 rounded-3xl border border-[var(--line)] bg-white shadow-xl space-y-4 transition-all">
              <div className="flex items-center justify-between border-b border-[var(--line)] pb-3">
                <div className="flex items-center gap-2">
                  <IconSearch size={20} className="text-[var(--signal)]" />
                  <span className="font-bold text-sm text-[var(--ink)]">Search Agent</span>
                </div>
                <span className="badge" data-variant="graph">
                  Company Brain & Web
                </span>
              </div>

              {/* Central Input Box */}
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Tippe deine Frage oder Aufgabe ein (z. B. 'Angebot für Malerbetrieb' oder 'Was steht aus?')..."
                  className="w-full bg-[color-mix(in_oklab,white_90%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-2xl px-4 py-3.5 text-xs placeholder-[var(--ink-soft)] focus:outline-none focus:border-[var(--signal)] transition-colors pr-10"
                />
                <IconSearch
                  size={18}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--ink-soft)]"
                />
              </div>

              {/* Smart Suggestion Chip if Intent Detected */}
              {suggestedAgentId && (
                <div className="p-2.5 rounded-xl bg-[color-mix(in_oklab,var(--signal)_8%,white)] border border-[var(--signal)] flex items-center justify-between text-xs animate-in fade-in duration-200">
                  <div className="flex items-center gap-2">
                    <IconSparkles size={16} className="text-[var(--signal)]" />
                    <span>
                      Passender Fachagent erkannt:{" "}
                      <strong>
                        {RADIAL_AGENTS.find((a) => a.id === suggestedAgentId)?.name}
                      </strong>
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveAgentId(suggestedAgentId)}
                    className="btn-ghost text-xs py-1 px-3 text-[var(--signal)] font-bold border-[var(--signal)] cursor-pointer"
                  >
                    Wechseln ➔
                  </button>
                </div>
              )}
            </div>
          </RadialNavigationWheel>
        </section>

        {/* 4. ACTIVE FACHAGENT WORKSPACE */}
        <section className="space-y-6 pt-4 border-t border-[var(--line)]">
          <div className="flex items-center justify-between">
            <h2 className="section-title text-lg font-bold text-[var(--ink)] m-0 flex items-center gap-2">
              <span>Aktivierter Fachagent:</span>
              <span className="text-[var(--signal)]">
                {RADIAL_AGENTS.find((a) => a.id === activeAgentId)?.name}
              </span>
            </h2>
            <span className="mono text-xs muted">
              Kategorie: {RADIAL_AGENTS.find((a) => a.id === activeAgentId)?.category}
            </span>
          </div>

          {/* DYNAMISCHER WORKSPACE JE NACH SELEKTIERTEM AGENTEN */}
          {activeAgentId === "research" ? (
            <ResearchAgentWorkspace />
          ) : activeAgentId === "handwerker" ? (
            <div className="p-6 rounded-2xl border border-[var(--line)] bg-white space-y-6 shadow-sm">
              <DynamicDataProductForm
                schema={{
                  title: "Handwerker Angebot & Kalkulation",
                  description: "Erstellt ein rechtssicheres Angebot mit Kundenansprache und Positionsliste.",
                  properties: {
                    kunden_name: { type: "string", title: "Kundenname / Firma", default: "Malerbetrieb Schulze GmbH" },
                    projekt_titel: { type: "string", title: "Projekttitel", default: "Fassadenanstrich & Gerüstbau" },
                    flaeche_qm: { type: "number", title: "Fläche in qm", default: 140 },
                    stundensatz_eur: { type: "number", title: "Stundensatz (EUR)", default: 75 },
                    material_pauschale_eur: { type: "number", title: "Materialpauschale (EUR)", default: 450 },
                  },
                  required: ["kunden_name", "projekt_titel"],
                }}
                onSubmit={(data) => {
                  setLastOutput({
                    dp_id: "dp-angebot-10492",
                    produced_by: "handwerker-angebot-agent",
                    kunden_name: data.kunden_name,
                    projekt_titel: data.projekt_titel,
                    gesamtsumme_eur: (data.flaeche_qm || 100) * 12 + (data.material_pauschale_eur || 300),
                    angebotstext: `Sehr geehrte Damen und Herren von ${data.kunden_name},\n\nvielen Dank für Ihre Anfrage bezüglich "${data.projekt_titel}". Wir bieten Ihnen die qualifizierte Ausführung der Arbeiten zu unseren Standardkonditionen an.\n\nFläche: ${data.flaeche_qm} qm\nGesamtsumme netto: EUR ${((data.flaeche_qm || 100) * 12 + (data.material_pauschale_eur || 300)).toFixed(2)}`,
                  });
                }}
                submitLabel="Angebot Kalkulieren & Erstellen"
              />

              {lastOutput && <DataProductViewer dataProduct={lastOutput} title="Generiertes Handwerker-Angebot" />}
            </div>
          ) : activeAgentId === "email" ? (
            <div className="space-y-6">
              <FileUploadDropzone
                onUploadSuccess={(res) => {
                  setLastOutput({
                    dp_id: res.asset_id || "dp-ingest-8812",
                    produced_by: "file-ingest-pipeline",
                    file_name: res.path || "Dokument.pdf",
                    char_count: res.text_length || 1420,
                    fts_status: "Indexed in SQLite memory.db",
                    knowledge_graph_commit: "OrgKnowledgeAsset committed",
                  });
                }}
              />
              {lastOutput && <DataProductViewer dataProduct={lastOutput} title="Ingestion DataProduct Commit" />}
            </div>
          ) : activeAgentId === "blog" ? (
            <div className="p-6 rounded-2xl border border-[var(--line)] bg-white space-y-6 shadow-sm">
              <DynamicDataProductForm
                schema={{
                  title: "Blog & Content Engine",
                  description: "Erstellt zielgruppengerechte KI-Artikel und Unternehmens-Posts.",
                  properties: {
                    thema: { type: "string", title: "Artikel-Thema", default: "Moderne KI-Konzepte für Handwerksbetriebe 2026" },
                    zielgruppe: { type: "string", title: "Zielgruppe", default: "Geschäftsführer & Handwerksmeister" },
                    tonfall: { type: "string", title: "Tonfall", enum: ["Professionell & Sachlich", "Inspirierend & Nahbar", "Kompakt & Direkt"] },
                  },
                  required: ["thema"],
                }}
                onSubmit={(data) => {
                  setLastOutput({
                    dp_id: "dp-blog-9921",
                    produced_by: "blog-agent",
                    titel: data.thema,
                    zielgruppe: data.zielgruppe,
                    artikel_text: `# ${data.thema}\n\nIn der heutigen Zeit stehen Handwerksbetriebe vor der Herausforderung, administrative Prozesse zu beschleunigen...\n\n- Automatisierte Angebotserstellung\n- Digitaler Rechnungsimport\n- Effiziente Terminplanung`,
                  });
                }}
                submitLabel="Blogbeitrag Generieren"
              />

              {lastOutput && <DataProductViewer dataProduct={lastOutput} title="Generierter Blogbeitrag" />}
            </div>
          ) : (
            <div className="p-6 rounded-2xl border border-[var(--line)] bg-white space-y-4 shadow-sm">
              <h3 className="section-title text-base font-bold m-0 flex items-center gap-2">
                <IconCalendar size={20} className="text-[var(--signal)]" />
                <span>Meeting- & Zeitmanagement Agent</span>
              </h3>
              <p className="text-xs muted m-0">
                Synchronisiert Google Calendar, analysiert freie Fokusblöcke und generiert Zusammenfassungen.
              </p>
              <div className="p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_90%,transparent)] text-xs mono space-y-2">
                <div>Calendar Sync Status: 68 Termine synchronisiert</div>
                <div>Nächster Freier Fokusblock: Morgen 14:00 - 16:30 Uhr</div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
