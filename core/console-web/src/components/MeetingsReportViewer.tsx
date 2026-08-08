"use client";

import { useMemo, useState } from "react";

type MeetingRow = {
  project?: string;
  title?: string;
  held_at?: string;
  participants_label?: string;
  participants?: string;
  has_summary?: boolean;
  meeting_id?: string;
  location?: string;
};

type ForecastRow = {
  project?: string;
  title?: string;
  held_at?: string;
  participants_label?: string;
  location?: string;
};

function formatDate(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
  return d.toLocaleString("de-DE", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatRange(from?: string, to?: string): string {
  const f = from ? formatDate(from).split(",")[0] : "—";
  const t = to ? formatDate(to).split(",")[0] : "—";
  return `${f} – ${t}`;
}

function participantsOf(row: MeetingRow | ForecastRow): string {
  return String(row.participants_label || (row as MeetingRow).participants || "—");
}

function MeetingsTable({
  rows,
  variant,
}: {
  rows: Array<MeetingRow | ForecastRow>;
  variant: "past" | "future";
}) {
  if (rows.length === 0) {
    return (
      <p className="text-xs muted m-0 p-3">Keine Termine in dieser Kategorie.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--line)] bg-[color-mix(in_oklab,white_92%,transparent)]">
            <th className="text-left p-2 font-semibold whitespace-nowrap">Projekt</th>
            <th className="text-left p-2 font-semibold">Titel</th>
            <th className="text-left p-2 font-semibold whitespace-nowrap">Datum</th>
            <th className="text-left p-2 font-semibold">Teilnehmer</th>
            {variant === "past" ? (
              <th className="text-left p-2 font-semibold">Summary</th>
            ) : (
              <th className="text-left p-2 font-semibold">Status</th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-[var(--line)] last:border-0 align-top hover:bg-[color-mix(in_oklab,var(--signal)_4%,white)]">
              <td className="p-2 whitespace-nowrap">
                {row.project ? (
                  <span className="badge" data-variant="curated">{row.project}</span>
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td className="p-2 font-semibold text-[var(--ink)] max-w-xs">{row.title || "—"}</td>
              <td className="p-2 mono whitespace-nowrap">{formatDate(row.held_at)}</td>
              <td className="p-2 text-[var(--ink-soft)] max-w-sm">{participantsOf(row)}</td>
              <td className="p-2 whitespace-nowrap">
                {variant === "past" ? (
                  (row as MeetingRow).has_summary ? (
                    <span className="text-[var(--signal)]">✓</span>
                  ) : (
                    <span className="muted">offen</span>
                  )
                ) : (
                  <span className="badge" data-variant="graph">geplant</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface MeetingsReportViewerProps {
  report: Record<string, unknown>;
}

export function MeetingsReportViewer({ report }: MeetingsReportViewerProps) {
  const [projectFilter, setProjectFilter] = useState<string>("all");

  const pastMeetings = (report.meetings || []) as MeetingRow[];
  const forecast = (report.forecast_next_month || []) as ForecastRow[];

  const projects = useMemo(() => {
    const fromReport = report.discovered_projects;
    if (Array.isArray(fromReport) && fromReport.length > 0) {
      return (fromReport as string[]).slice().sort((a, b) => a.localeCompare(b, "de"));
    }
    const set = new Set<string>();
    for (const m of pastMeetings) {
      if (m.project) set.add(m.project);
    }
    for (const f of forecast) {
      if (f.project) set.add(f.project);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, "de"));
  }, [pastMeetings, forecast]);

  const filteredPast = useMemo(() => {
    if (projectFilter === "all") return pastMeetings;
    if (projectFilter === "none") return pastMeetings.filter((m) => !m.project);
    return pastMeetings.filter((m) => m.project === projectFilter);
  }, [pastMeetings, projectFilter]);

  const filteredForecast = useMemo(() => {
    if (projectFilter === "all") return forecast;
    if (projectFilter === "none") return forecast.filter((f) => !f.project);
    return forecast.filter((f) => f.project === projectFilter);
  }, [forecast, projectFilter]);

  const since = String(report.since_date || "");
  const until = String(report.until_date || "");

  return (
    <div className="border border-[var(--line)] rounded-2xl bg-white shadow-sm overflow-hidden">
      <div className="p-4 border-b border-[var(--line)] space-y-3 bg-[color-mix(in_oklab,white_90%,transparent)]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-[var(--ink)] m-0">Kalender-Übersicht</h3>
            <p className="text-xs muted m-0 mt-1">
              Zeitraum importiert: {formatRange(since, until)} · {filteredPast.length} vergangen · {filteredForecast.length} geplant
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-[10px] mono uppercase muted">Projekt</label>
            <select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              className="bg-white border border-[var(--line)] rounded-lg px-2 py-1.5 text-xs min-w-[140px]"
            >
              <option value="all">Alle Projekte</option>
              <option value="none">Ohne Projekt</option>
              {projects.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>
        {String(report.summary || "").trim() ? (
          <p className="text-xs text-[var(--ink-soft)] m-0">{String(report.summary)}</p>
        ) : null}
      </div>

      <div className="p-4 space-y-5">
        <div>
          <div className="text-xs font-bold text-[var(--signal)] uppercase tracking-wider mono mb-2">
            Vergangene Termine ({filteredPast.length})
          </div>
          <MeetingsTable rows={filteredPast} variant="past" />
        </div>

        <div>
          <div className="text-xs font-bold text-[var(--signal)] uppercase tracking-wider mono mb-2">
            Geplante Termine — Forecast ({filteredForecast.length})
          </div>
          <MeetingsTable rows={filteredForecast} variant="future" />
        </div>
      </div>

      <div className="px-4 py-3 border-t border-[var(--line)] bg-[color-mix(in_oklab,var(--signal)_5%,white)] text-[10px] text-[var(--ink-soft)]">
        Nächster Schritt: Aufgabe „Zusammenfassung ins Company Brain“ → Meeting wählen → Text eingeben → Modus <strong>Live</strong>.
      </div>
    </div>
  );
}
