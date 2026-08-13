"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { RadialNavigationWheel, RADIAL_AGENTS, AgentNode } from "@/components/RadialNavigationWheel";
import {
  IconSearch,
  IconShieldCheck,
  IconShieldOff,
  IconSparkles,
  IconCpu,
  IconArrowRight,
  IconExternalLink,
  IconBrandGoogle,
} from "@tabler/icons-react";

export default function PrototypeStartPage() {
  const router = useRouter();

  // Search input & model state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("qwen2.5-coder:14b");
  const [ipProtection, setIpProtection] = useState(true);

  // Search Execution state
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any>(null);

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

  const handleAgentSelect = (agent: AgentNode) => {
    // KLICK ERFOLGT: Direkter Absprung zur Fachagenten-Seite
    router.push(agent.href);
  };

  const handleExecuteSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    // Simulierter / Echter SearXNG Webrecherche Call
    setTimeout(() => {
      setSearchResults({
        query: searchQuery,
        timestamp: new Date().toLocaleTimeString("de-DE"),
        sources: [
          { title: "SearXNG Egress Node #1", snippet: `Gefundene Ergebnisse und Recherchen für '${searchQuery}'`, url: "https://searxng.internal/search" },
          { title: "Company Brain Vector Store", snippet: "Lokale Dokumente und Kontext-Extraktion abgeschlossen.", url: "https://virki.internal/brain" }
        ],
        synthesis: `Souveräne KI-Synthese (Modell ${selectedModel}): Die Anfrage '${searchQuery}' wurde über anonymer SearXNG-Egress verarbeitet.`
      });
      setIsSearching(false);
    }, 800);
  };

  return (
    <div className="h-[calc(100vh-80px)] min-h-[580px] text-slate-100 font-sans p-1 sm:p-4 flex flex-col items-center justify-center overflow-hidden">
      {/* 100% VIEWPORT FIT RADIAL WHEEL SECTION */}
      <section className="w-full max-w-[1400px] h-full flex items-center justify-center mx-auto my-auto">
        <RadialNavigationWheel
          suggestedAgentId={suggestedAgentId}
          onSelectAgent={handleAgentSelect}
        >
          {/* ZENTRALE CYBER-SEARCH KARTE */}
          <div className="p-6 sm:p-7 rounded-3xl border border-cyan-500/40 bg-slate-900/95 shadow-[0_0_80px_rgba(6,182,212,0.22)] backdrop-blur-2xl space-y-5 transition-all">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                  <IconSearch size={22} />
                </div>
                <div>
                  <h3 className="font-extrabold text-sm sm:text-base tracking-wider text-white m-0 uppercase">
                    WEBRECHERCHE & COMPANY BRAIN <span className="text-cyan-400">SCHALTZENTRALE</span>
                  </h3>
                  <p className="text-[11px] text-slate-400 m-0">Anonyme SearXNG Egress & Dual Retrieval Pipeline</p>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/40 uppercase tracking-widest hidden sm:inline-block">
                Souveränes KI-OS
              </span>
            </div>

            {/* Central Large Input Form */}
            <form onSubmit={handleExecuteSearch} className="space-y-3.5">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Geben Sie Ihre Suchanfrage oder Webrecherche ein... (z. B. 'Aktuelle Handwerkerpreise Fassadendämmung 2026')"
                  className="w-full bg-slate-950/90 border-2 border-slate-800 focus:border-cyan-400 text-white rounded-2xl px-5 py-4 text-xs sm:text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 transition-all pr-32 shadow-inner"
                />
                <button
                  type="submit"
                  disabled={isSearching}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:scale-105 active:scale-95 transition-all cursor-pointer font-black text-xs shadow-[0_0_20px_#06b6d4] inline-flex items-center gap-1.5"
                >
                  {isSearching ? (
                    <span className="animate-pulse">Recherche...</span>
                  ) : (
                    <>
                      <span>Recherche</span>
                      <IconArrowRight size={15} />
                    </>
                  )}
                </button>
              </div>

              {/* Integrated Options Bar */}
              <div className="flex flex-wrap items-center justify-between gap-2.5 pt-1 text-xs">
                {/* Modellauswahl Dropdown */}
                <div className="flex items-center gap-2 bg-slate-950/70 px-3 py-1.5 rounded-xl border border-slate-800">
                  <IconCpu size={15} className="text-cyan-400" />
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
                      ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.2)]"
                      : "bg-slate-950/70 border-slate-800 text-slate-400"
                  }`}
                >
                  {ipProtection ? <IconShieldCheck size={15} className="text-cyan-400" /> : <IconShieldOff size={15} />}
                  <span>IP-Schutz: {ipProtection ? "AN (SearXNG Anonym)" : "AUS (Direkt)"}</span>
                </button>
              </div>
            </form>

            {/* Smart Intent Suggestion Banner */}
            {suggestedAgentId && (
              <div className="p-3 rounded-2xl bg-cyan-500/15 border border-cyan-400/50 flex items-center justify-between text-xs animate-in fade-in duration-200 shadow-[0_0_20px_rgba(6,182,212,0.25)]">
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
                  onClick={() => {
                    const agent = RADIAL_AGENTS.find((a) => a.id === suggestedAgentId);
                    if (agent) handleAgentSelect(agent);
                  }}
                  className="px-3 py-1 rounded-xl bg-cyan-400 text-slate-950 font-black text-xs hover:bg-cyan-300 transition-colors cursor-pointer shadow-[0_0_12px_#06b6d4]"
                >
                  Zu Agent ➔
                </button>
              </div>
            )}

            {/* WEBRECHERCHE ERGEBNISSEN ANZEIGE */}
            {searchResults && (
              <div className="mt-3 p-3.5 rounded-2xl bg-slate-950/90 border border-cyan-500/40 text-xs space-y-2.5 animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between text-cyan-400 font-mono font-bold border-b border-slate-800 pb-1.5">
                  <span className="flex items-center gap-1.5">
                    <IconBrandGoogle size={14} />
                    SearXNG Egress Ergebnisse ({searchResults.timestamp})
                  </span>
                  <span className="text-[10px] text-slate-400">Modell: {selectedModel}</span>
                </div>
                <p className="text-slate-200 leading-relaxed font-sans text-[11px]">{searchResults.synthesis}</p>
                <div className="space-y-1 pt-0.5">
                  {searchResults.sources.map((s: any, idx: number) => (
                    <div key={idx} className="p-1.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-[11px]">
                      <span className="text-slate-300 truncate max-w-md">{s.title}: {s.snippet}</span>
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline flex items-center gap-1">
                        <span>Quelle</span>
                        <IconExternalLink size={12} />
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </RadialNavigationWheel>
      </section>
    </div>
  );
}
