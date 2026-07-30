"use client";

import React, { useState } from "react";

interface FieldSchema {
  type?: string;
  title?: string;
  description?: string;
  default?: any;
}

interface JsonSchema {
  title?: string;
  properties?: Record<string, FieldSchema>;
  required?: string[];
}

interface DynamicDataProductFormProps {
  schema: JsonSchema;
  onSubmit: (formData: Record<string, any>) => void;
  loading?: boolean;
}

export function DynamicDataProductForm({
  schema,
  onSubmit,
  loading = false,
}: DynamicDataProductFormProps) {
  const properties = schema.properties || {};
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    Object.entries(properties).forEach(([key, field]) => {
      // Ignore framework metadata fields
      if (
        [
          "dp_id",
          "schema_version",
          "tenant_id",
          "produced_by",
          "produced_at",
          "workflow_run_id",
          "storage_target",
          "ingest_recommended",
        ].includes(key)
      ) {
        return;
      }
      if (field.default !== undefined) {
        initial[key] = field.default;
      }
    });
    return initial;
  });

  const handleChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const keys = Object.keys(properties).filter(
    (key) =>
      ![
        "dp_id",
        "schema_version",
        "tenant_id",
        "produced_by",
        "produced_at",
        "workflow_run_id",
        "storage_target",
        "ingest_recommended",
      ].includes(key)
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-slate-900/60 p-5 rounded-xl border border-slate-800">
      <h4 className="text-lg font-semibold text-emerald-400 mb-2">
        Eingaben für {schema.title || "DataProduct"}
      </h4>
      {keys.length === 0 ? (
        <p className="text-slate-400 text-sm">Keine zusätzlichen Eingabefelder erforderlich.</p>
      ) : (
        keys.map((key) => {
          const field = properties[key];
          const isNumber = field.type === "number" || field.type === "integer";
          const label = field.title || key.replace(/_/g, " ");

          return (
            <div key={key} className="flex flex-col space-y-1 text-left">
              <label className="text-xs font-mono uppercase text-slate-400 tracking-wider">
                {label}
                {schema.required?.includes(key) && <span className="text-red-400 ml-1">*</span>}
              </label>
              {field.description && (
                <span className="text-xs text-slate-500">{field.description}</span>
              )}
              <input
                type={isNumber ? "number" : "text"}
                step={isNumber ? "any" : undefined}
                value={formData[key] ?? ""}
                onChange={(e) =>
                  handleChange(key, isNumber ? parseFloat(e.target.value) || 0 : e.target.value)
                }
                className="bg-slate-950 border border-slate-750 text-slate-200 px-3 py-2 rounded-md text-sm focus:outline-none focus:border-emerald-500 transition-colors"
                required={schema.required?.includes(key)}
              />
            </div>
          );
        })
      )}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-lg transition-colors shadow-lg shadow-emerald-950 disabled:opacity-50 mt-4"
      >
        {loading ? "Ausführen..." : "Workflow Starten & DataProduct Erzeugen"}
      </button>
    </form>
  );
}
