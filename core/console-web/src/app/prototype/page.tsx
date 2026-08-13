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
} from "@tabler/icons-react";

export default function PrototypeStartPage() {
  const router = useRouter();

  // Search input & model state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("qwen2.5-coder:14b");
  const [ipProtection, setIpProtection] = useState(true);

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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 sm:p-6 flex flex-col items-center justify-center">
      {/* PURISTISCHE STARTSEITE: NUR DAS CENTRIERTE NAVIGATIONSRAD – KEINE UNTEREN BOXEN */}
      <section className="w-full max-w-5xl mx-auto my-auto space-y-4">
        <RadialNavigationWheel
          suggestedAgentId={suggestedAgentId}
          onSelectAgent={handleAgentSelect}
        >
          {/* ZENTRALE CYBER-SEARCH KARTE */}
          <div className="p-6 sm:p-7 rounded-3xl border border-cyan-500/30 bg-slate-900/90 shadow-[0_0_50px_rgba(6,182,212,0.18)] backdrop-blur-2xl space-y-5 transition-all">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  <IconSearch size={18} />
                </div>
                <span className="font-extrabold text-sm tracking-wide text-white">
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
                className="w-full bg-slate-950/80 border border-slate-800 focus:border-cyan-400 text-white rounded-2xl px-4 py-3.5 text-xs sm:text-sm placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-400 transition-all pr-12 shadow-inner"
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:scale-105 transition-transform cursor-pointer font-bold shadow-[0_0_12px_#06b6d4]"
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
                  onClick={() => {
                    const agent = RADIAL_AGENTS.find((a) => a.id === suggestedAgentId);
                    if (agent) handleAgentSelect(agent);
                  }}
                  className="px-3 py-1 rounded-xl bg-cyan-400 text-slate-950 font-black text-xs hover:bg-cyan-300 transition-colors cursor-pointer"
                >
                  Zu Agent ➔
                </button>
              </div>
            )}
          </div>
        </RadialNavigationWheel>
      </section>
    </div>
  );
}
