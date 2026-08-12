"use client";

import React, { useState, useEffect } from "react";

interface SourceItem {
  title: string;
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
  saved_to_brain?: boolean;
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
  s = s.replace(/<(script|style|svg)[^>]*>.*?<\/\1>/gis, "");
  s = s.replace(/<[^>]+>/g, " ");
  s = s.replace(/(?:var|let|const|function)\s+\w+\s*=.*?;/g, " ");
  s = s.replace(/&\w+;/g, " ");
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

export function ResearchAgentModal({
  isOpen,
  onClose,
  initialQuery = "",
}: {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}) {
  const [query, setQuery] = useState(initialQuery);
  const [depth, setDepth] = useState<"quick" | "deep">("quick");
  const [selectedModel, setSelectedModel] = useState("qwen2.5-coder:14b");
  const [computeMode, setComputeMode] = useState("sovereign");
  const [anonymize, setAnonymize] = useState(true);
  const [refinementText, setRefinementText] = useState("");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [showPromptInspector, setShowPromptInspector] = useState(false);
  const [showContextViewer, setShowContextViewer] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialQuery && !query) {
      setQuery(initialQuery);
    }
  }, [initialQuery, query]);

  if (!isOpen) return null;

  const executeResearch = async (isRefinement = false, saveToBrain = false) => {
    const activeQuery = query.trim();
    if (!activeQuery) return;

    setLoading(true);
    setError(null);
    if (!isRefinement) setSaveStatus(null);

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
            save_to_brain: saveToBrain,
          },
        }),
      });

      if (!res.ok) throw new Error(`Dispatch Fehler: HTTP ${res.status}`);

      const data = await res.json();
      if (data.error && !data.answer) throw new Error(data.error);

      setResult(data);
      if (saveToBrain || data.saved_to_brain) {
        setSaveStatus("✅ Im Unternehmensgedächtnis (Company Brain) gespeichert!");
      }
    } catch (err: unknown) {
      console.error("Research error:", err);
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Fehler bei der Recherche.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAndClose = async () => {
    if (result && !result.saved_to_brain) {
      await executeResearch(false, true);
    }
    setTimeout(() => {
      onClose();
    }, 400);
  };

  const currentModelMeta = LAGEBILD_MODELS.find((m) => m.id === selectedModel);
  const promptDetails: PromptContext | null = (result?.llmContext?.prompt as PromptContext) ?? null;
  const summaryText = result?.summary || result?.answer || "";

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col w-screen h-screen overflow-hidden rise">
      {/* Top Header Navigation Bar */}
      <header className="px-6 py-4 border-b border-[var(--line)] bg-white flex items-center justify-between gap-4 shrink-0 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[color-mix(in_oklab,var(--signal)_10%,white)] border border-[var(--signal)] flex items-center justify-center text-xl">
            🔎
          </div>
          <div>
            <h1 className="text-lg font-bold text-[var(--ink)] m-0 leading-tight">
              Recherche-Agent Workspace
            </h1>
            <p className="text-xs muted m-0 font-sans">
              Multi-Hop Dual-Retrieval: Unternehmensgedächtnis & SearXNG IP-Anonymisiert
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="badge" data-variant={anonymize ? "curated" : "raw"}>
            {anonymize ? "🛡️ SearXNG Proxy Aktiv" : "🌐 Direkt-Modus"}
          </span>

          {saveStatus && (
            <span className="badge" data-variant="ok">
              {saveStatus}
            </span>
          )}

          {/* Single primary save & close button */}
          <button
            type="button"
            onClick={handleSaveAndClose}
            className="btn-primary text-xs font-bold py-2.5 px-5 flex items-center gap-2"
          >
            💾 Speichern & Schließen
          </button>

          {/* Single clean close/cancel button */}
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost text-xs mono px-3"
          >
            ✕ Schließen
          </button>
        </div>
      </header>

      {/* Main Screen Layout: 2 Spacious Equal/Generous Columns */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden bg-[color-mix(in_oklab,white_98%,transparent)]">
        {/* Left Column (Width: 4/12) — Input, Parameters & Control Workspace */}
        <aside className="lg:col-span-4 p-6 border-r border-[var(--line)] bg-white overflow-y-auto space-y-6">
          {/* Query Textarea */}
          <div className="space-y-2">
            <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
              Recherchethema / Anfrage
            </label>
            <textarea
              rows={5}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Geben Sie hier das Thema ein, z. B. SAP S/4HANA Migration Performance im Vergleich zu Oracle Cloud ERP 2026..."
              className="w-full p-4 rounded-xl border border-[var(--line)] bg-white text-sm text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)] font-sans leading-relaxed shadow-xs"
            />
          </div>

          {/* Model Selector (Exact Lagebild Models) */}
          <div className="space-y-2">
            <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
              Modell auswählen (Lagebild / OpenRouter)
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full p-3 rounded-xl border border-[var(--line)] bg-white text-xs font-mono text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)]"
            >
              {LAGEBILD_MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
            {currentModelMeta && (
              <p className="text-[11px] text-[var(--ink-soft)] italic m-0 pt-1 leading-snug">
                💡 {currentModelMeta.desc}
              </p>
            )}
          </div>

          {/* Depth Selector */}
          <div className="space-y-2">
            <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
              Recherche-Tiefe
            </label>
            <div className="flex p-1 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] gap-1">
              <button
                type="button"
                onClick={() => setDepth("quick")}
                className={`flex-1 text-xs py-2 font-bold rounded-lg transition-all ${
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
                className={`flex-1 text-xs py-2 font-bold rounded-lg transition-all ${
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
          <div className="space-y-2">
            <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
              Compute-Modus
            </label>
            <select
              value={computeMode}
              onChange={(e) => setComputeMode(e.target.value)}
              className="w-full p-3 rounded-xl border border-[var(--line)] bg-white text-xs font-mono text-[var(--ink)] focus:outline-none"
            >
              <option value="sovereign">Sovereign (Lokal LAN)</option>
              <option value="balanced">Balanced Hybrid</option>
              <option value="premium">Premium Cloud API</option>
            </select>
          </div>

          {/* Anonymization Toggle */}
          <div className="space-y-2">
            <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
              Anonymisierung & IP-Schutz
            </label>
            <button
              type="button"
              onClick={() => setAnonymize(!anonymize)}
              className={`w-full p-3 rounded-xl border text-xs font-mono text-left flex items-center justify-between transition-all ${
                anonymize
                  ? "border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_8%,white)] text-[var(--ink)]"
                  : "border-[var(--line)] bg-white muted"
              }`}
            >
              <span>{anonymize ? "🛡️ SearXNG Proxy: Aktiv" : "🌐 Direkt-Modus"}</span>
              <span className="badge" data-variant={anonymize ? "curated" : "raw"}>
                {anonymize ? "Anonym" : "Direkt"}
              </span>
            </button>
          </div>

          {/* Start Button */}
          <button
            type="button"
            disabled={loading || !query.trim()}
            onClick={() => executeResearch(false)}
            className="w-full btn-primary text-xs font-bold py-3.5 text-center shadow-xs"
          >
            {loading ? "⌛ Recherchiere…" : "🚀 Recherche Starten"}
          </button>
        </aside>

        {/* Right Column (Width: 8/12) — Results, Context Viewer & Dialog Workspace */}
        <main className="lg:col-span-8 p-8 overflow-y-auto space-y-6 bg-[color-mix(in_oklab,white_97%,transparent)]">
          {error && (
            <div className="p-4 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono">
              ❌ Fehler: {error}
            </div>
          )}

          {result ? (
            <div className="space-y-6">
              {/* Metadata Toolbar */}
              <div className="p-4 rounded-2xl border border-[var(--line)] bg-white flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
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

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowContextViewer(!showContextViewer)}
                    className="btn-ghost text-xs mono"
                  >
                    {showContextViewer ? "🙈 Kontext verbergen" : "👁️ Kontext anzeigen"}
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowPromptInspector(!showPromptInspector)}
                    className="btn-ghost text-xs mono text-[var(--signal)] border-[var(--signal)]"
                  >
                    📄 Prompt Inspektor
                  </button>
                </div>
              </div>

              {/* Main Synthesis Result Box */}
              <div className="p-7 rounded-2xl border border-[var(--line)] bg-white space-y-4 shadow-xs">
                <h2 className="section-title text-lg font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                  <span>📋</span> Synthese & Befund
                </h2>
                <div className="p-5 rounded-xl bg-[color-mix(in_oklab,white_96%,var(--ink))] border border-[var(--line)] text-sm text-[var(--ink)] leading-relaxed whitespace-pre-wrap font-sans">
                  {summaryText || "Keine Zusammenfassung erzeugt."}
                </div>

                {result.sub_questions && result.sub_questions.length > 0 && (
                  <div className="pt-4 border-t border-[var(--line)] space-y-2">
                    <h3 className="mono text-[11px] uppercase muted font-bold tracking-wider">
                      Teilfragen & Zerlegung (Planner-State):
                    </h3>
                    <ul className="space-y-1.5 m-0 p-0 list-none">
                      {result.sub_questions.map((q, idx) => (
                        <li key={idx} className="text-xs text-[var(--ink)] flex items-start gap-2">
                          <span className="text-[var(--signal)] font-bold">▸</span> {q}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Context Chunks Viewer (Light VIRKI Theme) */}
              {showContextViewer && result.sources && result.sources.length > 0 && (
                <div className="p-7 rounded-2xl border border-[var(--line)] bg-white space-y-4 shadow-xs">
                  <h2 className="section-title text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                    <span>📖</span> Geladene Kontext-Abschnitte ({result.sources.length})
                  </h2>
                  <div className="space-y-3">
                    {result.sources.map((src, idx) => {
                      const cleanSnippet = cleanTextSnippet(src.snippet);
                      return (
                        <div
                          key={idx}
                          className="p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_98%,transparent)] text-xs space-y-2 hover:border-[var(--line-strong)] transition-all"
                        >
                          <div className="flex items-center justify-between gap-3">
                            {src.url ? (
                              <a
                                href={src.url}
                                target="_blank"
                                rel="noreferrer"
                                className="font-bold text-[var(--signal)] hover:underline truncate text-sm"
                              >
                                {src.title || "Quelle"}
                              </a>
                            ) : (
                              <span className="font-bold text-[var(--ink)] text-sm">{src.title || "Quelle"}</span>
                            )}
                            <span className="badge" data-variant="graph">
                              {src.source_type === "local_brain" ? "🧠 Company Brain" : "🌐 Web (SearXNG)"}
                            </span>
                          </div>
                          <p className="text-xs text-[var(--ink)] leading-relaxed m-0 font-sans">
                            {cleanSnippet || "Kein Textinhalt verfügbar."}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Dialogue Refinement Box */}
              <div className="p-7 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] space-y-3 shadow-xs">
                <h3 className="text-sm font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                  <span>💬</span> Interaktiver Dialog & Verfeinerung
                </h3>
                <p className="text-xs muted m-0">
                  Möchtest du bestimmte Punkte vertiefen oder eine korrigierte Suchrichtung eingeben?
                </p>
                <div className="flex gap-3 pt-1">
                  <input
                    type="text"
                    value={refinementText}
                    onChange={(e) => setRefinementText(e.target.value)}
                    placeholder="z. B. Fokussiere dich auf Lizenzaspekte und erstelle einen Tabellenvergleich..."
                    className="flex-1 p-3 rounded-xl border border-[var(--line)] bg-white text-xs text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)]"
                    onKeyDown={(e) => e.key === "Enter" && executeResearch(true)}
                  />
                  <button
                    type="button"
                    disabled={loading || !refinementText.trim()}
                    onClick={() => executeResearch(true)}
                    className="btn-ghost text-xs font-bold text-[var(--signal)] border-[var(--signal)] px-4"
                  >
                    Verfeinern
                  </button>
                </div>
              </div>

              {/* Prompt Inspector Sub-View (Light VIRKI Theme - No Pitch Black) */}
              {showPromptInspector && (
                <div className="p-6 rounded-2xl border border-[var(--line)] bg-white text-[var(--ink)] text-xs mono space-y-4 shadow-sm">
                  <div className="flex items-center justify-between border-b border-[var(--line)] pb-3">
                    <h3 className="font-bold text-[var(--signal)] m-0 text-sm">📄 Prompt Inspektor Context</h3>
                    <button
                      type="button"
                      onClick={() => setShowPromptInspector(false)}
                      className="btn-ghost text-xs mono"
                    >
                      ✕ Schließen
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-3 p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] text-[11px]">
                    <div>
                      <span className="muted">Zeichen:</span>{" "}
                      <strong>{promptDetails?.contextCharCount || 0} Zeichen</strong>
                    </div>
                    <div>
                      <span className="muted">Tokens:</span>{" "}
                      <strong>~{promptDetails?.token_estimate || 0} Tokens</strong>
                    </div>
                  </div>

                  <div>
                    <div className="text-[var(--signal)] font-bold mb-1.5 uppercase text-[10px] tracking-wider">System Prompt:</div>
                    <pre className="p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_97%,transparent)] text-[11px] whitespace-pre-wrap overflow-x-auto m-0 text-[var(--ink)]">
                      {promptDetails?.system || "Kein System-Prompt erfasst."}
                    </pre>
                  </div>

                  <div>
                    <div className="text-[var(--signal)] font-bold mb-1.5 uppercase text-[10px] tracking-wider">User Prompt:</div>
                    <pre className="p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_97%,transparent)] text-[11px] whitespace-pre-wrap overflow-x-auto m-0 text-[var(--ink)]">
                      {promptDetails?.user || "Kein User-Prompt erfasst."}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-12 muted">
              <span className="text-5xl mb-4">🔎</span>
              <h2 className="text-base font-bold text-[var(--ink)] m-0">Geben Sie ein Thema ein und starten Sie die Recherche.</h2>
              <p className="text-xs max-w-md mt-2 leading-relaxed">
                Der Recherche-Agent durchsucht Ihr Unternehmensgedächtnis (Company Brain) und führt bei Bedarf eine anonyme Web-Suche via SearXNG durch.
              </p>
            </div>
          )}
        </main>
      </div>

      {/* Footer Bar - Clean single status line (No duplicate buttons) */}
      <footer className="px-6 py-3 border-t border-[var(--line)] bg-white flex items-center justify-between shrink-0">
        <span className="text-xs muted font-mono">
          {result?.saved_to_brain
            ? "✅ Ergebnisse im Unternehmensgedächtnis gesichert."
            : "💾 Ergebnisse werden beim Schließen automatisch im Company Brain gespeichert."}
        </span>
      </footer>
    </div>
  );
}
