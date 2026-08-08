"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

export type MeetingOption = {
  id: string;
  title: string;
  project?: string;
  held_at: string;
  participants: string;
  location?: string;
  has_summary?: boolean;
};

function formatHeldAt(iso: string): string {
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

function optionLabel(m: MeetingOption): string {
  const parts: string[] = [];
  if (m.project) parts.push(`[${m.project}]`);
  parts.push(formatHeldAt(m.held_at), m.title || "(Ohne Titel)");
  if (m.participants) {
    const short = m.participants.length > 48 ? `${m.participants.slice(0, 45)}…` : m.participants;
    parts.push(short);
  }
  if (!m.has_summary) parts.push("· Summary fehlt");
  return parts.join(" — ");
}

interface MeetingPickerFieldProps {
  value: string;
  onChange: (meetingId: string) => void;
  required?: boolean;
}

export function MeetingPickerField({ value, onChange, required }: MeetingPickerFieldProps) {
  const [meetings, setMeetings] = useState<MeetingOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/meetings?limit=200", { cache: "no-store" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`);
      const rows = (data.meetings || []) as Array<Record<string, unknown>>;
      const mapped: MeetingOption[] = rows.map((m) => ({
        id: String(m.id || ""),
        title: String(m.title || ""),
        project: String(m.project || ""),
        held_at: String(m.held_at || ""),
        participants: String(m.participants || ""),
        location: String(m.location || ""),
        has_summary: Boolean(String(m.summary || "").trim()),
      }));
      mapped.sort((a, b) => (b.held_at || "").localeCompare(a.held_at || ""));
      setMeetings(mapped);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Meetings konnten nicht geladen werden");
      setMeetings([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const selected = useMemo(() => meetings.find((m) => m.id === value) ?? null, [meetings, value]);

  return (
    <div className="space-y-3 md:col-span-2">
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 min-w-[240px] w-full bg-[color-mix(in_oklab,white_85%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-[var(--signal)]"
          required={required}
          disabled={loading || meetings.length === 0}
        >
          <option value="">
            {loading
              ? "Meetings werden geladen…"
              : meetings.length === 0
                ? "Keine Meetings — zuerst Termine laden (Live)"
                : "Meeting wählen…"}
          </option>
          {meetings.map((m) => (
            <option key={m.id} value={m.id}>
              {optionLabel(m)}
            </option>
          ))}
        </select>
        <button type="button" className="btn-ghost text-xs" onClick={load} disabled={loading}>
          Aktualisieren
        </button>
      </div>
      {error ? <p className="text-[10px] text-[var(--danger)] m-0">{error}</p> : null}
      {selected ? (
        <div className="p-4 rounded-xl border border-[var(--line)] bg-white text-xs space-y-2">
          <div className="font-semibold text-sm text-[var(--ink)]">{selected.title}</div>
          {selected.project ? (
            <div><span className="muted">Projekt: </span><span className="badge" data-variant="curated">{selected.project}</span></div>
          ) : null}
          <div><span className="muted">Termin: </span><span className="mono">{formatHeldAt(selected.held_at)}</span></div>
          {selected.participants ? (
            <div><span className="muted">Teilnehmer: </span><span>{selected.participants}</span></div>
          ) : null}
          {selected.location ? (
            <div><span className="muted">Ort: </span><span>{selected.location}</span></div>
          ) : null}
          <div className="mono text-[10px] muted">ID: {selected.id}</div>
          {!selected.has_summary ? (
            <span className="badge" data-variant="curated">Noch keine Zusammenfassung</span>
          ) : (
            <span className="badge" data-variant="graph">Summary vorhanden</span>
          )}
        </div>
      ) : (
        <p className="text-[10px] muted m-0">
          Termin wählen — Titel, Datum und Teilnehmer erscheinen hier. Liste leer? Zuerst „Termine laden“ (Live).
        </p>
      )}
    </div>
  );
}
