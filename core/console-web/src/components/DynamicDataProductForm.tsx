"use client";

import React, { useState, useEffect } from "react";
import { MeetingPickerField } from "@/components/MeetingPickerField";

interface JsonSchemaProperty {
  type?: string;
  title?: string;
  description?: string;
  default?: any;
  enum?: string[];
  anyOf?: Array<{ type?: string }>;
  "x-enum-labels"?: Record<string, string>;
  "x-visible-when"?: Record<string, string>;
  "x-widget"?: string;
}

interface JsonSchema {
  title?: string;
  description?: string;
  properties?: Record<string, JsonSchemaProperty>;
  required?: string[];
}

/** Interne DataProduct-Felder — nicht in der Nutzer-UI anzeigen. */
const HIDDEN_FIELDS = new Set([
  "dp_id",
  "schema_version",
  "tenant_id",
  "produced_by",
  "produced_at",
  "workflow_run_id",
  "storage_target",
  "ingest_recommended",
]);

function enumLabel(prop: JsonSchemaProperty, value: string): string {
  return prop["x-enum-labels"]?.[value] ?? value;
}

function isFieldVisible(
  prop: JsonSchemaProperty,
  formData: Record<string, any>,
): boolean {
  const rule = prop["x-visible-when"];
  if (!rule) return true;
  return Object.entries(rule).every(([field, expected]) => formData[field] === expected);
}

interface DynamicDataProductFormProps {
  schema: JsonSchema;
  initialValues?: Record<string, any> | null;
  onSubmit: (data: Record<string, any>) => void;
  onFormDataChange?: (data: Record<string, any>) => void;
  loading?: boolean;
  submitLabel?: string;
  loadingLabel?: string;
}

export const DynamicDataProductForm: React.FC<DynamicDataProductFormProps> = ({
  schema,
  initialValues,
  onSubmit,
  onFormDataChange,
  loading = false,
  submitLabel = "Agent ausführen",
  loadingLabel = "Agent läuft…",
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
        if (HIDDEN_FIELDS.has(key)) return;
        if (prop.default !== undefined) {
          defaults[key] = prop.default;
        } else if (prop.enum && prop.enum.length > 0) {
          defaults[key] = prop.enum[0];
        } else if (prop.type === "number" || prop.type === "integer") {
          defaults[key] = key.includes("qm") ? 120.0 : key.includes("stundensatz") ? 70.0 : 0;
        } else if (prop.type === "boolean") {
          defaults[key] = false;
        } else {
          defaults[key] = key.includes("kunden")
            ? "Malerbetrieb Schulze GmbH"
            : key.includes("titel") || key.includes("projekt")
            ? "Fassadenanstrich & Gerüstbau"
            : "";
        }
      });
      setFormData(defaults);
    }
  }, [schema, initialValues]);

  const handleChange = (key: string, value: any, type?: string) => {
    let parsedValue = value;
    if (type === "number" || type === "integer") {
      parsedValue = value === "" ? "" : Number(value);
    } else if (type === "boolean") {
      parsedValue = Boolean(value);
    }
    setFormData((prev) => {
      const next = { ...prev, [key]: parsedValue };
      onFormDataChange?.(next);
      return next;
    });
  };

  useEffect(() => {
    if (Object.keys(formData).length > 0) {
      onFormDataChange?.(formData);
    }
  }, [formData, onFormDataChange]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!schema || !schema.properties || Object.keys(schema.properties).length === 0) {
    return (
      <div className="p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_50%,transparent)] text-xs muted">
        Keine Eingabefelder im Schema definiert.
      </div>
    );
  }

  const properties = Object.entries(schema.properties).filter(
    ([key]) => !HIDDEN_FIELDS.has(key),
  );
  const requiredFields = new Set(schema.required || []);

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="flex items-center justify-between border-b border-[var(--line)] pb-3 mb-4">
        <div>
          <h4 className="text-sm font-bold text-[var(--ink)] flex items-center gap-2 m-0">
            <span className="text-[var(--signal)]">📝</span> {schema.title || "Datenerfassung"}
          </h4>
          {schema.description && (
            <p className="text-xs muted mt-0.5 m-0">{schema.description}</p>
          )}
        </div>
        <span className="badge" data-variant="graph">
          JSON Schema Form
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {properties.map(([key, prop]) => {
          if (!isFieldVisible(prop, formData)) return null;
          const isRequired = requiredFields.has(key);
          const rawType = prop.type || (prop.anyOf && prop.anyOf[0]?.type) || "string";
          const label = prop.title || key.replace(/_/g, " ");
          const isTextarea =
            prop["x-widget"] === "textarea" ||
            key === "summary" ||
            (rawType === "string" && key.includes("beschreibung"));
          const isMeetingPicker = prop["x-widget"] === "meeting-picker";

          return (
            <div
              key={key}
              className={`space-y-1.5 ${isTextarea || isMeetingPicker ? "md:col-span-2" : ""}`}
            >
              <label className="block text-xs font-semibold text-[var(--ink)] flex items-center justify-between">
                <span>
                  {label}
                  {isRequired && <span className="text-[var(--danger)] ml-1">*</span>}
                </span>
                {!isMeetingPicker ? (
                  <span className="mono text-[10px] muted uppercase">{rawType}</span>
                ) : null}
              </label>

              {prop["x-widget"] === "meeting-picker" ? (
                <MeetingPickerField
                  value={String(formData[key] || "")}
                  onChange={(id) => handleChange(key, id, rawType)}
                  required={isRequired}
                />
              ) : prop.enum ? (
                <select
                  value={formData[key] || ""}
                  onChange={(e) => handleChange(key, e.target.value, rawType)}
                  className="w-full bg-[color-mix(in_oklab,white_85%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-[var(--signal)] transition-colors cursor-pointer"
                >
                  {prop.enum.map((opt) => (
                    <option key={opt} value={opt} className="bg-[var(--paper)] text-[var(--ink)]">
                      {enumLabel(prop, opt)}
                    </option>
                  ))}
                </select>
              ) : rawType === "boolean" ? (
                <div className="flex items-center gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => handleChange(key, !formData[key], "boolean")}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      formData[key] ? "bg-[var(--signal)]" : "bg-[color-mix(in_oklab,var(--ink)_20%,transparent)]"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        formData[key] ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                  <span className="text-xs muted">
                    {formData[key] ? "Ja / Aktiv" : "Nein / Inaktiv"}
                  </span>
                </div>
              ) : isTextarea ? (
                <textarea
                  rows={5}
                  value={formData[key] !== undefined ? formData[key] : ""}
                  placeholder={prop.description || `Eingabe für ${label}`}
                  onChange={(e) => handleChange(key, e.target.value, rawType)}
                  className="w-full bg-[color-mix(in_oklab,white_85%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-lg px-3 py-2 text-xs placeholder-[var(--ink-soft)] focus:outline-none focus:border-[var(--signal)] transition-colors min-h-[120px]"
                  required={isRequired}
                />
              ) : (
                <input
                  type={rawType === "number" || rawType === "integer" ? "number" : "text"}
                  step={rawType === "number" ? "any" : undefined}
                  value={formData[key] !== undefined ? formData[key] : ""}
                  placeholder={prop.description || `Eingabe für ${label}`}
                  onChange={(e) => handleChange(key, e.target.value, rawType)}
                  className="w-full bg-[color-mix(in_oklab,white_85%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-lg px-3 py-2 text-xs placeholder-[var(--ink-soft)] focus:outline-none focus:border-[var(--signal)] transition-colors"
                  required={isRequired}
                />
              )}
              {prop.description && prop["x-widget"] !== "meeting-picker" && (
                <p className="text-[10px] muted m-0">{prop.description}</p>
              )}
            </div>
          );
        })}
      </div>

      <div className="pt-2 flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="btn-primary rounded-lg text-xs font-bold"
        >
          {loading ? (
            <>
              <span className="animate-spin">⏳</span>
              <span>{loadingLabel}</span>
            </>
          ) : (
            <>
              <span>⚡</span>
              <span>{submitLabel}</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
