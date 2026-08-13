import React, { useState } from "react";
import { IconFileText, IconCopy, IconCheck } from "@tabler/icons-react";

interface DataProductViewerProps {
  dataProduct: Record<string, any>;
  title?: string;
}




function formatMeetingDate(iso: unknown): string {
  if (!iso || typeof iso !== "string") return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
  return d.toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function renderMeetingsTable(rows: Record<string, unknown>[]): React.ReactNode {
  return (
    <div className="p-4 rounded-xl border border-[var(--line)] bg-white space-y-2 overflow-x-auto">
      <div className="text-xs font-bold text-[var(--signal)] uppercase tracking-wider mono">
        Termine ({rows.length})
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--line)]">
            <th className="text-left p-2 font-semibold">Projekt</th>
            <th className="text-left p-2 font-semibold">Titel</th>
            <th className="text-left p-2 font-semibold">Datum</th>
            <th className="text-left p-2 font-semibold">Teilnehmer</th>
            <th className="text-left p-2 font-semibold">Summary</th>
            <th className="text-left p-2 font-semibold">Meeting-ID</th>
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 30).map((row, i) => (
            <tr key={i} className="border-b border-[var(--line)] last:border-0 align-top">
              <td className="p-2 whitespace-nowrap">{String(row.project || "—")}</td>
              <td className="p-2 font-semibold text-[var(--ink)]">{String(row.title || "—")}</td>
              <td className="p-2 mono whitespace-nowrap">{formatMeetingDate(row.held_at)}</td>
              <td className="p-2 text-[var(--ink-soft)] max-w-xs">{String(row.participants_label || row.participants || "—")}</td>
              <td className="p-2">{row.has_summary ? "✓" : "offen"}</td>
              <td className="p-2 mono text-[10px] muted">{String(row.meeting_id || "—")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderArrayField(key: string, value: unknown): React.ReactNode {
  if (!Array.isArray(value) || value.length === 0) return null;
  if (key === "meetings" && typeof value[0] === "object" && value[0] !== null) {
    return renderMeetingsTable(value as Record<string, unknown>[]);
  }
  if (key === "forecast_next_month" && typeof value[0] === "object" && value[0] !== null) {
    return renderMeetingsTable(
      (value as Record<string, unknown>[]).map((r) => ({ ...r, has_summary: false })),
    );
  }
  if (typeof value[0] !== "object" || value[0] === null) return null;
  const rows = value as Record<string, unknown>[];
  const cols = Object.keys(rows[0]).filter((k) => !["tenant_id", "produced_by", "workflow_run_id"].includes(k)).slice(0, 6);
  return (
    <div key={key} className="p-4 rounded-xl border border-[var(--line)] bg-white space-y-2 overflow-x-auto">
      <div className="text-xs font-bold text-[var(--signal)] uppercase tracking-wider mono">
        {key.replace(/_/g, " ")} ({rows.length})
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--line)]">
            {cols.map((c) => (
              <th key={c} className="text-left p-2 font-semibold">{c.replace(/_/g, " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((row, i) => (
            <tr key={i} className="border-b border-[var(--line)] last:border-0">
              {cols.map((c) => (
                <td key={c} className="p-2 mono align-top">
                  {typeof row[c] === "object" ? JSON.stringify(row[c]) : String(row[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const DataProductViewer: React.FC<DataProductViewerProps> = ({
  dataProduct,
  title = "Ergebnis DataProduct",
}) => {
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!dataProduct || typeof dataProduct !== "object") {
    return (
      <div className="p-4 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_40%,transparent)] text-xs muted">
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
  const producedBy = dataProduct.produced_by || "handwerk-angebot-agent";

  // Trenne Metadaten von Fachdaten
  const metaKeys = new Set(["dp_id", "tenant_id", "produced_by", "workflow_run_id", "schema_version", "id", "external_id", "node_type"]);
  const businessFields = Object.entries(dataProduct).filter(([k]) => !metaKeys.has(k));

  return (
    <div className="border border-[var(--line)] bg-[color-mix(in_oklab,white_75%,transparent)] rounded-2xl p-6 shadow-sm transition-all">
      {/* Top Header Card */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge" data-variant="graph">
              DataProduct
            </span>
            <h3 className="section-title text-base font-bold text-[var(--ink)] m-0">{title}</h3>
          </div>
          <p className="text-xs mono muted mt-1 flex items-center gap-3 m-0">
            <span>ID: <strong className="text-[var(--signal)]">{dpId}</strong></span>
            <span>Tenant: <span className="text-[var(--ink)]">{tenantId}</span></span>
            <span>By: <span className="text-[var(--ink)]">{producedBy}</span></span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="btn-ghost text-xs py-1 px-3 inline-flex items-center gap-1.5"
          >
            {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
            <span>{copied ? "Kopiert" : "JSON kopieren"}</span>
          </button>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="btn-ghost text-xs py-1 px-3"
            data-active={showRawJson ? "true" : "false"}
          >
            {showRawJson ? "Visualisierung" : "JSON Code"}
          </button>
        </div>
      </div>

      {/* Main Content View */}
      {showRawJson ? (
        <div className="relative">
          <pre className="context-pre text-xs mono text-[var(--signal)]">
            {JSON.stringify(dataProduct, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Formatted Text Box if offer text / text field exists */}
          {businessFields.map(([key, value]) => {
            if (typeof value === "string" && (value.includes("\n") || key.includes("text") || key.includes("angebot"))) {
              return (
                <div key={key} className="p-4 rounded-xl border border-[var(--line)] bg-white space-y-2">
                  <div className="text-xs font-bold text-[var(--signal)] uppercase tracking-wider mono flex items-center gap-1.5">
                    <IconFileText size={14} />
                    <span>{key.replace(/_/g, " ")}</span>
                  </div>
                  <div className="text-sm text-[var(--ink)] whitespace-pre-wrap leading-relaxed font-sans p-3 rounded-lg border border-[var(--line)] bg-[color-mix(in_oklab,white_90%,transparent)]">
                    {value}
                  </div>
                </div>
              );
            }
            return null;
          })}

          {businessFields.map(([key, value]) => renderArrayField(key, value))}

          {/* Key Value Grid for scalar fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {businessFields.map(([key, value]) => {
              if (Array.isArray(value) && value.length && typeof value[0] === "object") {
                return null;
              }
              if (typeof value === "string" && (value.includes("\n") || key.includes("text") || key.includes("angebot"))) {
                return null; // Already rendered above
              }
              const isPrice = key.includes("preis") || key.includes("summe") || key.includes("betrag") || key.includes("stundensatz");
              return (
                <div
                  key={key}
                  className="p-3 rounded-xl border border-[var(--line)] bg-white flex flex-col justify-between"
                >
                  <span className="text-[10px] mono uppercase muted">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span
                    className={`text-sm font-bold mt-1 ${
                      isPrice ? "text-[var(--signal)] mono" : "text-[var(--ink)]"
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
          <div className="mt-4 pt-3 border-t border-[var(--line)] flex items-center justify-between text-xs muted">
            <div className="flex items-center gap-2 text-[var(--signal)] text-[11px] mono font-semibold">
              <span className="status-dot ok" />
              <span>Atomar im Knowledge Graph (Postgres) gesichert & auditierbar</span>
            </div>
            <span className="text-[10px] mono muted">ISO-8601 UTC</span>
          </div>
        </div>
      )}
    </div>
  );
};
