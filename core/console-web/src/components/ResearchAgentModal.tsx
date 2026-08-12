"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";

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
  return s;
}

function renderMarkdownReport(text: string) {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div className="space-y-3 font-sans text-sm text-[var(--ink)] leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-2" />;
        if (trimmed === "---") {
          return <hr key={idx} className="border-t border-[var(--line)] my-4" />;
        }
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-base font-bold text-[var(--ink)] mt-5 mb-2 flex items-center gap-2">
              {trimmed.replace(/^###\s+/, "")}
            </h3>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={idx} className="text-lg font-bold text-[var(--ink)] mt-6 mb-2">
              {trimmed.replace(/^##\s+/, "")}
            </h2>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h1 key={idx} className="text-xl font-bold text-[var(--ink)] mt-6 mb-3">
              {trimmed.replace(/^#\s+/, "")}
            </h1>
          );
        }

        // Process bold text and citations inside paragraph / bullet lines
        const parts = line.split(/(\[\d+\]|\*\*[^*]+\*\*)/g);
        return (
          <div key={idx} className={trimmed.startsWith("- ") ? "ml-4 flex items-start gap-2" : ""}>
            {trimmed.startsWith("- ") ? <span className="text-[var(--signal)] font-bold">▸</span> : null}
            <span>
              {parts.map((part, pIdx) => {
                if (/^\[\d+\]$/.test(part)) {
                  return (
                    <span
                      key={pIdx}
                      className="inline-flex items-center justify-center px-1.5 py-0.5 mx-0.5 rounded bg-[color-mix(in_oklab,var(--signal)_12%,white)] border border-[var(--signal)] text-[var(--signal)] font-mono font-bold text-[10px] align-baseline"
                    >
                      {part}
                    </span>
                  );
                }
                if (part.startsWith("**") && part.endsWith("**")) {
                  return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
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

const RESEARCH_STEPS = [
  { label: "Rechercheauftrag analysieren & Entitäten extrahieren", icon: "🔍", percent: 20 },
  { label: "Anonymisierte Web- & SearXNG-Egress-Recherche ausführen", icon: "🌐", percent: 50 },
  { label: "Unternehmensgedächtnis (Company Brain) durchsuchen & evaluieren", icon: "🧠", percent: 75 },
  { label: "Ergebnisse synthetisieren & In-Text Citations formatieren", icon: "📄", percent: 95 },
];

export function ResearchAgentModal({
  isOpen,
  onClose,
  initialQuery = "",
}: {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}) {
  const [mounted, setMounted] = useState(false);
  const [query, setQuery] = useState(initialQuery);
  const [depth, setDepth] = useState<"quick" | "deep">("quick");
  const [selectedModel, setSelectedModel] = useState("qwen2.5-coder:14b");
  const [computeMode, setComputeMode] = useState("sovereign");
  const [anonymize, setAnonymize] = useState(true);
  const [refinementText, setRefinementText] = useState("");

  const [loading, setLoading] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [showPromptInspector, setShowPromptInspector] = useState(false);
  const [showContextViewer, setShowContextViewer] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (initialQuery && !query) {
      setQuery(initialQuery);
    }
  }, [initialQuery, query]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen || !mounted) return null;

  const executeResearch = async (isRefinement = false, saveToBrain = false) => {
    const activeQuery = query.trim();
    if (!activeQuery) return;

    setLoading(true);
    setError(null);
    setProgressStep(0);
    setProgressPercent(15);
    if (!isRefinement) setSaveStatus(null);

    // Live Step Timer for Progress Bar Feedback
    let stepCount = 0;
    const progressTimer = setInterval(() => {
      stepCount++;
      if (stepCount < RESEARCH_STEPS.length) {
        setProgressStep(stepCount);
        setProgressPercent(RESEARCH_STEPS[stepCount].percent);
      } else {
        setProgressPercent((prev) => Math.min(prev + 2, 96));
      }
    }, 2800);

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

      clearInterval(progressTimer);
      setProgressStep(4);
      setProgressPercent(100);

      if (!res.ok) throw new Error(`Dispatch Fehler: HTTP ${res.status}`);

      const data = await res.json();
      if (data.error && !data.answer) throw new Error(data.error);

      setResult(data);
      if (isRefinement) {
        setRefinementText("");
        setSaveStatus(`✅ Verfeinerung angewendet: „${refinementText.trim()}“`);
      } else if (saveToBrain || data.saved_to_brain) {
        setSaveStatus("✅ Im Unternehmensgedächtnis (Company Brain) gespeichert!");
      }
    } catch (err: unknown) {
      clearInterval(progressTimer);
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
    }, 300);
  };

  const handleNewResearch = () => {
    setResult(null);
    setError(null);
    setSaveStatus(null);
  };

  const currentModelMeta = LAGEBILD_MODELS.find((m) => m.id === selectedModel);
  const promptDetails: PromptContext | null = (result?.llmContext?.prompt as PromptContext) ?? null;
  const summaryText = result?.summary || result?.answer || "";

  const modalJSX = (
    <div className="fixed inset-0 top-0 left-0 right-0 bottom-0 z-[99999] bg-[var(--canvas)] flex flex-col w-full h-full min-h-screen overflow-hidden rise">
      {/* Top Header Toolbar */}
      <header className="px-8 py-4 border-b border-[var(--line)] bg-white flex items-center justify-between gap-4 shrink-0 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[color-mix(in_oklab,var(--signal)_10%,white)] border border-[var(--signal)] flex items-center justify-center text-xl">
            🔎
          </div>
          <div>
            <h1 className="text-lg font-bold text-[var(--ink)] m-0 leading-tight">
              Recherche-Agent Workspace
            </h1>
            <p className="text-xs muted m-0 font-sans">
              Multi-Hop Dual-Retrieval: Company Brain & SearXNG IP-Anonymisiert
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

          {result && (
            <button
              type="button"
              onClick={handleNewResearch}
              className="px-4 py-2 rounded-xl text-xs font-bold border border-[var(--line)] bg-white text-[var(--ink)] hover:bg-[color-mix(in_oklab,white_90%,var(--ink))] transition-all"
            >
              🔄 Neue Recherche
            </button>
          )}

          {/* Primary Action Button (VIRKI Signal Blue, NO pitch black) */}
          <button
            type="button"
            onClick={handleSaveAndClose}
            className="px-5 py-2.5 rounded-xl text-xs font-bold bg-[var(--signal)] text-white hover:opacity-90 transition-all shadow-xs flex items-center gap-2 cursor-pointer border-none"
          >
            💾 Speichern & Schließen
          </button>

          {/* Close Action */}
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost text-xs mono px-3"
          >
            ✕ Schließen
          </button>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex-1 overflow-y-auto bg-[color-mix(in_oklab,white_98%,transparent)]">
        {!result ? (
          /* Initial State: Clean Centered Input Hero Layout */
          <div className="max-w-3xl mx-auto py-12 px-6 space-y-8 flex flex-col items-center justify-center min-h-[calc(100vh-140px)]">
            <div className="text-center space-y-2">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[color-mix(in_oklab,var(--signal)_12%,white)] border border-[var(--signal)] text-3xl mb-2">
                🔎
              </div>
              <h2 className="text-2xl font-bold text-[var(--ink)] m-0">
                Was möchten Sie recherchieren?
              </h2>
              <p className="text-sm muted max-w-xl mx-auto leading-relaxed">
                Der Recherche-Agent durchsucht Ihr lokales Unternehmensgedächtnis und führt bei Bedarf eine anonymisierte Web-Recherche via SearXNG durch.
              </p>
            </div>

            {/* Centered Input Card */}
            <div className="w-full bg-white p-8 rounded-2xl border border-[var(--line)] shadow-sm space-y-6">
              <div className="space-y-2">
                <label className="mono text-[11px] uppercase muted font-bold block tracking-wider text-left">
                  Recherchethema / Anfrage
                </label>
                <textarea
                  rows={4}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="z. B. SAP S/4HANA Migration Performance im Vergleich zu Oracle Cloud ERP 2026..."
                  className="w-full p-4 rounded-xl border border-[var(--line)] bg-white text-base text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)] font-sans leading-relaxed shadow-xs"
                />
              </div>

              {/* Options Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
                {/* Model Selector */}
                <div className="space-y-2 text-left">
                  <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
                    Modell auswählen (Lagebild)
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
                    <p className="text-[11px] text-[var(--ink-soft)] italic m-0 pt-0.5 leading-snug">
                      💡 {currentModelMeta.desc}
                    </p>
                  )}
                </div>

                {/* Depth Selector */}
                <div className="space-y-2 text-left">
                  <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
                    Recherche-Tiefe
                  </label>
                  <div className="flex p-1 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] gap-1">
                    <button
                      type="button"
                      onClick={() => setDepth("quick")}
                      className={`flex-1 text-xs py-2.5 font-bold rounded-lg transition-all ${
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
                      className={`flex-1 text-xs py-2.5 font-bold rounded-lg transition-all ${
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
                <div className="space-y-2 text-left">
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
                <div className="space-y-2 text-left">
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
              </div>

              {error && (
                <div className="p-4 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono">
                  ❌ Fehler: {error}
                </div>
              )}

              {/* Live Agent Progress HUD & Animated Fortschrittsbalken */}
              {loading ? (
                <div className="w-full bg-white p-8 rounded-2xl border border-[var(--signal)] shadow-md space-y-6 text-left">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[color-mix(in_oklab,var(--signal)_12%,white)] border border-[var(--signal)] flex items-center justify-center text-xl animate-spin">
                        ⏳
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                          <span>🤖 Autonomer Recherche-Agent arbeitet…</span>
                        </h3>
                        <p className="text-xs text-[var(--signal)] font-mono font-bold m-0 pt-0.5">
                          {RESEARCH_STEPS[Math.min(progressStep, 3)]?.label}
                        </p>
                      </div>
                    </div>
                    <span className="font-mono text-2xl font-extrabold text-[var(--signal)]">
                      {progressPercent}%
                    </span>
                  </div>

                  {/* Animated Progress Bar Fill */}
                  <div className="w-full h-3 rounded-full bg-[color-mix(in_oklab,var(--signal)_15%,white)] overflow-hidden border border-[color-mix(in_oklab,var(--signal)_30%,white)]">
                    <div
                      className="h-full bg-[var(--signal)] transition-all duration-500 ease-out rounded-full shadow-xs"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>

                  {/* Step Checklist Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                    {RESEARCH_STEPS.map((s, sIdx) => {
                      const isDone = sIdx < progressStep;
                      const isCurrent = sIdx === progressStep;
                      return (
                        <div
                          key={sIdx}
                          className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2.5 transition-all ${
                            isDone
                              ? "border-[var(--line)] bg-[color-mix(in_oklab,white_96%,var(--ink))] text-[var(--ink)]"
                              : isCurrent
                              ? "border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_10%,white)] text-[var(--signal)] font-bold shadow-2xs"
                              : "border-[var(--line)] bg-white text-[var(--ink-soft)] opacity-40"
                          }`}
                        >
                          <span className="text-sm">{isDone ? "✅" : isCurrent ? "🔄" : "⚪"}</span>
                          <span className="truncate">{s.label}</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="pt-3 flex flex-wrap items-center justify-between text-[11px] font-mono muted border-t border-[var(--line)] gap-2">
                    <span>🛡️ SearXNG Proxy: {anonymize ? "Aktiv (IP-Schutz)" : "Direkt"}</span>
                    <span>🧠 Modell: {selectedModel}</span>
                    <span>⚡ Compute: {computeMode}</span>
                  </div>
                </div>
              ) : (
                /* Centered Big Start Button (VIRKI Signal Blue, ZERO black) */
                <button
                  type="button"
                  disabled={!query.trim()}
                  onClick={() => executeResearch(false)}
                  className="w-full py-4 rounded-xl text-base font-bold bg-[var(--signal)] text-white hover:opacity-90 transition-all shadow-md cursor-pointer border-none flex items-center justify-center gap-2"
                >
                  🚀 Recherche Jetzt Starten
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Result View Layout: Full-Width Centered Reader Layout */
          <div className="max-w-5xl mx-auto py-10 px-8 space-y-8">
            {error && (
              <div className="p-4 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono">
                ❌ Fehler: {error}
              </div>
            )}

            {/* Metadata Bar */}
            <div className="p-4 rounded-2xl border border-[var(--line)] bg-white flex flex-wrap items-center justify-between gap-4 text-xs shadow-xs">
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
                  className="px-3 py-1.5 rounded-lg border border-[var(--line)] bg-white text-xs mono text-[var(--ink)] hover:bg-[color-mix(in_oklab,white_90%,var(--ink))]"
                >
                  {showContextViewer ? "🙈 Kontext verbergen" : "👁️ Kontext anzeigen"}
                </button>

                <button
                  type="button"
                  onClick={() => setShowPromptInspector(!showPromptInspector)}
                  className="px-3 py-1.5 rounded-lg border border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_10%,white)] text-xs mono text-[var(--signal)] font-bold hover:bg-[var(--signal)] hover:text-white transition-all"
                >
                  📄 Prompt Inspektor
                </button>
              </div>
            </div>

            {/* Query & Executive Report Header */}
            <div className="p-6 rounded-2xl border border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] space-y-2 shadow-xs flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="mono text-[11px] uppercase text-[var(--signal)] font-bold tracking-wider block mb-1">
                  🤖 Autonomer Deep Research Bericht
                </span>
                <h2 className="text-xl font-bold text-[var(--ink)] m-0 leading-snug">
                  {query}
                </h2>
              </div>
              <span className="badge" data-variant="ok">
                ⚡ Autonom Ausgewertet
              </span>
            </div>

            {/* Main Executive Intelligence Report Box */}
            <div className="p-8 rounded-2xl border border-[var(--line)] bg-white space-y-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-[var(--line)] pb-4">
                <h2 className="section-title text-xl font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                  <span>📄</span> Forschungsbericht & Synthese
                </h2>
                <span className="text-xs mono muted">
                  Vertrauen: {result.confidence ? Math.round(result.confidence * 100) : 92}%
                </span>
              </div>

              {/* Formatted Report Content */}
              <div className="p-7 rounded-2xl bg-[color-mix(in_oklab,white_96%,var(--ink))] border border-[var(--line)] shadow-2xs">
                {renderMarkdownReport(summaryText)}
              </div>

              {result.sub_questions && result.sub_questions.length > 0 && (
                <div className="pt-4 border-t border-[var(--line)] space-y-2">
                  <h3 className="mono text-[11px] uppercase muted font-bold tracking-wider">
                    Analysierte Forschungsstränge & Teilhypothesen:
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

            {/* Context & Source Chunks Viewer */}
            {showContextViewer && result.sources && result.sources.length > 0 && (
              <div className="p-8 rounded-2xl border border-[var(--line)] bg-white space-y-6 shadow-xs">
                <div className="flex items-center justify-between border-b border-[var(--line)] pb-4">
                  <div>
                    <h2 className="section-title text-lg font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                      <span>📖</span> Gefundene Quellen & Nachweise ({result.sources.length})
                    </h2>
                    <p className="text-xs muted m-0 mt-0.5 font-sans">
                      Klicken Sie auf den Button einer Quelle, um das Original im Browser aufzurufen.
                    </p>
                  </div>
                  <span className="badge" data-variant="curated">
                    {result.anonymity_active ? "🛡️ SearXNG Proxy Aktiv" : "🌐 Direkt"}
                  </span>
                </div>

                <div className="space-y-5">
                  {result.sources.map((src, idx) => {
                    const cleanSnippet = cleanTextSnippet(src.snippet);
                    const isWeb = src.source_type === "web_searxng";
                    const trustScore = src.trust_score ? Math.round(src.trust_score * 100) : 85;

                    return (
                      <div
                        key={idx}
                        className="p-6 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,white_98%,transparent)] space-y-4 hover:border-[var(--line-strong)] transition-all shadow-2xs"
                      >
                        {/* Header Badge Row */}
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--line)] pb-3">
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 rounded-full bg-[var(--signal)] text-white text-xs font-bold font-mono flex items-center justify-center">
                              #{idx + 1}
                            </span>
                            <span className="badge" data-variant={isWeb ? "curated" : "graph"}>
                              {isWeb ? "🌐 Web (SearXNG Anonym)" : "🧠 Company Brain"}
                            </span>
                            <span className="badge" data-variant="ok">
                              Vertrauen: {trustScore}%
                            </span>
                          </div>

                          {src.url && (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noreferrer"
                              className="px-4 py-1.5 rounded-xl bg-[color-mix(in_oklab,var(--signal)_10%,white)] border border-[var(--signal)] text-[var(--signal)] font-bold text-xs hover:bg-[var(--signal)] hover:text-white transition-all inline-flex items-center gap-1.5 no-underline"
                            >
                              <span>🌐 Originalquelle im Browser öffnen</span>
                              <span>↗</span>
                            </a>
                          )}
                        </div>

                        {/* Title & Domain URL */}
                        <div className="space-y-1">
                          <h3 className="text-base font-bold text-[var(--ink)] m-0 leading-snug">
                            {src.title || "Recherche-Quelle"}
                          </h3>
                          {src.url && (
                            <div className="mono text-xs text-[var(--signal)] truncate">
                              🔗 {src.url}
                            </div>
                          )}
                        </div>

                        {/* Formatted Text Snippet Box */}
                        <div className="p-4 rounded-xl bg-white border border-[var(--line)] text-xs text-[var(--ink)] leading-relaxed font-sans whitespace-pre-wrap">
                          {cleanSnippet || "Kein Textinhalt verfügbar."}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Interactive Refinement Box */}
            <div className="p-8 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] space-y-4 shadow-xs">
              <h3 className="text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
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
                  className="flex-1 p-3.5 rounded-xl border border-[var(--line)] bg-white text-xs text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)]"
                  onKeyDown={(e) => e.key === "Enter" && executeResearch(true)}
                />
                <button
                  type="button"
                  disabled={loading || !refinementText.trim()}
                  onClick={() => executeResearch(true)}
                  className="px-5 py-3.5 rounded-xl text-xs font-bold border border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_10%,white)] text-[var(--signal)] hover:bg-[var(--signal)] hover:text-white transition-all cursor-pointer"
                >
                  Verfeinern
                </button>
              </div>
            </div>

            {/* Prompt Inspector Sub-View */}
            {showPromptInspector && (
              <div className="p-8 rounded-2xl border border-[var(--line)] bg-white text-[var(--ink)] text-xs mono space-y-5 shadow-sm">
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

                <div className="grid grid-cols-2 gap-4 p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] text-xs">
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
                  <div className="text-[var(--signal)] font-bold mb-2 uppercase text-[10px] tracking-wider">System Prompt:</div>
                  <pre className="p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_97%,transparent)] text-xs whitespace-pre-wrap overflow-x-auto m-0 text-[var(--ink)]">
                    {promptDetails?.system || "Kein System-Prompt erfasst."}
                  </pre>
                </div>

                <div>
                  <div className="text-[var(--signal)] font-bold mb-2 uppercase text-[10px] tracking-wider">User Prompt:</div>
                  <pre className="p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_97%,transparent)] text-[11px] whitespace-pre-wrap overflow-x-auto m-0 text-[var(--ink)]">
                    {promptDetails?.user || "Kein User-Prompt erfasst."}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Bar */}
      <footer className="px-8 py-3.5 border-t border-[var(--line)] bg-white flex items-center justify-between shrink-0">
        <span className="text-xs muted font-mono">
          {result?.saved_to_brain
            ? "✅ Ergebnisse im Unternehmensgedächtnis gesichert."
            : "💾 Ergebnisse werden beim Schließen automatisch im Company Brain gespeichert."}
        </span>
      </footer>
    </div>
  );

  return createPortal(modalJSX, document.body);
}
