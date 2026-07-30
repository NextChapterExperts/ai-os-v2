"use client";

import React, { useState } from "react";

interface DataProductViewerProps {
  dataProduct: Record<string, any>;
  title?: string;
}

export const DataProductViewer: React.FC<DataProductViewerProps> = ({
  dataProduct,
  title = "Ergebnis DataProduct",
}) => {
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!dataProduct || typeof dataProduct !== "object") {
    return (
      <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-800 text-xs text-slate-400">
        Keine gültigen DataProduct-Daten vorhanden.
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(dataProduct, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const dpId = dataProduct.dp_id || dataProduct.id || dataProduct.external_id || "dp-generated";
  const tenantId = dataProduct.tenant_id || "nextchapter";
  const producedBy = dataProduct.produced_by || "workflow-engine";

  // Trenne Metadaten von Fachdaten
  const metaKeys = new Set(["dp_id", "tenant_id", "produced_by", "workflow_run_id", "schema_version", "id", "external_id", "node_type"]);
  const businessFields = Object.entries(dataProduct).filter(([k]) => !metaKeys.has(k));

  return (
    <div className="bg-slate-900/60 backdrop-blur-xl border border-emerald-800/40 rounded-2xl p-6 shadow-xl shadow-emerald-950/20 transition-all">
      {/* Top Header Card */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-700/60">
              DataProduct
            </span>
            <h3 className="text-base font-bold text-slate-100">{title}</h3>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1 flex items-center gap-3">
            <span>ID: <span className="text-emerald-400">{dpId}</span></span>
            <span>Tenant: <span className="text-slate-300">{tenantId}</span></span>
            <span>By: <span className="text-slate-300">{producedBy}</span></span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors flex items-center gap-1.5"
          >
            {copied ? <span>✓ Kopiert</span> : <span>📋 JSON kopieren</span>}
          </button>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
              showRawJson
                ? "bg-emerald-900/60 text-emerald-300 border border-emerald-700"
                : "bg-slate-800 hover:bg-slate-700 text-slate-300"
            }`}
          >
            {showRawJson ? "Visualisierung" : "JSON Code"}
          </button>
        </div>
      </div>

      {/* Main Content View */}
      {showRawJson ? (
        <div className="relative">
          <pre className="bg-slate-950 p-4 rounded-xl text-xs font-mono text-emerald-300/90 overflow-x-auto border border-slate-800 max-h-96">
            {JSON.stringify(dataProduct, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Formatted Text Box if offer text / text field exists */}
          {businessFields.map(([key, value]) => {
            if (typeof value === "string" && (value.includes("\n") || key.includes("text") || key.includes("angebot"))) {
              return (
                <div key={key} className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider font-mono">
                    📄 {key.replace(/_/g, " ")}
                  </div>
                  <div className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed font-sans bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                    {value}
                  </div>
                </div>
              );
            }
            return null;
          })}

          {/* Key Value Grid for scalar fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {businessFields.map(([key, value]) => {
              if (typeof value === "string" && (value.includes("\n") || key.includes("text") || key.includes("angebot"))) {
                return null; // Already rendered above
              }
              const isPrice = key.includes("preis") || key.includes("summe") || key.includes("betrag") || key.includes("stundensatz");
              return (
                <div
                  key={key}
                  className="bg-slate-950/40 p-3 rounded-xl border border-slate-800/60 flex flex-col justify-between"
                >
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span
                    className={`text-sm font-semibold mt-1 ${
                      isPrice ? "text-emerald-400 font-mono" : "text-slate-200"
                    }`}
                  >
                    {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    {isPrice && typeof value === "number" && " EUR"}
                  </span>
                </div>
              );
            })}
          </div>

          {/* KG Commit Confirmation Pill */}
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2 text-emerald-400 text-[11px] font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Atomar im Knowledge Graph (Postgres) gesichert & auditierbar</span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">ISO-8601 UTC</span>
          </div>
        </div>
      )}
    </div>
  );
};
