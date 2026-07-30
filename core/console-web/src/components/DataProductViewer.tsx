"use client";

import React from "react";

interface DataProductViewerProps {
  dataProduct: Record<string, any>;
  title?: string;
}

export function DataProductViewer({ dataProduct, title = "DataProduct Ergebnis" }: DataProductViewerProps) {
  if (!dataProduct) return null;

  const metadataKeys = [
    "dp_id",
    "schema_version",
    "tenant_id",
    "produced_by",
    "produced_at",
    "workflow_run_id",
    "storage_target",
    "ingest_recommended",
  ];

  const payloadEntries = Object.entries(dataProduct).filter(
    ([key]) => !metadataKeys.includes(key)
  );

  return (
    <div className="bg-slate-900/80 border border-emerald-900/60 rounded-xl p-5 shadow-xl text-left space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-lg font-bold text-emerald-400">{title}</h4>
          <p className="text-xs text-slate-400 font-mono">
            ID: {dataProduct.dp_id || "n/a"} | Agent: {dataProduct.produced_by || "system"}
          </p>
        </div>
        <span className="bg-emerald-950 text-emerald-300 text-xs px-2.5 py-1 rounded-full border border-emerald-750 font-mono">
          {dataProduct.storage_target ? `Storage: [${dataProduct.storage_target.join(", ")}]` : "Committed"}
        </span>
      </div>

      <div className="space-y-3">
        {payloadEntries.map(([key, val]) => {
          const formattedKey = key.replace(/_/g, " ").toUpperCase();

          if (typeof val === "string" && (val.includes("\n") || val.length > 80)) {
            return (
              <div key={key} className="space-y-1">
                <span className="text-xs font-mono text-slate-400">{formattedKey}</span>
                <div className="bg-slate-950 p-3 rounded border border-slate-800 text-slate-200 text-sm whitespace-pre-wrap font-sans">
                  {val}
                </div>
              </div>
            );
          }

          return (
            <div key={key} className="flex justify-between items-center bg-slate-950/60 px-3 py-2 rounded border border-slate-850">
              <span className="text-xs font-mono text-slate-400">{formattedKey}</span>
              <span className="text-sm font-semibold text-emerald-200 font-mono">
                {typeof val === "object" ? JSON.stringify(val) : String(val)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
