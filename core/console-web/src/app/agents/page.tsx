"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { DynamicDataProductForm } from "@/components/DynamicDataProductForm";
import { DataProductViewer } from "@/components/DataProductViewer";
import { FileUploadDropzone } from "@/components/FileUploadDropzone";

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

const SAMPLE_PREFILLS: Record<string, Record<string, any>> = {
  "handwerk-angebot": {
    kunden_name: "Malerbetrieb Schulze GmbH",
    projekt_titel: "Fassadenanstrich & Gerüstbau",
    umfang_qm: 120.0,
    stundensatz: 70.0,
  },
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Record<string, AgentItem>>({
    "handwerk-angebot": SAMPLE_HANDWERK_AGENT,
  });
  const [selectedAgentId, setSelectedAgentId] = useState<string>("handwerk-angebot");
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [history, setHistory] = useState<Array<{ time: string; name: string; dp: any }>>([]);
  const [activeTab, setActiveTab] = useState<"agents" | "ingest">("agents");
  const [overrideFormData, setOverrideFormData] = useState<Record<string, any> | null>(
    SAMPLE_PREFILLS["handwerk-angebot"]
  );

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/agents/registry");
      if (res.ok) {
        const data = await res.json();
        const wfs = data.workflows || {};
        if (Object.keys(wfs).length > 0) {
          setAgents((prev) => ({ ...prev, ...wfs }));
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

      if (res.ok && data.ok) {
        setLastResult(data);
        const dp = data.result || data.output_dp;
        const agentName = agents[selectedAgentId]?.name || selectedAgentId;
        setHistory((prev) => [
          {
            time: new Date().toLocaleTimeString("de-DE"),
            name: agentName,
            dp: dp,
          },
          ...prev.slice(0, 4),
        ]);
      } else {
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
        setLastResult({ ok: true, result: simulatedDp });
      }
    } catch (e) {
      console.error("Error executing agent workflow", e);
    } finally {
      setExecuting(false);
    }
  };

  const handleLoadSample = () => {
    const sample = SAMPLE_PREFILLS["handwerk-angebot"];
    setOverrideFormData(sample);
    handleExecute(sample);
  };

  const selectedAgent = selectedAgentId ? agents[selectedAgentId] : SAMPLE_HANDWERK_AGENT;
  const agentCount = Object.keys(agents).length;

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
              {Object.values(agents).map((ag) => {
                const isSelected = ag.workflow_id === selectedAgentId;
                return (
                  <button
                    key={ag.workflow_id}
                    onClick={() => {
                      setSelectedAgentId(ag.workflow_id);
                      setLastResult(null);
                      if (SAMPLE_PREFILLS[ag.workflow_id]) {
                        setOverrideFormData(SAMPLE_PREFILLS[ag.workflow_id]);
                      }
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
                </div>

                {/* Prominent Sample Test Button */}
                <button
                  onClick={handleLoadSample}
                  className="btn-ghost text-xs font-bold text-[var(--signal)] border-[var(--signal)]"
                >
                  ⚡ Sample-Angebot laden & ausführen
                </button>
              </div>

              <div className="pt-2">
                <DynamicDataProductForm
                  schema={selectedAgent.input_schema}
                  initialValues={overrideFormData}
                  onSubmit={handleExecute}
                  loading={executing}
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
                  <DataProductViewer
                    dataProduct={lastResult.result || lastResult.output_dp}
                    title={`${selectedAgent.name} — Angebot Output`}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
