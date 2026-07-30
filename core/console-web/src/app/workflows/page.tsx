"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { DynamicDataProductForm } from "@/components/DynamicDataProductForm";
import { DataProductViewer } from "@/components/DataProductViewer";
import { FileUploadDropzone } from "@/components/FileUploadDropzone";

interface WorkflowItem {
  workflow_id: string;
  name: string;
  description: string;
  input_schema: any;
  output_schema: any;
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Record<string, WorkflowItem>>({});
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [history, setHistory] = useState<Array<{ time: string; name: string; dp: any }>>([]);
  const [activeTab, setActiveTab] = useState<"workflows" | "ingest">("workflows");

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/workflows/registry");
      if (res.ok) {
        const data = await res.json();
        const wfs = data.workflows || {};
        setWorkflows(wfs);
        const keys = Object.keys(wfs);
        if (keys.length > 0) {
          setSelectedWorkflowId(keys[0]);
        }
      }
    } catch (e) {
      console.error("Error loading workflows", e);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (formData: Record<string, any>) => {
    if (!selectedWorkflowId) return;
    setExecuting(true);
    setLastResult(null);
    try {
      const res = await fetch("/api/workflows/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: selectedWorkflowId,
          tenant_id: "nextchapter",
          payload: formData,
        }),
      });
      const data = await res.json();
      setLastResult(data);

      if (data.ok) {
        const dp = data.result || data.output_dp;
        const wfName = workflows[selectedWorkflowId]?.name || selectedWorkflowId;
        setHistory((prev) => [
          {
            time: new Date().toLocaleTimeString("de-DE"),
            name: wfName,
            dp: dp,
          },
          ...prev.slice(0, 4),
        ]);
      }
    } catch (e) {
      console.error("Error executing workflow", e);
    } finally {
      setExecuting(false);
    }
  };

  const selectedWf = selectedWorkflowId ? workflows[selectedWorkflowId] : null;
  const workflowCount = Object.keys(workflows).length;

  return (
    <section className="rise pt-8 pb-20 max-w-6xl mx-auto px-4">
      {/* Header Banner */}
      <div className="mb-8 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="h-3 w-3 rounded-full bg-emerald-400 animate-pulse shadow-lg shadow-emerald-400/50" />
            <h1 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              Workflows & DataProduct Cockpit
            </h1>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed mt-1">
            Ebene 2 — Deterministische Code-Workflows mit automatischer Schema-Formulargenerierung, DataProduct Output-Visualisierung und atomarem Knowledge Graph Commit.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-300 flex items-center gap-2">
            <span className="text-slate-500">Tenant:</span>
            <span className="text-emerald-400 font-bold">nextchapter</span>
          </div>
          <Link
            href="/platform"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700 flex items-center gap-1.5"
          >
            <span>←</span> Plattform Lagebild
          </Link>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800/80 pb-4 mb-8">
        <button
          onClick={() => setActiveTab("workflows")}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            activeTab === "workflows"
              ? "bg-emerald-950/80 text-emerald-300 border border-emerald-700/80 shadow-lg shadow-emerald-950/40"
              : "bg-slate-900/40 text-slate-400 border border-slate-800 hover:text-slate-200 hover:bg-slate-900/80"
          }`}
        >
          <span>⚡</span> Deterministische Workflows ({workflowCount})
        </button>

        <button
          onClick={() => setActiveTab("ingest")}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 ${
            activeTab === "ingest"
              ? "bg-emerald-950/80 text-emerald-300 border border-emerald-700/80 shadow-lg shadow-emerald-950/40"
              : "bg-slate-900/40 text-slate-400 border border-slate-800 hover:text-slate-200 hover:bg-slate-900/80"
          }`}
        >
          <span>📄</span> Dokument-Upload & Ingestion Pipeline
        </button>
      </div>

      {activeTab === "ingest" ? (
        <div className="space-y-6">
          <FileUploadDropzone />
        </div>
      ) : (
        <>
          {loading ? (
            <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800 animate-pulse font-mono text-xs">
              ⏳ Lade registrierte Workflows aus dem Orchestrator (:8091)...
            </div>
          ) : workflowCount === 0 ? (
            <div className="p-10 bg-slate-900/60 rounded-2xl border border-slate-800 text-center space-y-3">
              <div className="text-3xl">⚠️</div>
              <h3 className="text-base font-bold text-slate-200">Keine aktiven Workflows registriert</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Stelle sicher, dass der Orchestrator-Server auf Port 8091 aktiv ist. Die Beispiel-Workflows werden beim Serverstart registriert.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left Column: Workflow Selector */}
              <div className="lg:col-span-4 space-y-4">
                <h3 className="text-xs font-mono uppercase text-slate-400 tracking-wider flex items-center justify-between">
                  <span>Registrierte Workflows</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-emerald-400 text-[10px]">
                    {workflowCount} bereit
                  </span>
                </h3>

                <div className="space-y-3">
                  {Object.values(workflows).map((wf) => {
                    const isSelected = wf.workflow_id === selectedWorkflowId;
                    return (
                      <button
                        key={wf.workflow_id}
                        onClick={() => {
                          setSelectedWorkflowId(wf.workflow_id);
                          setLastResult(null);
                        }}
                        className={`w-full text-left p-4 rounded-2xl border transition-all duration-200 ${
                          isSelected
                            ? "bg-gradient-to-br from-emerald-950/90 to-slate-900 border-emerald-500/90 text-emerald-100 shadow-xl shadow-emerald-950/50 scale-[1.01]"
                            : "bg-slate-900/50 border-slate-800/80 text-slate-300 hover:border-slate-700 hover:bg-slate-900/90"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-sm text-slate-100 flex items-center gap-2">
                            <span>🛠️</span> {wf.name}
                          </span>
                          {isSelected && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                              Aktiv
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                          {wf.description}
                        </p>
                        <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
                          <span>ID: {wf.workflow_id}</span>
                          <span className="text-emerald-400/80">Code Workflow</span>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Execution History Panel */}
                {history.length > 0 && (
                  <div className="mt-8 pt-6 border-t border-slate-800/80 space-y-3">
                    <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider">
                      Letzte Ausführungen
                    </h4>
                    <div className="space-y-2">
                      {history.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/60 text-xs flex items-center justify-between"
                        >
                          <div>
                            <div className="font-semibold text-slate-200">{item.name}</div>
                            <div className="text-[10px] font-mono text-emerald-400 mt-0.5">
                              {item.dp?.dp_id || item.dp?.external_id || "DataProduct"}
                            </div>
                          </div>
                          <span className="text-[10px] font-mono text-slate-500">{item.time}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Execution Form & Results Workspace */}
              <div className="lg:col-span-8 space-y-6">
                {selectedWf ? (
                  <>
                    <div className="bg-slate-900/60 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
                            Deterministischer Code Workflow
                          </span>
                        </div>
                        <h2 className="text-xl font-bold text-slate-100 mt-2">{selectedWf.name}</h2>
                        <p className="text-xs text-slate-400 mt-1 leading-relaxed">{selectedWf.description}</p>
                      </div>

                      <div className="pt-2">
                        <DynamicDataProductForm
                          schema={selectedWf.input_schema}
                          onSubmit={handleExecute}
                          loading={executing}
                        />
                      </div>
                    </div>

                    {/* Result View */}
                    {lastResult && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider flex items-center gap-2">
                          <span>📊</span> Ausführungsergebnis & Output DataProduct
                        </h4>

                        {lastResult.error ? (
                          <div className="bg-rose-950/70 border border-rose-800/80 p-5 rounded-2xl text-rose-300 text-xs font-mono">
                            ❌ Ausführungsfehler: {lastResult.error}
                          </div>
                        ) : (
                          <DataProductViewer
                            dataProduct={lastResult.result || lastResult.output_dp}
                            title={`${selectedWf.name} — Ergebnis`}
                          />
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 text-slate-400 text-xs">
                    Wähle einen Workflow auf der linken Seite aus, um die Formulargenerierung zu starten.
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
