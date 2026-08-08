"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { DynamicDataProductForm } from "@/components/DynamicDataProductForm";
import { DataProductViewer } from "@/components/DataProductViewer";
import { MeetingsReportViewer } from "@/components/MeetingsReportViewer";
import { FileUploadDropzone } from "@/components/FileUploadDropzone";
import { mergeAgentInputSchema } from "@/lib/merge-agent-schema";

interface AgentItem {
  workflow_id: string;
  name: string;
  description: string;
  input_schema: any;
  output_schema: any;
}

const SAMPLE_HANDWERK_AGENT: AgentItem = {
  workflow_id: "handwerk-angebot",
  name: "Handwerker Angebots-Agent",
  description: "Spezialisierter Fachagent zur automatischen Angebotserstellung für Maler-, Bau- und Handwerksbetriebe. Berechnet Netto-/Bruttopreise und committed das Angebot-DataProduct in den Knowledge Graph.",
  input_schema: {
    title: "AngebotInput",
    description: "Kunden- & Auftragsdaten zur Berechnung des Handwerkerangebots",
    required: ["kunden_name", "projekt_titel", "umfang_qm", "stundensatz"],
    properties: {
      kunden_name: {
        type: "string",
        title: "Kunden Name",
        description: "Name des Auftraggebers / Unternehmens",
      },
      projekt_titel: {
        type: "string",
        title: "Projekt Titel",
        description: "Bezeichnung der auszuführenden Handwerksleistung",
      },
      umfang_qm: {
        type: "number",
        title: "Umfang (qm)",
        description: "Gesamtfläche in Quadratmetern",
      },
      stundensatz: {
        type: "number",
        title: "Stundensatz (€)",
        description: "Vereinbarter Stundensatz in EUR",
      },
    },
  },
  output_schema: {
    title: "AngebotOutput",
    description: "Kalkuliertes Angebot-DataProduct mit Ausweis von Netto & Brutto",
  },
};


const EMAIL_INVOICES_AGENT: AgentItem = {
  workflow_id: "email-invoices",
  name: "Gmail-Rechnungen extrahieren",
  description:
    "Scannt Gmail nach Rechnungs-Kandidaten, archiviert PDFs in Google Drive und schreibt neue Zeilen ins Google Sheet.",
  input_schema: {
    title: "Gmail-Rechnungen extrahieren",
    description: "Gmail-Rechnungs-Pipeline (email-agent via MCP)",
    properties: {
      run_mode: {
        type: "string",
        enum: ["dry_run", "live"],
        default: "dry_run",
        title: "Ausführungsmodus",
        "x-enum-labels": {
          dry_run: "Nur Vorschau (Dry-Run) — nichts schreiben",
          live: "Live — Sheet & Drive aktualisieren",
        },
      },
      archive_mode: {
        type: "string",
        enum: ["archive", "skip"],
        default: "archive",
        title: "PDF-Archiv in Drive",
        "x-enum-labels": {
          archive: "PDFs nach Drive archivieren",
          skip: "Archivierung überspringen",
        },
      },
    },
  },
  output_schema: { title: "InvoicePipelineReport" },
};

const MEETINGS_AGENT: AgentItem = {
  workflow_id: "meetings-agent",
  name: "Meetings-Agent",
  description:
    "Termine aus Google-Kalender laden (ab 1. Juli 2026) oder Meeting-Zusammenfassung ins Company Brain speichern.",
  input_schema: {
    title: "Meetings-Agent",
    properties: {
      aufgabe: {
        type: "string",
        enum: ["termine_abrufen", "zusammenfassung_speichern"],
        default: "termine_abrufen",
        title: "Aufgabe",
        "x-enum-labels": {
          termine_abrufen: "Termine aus Kalender laden",
          zusammenfassung_speichern: "Zusammenfassung ins Company Brain",
        },
      },
      run_mode: {
        type: "string",
        enum: ["dry_run", "live"],
        default: "dry_run",
        title: "Ausführungsmodus",
        "x-enum-labels": {
          dry_run: "Nur Vorschau (Dry-Run)",
          live: "Live ausführen",
        },
      },
      since_date: {
        type: "string",
        default: "2026-07-01",
        title: "Kalender ab Datum",
        "x-visible-when": { aufgabe: "termine_abrufen" },
      },
      include_forecast: {
        type: "string",
        enum: ["yes", "no"],
        default: "yes",
        title: "Forecast (31 Tage)",
        "x-enum-labels": { yes: "Ja", no: "Nein" },
        "x-visible-when": { aufgabe: "termine_abrufen" },
      },
      meeting_id: {
        type: "string",
        default: "",
        title: "Meeting auswählen",
        "x-visible-when": { aufgabe: "zusammenfassung_speichern" },
        "x-widget": "meeting-picker",
      },
      summary: {
        type: "string",
        default: "",
        title: "Zusammenfassung",
        "x-visible-when": { aufgabe: "zusammenfassung_speichern" },
        "x-widget": "textarea",
      },
    },
  },
  output_schema: { title: "MeetingsAgentReport" },
};

/** Fachagenten — immer in der UI, auch wenn Registry kurz offline ist. */
const CORE_FACHAGENTS: Record<string, AgentItem> = {
  "email-invoices": EMAIL_INVOICES_AGENT,
  "meetings-agent": MEETINGS_AGENT,
};

const AGENT_DISPLAY_ORDER = ["email-invoices", "meetings-agent", "handwerk-angebot"];

const SAMPLE_PREFILLS: Record<string, Record<string, any>> = {
  "handwerk-angebot": {
    kunden_name: "Malerbetrieb Schulze GmbH",
    projekt_titel: "Fassadenanstrich & Gerüstbau",
    umfang_qm: 120.0,
    stundensatz: 70.0,
  },
};

const AGENT_ACTION_LABELS: Record<string, { submit: string; loading: string }> = {
  "handwerk-angebot": {
    submit: "Angebot erstellen",
    loading: "Angebot wird berechnet…",
  },
  "email-invoices": {
    submit: "Rechnungen extrahieren",
    loading: "Gmail wird gescannt…",
  },
  "meetings-agent": {
    submit: "Ausführen",
    loading: "Meetings-Agent läuft…",
  },
};

const EMAIL_INVOICE_AGENT_IDS = new Set(["email-invoices"]);

type InvoiceResources = {
  sheet_url?: string;
  sheet_name?: string;
  drive_root?: string;
  drive_folder_url?: string;
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Record<string, AgentItem>>({
    ...CORE_FACHAGENTS,
    "handwerk-angebot": SAMPLE_HANDWERK_AGENT,
  });
  const [selectedAgentId, setSelectedAgentId] = useState<string>("email-invoices");
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [history, setHistory] = useState<Array<{ time: string; name: string; dp: any }>>([]);
  const [activeTab, setActiveTab] = useState<"agents" | "ingest">("agents");
  const [overrideFormData, setOverrideFormData] = useState<Record<string, any> | null>(
    SAMPLE_PREFILLS["handwerk-angebot"]
  );
  const [invoiceResources, setInvoiceResources] = useState<InvoiceResources | null>(null);
  const [agentFormData, setAgentFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    if (!EMAIL_INVOICE_AGENT_IDS.has(selectedAgentId)) {
      setInvoiceResources(null);
      return;
    }
    let cancelled = false;
    fetch("/api/agents/invoice-resources", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) return null;
        return (await res.json()) as InvoiceResources;
      })
      .then((data) => {
        if (!cancelled && data) setInvoiceResources(data);
      })
      .catch(() => {
        if (!cancelled) setInvoiceResources(null);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedAgentId]);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/agents/registry");
      if (res.ok) {
        const data = await res.json();
        const wfs = data.workflows || {};
        if (Object.keys(wfs).length > 0) {
          const merged: Record<string, AgentItem> = {};
          for (const [id, wf] of Object.entries(wfs) as [string, AgentItem][]) {
            const fallback = CORE_FACHAGENTS[id];
            merged[id] = fallback
              ? {
                  ...wf,
                  input_schema: mergeAgentInputSchema(
                    fallback.input_schema,
                    wf.input_schema,
                  ),
                }
              : wf;
          }
          setAgents((prev) => ({ ...prev, ...merged }));
        }
      }
    } catch (e) {
      console.warn("Backend Registry offline — verwende lokalen Sample-Agenten", e);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (formData: Record<string, any>) => {
    if (!selectedAgentId) return;
    setExecuting(true);
    setLastResult(null);
    try {
      const res = await fetch("/api/agents/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: selectedAgentId,
          tenant_id: "nextchapter",
          payload: formData,
        }),
      });
      const data = await res.json();
      const outputDp = data.output_dp || data.result;
      const completed = res.ok && (data.status === "completed" || data.ok) && outputDp;

      if (completed) {
        setLastResult({
          ok: true,
          output_dp: outputDp,
          commit: data.commit,
          services: data.services,
        });
        const agentName = agents[selectedAgentId]?.name || selectedAgentId;
        setHistory((prev) => [
          {
            time: new Date().toLocaleTimeString("de-DE"),
            name: agentName,
            dp: outputDp,
          },
          ...prev.slice(0, 4),
        ]);
        if (
          selectedAgentId === "meetings-agent" &&
          formData.aufgabe === "termine_abrufen" &&
          formData.run_mode === "live"
        ) {
          const meetings = (outputDp?.meetings || []) as Array<Record<string, unknown>>;
          const pick =
            meetings.find((m) => !m.has_summary) ??
            meetings[0];
          const meetingId = String(pick?.meeting_id || pick?.id || "");
          if (meetingId) {
            setOverrideFormData({
              ...formData,
              aufgabe: "zusammenfassung_speichern",
              meeting_id: meetingId,
              summary: "",
            });
          }
        }
      } else if (!res.ok || data.detail || data.error) {
        const errMsg =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
              : data.error || `HTTP ${res.status}`;
        setLastResult({
          error: errMsg,
        });
      } else if (selectedAgentId === "handwerk-angebot") {
        // Fallback simulation for local UI demonstration if Orchestrator port 8091 is offline
        const qm = Number(formData.umfang_qm || 120.0);
        const rate = Number(formData.stundensatz || 70.0);
        const netto = qm * rate + 500.0;
        const brutto = netto * 1.19;
        const simulatedDp = {
          dp_id: `dp-simulated-${Date.now().toString(36)}`,
          tenant_id: "nextchapter",
          produced_by: "handwerk-angebot-agent",
          kunden_name: formData.kunden_name || "Malerbetrieb Schulze GmbH",
          projekt_titel: formData.projekt_titel || "Fassadenanstrich & Gerüstbau",
          netto_betrag: netto,
          brutto_betrag: brutto,
          angebot_text: `Angebot für ${formData.kunden_name || "Malerbetrieb Schulze GmbH"}:\nProjekt: ${formData.projekt_titel || "Fassadenanstrich & Gerüstbau"} (${qm} qm)\nGesamtpreis netto: ${netto.toFixed(2)} EUR | brutto: ${brutto.toFixed(2)} EUR`,
          status: "COMMITTED_TO_KNOWLEDGE_GRAPH",
        };
        setLastResult({ ok: true, output_dp: simulatedDp });
      }
    } catch (e) {
      console.error("Error executing agent workflow", e);
    } finally {
      setExecuting(false);
    }
  };

  const handleLoadSample = () => {
    const sample = SAMPLE_PREFILLS[selectedAgentId];
    if (!sample) return;
    setOverrideFormData(sample);
    handleExecute(sample);
  };

  const selectedAgent = selectedAgentId ? agents[selectedAgentId] : EMAIL_INVOICES_AGENT;
  const agentCount = Object.keys(agents).length;
  const sortedAgents = Object.values(agents).sort((a, b) => {
    const ia = AGENT_DISPLAY_ORDER.indexOf(a.workflow_id);
    const ib = AGENT_DISPLAY_ORDER.indexOf(b.workflow_id);
    const ra = ia === -1 ? 99 : ia;
    const rb = ib === -1 ? 99 : ib;
    return ra - rb;
  });
  const hasSamplePrefill = Boolean(SAMPLE_PREFILLS[selectedAgentId]);
  const baseActionLabels = AGENT_ACTION_LABELS[selectedAgentId] ?? {
    submit: "Agent ausführen",
    loading: "Agent läuft…",
  };
  const actionLabels =
    selectedAgentId === "meetings-agent"
      ? agentFormData.aufgabe === "zusammenfassung_speichern"
        ? {
            submit:
              agentFormData.run_mode === "live"
                ? "Zusammenfassung ins Company Brain speichern"
                : "Zusammenfassung (Dry-Run) prüfen",
            loading: "Wird gespeichert…",
          }
        : { submit: "Termine aus Kalender laden", loading: "Kalender wird gelesen…" }
      : baseActionLabels;
  const isMeetingsAgent = selectedAgentId === "meetings-agent";
  const isEmailInvoiceAgent = EMAIL_INVOICE_AGENT_IDS.has(selectedAgentId);

  return (
    <section className="rise pt-6 pb-16 max-w-6xl mx-auto">
      {/* Top Banner styled with VIRKI tokens */}
      <div className="mb-8 p-6 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,white_75%,transparent)] shadow-sm flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="status-dot ok" />
            <h1 className="section-title text-2xl font-extrabold text-[var(--ink)] m-0">
              Fachagenten Cockpit
            </h1>
          </div>
          <p className="text-xs muted max-w-2xl leading-relaxed mt-1 m-0">
            Spezialisierte Fachagenten für Ihren Betrieb. Die Benutzeroberfläche zur Datenerfassung und Erstellung des Datenprodukts generiert sich automatisch aus den Verträgen des Agenten.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="badge" data-variant="graph">
            Mandant: nextchapter
          </span>
          <Link href="/platform" className="btn-ghost text-xs">
            ← Plattform Lagebild
          </Link>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-[var(--line)] pb-4 mb-8">
        <button
          onClick={() => setActiveTab("agents")}
          className="btn-ghost text-xs font-bold"
          data-active={activeTab === "agents" ? "true" : "false"}
        >
          🤖 Ihre Fachagenten ({agentCount})
        </button>

        <button
          onClick={() => setActiveTab("ingest")}
          className="btn-ghost text-xs font-bold"
          data-active={activeTab === "ingest" ? "true" : "false"}
        >
          📄 Dokument-Upload & Ingestion
        </button>
      </div>

      {activeTab === "ingest" ? (
        <div className="space-y-6">
          <FileUploadDropzone />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Agent Selector List */}
          <div className="lg:col-span-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="section-title text-sm font-bold text-[var(--ink)] m-0">
                Verfügbare Agenten
              </h3>
              <span className="mono text-xs muted">{agentCount} bereit</span>
            </div>

            <div className="space-y-3">
              {sortedAgents.map((ag) => {
                const isSelected = ag.workflow_id === selectedAgentId;
                return (
                  <button
                    key={ag.workflow_id}
                    onClick={() => {
                      setSelectedAgentId(ag.workflow_id);
                      setLastResult(null);
                      setOverrideFormData(SAMPLE_PREFILLS[ag.workflow_id] ?? null);
                    }}
                    className={`w-full text-left p-4 rounded-xl border transition-all ${
                      isSelected
                        ? "border-[var(--signal)] bg-white shadow-sm ring-1 ring-[var(--signal)]"
                        : "border-[var(--line)] bg-[color-mix(in_oklab,white_60%,transparent)] hover:border-[var(--ink-soft)]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-[var(--ink)] flex items-center gap-2">
                        <span>🛠️</span> {ag.name}
                      </span>
                      {isSelected && (
                        <span className="badge" data-variant="graph">
                          Aktiv
                        </span>
                      )}
                    </div>
                    <p className="text-xs muted mt-1.5 leading-relaxed line-clamp-2 m-0">
                      {ag.description}
                    </p>
                    <div className="mt-3 pt-2 border-t border-[var(--line)] flex items-center justify-between text-[10px] mono muted">
                      <span>ID: {ag.workflow_id}</span>
                      <span className="text-[var(--signal)]">Deterministischer Workflow</span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Execution History Panel */}
            {history.length > 0 && (
              <div className="mt-8 pt-6 border-t border-[var(--line)] space-y-3">
                <h4 className="mono text-xs uppercase muted tracking-wider">
                  Letzte Agenten-Ergebnisse
                </h4>
                <div className="space-y-2">
                  {history.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white rounded-xl border border-[var(--line)] text-xs flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-[var(--ink)]">{item.name}</div>
                        <div className="mono text-[10px] text-[var(--signal)] mt-0.5">
                          {item.dp?.dp_id || item.dp?.external_id || "DataProduct"}
                        </div>
                      </div>
                      <span className="mono text-[10px] muted">{item.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Interactive Agent Workspace */}
          <div className="lg:col-span-8 space-y-6">
            <div className="p-6 rounded-2xl border border-[var(--line)] bg-[color-mix(in_oklab,white_75%,transparent)] shadow-sm space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--line)] pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="badge" data-variant="graph">
                      Fachagent · Code Agent
                    </span>
                    <span className="badge" data-variant="curated">
                      Input: {selectedAgent.input_schema?.title || "AngebotInput"}
                    </span>
                  </div>
                  <h2 className="section-title text-xl font-bold text-[var(--ink)] m-0 flex items-center gap-2">
                    <span>🛠️</span> {selectedAgent.name}
                  </h2>
                  <p className="text-xs muted mt-1 leading-relaxed m-0">{selectedAgent.description}</p>
                  {isEmailInvoiceAgent && (invoiceResources?.sheet_url || invoiceResources?.drive_folder_url) ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {invoiceResources.sheet_url ? (
                        <a
                          href={invoiceResources.sheet_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-ghost text-xs"
                        >
                          Google Sheet ({invoiceResources.sheet_name || "Übersicht"})
                        </a>
                      ) : null}
                      {invoiceResources.drive_folder_url ? (
                        <a
                          href={invoiceResources.drive_folder_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-ghost text-xs"
                        >
                          Drive-Ordner ({invoiceResources.drive_root || "Rechnungen"})
                        </a>
                      ) : null}
                    </div>
                  ) : null}
                </div>

                {hasSamplePrefill ? (
                  <button
                    onClick={handleLoadSample}
                    className="btn-ghost text-xs font-bold text-[var(--signal)] border-[var(--signal)]"
                  >
                    ⚡ Sample laden & ausführen
                  </button>
                ) : null}
              </div>

              <div className="pt-2">
                <DynamicDataProductForm
                  schema={selectedAgent.input_schema}
                  initialValues={overrideFormData}
                  onFormDataChange={setAgentFormData}
                  onSubmit={handleExecute}
                  loading={executing}
                  submitLabel={actionLabels.submit}
                  loadingLabel={actionLabels.loading}
                />
              </div>
            </div>

            {/* Result View */}
            {lastResult && (
              <div className="space-y-3">
                <h4 className="mono text-xs uppercase muted tracking-wider flex items-center gap-2">
                  <span>📊</span> Generiertes Output DataProduct
                </h4>

                {lastResult.error ? (
                  <div className="p-5 rounded-2xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono">
                    ❌ Ausführungsfehler: {lastResult.error}
                  </div>
                ) : (
                  <>
                    {Array.isArray(lastResult.services?.started) &&
                    lastResult.services.started.length > 0 ? (
                      <div className="p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,var(--signal)_8%,white)] text-xs text-[var(--ink)]">
                        Backend automatisch gestartet:{" "}
                        {lastResult.services.started.join(", ")}
                      </div>
                    ) : null}
                    {isMeetingsAgent &&
                    lastResult.output_dp?.operation === "zusammenfassung_speichern" ? (
                      <div
                        className={`p-4 rounded-xl border text-xs space-y-2 ${
                          lastResult.output_dp?.dry_run
                            ? "border-[var(--line)] bg-[color-mix(in_oklab,white_90%,transparent)]"
                            : "border-[var(--signal)] bg-[color-mix(in_oklab,var(--signal)_10%,white)]"
                        }`}
                      >
                        <div className="font-semibold text-[var(--ink)]">
                          {lastResult.output_dp?.dry_run
                            ? "Dry-Run: Würde ins Company Brain committen"
                            : "Im Company Brain gespeichert (org:Meeting)"}
                        </div>
                        {lastResult.output_dp?.kg_external_id ? (
                          <div className="mono text-[10px] muted">
                            KG: {lastResult.output_dp.kg_node_type} ·{" "}
                            {lastResult.output_dp.kg_external_id}
                          </div>
                        ) : null}
                        {lastResult.commit?.node_id && !lastResult.output_dp?.dry_run ? (
                          <Link
                            href={`/platform/kg?node=${encodeURIComponent(lastResult.commit.node_id)}`}
                            className="btn-ghost text-xs inline-flex"
                          >
                            Im Knowledge Graph ansehen
                          </Link>
                        ) : null}
                        {lastResult.output_dp?.dry_run ? (
                          <p className="text-[10px] muted m-0">
                            Modus auf <strong>Live</strong> stellen, um wirklich zu speichern.
                          </p>
                        ) : null}
                      </div>
                    ) : null}
                    {isMeetingsAgent &&
                    lastResult.output_dp?.operation === "termine_abrufen" ? (
                      <MeetingsReportViewer report={lastResult.output_dp} />
                    ) : (
                    <DataProductViewer
                      dataProduct={lastResult.output_dp || lastResult.result}
                      title={`${selectedAgent.name} — Output`}
                    />
                    )}
                    
                    {isEmailInvoiceAgent && lastResult.output_dp?.sheet_url ? (
                      <div className="flex flex-wrap gap-2">
                        <a
                          href={lastResult.output_dp.sheet_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-ghost text-xs"
                        >
                          Google Sheet öffnen
                        </a>
                        {invoiceResources?.drive_folder_url ? (
                          <a
                            href={invoiceResources.drive_folder_url}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-ghost text-xs"
                          >
                            Drive-Ordner öffnen
                          </a>
                        ) : null}
                      </div>
                    ) : null}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
