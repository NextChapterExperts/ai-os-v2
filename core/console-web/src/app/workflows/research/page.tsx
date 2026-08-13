"use client";

import React, { useState } from "react";
import {
  IconSearch,
  IconShieldCheck,
  IconShieldOff,
  IconGlobe,
  IconBrain,
  IconBolt,
  IconMicroscope,
  IconRocket,
  IconLock,
  IconFileText,
  IconBook,
  IconExternalLink,
  IconX,
  IconRefresh,
  IconMessageDots,
  IconLoader2,
  IconSparkles,
  IconAlertTriangle,
  IconClipboardText,
} from "@tabler/icons-react";

interface SourceItem {
  title?: string;
  url?: string;
  snippet?: string;
  source_type?: string;
  trust_score?: number;
}

interface PromptContext {
  system?: string;
  user?: string;
  full_prompt_text?: string;
  contextCharCount?: number;
  token_estimate?: number;
  orchestratorContext?: any;
}

interface ResearchResponse {
  query?: string;
  summary?: string;
  answer?: string;
  sources?: SourceItem[];
  confidence: number;
  anonymity_active: boolean;
  model_used: string;
  sub_questions?: string[];
  llmContext?: any;
}

const AVAILABLE_MODELS = [
  { id: "qwen2.5-coder:14b", label: "Qwen 2.5 Coder 14B (Souverän & Schnell)" },
  { id: "deepseek-r1:32b", label: "DeepSeek-R1 32B (Reasoning & Logik)" },
  { id: "mistral-nemo:12b", label: "Mistral Nemo 12B (Deutsche Texte)" },
  { id: "hermes3:8b", label: "Hermes 3 8B (Multi-Agent)" },
  { id: "llama3.2-vision:11b", label: "Llama 3.2 Vision 11B (Vision/PDF)" },
];

function renderMarkdownReport(text?: string) {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div className="space-y-2 text-xs font-sans leading-relaxed text-slate-200">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1" />;
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-sm font-bold text-indigo-300 mt-4 mb-1">
              {trimmed.replace(/^###\s+/, "")}
            </h3>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={idx} className="text-base font-bold text-slate-100 mt-5 mb-2">
              {trimmed.replace(/^##\s+/, "")}
            </h2>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h1 key={idx} className="text-lg font-bold text-slate-100 mt-6 mb-3">
              {trimmed.replace(/^#\s+/, "")}
            </h1>
          );
        }
        return (
          <p key={idx} className={trimmed.startsWith("- ") ? "ml-3 border-l-2 border-indigo-500/40 pl-2 text-slate-300" : ""}>
            {trimmed.replace(/^- /, "")}
          </p>
        );
      })}
    </div>
  );
}

export default function ResearchWorkflowPage() {
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState<"quick" | "deep">("quick");
  const [selectedModel, setSelectedModel] = useState("qwen2.5-coder:14b");
  const [computeMode, setComputeMode] = useState("sovereign");
  const [anonymize, setAnonymize] = useState(true);
  const [refinementText, setRefinementText] = useState("");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeResearch = async (isRefinement = false) => {
    const activeQuery = isRefinement ? query : query.trim();
    if (!activeQuery) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent: "research",
          tenant_id: "nextchapter",
          params: {
            query: activeQuery,
            depth,
            model: selectedModel,
            compute_mode: computeMode,
            anonymize,
            refinement_feedback: isRefinement ? refinementText : undefined,
          },
        }),
      });

      if (!res.ok) {
        throw new Error(`Dispatch Fehler: HTTP ${res.status}`);
      }

      const data = await res.json();
      if (data.error && !data.answer) {
        throw new Error(data.error);
      }
      setResult(data);
    } catch (err: unknown) {
      console.error("Research error:", err);
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Fehler bei der Ausführung der Recherche.");
    } finally {
      setLoading(false);
    }
  };

  const promptDetails: PromptContext | null = result?.llmContext?.prompt ?? null;

  return (
    <div className="max-w-6xl mx-auto p-6 md:p-10 font-sans">
      {/* Top Banner Header */}
      <div className="bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-950 border border-indigo-900/40 rounded-2xl p-6 mb-8 shadow-2xl backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3 font-display">
              <IconSearch size={24} className="text-indigo-400" />
              <span>AI-OS Recherche-Agent & Deep-Web Cockpit</span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Multi-Hop Dual-Retrieval: Durchsucht gleichzeitig das lokale Company Brain & das Internet via SearXNG.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1 text-xs font-mono rounded-full border inline-flex items-center gap-1.5 ${
                anonymize
                  ? "bg-emerald-950/60 border-emerald-600/40 text-emerald-400"
                  : "bg-amber-950/60 border-amber-600/40 text-amber-400"
              }`}
            >
              {anonymize ? <IconShieldCheck size={14} /> : <IconShieldOff size={14} />}
              <span>{anonymize ? "Anonymer SearXNG Egress Aktiv" : "Direkter Modus"}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Control Form */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 mb-8 shadow-xl backdrop-blur-md">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-2 uppercase tracking-wider">
              Rechercheanfrage / Thema
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="z. B. SAP S/4HANA Migration Performance im Vergleich zu Oracle Cloud ERP 2026..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-slate-100 text-sm focus:outline-none focus:border-indigo-500 font-sans transition-all"
              onKeyDown={(e) => e.key === "Enter" && executeResearch(false)}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {/* Model Selector Dropdown */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1 uppercase tracking-wider">
                Modell auswählen
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-xs font-mono focus:outline-none focus:border-indigo-500"
              >
                {AVAILABLE_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Depth Selector */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1 uppercase tracking-wider">
                Recherche-Tiefe
              </label>
              <div className="flex bg-slate-950 border border-slate-700 rounded-lg p-1">
                <button
                  type="button"
                  onClick={() => setDepth("quick")}
                  className={`flex-1 text-xs py-1.5 font-medium rounded-md transition-colors inline-flex items-center justify-center gap-1 ${
                    depth === "quick"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <IconBolt size={14} />
                  <span>Quick (30s)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setDepth("deep")}
                  className={`flex-1 text-xs py-1.5 font-medium rounded-md transition-colors inline-flex items-center justify-center gap-1 ${
                    depth === "deep"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <IconMicroscope size={14} />
                  <span>Deep (Multi-Hop)</span>
                </button>
              </div>
            </div>

            {/* Anonymity Toggle */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1 uppercase tracking-wider">
                IP / Anonymisierung
              </label>
              <button
                type="button"
                onClick={() => setAnonymize(!anonymize)}
                className={`w-full py-2 px-3 text-xs font-mono rounded-lg border text-left transition-colors flex items-center justify-between cursor-pointer ${
                  anonymize
                    ? "bg-emerald-950/40 border-emerald-700/50 text-emerald-300"
                    : "bg-slate-950 border-slate-700 text-slate-400"
                }`}
              >
                <span>{anonymize ? "Anonym: An" : "Anonym: Aus"}</span>
                <span className="text-xs inline-flex items-center gap-1">
                  {anonymize ? <IconLock size={13} /> : <IconGlobe size={13} />}
                  <span>{anonymize ? "Proxy/SearXNG" : "Direkt"}</span>
                </span>
              </button>
            </div>
          </div>

          <div className="pt-3 flex items-center justify-between border-t border-slate-800/80">
            <span className="text-xs font-mono text-slate-500">
              Compute-Modus: <span className="text-indigo-400 font-semibold">{computeMode}</span>
            </span>
            <button
              type="button"
              disabled={loading || !query.trim()}
              onClick={() => executeResearch(false)}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold px-6 py-2.5 rounded-lg shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer border-none"
            >
              {loading ? (
                <>
                  <IconLoader2 size={16} className="animate-spin" />
                  <span>Recherchiere...</span>
                </>
              ) : (
                <>
                  <IconRocket size={16} />
                  <span>Recherche Starten</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-8 p-4 bg-rose-950/50 border border-rose-700/50 text-rose-300 rounded-xl text-sm font-mono flex items-center gap-2">
          <IconAlertTriangle size={16} />
          <span>Fehler: {error}</span>
        </div>
      )}

      {/* Results & Prompt Inspector Panel */}
      {result && (
        <div className="space-y-6 rise">
          {/* Action Toolbar */}
          <div className="flex items-center justify-between bg-slate-900/90 border border-slate-800 rounded-xl px-5 py-3 shadow-md">
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="text-slate-400">
                Modell: <span className="text-indigo-300 font-semibold">{result.model_used}</span>
              </span>
              <span className="text-slate-400">
                Vertrauen:{" "}
                <span
                  className={
                    result.confidence >= 0.8
                      ? "text-emerald-400 font-semibold"
                      : "text-amber-400 font-semibold"
                  }
                >
                  {Math.round(result.confidence * 100)}%
                </span>
              </span>
              <span className="text-slate-400">
                Quellen: <span className="text-slate-200 font-semibold">{result.sources?.length || 0}</span>
              </span>
            </div>

            {/* Prompt Inspector Modal Trigger Button */}
            <button
              type="button"
              onClick={() => setShowPromptModal(true)}
              className="bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/30 text-xs font-mono px-3.5 py-1.5 rounded-lg transition-colors inline-flex items-center gap-1.5 cursor-pointer"
            >
              <IconFileText size={14} />
              <span>Kompletten Prompt anzeigen</span>
            </button>
          </div>

          {/* Research Summary Card */}

          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-100 mb-4 font-display flex items-center gap-2">
              <IconClipboardText size={20} className="text-indigo-400" />
              <span>Synthese & Befund</span>
            </h2>
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              {renderMarkdownReport(result.summary)}
            </div>


            {/* Sub-Questions Decomposition */}
            {result.sub_questions && result.sub_questions.length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-800">
                <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2">
                  Teilfragen & Zerlegung (Planner-State):
                </h3>
                <ul className="space-y-1.5">
                  {result.sub_questions.map((q, idx) => (
                    <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                      <span className="text-indigo-400 font-bold">▸</span> {q}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Sources & Citations */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-100 mb-4 font-display flex items-center gap-2">
              <IconBook size={20} className="text-indigo-400" />
              <span>Quellennachweise & Citations ({result.sources?.length || 0})</span>
            </h2>
            {result.sources && result.sources.length > 0 ? (
              <div className="grid grid-cols-1 gap-3">
                {result.sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-lg hover:border-slate-700 transition-all"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:text-indigo-300 font-medium text-sm transition-colors truncate max-w-xl inline-flex items-center gap-1"
                      >
                        <span>{src.title}</span>
                        <IconExternalLink size={13} />
                      </a>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border inline-flex items-center gap-1 ${
                          src.source_type === "local_brain"
                            ? "bg-purple-950/50 border-purple-600/40 text-purple-300"
                            : "bg-blue-950/50 border-blue-600/40 text-blue-300"
                        }`}
                      >
                        {src.source_type === "local_brain" ? <IconBrain size={12} /> : <IconGlobe size={12} />}
                        <span>{src.source_type === "local_brain" ? "Company Brain" : "Web (SearXNG)"}</span>
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2">{src.snippet}</p>
                    <div className="mt-2 text-[10px] font-mono text-slate-500 truncate">{src.url}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 font-mono">Keine Quellenverweise vorhanden.</p>
            )}
          </div>

          {/* Interactive Refinement Panel */}
          <div className="bg-slate-900/80 border border-indigo-900/50 rounded-xl p-6 shadow-xl">
            <h3 className="text-sm font-bold text-indigo-300 mb-2 font-display flex items-center gap-2">
              <IconMessageDots size={18} className="text-indigo-400" />
              <span>Interaktiver Dialog & Verfeinerung</span>
            </h3>
            <p className="text-xs text-slate-400 mb-3">
              Möchtest du bestimmte Punkte vertiefen oder eine korrigierte Suchrichtung eingeben?
            </p>
            <div className="flex gap-3">
              <input
                type="text"
                value={refinementText}
                onChange={(e) => setRefinementText(e.target.value)}
                placeholder="z. B. Fokussiere dich auf Lizenzaspekte und erstelle einen Tabellenvergleich..."
                className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                onKeyDown={(e) => e.key === "Enter" && executeResearch(true)}
              />
              <button
                type="button"
                disabled={loading || !refinementText.trim()}
                onClick={() => executeResearch(true)}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all inline-flex items-center gap-1.5 cursor-pointer border-none"
              >
                <IconSparkles size={14} />
                <span>Verfeinern</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PROMPT INSPECTOR MODAL */}
      {showPromptModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl rise">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80 rounded-t-xl">
              <div className="flex items-center gap-2">
                <IconFileText size={18} className="text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-100 font-mono">
                  Prompt Inspektor & Context Bundle
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPromptModal(false)}
                className="text-slate-400 hover:text-white font-mono text-sm px-2 py-1 rounded inline-flex items-center gap-1 cursor-pointer"
              >
                <IconX size={14} />
                <span>Schließen</span>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs font-mono text-slate-300">
              <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500">Zeichenanzahl:</span>{" "}
                  <span className="text-indigo-400 font-bold">
                    {promptDetails?.contextCharCount || result?.llmContext?.prompt?.contextCharCount || 0} Zeichen
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Geschätzte Tokens:</span>{" "}
                  <span className="text-indigo-400 font-bold">
                    ~{promptDetails?.token_estimate || Math.round((promptDetails?.contextCharCount || 0) / 4)} Tokens
                  </span>
                </div>
              </div>

              <div>
                <h4 className="text-indigo-400 font-semibold mb-1 uppercase tracking-wider text-[11px]">
                  System Prompt (SystemSlice & Guardrails):
                </h4>
                <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 whitespace-pre-wrap overflow-x-auto text-[11px]">
                  {promptDetails?.system || result?.llmContext?.prompt?.system || "Kein System-Prompt erfasst."}
                </pre>
              </div>

              <div>
                <h4 className="text-indigo-400 font-semibold mb-1 uppercase tracking-wider text-[11px]">
                  User Prompt (TaskSlice & Context):
                </h4>
                <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 whitespace-pre-wrap overflow-x-auto text-[11px]">
                  {promptDetails?.user || result?.llmContext?.prompt?.user || "Kein User-Prompt erfasst."}
                </pre>
              </div>

              <div>
                <h4 className="text-indigo-400 font-semibold mb-1 uppercase tracking-wider text-[11px]">
                  Vollständiges Raw LLM-Context JSON:
                </h4>
                <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-emerald-400 text-[10px] overflow-x-auto max-h-60 p-2">
                  {JSON.stringify(result?.llmContext || {}, null, 2)}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-slate-800 bg-slate-950/80 rounded-b-xl flex justify-end">
              <button
                type="button"
                onClick={() => setShowPromptModal(false)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs px-4 py-1.5 rounded-lg"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
