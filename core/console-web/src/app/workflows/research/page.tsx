"use client";

import { useState } from "react";

interface SourceItem {
  title: str;
  url: str;
  snippet: str;
  source_type: "local_brain" | "web_searxng";
  trust_score: number;
}

interface PromptContext {
  system: string;
  user: string;
  full_prompt_text?: string;
  contextCharCount?: number;
  token_estimate?: number;
  orchestratorContext?: any;
}

interface ResearchResponse {
  query: string;
  summary: string;
  sources: SourceItem[];
  confidence: number;
  anonymity_active: boolean;
  model_used: string;
  sub_questions?: string[];
  llmContext?: any;
}

const AVAILABLE_MODELS = [
  { id: "qwen2.5-coder:14b", label: "Qwen 2.5 Coder 14B (Sovereign Local Default)" },
  { id: "mistral-nemo:12b", label: "Mistral Nemo 12B (Fast Sovereign)" },
  { id: "hermes-3:8b", label: "Hermes 3 8B (Lightweight Local)" },
  { id: "deepseek-r1:32b", label: "DeepSeek R1 32B (Reasoning Heavy)" },
  { id: "openrouter/auto", label: "OpenRouter Cloud (Premium Fallback)" },
];

function renderMarkdownReport(text: string) {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div className="space-y-3 font-sans text-sm text-slate-200 leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-2" />;
        if (trimmed === "---") {
          return <hr key={idx} className="border-t border-slate-800 my-4" />;
        }
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-base font-bold text-indigo-300 mt-5 mb-2 flex items-center gap-2 font-display">
              {trimmed.replace(/^###\s+/, "")}
            </h3>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={idx} className="text-lg font-bold text-slate-100 mt-6 mb-2 font-display">
              {trimmed.replace(/^##\s+/, "")}
            </h2>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h1 key={idx} className="text-xl font-bold text-slate-100 mt-6 mb-3 font-display">
              {trimmed.replace(/^#\s+/, "")}
            </h1>
          );
        }

        const parts = line.split(/(\[\d+\]|\*\*[^*]+\*\*)/g);
        return (
          <div key={idx} className={trimmed.startsWith("- ") ? "ml-4 flex items-start gap-2" : ""}>
            {trimmed.startsWith("- ") ? <span className="text-indigo-400 font-bold">▸</span> : null}
            <span>
              {parts.map((part, pIdx) => {
                if (/^\[\d+\]$/.test(part)) {
                  return (
                    <span
                      key={pIdx}
                      className="inline-flex items-center justify-center px-1.5 py-0.5 mx-0.5 rounded bg-indigo-950/80 border border-indigo-500/50 text-indigo-300 font-mono font-bold text-[10px] align-baseline"
                    >
                      {part}
                    </span>
                  );
                }
                if (part.startsWith("**") && part.endsWith("**")) {
                  return <strong key={pIdx} className="text-slate-100">{part.slice(2, -2)}</strong>;
                }
                return part.replace(/^- /, "");
              })}
            </span>
          </div>
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
    const activeQuery = query.trim();
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

      const data = await res.json();
      const payloadObj = data.result && typeof data.result === "object" ? data.result : data;
      const summaryText = payloadObj.summary || payloadObj.answer || data.summary || data.answer || "";

      if (!res.ok && !summaryText) {
        throw new Error(data.error || data.message || `Dispatch Fehler: HTTP ${res.status}`);
      }

      if (summaryText) {
        setResult({
          query: payloadObj.query || activeQuery,
          summary: summaryText,
          sources: payloadObj.sources || [],
          confidence: payloadObj.confidence || 0.9,
          anonymity_active: payloadObj.anonymity_active ?? anonymize,
          model_used: payloadObj.model_used || payloadObj.model || selectedModel,
          sub_questions: payloadObj.sub_questions || [],
          llmContext: payloadObj.llmContext || data.llmContext,
        });
      } else {
        throw new Error(data.error || "Keine Zusammenfassung erhalten.");
      }
    } catch (err: any) {
      console.error("Research error:", err);
      setError(err.message || "Fehler bei der Ausführung der Recherche.");
    } finally {
      setLoading(false);
    }
  };


  const getPromptDetails = (): PromptContext | null => {
    if (!result?.llmContext?.prompt) return null;
    return result.llmContext.prompt;
  };

  const promptDetails = getPromptDetails();

  return (
    <section className="rise pt-8 pb-16 max-w-5xl mx-auto px-4">
      {/* Header */}
      <div className="mb-8 border-b border-slate-800 pb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3 font-display">
              <span>🔍</span> AI-OS Recherche-Agent & Deep-Web Cockpit
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Multi-Hop Dual-Retrieval: Durchsucht gleichzeitig das lokale Company Brain & das Internet via SearXNG.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1 text-xs font-mono rounded-full border ${
                anonymize
                  ? "bg-emerald-950/60 border-emerald-600/40 text-emerald-400"
                  : "bg-amber-950/60 border-amber-600/40 text-amber-400"
              }`}
            >
              {anonymize ? "🛡️ Anonymer SearXNG Egress Aktiv" : "⚠️ Direkter Modus"}
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
                  className={`flex-1 text-xs py-1.5 font-medium rounded-md transition-colors ${
                    depth === "quick"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  ⚡ Quick (30s)
                </button>
                <button
                  type="button"
                  onClick={() => setDepth("deep")}
                  className={`flex-1 text-xs py-1.5 font-medium rounded-md transition-colors ${
                    depth === "deep"
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  🔬 Deep (Multi-Hop)
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
                className={`w-full py-2 px-3 text-xs font-mono rounded-lg border text-left transition-colors flex items-center justify-between ${
                  anonymize
                    ? "bg-emerald-950/40 border-emerald-700/50 text-emerald-300"
                    : "bg-slate-950 border-slate-700 text-slate-400"
                }`}
              >
                <span>{anonymize ? "Anonym: An" : "Anonym: Aus"}</span>
                <span className="text-xs">{anonymize ? "🔒 Proxy/SearXNG" : "🌐 Direkt"}</span>
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
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold px-6 py-2.5 rounded-lg shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin">⏳</span> Recherchiere...
                </>
              ) : (
                <>🚀 Recherche Starten</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-8 p-4 bg-rose-950/50 border border-rose-700/50 text-rose-300 rounded-xl text-sm font-mono">
          ⚠️ {error}
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
              className="bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/30 text-xs font-mono px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-2"
            >
              <span>📄</span> Kompletten Prompt anzeigen
            </button>
          </div>

          {/* Research Summary Card */}

          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-100 mb-4 font-display flex items-center gap-2">
              <span>📋</span> Synthese & Befund
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
                      <span className="text-indigo-400">▸</span> {q}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Sources & Citations */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-100 mb-4 font-display flex items-center gap-2">
              <span>📚</span> Quellennachweise & Citations ({result.sources?.length || 0})
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
                        className="text-indigo-400 hover:text-indigo-300 font-medium text-sm transition-colors truncate max-w-xl"
                      >
                        {src.title}
                      </a>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          src.source_type === "local_brain"
                            ? "bg-purple-950/50 border-purple-600/40 text-purple-300"
                            : "bg-blue-950/50 border-blue-600/40 text-blue-300"
                        }`}
                      >
                        {src.source_type === "local_brain" ? "🧠 Company Brain" : "🌐 Web (SearXNG)"}
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

          {/* Interactive Refinement Panel (Human-in-the-Loop) */}
          <div className="bg-slate-900/80 border border-indigo-900/50 rounded-xl p-6 shadow-xl">
            <h3 className="text-sm font-bold text-indigo-300 mb-2 font-display flex items-center gap-2">
              <span>💬</span> Interaktiver Dialog & Verfeinerung
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
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all"
              >
                Verfeinern
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
                <span className="text-lg">📄</span>
                <h3 className="text-sm font-bold text-slate-100 font-mono">
                  Prompt Inspektor & Context Bundle
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPromptModal(false)}
                className="text-slate-400 hover:text-white font-mono text-sm px-2 py-1 rounded"
              >
                ✕ Schließen
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
    </section>
  );
}
