"use client";

import React, { useState } from "react";
import { ResearchAgentModal } from "@/components/ResearchAgentModal";

interface SourceItem {
  title: string;
  url?: string;
  snippet?: string;
  source_type?: string;
  trust_score?: number;
  score?: number;
}

interface PromptContext {
  system?: string;
  user?: string;
  full_prompt_text?: string;
  contextCharCount?: number;
  token_estimate?: number;
  orchestratorContext?: Record<string, unknown>;
}

interface ResearchResponse {
  query?: string;
  summary?: string;
  answer?: string;
  sources?: SourceItem[];
  confidence?: number;
  anonymity_active?: boolean;
  model_used?: string;
  model?: string;
  sub_questions?: string[];
  llmContext?: Record<string, unknown>;
}

const LAGEBILD_MODELS = [
  { id: "auto", label: "✨ Auto-Router (Smart)", desc: "Analysiert Intent & wählt automatisch das optimale Monster-Modell" },
  { id: "qwen2.5-coder:14b", label: "Qwen 2.5 Coder 14B (Souverän & Schnelligkeit)", desc: "Ultra-schnelle lokale Inferenz (0.35s VRAM-Hit), Code, JSON & Tool-Calling" },
  { id: "deepseek-r1:32b", label: "DeepSeek-R1 32B (Reasoning & Logik)", desc: "Logik, Reasoning & komplexe Problemlösung (128k Kontext)" },
  { id: "mistral-nemo:12b", label: "Mistral Nemo 12B (Deutsche Texte)", desc: "E-Mails, Blogs & deutsche Texte (128k Kontext)" },
  { id: "hermes3:8b", label: "Hermes 3 8B (Multi-Agent)", desc: "Multi-Agenten Orchestrierung & Tool-Calling" },
  { id: "llama3.2-vision:11b", label: "Llama 3.2 Vision 11B (Vision/PDF)", desc: "OCR, Bild-, PDF- & Dokumentenanalyse" },
  { id: "openrouter/balanced", label: "☁️ OpenRouter Cloud (Balanced)", desc: "Nemotron Super 120B — OpenRouter Cloud (262K Kontext)" },
  { id: "openrouter/premium", label: "☁️ OpenRouter Cloud (Premium)", desc: "Nemotron Ultra 550B / Claude 3.5 — OpenRouter Frontier (1M Kontext)" },
  { id: "openrouter/coding", label: "☁️ OpenRouter Cloud (Coding)", desc: "Qwen 2.5 Coder 32B Instruct — Agentic Coding" },
];

function cleanTextSnippet(text?: string): string {
  if (!text) return "";
  let s = String(text);
  s = s.replace(/<(script|style|svg)[^>]*>[\s\S]*?<\/\1>/gi, "");
  s = s.replace(/<[^>]+>/g, " ");
  s = s.replace(/(?:var|let|const|function)\s+\w+\s*=.*?;/g, " ");
  s = s.replace(/&\w+;/g, " ");
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

export function ResearchAgentWorkspace() {
  const [isModalOpen, setIsModalOpen] = useState(false);
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
  const summaryText = result?.summary || result?.answer || "";

  return (
    <div className="space-y-6">
      {/* Fullscreen Pop-up Launcher Banner */}
      <div className="p-5 rounded-2xl border border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_8%,white)] shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="badge" data-variant="graph">
              Vollbild-Arbeitsfenster
            </span>
            <span className="badge" data-variant="curated">
              Company Brain Auto-Save
            </span>
          </div>
          <h3 className="section-title text-base font-bold text-[var(--ink)] m-0">
            Recherche in großem Arbeitsfenster (Pop-up) ausführen
          </h3>
          <p className="text-xs muted m-0 mt-0.5">
            Öffnet das volle Fenster für tiefgehende Recherche, Modellauswahl, Kontext-Inspektion und automatisches Speichern im Unternehmensgedächtnis.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="btn-primary text-xs font-bold py-2.5 px-6 flex items-center gap-2"
        >
          🚀 Recherche-Workspace in Vollbild öffnen
        </button>
      </div>

      {/* Top Card & Form */}
      <div className="p-6 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,white_75%,transparent)] shadow-sm space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--line)] pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="badge" data-variant="graph">
                Fachagent · Recherche-Agent
              </span>
              <span
                className="badge"
                data-variant={anonymize ? "curated" : "raw"}
              >
                {anonymize ? "🛡️ SearXNG Anonym Aktiv" : "🌐 Direkt-Modus"}
              </span>
            </div>
            <h2 className="section-title text-xl font-bold text-[var(--ink)] m-0 flex items-center gap-2">
              <span>🔎</span> Recherche-Agent Vorschau
            </h2>
            <p className="text-xs muted mt-1 leading-relaxed m-0">
              Multi-Hop Dual-Retrieval: Durchsucht gleichzeitig das lokale Company Brain & das Internet via SearXNG (IP-anonymisiert).
            </p>
          </div>

          <button
            type="button"
            onClick={() => setAnonymize(!anonymize)}
            className="btn-ghost text-xs font-mono"
          >
            {anonymize ? "🔒 IP-Schutz: Aktiv" : "🔓 IP-Schutz: Deaktiviert"}
          </button>
        </div>

        {/* Query Input */}
        <div className="space-y-4 pt-1">
          <div>
            <label className="mono text-[11px] uppercase muted block mb-1.5 font-bold">
              Rechercheanfrage / Thema
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="z. B. SAP S/4HANA Migration Performance im Vergleich zu Oracle Cloud ERP 2026..."
              className="w-full p-3 rounded-xl border border-[var(--line)] bg-white text-sm text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)] font-sans"
              onKeyDown={(e) => e.key === "Enter" && executeResearch(false)}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Model Selector */}
            <div>
              <label className="mono text-[11px] uppercase muted block mb-1 font-bold">
                Modell auswählen (Lagebild)
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-[var(--line)] bg-white text-xs font-mono text-[var(--ink)] focus:outline-none"
              >
                {LAGEBILD_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Depth Selector */}
            <div>
              <label className="mono text-[11px] uppercase muted block mb-1 font-bold">
                Recherche-Tiefe
              </label>
              <div className="flex p-1 rounded-xl border border-[var(--line)] bg-white gap-1">
                <button
                  type="button"
                  onClick={() => setDepth("quick")}
                  className={`flex-1 text-xs py-1.5 font-bold rounded-lg transition-all ${
                    depth === "quick"
                      ? "bg-[var(--signal)] text-white shadow-xs"
                      : "text-[var(--ink-soft)] hover:text-[var(--ink)]"
                  }`}
                >
                  ⚡ Quick (30s)
                </button>
                <button
                  type="button"
                  onClick={() => setDepth("deep")}
                  className={`flex-1 text-xs py-1.5 font-bold rounded-lg transition-all ${
                    depth === "deep"
                      ? "bg-[var(--signal)] text-white shadow-xs"
                      : "text-[var(--ink-soft)] hover:text-[var(--ink)]"
                  }`}
                >
                  🔬 Deep (Multi-Hop)
                </button>
              </div>
            </div>

            {/* Compute Mode */}
            <div>
              <label className="mono text-[11px] uppercase muted block mb-1 font-bold">
                Compute-Modus
              </label>
              <select
                value={computeMode}
                onChange={(e) => setComputeMode(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-[var(--line)] bg-white text-xs font-mono text-[var(--ink)] focus:outline-none"
              >
                <option value="sovereign">Local Sovereign (Lokal)</option>
                <option value="balanced">Balanced Hybrid</option>
                <option value="premium">Premium Cloud API</option>
              </select>
            </div>
          </div>

          <div className="pt-3 flex items-center justify-between border-t border-[var(--line)]">
            <span className="mono text-xs muted">
              Modell: <strong className="text-[var(--ink)]">{selectedModel}</strong>
            </span>
            <button
              type="button"
              disabled={loading || !query.trim()}
              onClick={() => executeResearch(false)}
              className="btn-primary text-xs font-bold py-2.5 px-6"
            >
              {loading ? "⌛ Recherchiere…" : "🚀 Recherche Starten"}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono">
          ❌ Fehler: {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-5">
          {/* Action Toolbar with Prompt Inspector */}
          <div className="p-4 rounded-xl border border-[var(--line)] bg-white flex items-center justify-between gap-4 text-xs">
            <div className="flex flex-wrap items-center gap-3 mono">
              <span className="badge" data-variant="graph">
                Modell: {result.model || result.model_used || selectedModel}
              </span>
              <span className="badge" data-variant="curated">
                Quellen: {result.sources?.length || 0}
              </span>
              {result.confidence ? (
                <span className="badge" data-variant="ok">
                  Vertrauen: {Math.round(result.confidence * 100)}%
                </span>
              ) : null}
            </div>

            <button
              type="button"
              onClick={() => setShowPromptModal(true)}
              className="btn-ghost text-xs font-mono flex items-center gap-1.5 text-[var(--signal)] border-[var(--signal)]"
            >
              <span>📄</span> Kompletten Prompt anzeigen
            </button>
          </div>

          {/* Synthesis Result Card */}
          <div className="p-6 rounded-2xl border border-[var(--line)] bg-white space-y-4 shadow-sm">
            <h3 className="section-title text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
              <span>📋</span> Synthese & Befund
            </h3>
            <div className="p-4 rounded-xl bg-[color-mix(in_oklab,white_95%,var(--ink))] border border-[var(--line)] text-xs text-[var(--ink)] leading-relaxed whitespace-pre-wrap">
              {summaryText || "Keine Zusammenfassung erzeugt."}
            </div>

            {/* Sub-Questions */}
            {result.sub_questions && result.sub_questions.length > 0 && (
              <div className="pt-3 border-t border-[var(--line)] space-y-2">
                <h4 className="mono text-[11px] uppercase muted font-bold">
                  Teilfragen & Zerlegung (Planner-State):
                </h4>
                <ul className="space-y-1">
                  {result.sub_questions.map((q, idx) => (
                    <li key={idx} className="text-xs text-[var(--ink)] flex items-start gap-2">
                      <span className="text-[var(--signal)]">▸</span> {q}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Citations List */}
          {result.sources && result.sources.length > 0 && (
            <div className="p-6 rounded-2xl border border-[var(--line)] bg-white space-y-4 shadow-sm">
              <h3 className="section-title text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                <span>📚</span> Quellennachweise & Citations ({result.sources.length})
              </h3>
              <div className="space-y-3">
                {result.sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_90%,transparent)] text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      {src.url ? (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-bold text-[var(--signal)] hover:underline truncate"
                        >
                          {src.title || "Quelle"}
                        </a>
                      ) : (
                        <span className="font-bold text-[var(--ink)]">{src.title || "Quelle"}</span>
                      )}
                      <span className="badge" data-variant="graph">
                        {src.source_type === "local_brain" ? "🧠 Company Brain" : "🌐 Web (SearXNG)"}
                      </span>
                    </div>
                    {src.snippet ? (
                      <p className="muted text-[11px] line-clamp-2 m-0">{cleanTextSnippet(src.snippet)}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Interactive Dialogue Refinement Panel */}
          <div className="p-6 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] space-y-3">
            <h4 className="text-xs font-bold text-[var(--ink)] m-0 flex items-center gap-2">
              <span>💬</span> Interaktiver Dialog & Verfeinerung
            </h4>
            <p className="text-xs muted m-0">
              Möchtest du bestimmte Punkte vertiefen oder eine korrigierte Suchrichtung eingeben?
            </p>
            <div className="flex gap-3 pt-1">
              <input
                type="text"
                value={refinementText}
                onChange={(e) => setRefinementText(e.target.value)}
                placeholder="z. B. Fokussiere dich auf Lizenzaspekte und erstelle einen Tabellenvergleich..."
                className="flex-1 p-2.5 rounded-xl border border-[var(--line)] bg-white text-xs text-[var(--ink)] focus:outline-none"
                onKeyDown={(e) => e.key === "Enter" && executeResearch(true)}
              />
              <button
                type="button"
                disabled={loading || !refinementText.trim()}
                onClick={() => executeResearch(true)}
                className="btn-ghost text-xs font-bold text-[var(--signal)] border-[var(--signal)]"
              >
                Verfeinern
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PROMPT INSPECTOR MODAL */}
      {showPromptModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[var(--line)] rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl rise">
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--line)] flex items-center justify-between bg-[color-mix(in_oklab,white_95%,var(--ink))] rounded-t-2xl">
              <div className="flex items-center gap-2">
                <span>📄</span>
                <h3 className="text-sm font-bold text-[var(--ink)] mono m-0">
                  Prompt Inspektor & Context Bundle
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPromptModal(false)}
                className="btn-ghost text-xs mono"
              >
                ✕ Schließen
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs mono text-[var(--ink)]">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_90%,transparent)]">
                <div>
                  <span className="muted">Zeichenanzahl:</span>{" "}
                  <strong>
                    {promptDetails?.contextCharCount || (result?.llmContext?.prompt as any)?.contextCharCount || 0} Zeichen
                  </strong>
                </div>
                <div>
                  <span className="muted">Geschätzte Tokens:</span>{" "}
                  <strong>
                    ~{promptDetails?.token_estimate || Math.round((promptDetails?.contextCharCount || 0) / 4)} Tokens
                  </strong>
                </div>
              </div>

              <div>
                <h4 className="text-[var(--signal)] font-bold mb-1 uppercase tracking-wider text-[10px]">
                  System Prompt (SystemSlice & Guardrails):
                </h4>
                <pre className="p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] text-[11px] whitespace-pre-wrap overflow-x-auto m-0">
                  {promptDetails?.system || (result?.llmContext?.prompt as any)?.system || "Kein System-Prompt erfasst."}
                </pre>
              </div>

              <div>
                <h4 className="text-[var(--signal)] font-bold mb-1 uppercase tracking-wider text-[10px]">
                  User Prompt (TaskSlice & Context):
                </h4>
                <pre className="p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] text-[11px] whitespace-pre-wrap overflow-x-auto m-0">
                  {promptDetails?.user || (result?.llmContext?.prompt as any)?.user || "Kein User-Prompt erfasst."}
                </pre>
              </div>

              <div>
                <h4 className="text-[var(--signal)] font-bold mb-1 uppercase tracking-wider text-[10px]">
                  Vollständiges Raw LLM-Context JSON:
                </h4>
                <pre className="p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_96%,var(--ink))] text-[var(--ink)] text-[10px] overflow-x-auto max-h-56 m-0">
                  {JSON.stringify(result?.llmContext || {}, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FULLSCREEN POPUP MODAL */}
      <ResearchAgentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialQuery={query}
      />
    </div>
  );
}
