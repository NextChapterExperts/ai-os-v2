"use client";

import React, { useState, useEffect } from "react";

interface JsonSchemaProperty {
  type?: string;
  title?: string;
  description?: string;
  default?: any;
  enum?: string[];
  anyOf?: Array<{ type?: string }>;
}

interface JsonSchema {
  title?: string;
  description?: string;
  properties?: Record<string, JsonSchemaProperty>;
  required?: string[];
}

interface DynamicDataProductFormProps {
  schema: JsonSchema;
  initialValues?: Record<string, any> | null;
  onSubmit: (data: Record<string, any>) => void;
  loading?: boolean;
}

export const DynamicDataProductForm: React.FC<DynamicDataProductFormProps> = ({
  schema,
  initialValues,
  onSubmit,
  loading = false,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    if (initialValues && Object.keys(initialValues).length > 0) {
      setFormData(initialValues);
      return;
    }
    if (schema?.properties) {
      const defaults: Record<string, any> = {};
      Object.entries(schema.properties).forEach(([key, prop]) => {
        if (prop.default !== undefined) {
          defaults[key] = prop.default;
        } else if (prop.enum && prop.enum.length > 0) {
          defaults[key] = prop.enum[0];
        } else if (prop.type === "number" || prop.type === "integer") {
          defaults[key] = key.includes("qm") ? 100.0 : key.includes("stundensatz") ? 70.0 : 0;
        } else if (prop.type === "boolean") {
          defaults[key] = false;
        } else {
          defaults[key] = key.includes("kunden")
            ? "Malerbetrieb Schulze"
            : key.includes("titel") || key.includes("projekt")
            ? "Fassadenanstrich"
            : "";
        }
      });
      setFormData(defaults);
    }
  }, [schema]);

  const handleChange = (key: string, value: any, type?: string) => {
    let parsedValue = value;
    if (type === "number" || type === "integer") {
      parsedValue = value === "" ? "" : Number(value);
    } else if (type === "boolean") {
      parsedValue = Boolean(value);
    }
    setFormData((prev) => ({ ...prev, [key]: parsedValue }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!schema || !schema.properties || Object.keys(schema.properties).length === 0) {
    return (
      <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-800 text-xs text-slate-400">
        Keine Eingabefelder im Schema definiert.
      </div>
    );
  }

  const properties = Object.entries(schema.properties);
  const requiredFields = new Set(schema.required || []);

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <span className="text-emerald-400">📝</span> {schema.title || "Workflow Eingabe"}
          </h4>
          {schema.description && (
            <p className="text-xs text-slate-400 mt-0.5">{schema.description}</p>
          )}
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
          JSON Schema Form
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {properties.map(([key, prop]) => {
          const isRequired = requiredFields.has(key);
          const rawType = prop.type || (prop.anyOf && prop.anyOf[0]?.type) || "string";
          const label = prop.title || key.replace(/_/g, " ");

          return (
            <div
              key={key}
              className={`space-y-1.5 ${
                rawType === "string" && !prop.enum && key.includes("beschreibung")
                  ? "md:col-span-2"
                  : ""
              }`}
            >
              <label className="block text-xs font-medium text-slate-300 flex items-center justify-between">
                <span>
                  {label}
                  {isRequired && <span className="text-rose-400 ml-1">*</span>}
                </span>
                <span className="text-[10px] font-mono text-slate-500 uppercase">{rawType}</span>
              </label>

              {prop.enum ? (
                <select
                  value={formData[key] || ""}
                  onChange={(e) => handleChange(key, e.target.value, rawType)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all cursor-pointer"
                >
                  {prop.enum.map((opt) => (
                    <option key={opt} value={opt} className="bg-slate-900 text-slate-200">
                      {opt}
                    </option>
                  ))}
                </select>
              ) : rawType === "boolean" ? (
                <div className="flex items-center gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => handleChange(key, !formData[key], "boolean")}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      formData[key] ? "bg-emerald-500" : "bg-slate-800"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        formData[key] ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                  <span className="text-xs text-slate-400">
                    {formData[key] ? "Ja / Aktiv" : "Nein / Inaktiv"}
                  </span>
                </div>
              ) : (
                <input
                  type={rawType === "number" || rawType === "integer" ? "number" : "text"}
                  step={rawType === "number" ? "any" : undefined}
                  value={formData[key] !== undefined ? formData[key] : ""}
                  placeholder={prop.description || `Eingabe für ${label}`}
                  onChange={(e) => handleChange(key, e.target.value, rawType)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                  required={isRequired}
                />
              )}
              {prop.description && (
                <p className="text-[10px] text-slate-500">{prop.description}</p>
              )}
            </div>
          );
        })}
      </div>

      <div className="pt-2 flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-semibold text-xs shadow-lg shadow-emerald-950/50 flex items-center gap-2 transition-all disabled:opacity-50"
        >
          {loading ? (
            <>
              <span className="animate-spin">⏳</span>
              <span>Führe Workflow aus...</span>
            </>
          ) : (
            <>
              <span>⚡</span>
              <span>Workflow Ausführen</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
