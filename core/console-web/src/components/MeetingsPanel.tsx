"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState, useTransition } from "react";

type Todo = { text: string; done: boolean };

type Meeting = {
  id: string;
  title: string;
  held_at: string;
  participants: string;
  summary: string;
  engagement_ids: string[];
  tags: string[];
  todos: Todo[];
  open_todo_count?: number;
};

type EngagementOption = { id: string; title: string };

type MeetingsResponse = {
  meetings: Meeting[];
  engagement_options: EngagementOption[];
  count: number;
  error?: string;
};

const EMPTY_FORM = {
  title: "",
  held_at: "",
  participants: "",
  summary: "",
  engagement_ids: [] as string[],
  tags: "",
  todos: "",
};

function toLocalDatetimeValue(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function localDatetimeToIso(local: string): string {
  if (!local) return new Date().toISOString();
  const d = new Date(local);
  return Number.isNaN(d.getTime()) ? local : d.toISOString();
}

function parseTodos(text: string): Todo[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const done = /^\[[xX]\]/.test(line);
      const textOnly = line.replace(/^\[[ xX]?\]\s*/, "");
      return { text: textOnly, done };
    });
}

function formatTodos(todos: Todo[]): string {
  return todos.map((t) => `${t.done ? "[x]" : "[ ]"} ${t.text}`).join("\n");
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("de-DE", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

type FilterState = {
  q: string;
  unassigned: boolean;
  openTodo: boolean;
};

export function MeetingsPanel() {
  const [data, setData] = useState<MeetingsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [queryInput, setQueryInput] = useState("");
  const [filters, setFilters] = useState<FilterState>({
    q: "",
    unassigned: false,
    openTodo: false,
  });
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const fetchSeq = useRef(0);

  const fetchMeetings = useCallback((next: FilterState) => {
    const seq = ++fetchSeq.current;
    startTransition(async () => {
      try {
        setError(null);
        const params = new URLSearchParams();
        if (next.q.trim()) params.set("q", next.q.trim());
        if (next.unassigned) params.set("unassigned", "true");
        if (next.openTodo) params.set("has_open_todo", "true");
        const res = await fetch(`/api/meetings?${params}`, { cache: "no-store" });
        const json = (await res.json()) as MeetingsResponse;
        if (seq !== fetchSeq.current) return;
        if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`);
        setData(json);
      } catch (err) {
        if (seq !== fetchSeq.current) return;
        setError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
      }
    });
  }, []);

  useEffect(() => {
    fetchMeetings(filters);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps -- initial load only

  const applySearch = () => {
    const next = { ...filters, q: queryInput.trim() };
    setFilters(next);
    fetchMeetings(next);
  };

  const toggleUnassigned = () => {
    const next = { ...filters, unassigned: !filters.unassigned };
    setFilters(next);
    fetchMeetings(next);
  };

  const toggleOpenTodo = () => {
    const next = { ...filters, openTodo: !filters.openTodo };
    setFilters(next);
    fetchMeetings(next);
  };

  const refresh = () => fetchMeetings(filters);

  const engagementOptions = data?.engagement_options ?? [];

  const engagementTitleById = useMemo(() => {
    const map = new Map<string, string>();
    for (const o of engagementOptions) map.set(o.id, o.title);
    return map;
  }, [engagementOptions]);

  function openCreate() {
    setEditingId(null);
    setForm({
      ...EMPTY_FORM,
      held_at: toLocalDatetimeValue(new Date().toISOString()),
    });
    setShowForm(true);
  }

  function openEdit(m: Meeting) {
    setEditingId(m.id);
    setForm({
      title: m.title,
      held_at: toLocalDatetimeValue(m.held_at),
      participants: m.participants,
      summary: m.summary,
      engagement_ids: [...m.engagement_ids],
      tags: m.tags.join(", "),
      todos: formatTodos(m.todos),
    });
    setShowForm(true);
  }

  function toggleEngagement(id: string) {
    setForm((f) => ({
      ...f,
      engagement_ids: f.engagement_ids.includes(id)
        ? f.engagement_ids.filter((x) => x !== id)
        : [...f.engagement_ids, id],
    }));
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const payload = {
      title: form.title.trim(),
      held_at: localDatetimeToIso(form.held_at),
      participants: form.participants.trim(),
      summary: form.summary.trim(),
      engagement_ids: form.engagement_ids,
      tags: form.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      todos: parseTodos(form.todos),
    };
    if (!payload.title) return;

    startTransition(async () => {
      try {
        setError(null);
        const url = editingId ? `/api/meetings/${editingId}` : "/api/meetings";
        const method = editingId ? "PATCH" : "POST";
        const res = await fetch(url, {
          method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.detail ?? json.error ?? `HTTP ${res.status}`);
        setShowForm(false);
        setEditingId(null);
        setForm(EMPTY_FORM);
        refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
      }
    });
  }

  function onDelete(id: string) {
    if (!confirm("Meeting wirklich löschen?")) return;
    startTransition(async () => {
      try {
        const res = await fetch(`/api/meetings/${id}`, { method: "DELETE" });
        if (!res.ok) {
          const json = await res.json();
          throw new Error(json.detail ?? json.error ?? `HTTP ${res.status}`);
        }
        if (editingId === id) {
          setShowForm(false);
          setEditingId(null);
        }
        refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Löschen fehlgeschlagen");
      }
    });
  }

  return (
    <div className="meetings-panel">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">Inbox</p>
          <p className="muted m-0 text-sm">
            {data?.count ?? 0} Meetings
            {filters.unassigned ? " · ohne Projekt" : ""}
            {filters.openTodo ? " · offene To-dos" : ""}
            {filters.q ? ` · Suche „${filters.q}"` : ""}
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={openCreate}>
          Meeting erfassen
        </button>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        <input
          className="meetings-search"
          placeholder="Suche Titel, Teilnehmer, Summary, Tags…"
          value={queryInput}
          onChange={(e) => setQueryInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              applySearch();
            }
          }}
        />
        <button type="button" className="btn-ghost" onClick={applySearch} disabled={pending}>
          Suchen
        </button>
        <button type="button" className="btn-ghost" onClick={refresh} disabled={pending}>
          Aktualisieren
        </button>
        <button
          type="button"
          className="btn-ghost"
          data-active={filters.unassigned ? "true" : "false"}
          onClick={toggleUnassigned}
        >
          Ohne Projekt
        </button>
        <button
          type="button"
          className="btn-ghost"
          data-active={filters.openTodo ? "true" : "false"}
          onClick={toggleOpenTodo}
        >
          Offene To-dos
        </button>
      </div>

      {error ? <p className="text-danger">{error}</p> : null}

      {showForm ? (
        <form className="meetings-form rise mb-8" onSubmit={onSubmit}>
          <h2 className="section-title text-lg">
            {editingId ? "Meeting bearbeiten" : "Neues Meeting"}
          </h2>
          <label className="meetings-field">
            <span>Titel *</span>
            <input
              required
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="z. B. Georgia Launchpad — SAP AI Hub Call"
            />
          </label>
          <label className="meetings-field">
            <span>Datum & Uhrzeit *</span>
            <input
              type="datetime-local"
              required
              value={form.held_at}
              onChange={(e) => setForm((f) => ({ ...f, held_at: e.target.value }))}
            />
          </label>
          <label className="meetings-field">
            <span>Teilnehmer</span>
            <input
              value={form.participants}
              onChange={(e) => setForm((f) => ({ ...f, participants: e.target.value }))}
              placeholder="Michael, Juri, …"
            />
          </label>
          <label className="meetings-field">
            <span>Kurzfassung</span>
            <textarea
              rows={4}
              value={form.summary}
              onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
              placeholder="3–5 Bulletpoints — was wurde besprochen?"
            />
          </label>
          <fieldset className="meetings-field">
            <legend>Projekte (optional)</legend>
            <div className="meetings-checkgrid">
              {engagementOptions.map((o) => (
                <label key={o.id} className="meetings-check">
                  <input
                    type="checkbox"
                    checked={form.engagement_ids.includes(o.id)}
                    onChange={() => toggleEngagement(o.id)}
                  />
                  <span>{o.title}</span>
                  <span className="mono muted text-xs">{o.id}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <label className="meetings-field">
            <span>Tags (kommagetrennt)</span>
            <input
              value={form.tags}
              onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
              placeholder="launchpad, kollegen, michael, planung"
            />
          </label>
          <label className="meetings-field">
            <span>To-dos (eine Zeile pro Punkt, [ ] oder [x])</span>
            <textarea
              rows={3}
              value={form.todos}
              onChange={(e) => setForm((f) => ({ ...f, todos: e.target.value }))}
              placeholder="[ ] Angebot bis Freitag&#10;[x] Termin bestätigt"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button type="submit" className="btn-primary" disabled={pending}>
              {pending ? "Speichere…" : "Speichern"}
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
              }}
            >
              Abbrechen
            </button>
            {editingId ? (
              <button
                type="button"
                className="btn-ghost text-danger"
                onClick={() => onDelete(editingId)}
              >
                Löschen
              </button>
            ) : null}
          </div>
        </form>
      ) : null}

      {pending && !data ? <p className="muted">Lade Meetings…</p> : null}

      <div className="row-list">
        {(data?.meetings ?? []).map((m) => (
          <div key={m.id} className="meetings-row">
            <div>
              <button type="button" className="meetings-row-title" onClick={() => openEdit(m)}>
                {m.title}
              </button>
              <p className="mono muted m-0 mt-1 text-xs">{formatDate(m.held_at)}</p>
              {m.participants ? (
                <p className="muted m-0 mt-2 text-sm">Teilnehmer: {m.participants}</p>
              ) : null}
              {m.summary ? (
                <p className="muted m-0 mt-2 text-sm whitespace-pre-wrap">{m.summary}</p>
              ) : null}
              <div className="mt-2 flex flex-wrap gap-2">
                {m.engagement_ids.map((eid) => (
                  <span key={eid} className="badge" data-variant="graph">
                    {engagementTitleById.get(eid) ?? eid}
                  </span>
                ))}
                {m.tags.map((tag) => (
                  <span key={tag} className="badge">
                    {tag}
                  </span>
                ))}
                {m.open_todo_count ? (
                  <span className="badge" data-variant="episodic">
                    {m.open_todo_count} offen
                  </span>
                ) : null}
              </div>
            </div>
            <button type="button" className="btn-ghost" onClick={() => openEdit(m)}>
              Bearbeiten
            </button>
          </div>
        ))}
      </div>

      {data && data.meetings.length === 0 && !pending ? (
        <p className="muted mt-4">
          {filters.unassigned || filters.openTodo || filters.q
            ? "Keine Treffer für diesen Filter."
            : "Noch keine Meetings — oben erfassen."}
        </p>
      ) : null}
    </div>
  );
}
