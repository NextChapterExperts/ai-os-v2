"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { DynamicDataProductForm } from "@/components/DynamicDataProductForm";
import { DataProductViewer } from "@/components/DataProductViewer";
import { FileUploadDropzone } from "@/components/FileUploadDropzone";

interface WorkflowItem {
  workflow_id: str;
  name: str;
  description: str;
  input_schema: any;
  output_schema: any;
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Record<string, WorkflowItem>>({});
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/workflows/registry");
      if (res.ok) {
        const data = await res.json();
        setWorkflows(data.workflows || {});
        const keys = Object.keys(data.workflows || {});
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
    } catch (e) {
      console.error("Error executing workflow", e);
    } finally {
      setExecuting(false);
    }
  };

  const selectedWf = selectedWorkflowId ? workflows[selectedWorkflowId] : null;

  return (
    <section className="rise pt-10 pb-16 max-w-5xl mx-auto px-4">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="section-title text-3xl font-bold text-emerald-400">Workflows Cockpit</h1>
          <p className="muted m-0 max-w-xl text-slate-400 text-sm mt-1">
            Ebene 2 — Ausführung deterministischer Workflows mit dynamischer DataProduct-Generierung & Renderern.
          </p>
        </div>
        <Link href="/platform" className="btn-ghost text-sm">
          Zur Plattform
        </Link>
      </div>

      <div className="mb-10">
        <FileUploadDropzone />
      </div>

      {loading ? (
        <div className="p-8 text-center text-slate-400 animate-pulse font-mono">
          Lade registrierte Workflows aus dem Orchestrator...
        </div>
      ) : Object.keys(workflows).length === 0 ? (
        <div className="p-8 bg-slate-900/50 rounded-xl border border-slate-800 text-center">
          <p className="text-slate-300">Keine aktiven Workflows registriert.</p>
          <p className="text-xs text-slate-500 mt-1">
            Stelle sicher, dass der Orchestrator-Server (Port 8091) online ist.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Workflow List */}
          <div className="lg:col-span-4 space-y-3">
            <h3 className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2">
              Registrierte Workflows ({Object.keys(workflows).length})
            </h3>
            {Object.values(workflows).map((wf) => {
              const isSelected = wf.workflow_id === selectedWorkflowId;
              return (
                <button
                  key={wf.workflow_id}
                  onClick={() => {
                    setSelectedWorkflowId(wf.workflow_id);
                    setLastResult(null);
                  }}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-emerald-950/60 border-emerald-500 text-emerald-100 shadow-lg shadow-emerald-950/40"
                      : "bg-slate-900/40 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/80"
                  }`}
                >
                  <div className="font-semibold text-sm">{wf.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{wf.description}</div>
                  <div className="text-[10px] font-mono text-emerald-400/80 mt-2">
                    ID: {wf.workflow_id}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Execution & Result View */}
          <div className="lg:col-span-8 space-y-6">
            {selectedWf && (
              <>
                <div className="bg-slate-900/40 p-5 rounded-xl border border-slate-800">
                  <h3 className="text-xl font-bold text-emerald-300">{selectedWf.name}</h3>
                  <p className="text-xs text-slate-400 mt-1">{selectedWf.description}</p>

                  <div className="mt-5">
                    <DynamicDataProductForm
                      schema={selectedWf.input_schema}
                      onSubmit={handleExecute}
                      loading={executing}
                    />
                  </div>
                </div>

                {lastResult && (
                  <div className="space-y-4">
                    <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider">
                      Ausführungsergebnis
                    </h4>
                    {lastResult.error ? (
                      <div className="bg-red-950/60 border border-red-800 p-4 rounded-xl text-red-200 text-sm">
                        Fehler bei Ausführung: {lastResult.error}
                      </div>
                    ) : (
                      <DataProductViewer
                        dataProduct={lastResult.output_dp}
                        title={`Ergebnis DataProduct (${selectedWf.output_schema?.title || "Output"})`}
                      />
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
