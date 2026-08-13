"use client";

import React, { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import {
  IconSearch,
  IconShieldCheck,
  IconGlobe,
  IconBrain,
  IconBolt,
  IconMicroscope,
  IconRocket,
  IconLock,
  IconFileText,
  IconBook,
  IconZoomCode,
  IconExternalLink,
  IconX,
  IconRefresh,
  IconDeviceFloppy,
  IconBulb,
  IconMessageDots,
  IconLoader2,
  IconSparkles,
  IconCpu,
  IconCheck,
  IconInfoCircle,
  IconEye,
  IconEyeOff,
} from "@tabler/icons-react";

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
  { id: "auto", label: "Auto-Router (Smart)", desc: "Analysiert Intent & wählt automatisch das optimale Monster-Modell" },
  { id: "qwen2.5-coder:14b", label: "Qwen 2.5 Coder 14B (Souverän & Schnelligkeit)", desc: "Ultra-schnelle lokale Inferenz (0.35s VRAM-Hit), Code, JSON & Tool-Calling" },
  { id: "deepseek-r1:32b", label: "DeepSeek-R1 32B (Reasoning & Logik)", desc: "Logik, Reasoning & komplexe Problemlösung (128k Kontext)" },
  { id: "mistral-nemo:12b", label: "Mistral Nemo 12B (Deutsche Texte)", desc: "E-Mails, Blogs & deutsche Texte (128k Kontext)" },
  { id: "hermes3:8b", label: "Hermes 3 8B (Multi-Agent)", desc: "Multi-Agenten Orchestrierung & Tool-Calling" },
  { id: "llama3.2-vision:11b", label: "Llama 3.2 Vision 11B (Vision/PDF)", desc: "OCR, Bild-, PDF- & Dokumentenanalyse" },
  { id: "openrouter/balanced", label: "OpenRouter Cloud (Balanced)", desc: "Nemotron Super 120B — OpenRouter Cloud (262K Kontext)" },
  { id: "openrouter/premium", label: "OpenRouter Cloud (Premium)", desc: "Nemotron Ultra 550B / Claude 3.5 — OpenRouter Frontier (1M Kontext)" },
  { id: "openrouter/coding", label: "OpenRouter Cloud (Coding)", desc: "Qwen 2.5 Coder 32B Instruct — Agentic Coding" },
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

function SourcePreviewModal({
  source,
  onClose,
}: {
  source: SourceItem;
  onClose: () => void;
}) {
  const isWeb = Boolean(source.url && source.url.startsWith("http"));
  const cleanSnippet = cleanTextSnippet(source.snippet);

  return (
    <div className="fixed inset-0 z-[100000] bg-black/75 backdrop-blur-md flex items-center justify-center p-4 rise">
      <div className="bg-white border border-[var(--line)] rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[var(--line)] bg-[color-mix(in_oklab,white_95%,var(--ink))] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-[color-mix(in_oklab,var(--signal)_12%,white)] border border-[var(--signal)] flex items-center justify-center shrink-0">
              {isWeb ? <IconGlobe size={20} className="text-[var(--signal)]" /> : <IconBrain size={20} className="text-[var(--signal)]" />}
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-[var(--ink)] m-0 truncate">
                {source.title || "Quellen-Vorschau"}
              </h3>
              <p className="text-xs font-mono muted m-0 truncate">{source.url || "brain://internal"}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isWeb && (
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="px-3.5 py-1.5 rounded-xl bg-[var(--signal)] text-white text-xs font-bold font-mono no-underline hover:opacity-90 transition-all inline-flex items-center gap-1.5"
              >
                <span>Extern im Tab öffnen</span>
                <IconExternalLink size={14} />
              </a>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-xl border border-[var(--line)] bg-white text-xs font-bold font-mono text-[var(--ink)] hover:bg-slate-100 transition-all cursor-pointer inline-flex items-center gap-1"
            >
              <IconX size={14} />
              <span>Schließen</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="p-4 rounded-xl bg-[color-mix(in_oklab,white_96%,var(--ink))] border border-[var(--line)] space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-[var(--signal)] flex items-center gap-1.5">
                {isWeb ? <IconGlobe size={15} /> : <IconBrain size={15} />}
                <span>{isWeb ? "Web-Quelle (SearXNG Egress)" : "Company Brain Asset"}</span>
              </span>
              <span className="muted">Vertrauen: {source.trust_score ? Math.round(source.trust_score * 100) : 88}%</span>
            </div>
            <p className="text-xs text-[var(--ink)] font-sans leading-relaxed m-0 pt-1">
              {cleanSnippet || "Keine Textzusammenfassung verfügbar."}
            </p>
          </div>

          {/* Embedded Web Preview Iframe for External URLs with Firefox Fallback Banner */}
          {isWeb ? (
            <div className="space-y-2">
              <div className="px-4 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1.5">
                  <IconInfoCircle size={16} className="text-amber-700 shrink-0" />
                  <span><strong>Firefox / Browser-Hinweis:</strong> Falls die Zielwebsite das Einbetten im Pop-up blockiert (X-Frame-Options), nutzen Sie den Button:</span>
                </span>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 rounded-lg bg-[var(--signal)] text-white text-xs font-bold font-mono no-underline hover:opacity-90 transition-all shrink-0 inline-flex items-center gap-1"
                >
                  <span>Direkt im Tab öffnen</span>
                  <IconExternalLink size={14} />
                </a>
              </div>
              <div className="w-full h-[430px] rounded-xl border border-[var(--line)] overflow-hidden bg-slate-100 relative">
                <iframe
                  src={source.url}
                  title={source.title}
                  className="w-full h-full border-none"
                  sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                />
              </div>
            </div>
          ) : (
            <div className="p-8 text-center muted text-xs font-mono border border-dashed border-[var(--line)] rounded-xl flex items-center justify-center gap-2">
              <IconBrain size={18} />
              <span>Dies ist ein internes Dokument aus dem Company Brain. Der Inhalt wurde ausgewertet und im Recherchebericht synthetisiert.</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-[var(--line)] bg-[color-mix(in_oklab,white_96%,var(--ink))] flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[var(--signal)] text-white text-xs font-bold hover:opacity-90 transition-all"
          >
            Zurück zur Recherche
          </button>
        </div>
      </div>
    </div>
  );
}

function renderMarkdownReport(text: string, sources: SourceItem[] = [], onSelectSource?: (src: SourceItem) => void) {
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
                const citeMatch = part.match(/^\[(\d+)\]$/);
                if (citeMatch) {
                  const srcNum = parseInt(citeMatch[1], 10);
                  const matchingSrc = sources[srcNum - 1];
                  return (
                    <button
                      key={pIdx}
                      type="button"
                      onClick={() => matchingSrc && onSelectSource?.(matchingSrc)}
                      title={matchingSrc ? `Quelle #${srcNum}: ${matchingSrc.title}` : `Quelle #${srcNum}`}
                      className="inline-flex items-center justify-center px-1.5 py-0.5 mx-0.5 rounded bg-[color-mix(in_oklab,var(--signal)_15%,white)] hover:bg-[var(--signal)] hover:text-white border border-[var(--signal)] text-[var(--signal)] font-mono font-bold text-[10px] align-baseline transition-all cursor-pointer border-none"
                    >
                      [{srcNum}]
                    </button>
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
  { label: "Rechercheauftrag analysieren & Entitäten extrahieren", icon: IconSearch, percent: 20 },
  { label: "Anonymisierte Web- & SearXNG-Egress-Recherche ausführen", icon: IconGlobe, percent: 50 },
  { label: "Unternehmensgedächtnis (Company Brain) durchsuchen & evaluieren", icon: IconBrain, percent: 75 },
  { label: "Ergebnisse synthetisieren & In-Text Citations formatieren", icon: IconFileText, percent: 95 },
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
  const [activePreviewSource, setActivePreviewSource] = useState<SourceItem | null>(null);
  const [showPromptInspector, setShowPromptInspector] = useState(false);
  const [showContextViewer, setShowContextViewer] = useState(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isAutoExecutingRef = useRef(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isOpen && initialQuery && initialQuery.trim() && !result && !loading && !isAutoExecutingRef.current) {
      isAutoExecutingRef.current = true;
      executeResearch(false, false, initialQuery.trim());
    }
  }, [isOpen, initialQuery]);

  useEffect(() => {
    if (!isOpen) {
      isAutoExecutingRef.current = false;
    }
  }, [isOpen]);

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

  const executeResearch = async (isRefinement = false, saveToBrain = false, queryOverride?: string) => {
    const activeQuery = (queryOverride || (isRefinement ? query : query.trim())).trim();
    if (!activeQuery) return;

    if (queryOverride) {
      setQuery(queryOverride);
    }

    setLoading(true);
    setError(null);
    setProgressStep(0);
    setProgressPercent(10);

    const progressTimer = setInterval(() => {
      setProgressPercent((prev) => {
        if (prev >= 90) {
          clearInterval(progressTimer);
          return 90;
        }
        const next = prev + Math.floor(Math.random() * 15) + 5;
        if (next >= 30 && next < 60) setProgressStep(1);
        else if (next >= 60 && next < 85) setProgressStep(2);
        else if (next >= 85) setProgressStep(3);
        return Math.min(next, 90);
      });
    }, 600);

    try {
      const currentRefinement = isRefinement ? refinementText.trim() : undefined;
      const effectiveQuery = currentRefinement ? `${activeQuery} ${currentRefinement}` : activeQuery;

      const res = await fetch("/api/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent: "research",
          tenant_id: "nextchapter",
          params: {
            query: effectiveQuery,
            depth,
            model: selectedModel,
            compute_mode: computeMode,
            anonymize,
            refinement_feedback: currentRefinement,
            save_to_brain: saveToBrain,
          },
        }),
      });

      clearInterval(progressTimer);
      setProgressPercent(100);
      setProgressStep(3);

      const data = await res.json().catch(() => ({}));

      const payloadObj = data.result && typeof data.result === "object" ? data.result : data;
      const summaryText = payloadObj.summary || payloadObj.answer || data.summary || data.answer || "";

      if (!res.ok && !summaryText) {
        throw new Error(data.error || data.message || `Dispatch Fehler: HTTP ${res.status}`);
      }

      if (summaryText) {
        const finalResult: ResearchResponse = {
          query: payloadObj.query || activeQuery,
          summary: summaryText,
          answer: summaryText,
          sources: payloadObj.sources || [],
          confidence: payloadObj.confidence || 0.9,
          anonymity_active: payloadObj.anonymity_active ?? anonymize,
          model_used: payloadObj.model_used || payloadObj.model || selectedModel,
          sub_questions: payloadObj.sub_questions || [],
          llmContext: payloadObj.llmContext || data.llmContext,
          saved_to_brain: payloadObj.saved_to_brain,
        };
        setResult(finalResult);
      } else {
        throw new Error(data.error || "Keine Zusammenfassung vom Recherche-Agenten erhalten.");
      }

      if (isRefinement && currentRefinement) {
        setRefinementText("");
        setSaveStatus(`Verfeinerung angewendet: „${currentRefinement}“`);
      } else if (saveToBrain || data.saved_to_brain) {
        setSaveStatus("Im Unternehmensgedächtnis (Company Brain) gespeichert!");
      }
    } catch (err: unknown) {
      clearInterval(progressTimer);
      const msg = err instanceof Error ? err.message : String(err);
      console.error("Research error in modal:", err);
      setError(msg || "Fehler bei der Ausführung der Recherche.");
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

  const handleSelectSuggestedQuestion = (qText: string) => {
    const cleanQ = qText.replace(/^[💡🔍]\s*/, "");
    setRefinementText(cleanQ);
  };

  const currentModelMeta = LAGEBILD_MODELS.find((m) => m.id === selectedModel);
  const promptDetails: PromptContext | null = (result?.llmContext?.prompt as PromptContext) ?? null;
  const summaryText = result?.summary || result?.answer || "";

  const modalJSX = (
    <div className="fixed inset-0 top-0 left-0 right-0 bottom-0 z-[99999] bg-[var(--canvas)] flex flex-col w-full h-full min-h-screen overflow-hidden rise">
      {/* Top Header Toolbar */}
      <header className="px-8 py-4 border-b border-[var(--line)] bg-white flex items-center justify-between gap-4 shrink-0 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[color-mix(in_oklab,var(--signal)_10%,white)] border border-[var(--signal)] flex items-center justify-center shrink-0">
            <IconSearch size={22} className="text-[var(--signal)]" />
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
          <span
            className="badge inline-flex items-center gap-1.5"
            data-variant={anonymize ? "curated" : "raw"}
          >
            {anonymize ? <IconShieldCheck size={14} /> : <IconGlobe size={14} />}
            <span>{anonymize ? "SearXNG Proxy Aktiv" : "Direkt-Modus"}</span>
          </span>

          {saveStatus && (
            <span className="badge inline-flex items-center gap-1" data-variant="ok">
              <IconCheck size={14} />
              <span>{saveStatus}</span>
            </span>
          )}

          {result && (
            <button
              type="button"
              onClick={handleNewResearch}
              className="px-4 py-2 rounded-xl text-xs font-bold border border-[var(--line)] bg-white text-[var(--ink)] hover:bg-[color-mix(in_oklab,white_90%,var(--ink))] transition-all inline-flex items-center gap-1.5"
            >
              <IconRefresh size={14} />
              <span>Neue Recherche</span>
            </button>
          )}

          {/* Primary Action Button */}
          <button
            type="button"
            onClick={handleSaveAndClose}
            className="px-5 py-2.5 rounded-xl text-xs font-bold bg-[var(--signal)] text-white hover:opacity-90 transition-all shadow-xs inline-flex items-center gap-2 cursor-pointer border-none"
          >
            <IconDeviceFloppy size={16} />
            <span>Speichern & Schließen</span>
          </button>

          {/* Close Action */}
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost text-xs mono px-3 inline-flex items-center gap-1"
          >
            <IconX size={14} />
            <span>Schließen</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex-1 overflow-y-auto bg-[color-mix(in_oklab,white_98%,transparent)]">
        {!result ? (
          /* Initial State: Clean Centered Input Hero Layout */
          <div className="max-w-3xl mx-auto py-12 px-6 space-y-8 flex flex-col items-center justify-center min-h-[calc(100vh-140px)]">
            <div className="text-center space-y-2">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[color-mix(in_oklab,var(--signal)_12%,white)] border border-[var(--signal)] mb-2">
                <IconSearch size={32} className="text-[var(--signal)]" />
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
                    <p className="text-[11px] text-[var(--ink-soft)] italic m-0 pt-0.5 leading-snug flex items-center gap-1">
                      <IconBulb size={13} className="text-[var(--signal)] shrink-0" />
                      <span>{currentModelMeta.desc}</span>
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
                      className={`flex-1 text-xs py-2.5 font-bold rounded-lg transition-all inline-flex items-center justify-center gap-1.5 ${
                        depth === "quick"
                          ? "bg-[var(--signal)] text-white shadow-xs"
                          : "text-[var(--ink-soft)] hover:text-[var(--ink)]"
                      }`}
                    >
                      <IconBolt size={14} />
                      <span>Quick (30s)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setDepth("deep")}
                      className={`flex-1 text-xs py-2.5 font-bold rounded-lg transition-all inline-flex items-center justify-center gap-1.5 ${
                        depth === "deep"
                          ? "bg-[var(--signal)] text-white shadow-xs"
                          : "text-[var(--ink-soft)] hover:text-[var(--ink)]"
                      }`}
                    >
                      <IconMicroscope size={14} />
                      <span>Deep (Multi-Hop)</span>
                    </button>
                  </div>
                </div>

                {/* Anonymization Toggle */}
                <div className="space-y-2 text-left md:col-span-2">
                  <label className="mono text-[11px] uppercase muted font-bold block tracking-wider">
                    Anonymisierung & IP-Schutz
                  </label>
                  <button
                    type="button"
                    onClick={() => setAnonymize(!anonymize)}
                    className={`w-full p-3.5 rounded-xl border text-xs font-mono text-left flex items-center justify-between transition-all cursor-pointer ${
                      anonymize
                        ? "border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_8%,white)] text-[var(--ink)]"
                        : "border-[var(--line)] bg-white muted"
                    }`}
                  >
                    <span className="inline-flex items-center gap-2">
                      {anonymize ? <IconShieldCheck size={18} className="text-[var(--signal)]" /> : <IconGlobe size={18} />}
                      <span>{anonymize ? "SearXNG Proxy: Aktiv (IP verborgen)" : "Direkt-Modus (Ohne Proxy)"}</span>
                    </span>
                    <span className="badge" data-variant={anonymize ? "curated" : "raw"}>
                      {anonymize ? "Anonym" : "Direkt"}
                    </span>
                  </button>
                </div>
              </div>

              {error && (
                <div className="p-4 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono flex items-center gap-2">
                  <IconX size={16} />
                  <span>Fehler: {error}</span>
                </div>
              )}

              {/* Live Agent Progress HUD & Animated Fortschrittsbalken */}
              {loading ? (
                <div className="w-full bg-white p-8 rounded-2xl border border-[var(--signal)] shadow-md space-y-6 text-left">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[color-mix(in_oklab,var(--signal)_12%,white)] border border-[var(--signal)] flex items-center justify-center">
                        <IconLoader2 size={22} className="animate-spin text-[var(--signal)]" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                          <span>Autonomer Recherche-Agent arbeitet…</span>
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
                      const StepIcon = s.icon;
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
                          {isDone ? (
                            <IconCheck size={16} className="text-emerald-600 shrink-0" />
                          ) : isCurrent ? (
                            <IconLoader2 size={16} className="animate-spin text-[var(--signal)] shrink-0" />
                          ) : (
                            <StepIcon size={16} className="shrink-0 muted" />
                          )}
                          <span className="truncate">{s.label}</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="pt-3 flex flex-wrap items-center justify-between text-[11px] font-mono muted border-t border-[var(--line)] gap-2">
                    <span className="inline-flex items-center gap-1">
                      <IconShieldCheck size={13} />
                      <span>SearXNG Proxy: {anonymize ? "Aktiv (IP-Schutz)" : "Direkt"}</span>
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <IconCpu size={13} />
                      <span>Modell: {selectedModel}</span>
                    </span>
                  </div>
                </div>
              ) : (
                /* Centered Big Start Button */
                <button
                  type="button"
                  disabled={!query.trim()}
                  onClick={() => executeResearch(false)}
                  className="w-full py-4 rounded-xl text-base font-bold bg-[var(--signal)] text-white hover:opacity-90 transition-all shadow-md cursor-pointer border-none flex items-center justify-center gap-2"
                >
                  <IconRocket size={20} />
                  <span>Recherche Jetzt Starten</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Result View Layout: Full-Width Centered Reader Layout */
          <div className="max-w-5xl mx-auto py-10 px-8 space-y-8">
            {error && (
              <div className="p-4 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono flex items-center gap-2">
                <IconX size={16} />
                <span>Fehler: {error}</span>
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
                  className="px-3 py-1.5 rounded-lg border border-[var(--line)] bg-white text-xs mono text-[var(--ink)] hover:bg-[color-mix(in_oklab,white_90%,var(--ink))] inline-flex items-center gap-1.5 cursor-pointer"
                >
                  {showContextViewer ? (
                    <>
                      <IconEyeOff size={14} />
                      <span>Kontext verbergen</span>
                    </>
                  ) : (
                    <>
                      <IconEye size={14} />
                      <span>Kontext anzeigen</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setShowPromptInspector(!showPromptInspector)}
                  className="px-3 py-1.5 rounded-lg border border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_10%,white)] text-xs mono text-[var(--signal)] font-bold hover:bg-[var(--signal)] hover:text-white transition-all inline-flex items-center gap-1.5"
                >
                  <IconFileText size={14} />
                  <span>Prompt Inspektor</span>
                </button>
              </div>
            </div>

            {/* Query & Executive Report Header */}
            <div className="p-6 rounded-2xl border border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] space-y-2 shadow-xs flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="mono text-[11px] uppercase text-[var(--signal)] font-bold tracking-wider block mb-1">
                  Autonomer Deep Research Bericht
                </span>
                <h2 className="text-xl font-bold text-[var(--ink)] m-0 leading-snug">
                  {query}
                </h2>
              </div>
              <span className="badge inline-flex items-center gap-1" data-variant="ok">
                <IconCheck size={14} />
                <span>Autonom Ausgewertet</span>
              </span>
            </div>

            {/* Main Executive Intelligence Report Box */}
            <div className="p-8 rounded-2xl border border-[var(--line)] bg-white space-y-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-[var(--line)] pb-4">
                <h2 className="section-title text-xl font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                  <IconFileText size={22} className="text-[var(--signal)]" />
                  <span>Forschungsbericht & Synthese</span>
                </h2>
                <span className="text-xs mono muted">
                  Vertrauen: {result.confidence ? Math.round(result.confidence * 100) : 92}%
                </span>
              </div>

              {/* Formatted Report Content */}
              <div className="p-7 rounded-2xl bg-[color-mix(in_oklab,white_96%,var(--ink))] border border-[var(--line)] shadow-2xs">
                {renderMarkdownReport(summaryText, result.sources || [], setActivePreviewSource)}
              </div>

              {result.sub_questions && result.sub_questions.length > 0 && (
                <div className="pt-4 border-t border-[var(--line)] space-y-2">
                  <h3 className="mono text-[11px] uppercase muted font-bold tracking-wider flex items-center gap-1.5">
                    <IconBulb size={15} className="text-[var(--signal)]" />
                    <span>Analysierte Forschungsstränge & Teilhypothesen:</span>
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
            {/* Decluttered & Professional Source Link List */}
            {showContextViewer && result.sources && result.sources.length > 0 && (
              <div className="p-8 rounded-2xl border border-[var(--line)] bg-white space-y-6 shadow-xs">
                <div className="flex items-center justify-between border-b border-[var(--line)] pb-4">
                  <div>
                    <h2 className="section-title text-lg font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                      <IconBook size={20} className="text-[var(--signal)]" />
                      <span>Evaluierte Quellen & Nachweise ({result.sources.length})</span>
                    </h2>
                    <p className="text-xs muted m-0 mt-0.5 font-sans">
                      Klicken Sie auf den Vorschau-Button einer Quelle, um den Inhalt im In-App Pop-up zu öffnen.
                    </p>
                  </div>
                  <span className="badge inline-flex items-center gap-1" data-variant={result.anonymity_active ? "curated" : "raw"}>
                    {result.anonymity_active ? <IconShieldCheck size={14} /> : <IconGlobe size={14} />}
                    <span>{result.anonymity_active ? "SearXNG Proxy Aktiv" : "Direkt"}</span>
                  </span>
                </div>

                {/* Sleek High-Contrast Sources List */}
                <div className="space-y-3">
                  {result.sources.map((src, idx) => {
                    const cleanSnippet = cleanTextSnippet(src.snippet);
                    const isWeb = src.source_type === "web_searxng";
                    const trustScore = src.trust_score ? Math.round(src.trust_score * 100) : 85;

                    return (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-[var(--line)] bg-white hover:border-[var(--signal)] transition-all shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-left"
                      >
                        <div className="space-y-1 flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="w-5 h-5 rounded-md bg-[color-mix(in_oklab,var(--signal)_15%,white)] text-[var(--signal)] text-xs font-bold font-mono flex items-center justify-center">
                              #{idx + 1}
                            </span>
                            <span className="font-bold text-sm text-[var(--ink)] truncate">
                              {src.title || "Recherche-Quelle"}
                            </span>
                            <span className="badge inline-flex items-center gap-1" data-variant={isWeb ? "curated" : "graph"}>
                              {isWeb ? <IconGlobe size={12} /> : <IconBrain size={12} />}
                              <span>{isWeb ? "Web" : "Brain"}</span>
                            </span>
                            <span className="text-[11px] font-mono muted">
                              Vertrauen: {trustScore}%
                            </span>
                          </div>
                          <p className="text-xs text-[var(--ink-soft)] line-clamp-2 m-0 font-sans leading-relaxed">
                            {cleanSnippet || "Kein Textinhalt verfügbar."}
                          </p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            onClick={() => setActivePreviewSource(src)}
                            className="px-4 py-2 rounded-xl bg-[color-mix(in_oklab,var(--signal)_10%,white)] border border-[var(--signal)] text-[var(--signal)] font-bold text-xs hover:bg-[var(--signal)] hover:text-white transition-all cursor-pointer inline-flex items-center gap-1.5"
                          >
                            <IconZoomCode size={15} />
                            <span>Vorschau (Pop-up)</span>
                          </button>
                          {src.url && isWeb && (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-2 rounded-xl border border-[var(--line)] bg-white text-[var(--ink)] font-bold text-xs hover:bg-slate-100 transition-all no-underline shrink-0 inline-flex items-center justify-center"
                              title="In neuem Tab öffnen"
                            >
                              <IconExternalLink size={15} />
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}


            {/* WebUI-Style Interactive Refinement Box with Clickable Question Chips */}
            <div className="p-8 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] space-y-5 shadow-xs">
              <div className="space-y-1 text-left">
                <h3 className="text-base font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                  <IconMessageDots size={20} className="text-[var(--signal)]" />
                  <span>Interaktiver Dialog & Vertiefung</span>
                </h3>
                <p className="text-xs muted m-0">
                  Wähle eine vorgeschlagene Vertiefungsfrage aus oder gib eigene Wünsche ein:
                </p>
              </div>

              {/* WebUI Suggested Questions Chips */}
              {result.sub_questions && result.sub_questions.length > 0 && (
                <div className="space-y-2 text-left">
                  <label className="mono text-[11px] uppercase text-[var(--signal)] font-bold tracking-wider flex items-center gap-1">
                    <IconBulb size={14} />
                    <span>Empfohlene Folgefragen (Klick zum Übernehmen):</span>
                  </label>
                  <div className="flex flex-wrap gap-2 text-left">
                    {result.sub_questions.map((sq, sqIdx) => (
                      <button
                        key={sqIdx}
                        type="button"
                        onClick={() => handleSelectSuggestedQuestion(sq)}
                        className="px-3.5 py-2 rounded-xl border border-[color-mix(in_oklab,var(--signal)_30%,white)] bg-white hover:bg-[color-mix(in_oklab,var(--signal)_10%,white)] hover:border-[var(--signal)] text-xs text-[var(--ink)] font-sans font-medium transition-all text-left shadow-2xs cursor-pointer flex items-center gap-1.5"
                      >
                        <IconBulb size={14} className="text-[var(--signal)] shrink-0" />
                        <span>{sq}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Refinement Input & Action */}
              <div className="flex gap-3 pt-1">
                <input
                  type="text"
                  value={refinementText}
                  onChange={(e) => setRefinementText(e.target.value)}
                  placeholder="Eigene Nachfrage eingeben oder aus den Chips wählen..."
                  className="flex-1 p-3.5 rounded-xl border border-[var(--line)] bg-white text-xs text-[var(--ink)] focus:outline-none focus:ring-1 focus:ring-[var(--signal)]"
                  onKeyDown={(e) => e.key === "Enter" && executeResearch(true)}
                />
                <button
                  type="button"
                  disabled={loading || !refinementText.trim()}
                  onClick={() => executeResearch(true)}
                  className="px-5 py-3.5 rounded-xl text-xs font-bold border border-[var(--signal)] bg-[var(--signal)] text-white hover:opacity-90 transition-all cursor-pointer shadow-xs inline-flex items-center gap-1.5"
                >
                  <IconSparkles size={16} />
                  <span>Verfeinern</span>
                </button>
              </div>
            </div>

            {/* Prompt Inspector Sub-View */}
            {showPromptInspector && (
              <div className="p-8 rounded-2xl border border-[var(--line)] bg-white text-[var(--ink)] text-xs mono space-y-5 shadow-sm">
                <div className="flex items-center justify-between border-b border-[var(--line)] pb-3">
                  <h3 className="font-bold text-[var(--signal)] m-0 text-sm flex items-center gap-2">
                    <IconFileText size={16} />
                    <span>Prompt Inspektor Context</span>
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowPromptInspector(false)}
                    className="btn-ghost text-xs mono inline-flex items-center gap-1"
                  >
                    <IconX size={14} />
                    <span>Schließen</span>
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
        <span className="text-xs muted font-mono inline-flex items-center gap-1.5">
          <IconDeviceFloppy size={14} className="text-emerald-600" />
          <span>
            {result?.saved_to_brain
              ? "Ergebnisse im Unternehmensgedächtnis gesichert."
              : "Ergebnisse werden beim Schließen automatisch im Company Brain gespeichert."}
          </span>
        </span>
      </footer>

      {activePreviewSource && (
        <SourcePreviewModal
          source={activePreviewSource}
          onClose={() => setActivePreviewSource(null)}
        />
      )}
    </div>
  );

  return createPortal(modalJSX, document.body);
}
