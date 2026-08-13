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
  IconSparkles,
  IconCpu,
  IconAdjustments,
} from "@tabler/icons-react";

export default function PrototypeStartPage() {
  // Active Agent State for Radial Wheel Navigation (Standard: Leer für pure Rad-Ansicht)
  const [activeAgentId, setActiveAgentId] = useState<string>("");

  // Search input & model state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("qwen2.5-coder:14b");
  const [ipProtection, setIpProtection] = useState(true);

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
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 sm:p-6 space-y-10">
      {/* 1. RADIAL NAVIGATION WHEEL & ZENTRALES SEARCH AGENT PANEL */}
      <section className="max-w-6xl mx-auto space-y-4">
        <RadialNavigationWheel
          activeAgentId={activeAgentId}
          suggestedAgentId={suggestedAgentId}
          onSelectAgent={(id) => {
            setActiveAgentId(id);
            setLastOutput(null);
          }}
        >
          {/* ZENTRALE CYBER-SEARCH KARTE */}
          <div className="p-6 rounded-3xl border border-cyan-500/30 bg-slate-900/90 shadow-[0_0_50px_rgba(6,182,212,0.15)] backdrop-blur-2xl space-y-5 transition-all">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  <IconSearch size={18} />
                </div>
                <span className="font-bold text-sm tracking-wide text-white">
                  SEARCH AGENT <span className="text-cyan-400">SCHALTZENTRALE</span>
                </span>
              </div>
              <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 uppercase tracking-wider">
                Company Brain & Web
              </span>
            </div>

            {/* Central Input Bar */}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Wonach suchen Sie, Max? (z. B. 'Angebot Malerarbeiten Schulze' oder 'Rechnungen')"
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-400 text-white rounded-2xl px-4 py-3.5 text-xs placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-400 transition-all pr-12 shadow-inner"
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:scale-105 transition-transform cursor-pointer font-bold"
                title="Suche ausführen"
              >
                <IconSearch size={16} />
              </button>
            </div>

            {/* Integrated Options Bar: Model Dropdown & IP-Protection Toggle */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-800/80 text-xs">
              {/* Modellauswahl Dropdown */}
              <div className="flex items-center gap-2 bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800">
                <IconCpu size={14} className="text-cyan-400" />
                <span className="text-[11px] text-slate-400 font-mono">Modell:</span>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="bg-transparent text-white font-bold text-xs outline-none cursor-pointer"
                >
                  <option value="qwen2.5-coder:14b" className="bg-slate-900 text-white">Qwen 2.5 Coder 14B</option>
                  <option value="deepseek-r1:32b" className="bg-slate-900 text-white">DeepSeek R1 32B</option>
                  <option value="mistral-nemo:12b" className="bg-slate-900 text-white">Mistral Nemo 12B</option>
                  <option value="hermes3:8b" className="bg-slate-900 text-white">Hermes 3 8B</option>
                  <option value="llama3.2-vision:11b" className="bg-slate-900 text-white">Llama 3.2 Vision 11B</option>
                </select>
              </div>

              {/* IP-Schutz Toggle */}
              <button
                type="button"
                onClick={() => setIpProtection(!ipProtection)}
                className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                  ipProtection
                    ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-300"
                    : "bg-slate-950/60 border-slate-800 text-slate-400"
                }`}
              >
                {ipProtection ? <IconShieldCheck size={14} className="text-cyan-400" /> : <IconShieldOff size={14} />}
                <span>IP-Schutz: {ipProtection ? "AN (Anonym)" : "AUS"}</span>
              </button>
            </div>

            {/* Smart Intent Suggestion Banner */}
            {suggestedAgentId && (
              <div className="p-3 rounded-2xl bg-cyan-500/15 border border-cyan-400/50 flex items-center justify-between text-xs animate-in fade-in duration-200 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
                <div className="flex items-center gap-2 text-cyan-200">
                  <IconSparkles size={16} className="text-cyan-400 animate-spin" />
                  <span>
                    Intelligente Absprung-Empfehlung:{" "}
                    <strong className="text-white">
                      {RADIAL_AGENTS.find((a) => a.id === suggestedAgentId)?.name}
                    </strong>
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveAgentId(suggestedAgentId)}
                  className="px-3 py-1 rounded-xl bg-cyan-400 text-slate-950 font-black text-xs hover:bg-cyan-300 transition-colors cursor-pointer"
                >
                  Zu Agent ➔
                </button>
              </div>
            )}
          </div>
        </RadialNavigationWheel>
      </section>

      {/* 2. FACHAGENT WORKSPACE MODAL / FULL VIEW (Nur aktiv bei expliziter Selektion) */}
      {activeAgentId && (
        <div className="max-w-6xl mx-auto space-y-6 pt-6 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-extrabold text-white uppercase tracking-wider m-0 flex items-center gap-2">
              <span className="text-slate-400">Aktivierter Fachagent:</span>
              <span className="text-cyan-400">
                {RADIAL_AGENTS.find((a) => a.id === activeAgentId)?.name}
              </span>
            </h2>
            <button
              type="button"
              onClick={() => setActiveAgentId("")}
              className="text-xs font-mono text-slate-400 hover:text-white px-3 py-1 rounded-xl bg-slate-900 border border-slate-800 cursor-pointer"
            >
              Schließen ✕
            </button>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl shadow-2xl">
            {activeAgentId === "research" ? (
              <ResearchAgentWorkspace />
            ) : activeAgentId === "handwerker" ? (
              <div className="space-y-6">
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
              <div className="space-y-6">
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
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2 m-0">
                  <IconCalendar size={20} className="text-cyan-400" />
                  <span>Meeting- & Zeitmanagement Agent</span>
                </h3>
                <p className="text-xs text-slate-400 m-0">
                  Synchronisiert Google Calendar, analysiert freie Fokusblöcke und generiert Zusammenfassungen.
                </p>
                <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950 text-xs font-mono text-cyan-300 space-y-2">
                  <div>Calendar Sync Status: 68 Termine synchronisiert</div>
                  <div>Nächster Freier Fokusblock: Morgen 14:00 - 16:30 Uhr</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
