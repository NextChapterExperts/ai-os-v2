"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

type Todo = { text: string; done: boolean };

type Attachment = {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

type Meeting = {
  id: string;
  title: string;
  held_at: string;
  participants: string;
  participant_refs?: Array<string | { email?: string; name?: string }>;
  summary: string;
  engagement_ids: string[];
  tags: string[];
  todos: Todo[];
  open_todo_count?: number;
  attachments?: Attachment[];
  attachment_count?: number;
  source?: string;
  calendar_event_id?: string;
  location?: string;
};

type PersonStat = {
  email: string;
  name?: string;
  meeting_count: number;
  last_meeting_at?: string;
  first_meeting_at?: string;
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

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

async function uploadFiles(meetingId: string, files: File[]): Promise<void> {
  for (const file of files) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`/api/meetings/${meetingId}/attachments`, {
      method: "POST",
      body: fd,
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.detail ?? json.error ?? `Upload fehlgeschlagen: ${file.name}`);
    }
  }
}

type FilterState = {
  q: string;
  unassigned: boolean;
  openTodo: boolean;
};

type ParsedParticipant = {
  email: string;
  name: string;
  domain: string;
  person_id: string;
  org_id?: string | null;
  org_name?: string | null;
  company_website?: string | null;
  linkedin_url?: string | null;
  role?: string | null;
  status: string;
  existing_node_id?: string | null;
  notes?: string;
};

export function MeetingsPanel() {
  const [data, setData] = useState<MeetingsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [queryInput, setQueryInput] = useState("");
  const [personQuery, setPersonQuery] = useState("");
  const [personStat, setPersonStat] = useState<PersonStat | null>(null);
  const [personLoading, setPersonLoading] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    q: "",
    unassigned: false,
    openTodo: false,
  });
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formAttachments, setFormAttachments] = useState<Attachment[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [participantPaste, setParticipantPaste] = useState("");
  const [participantPreview, setParticipantPreview] = useState<ParsedParticipant[]>([]);
  const [participantSummary, setParticipantSummary] = useState("");
  const [participantBusy, setParticipantBusy] = useState(false);
  const fetchSeq = useRef(0);

  const fetchMeetings = useCallback(async (next: FilterState) => {
    const seq = ++fetchSeq.current;
    setPending(true);
    try {
      setError(null);
      const params = new URLSearchParams();
      if (next.q.trim()) params.set("q", next.q.trim());
      if (next.unassigned) params.set("unassigned", "true");
      if (next.openTodo) params.set("has_open_todo", "true");
      params.set("_t", String(Date.now()));
      const res = await fetch(`/api/meetings?${params}`, { cache: "no-store" });
      const json = (await res.json()) as MeetingsResponse;
      if (seq !== fetchSeq.current) return;
      if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`);
      setData(json);
    } catch (err) {
      if (seq !== fetchSeq.current) return;
      setError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
    } finally {
      if (seq === fetchSeq.current) setPending(false);
    }
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

  const refresh = () => {
    const next = { ...filters, q: queryInput.trim() };
    setFilters(next);
    fetchMeetings(next);
  };

  const engagementOptions = data?.engagement_options ?? [];

  const engagementTitleById = useMemo(() => {
    const map = new Map<string, string>();
    for (const o of engagementOptions) map.set(o.id, o.title);
    return map;
  }, [engagementOptions]);

  function openCreate() {
    setEditingId(null);
    setFormAttachments([]);
    setPendingFiles([]);
    setParticipantPaste("");
    setParticipantPreview([]);
    setParticipantSummary("");
    setForm({
      ...EMPTY_FORM,
      held_at: toLocalDatetimeValue(new Date().toISOString()),
    });
    setShowForm(true);
  }

  function openEdit(m: Meeting) {
    setEditingId(m.id);
    setFormAttachments(m.attachments ?? []);
    setPendingFiles([]);
    setParticipantPaste("");
    setParticipantPreview([]);
    setParticipantSummary("");
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

  async function onFilesSelected(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    if (!editingId) {
      setPendingFiles((prev) => [...prev, ...list]);
      return;
    }
    setPending(true);
    try {
      setError(null);
      await uploadFiles(editingId, list);
      const res = await fetch(`/api/meetings/${editingId}?_t=${Date.now()}`, { cache: "no-store" });
      const json = await res.json();
      if (res.ok && json.meeting?.attachments) {
        setFormAttachments(json.meeting.attachments);
      }
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }

  async function removeAttachment(att: Attachment) {
    if (!editingId) return;
    if (!confirm(`Anhang „${att.filename}" löschen?`)) return;
    setPending(true);
    try {
      const res = await fetch(
        `/api/meetings/${editingId}/attachments/${att.id}`,
        { method: "DELETE" },
      );
      if (!res.ok) {
        const json = await res.json();
        throw new Error(json.detail ?? json.error ?? `HTTP ${res.status}`);
      }
      setFormAttachments((prev) => prev.filter((a) => a.id !== att.id));
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Anhang löschen fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }

  function toggleEngagement(id: string) {
    setForm((f) => ({
      ...f,
      engagement_ids: f.engagement_ids.includes(id)
        ? f.engagement_ids.filter((x) => x !== id)
        : [...f.engagement_ids, id],
    }));
  }

  async function onProcessParticipants() {
    const raw = participantPaste.trim() || form.participants.trim();
    if (!raw) {
      setError("Bitte Google-Teilnehmerliste einfügen.");
      return;
    }
    setParticipantBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/meetings/participants/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw, enrich: true }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail ?? json.error ?? `HTTP ${res.status}`);
      const items = (json.participants ?? []) as ParsedParticipant[];
      setParticipantPreview(items);
      setParticipantSummary(String(json.summary ?? ""));
      if (items.length > 0) {
        setForm((f) => ({
          ...f,
          participants: items.map((p) => p.name || p.email).join(", "),
        }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teilnehmer extrahieren fehlgeschlagen");
    } finally {
      setParticipantBusy(false);
    }
  }

  async function onCommitParticipants() {
    setParticipantBusy(true);
    setError(null);
    try {
      let items = participantPreview;
      if (items.length === 0) {
        const raw = participantPaste.trim() || form.participants.trim();
        if (!raw) throw new Error("Bitte zuerst Google-Teilnehmerliste einfügen.");
        const procRes = await fetch("/api/meetings/participants/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ raw, enrich: true }),
        });
        const procJson = await procRes.json();
        if (!procRes.ok) {
          throw new Error(procJson.detail ?? procJson.error ?? `HTTP ${procRes.status}`);
        }
        items = (procJson.participants ?? []) as ParsedParticipant[];
        setParticipantPreview(items);
        setParticipantSummary(String(procJson.summary ?? ""));
      }
      if (items.length === 0) throw new Error("Keine E-Mail-Adressen erkannt.");

      const res = await fetch("/api/meetings/participants/commit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items,
          meeting_id: editingId,
          update_meeting: Boolean(editingId),
        }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail ?? json.error ?? `HTTP ${res.status}`);
      const display =
        (json.participants_display as string | undefined) ??
        items.map((p) => p.name || p.email).join(", ");
      setForm((f) => ({ ...f, participants: display }));
      if (json.errors?.length) {
        setError(`Teilweise gespeichert: ${(json.errors as string[]).join("; ")}`);
      }
      if (editingId && json.meeting) {
        refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kontakte speichern fehlgeschlagen");
    } finally {
      setParticipantBusy(false);
    }
  }

  async function onSubmit(e: FormEvent) {
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

    setPending(true);
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
      const meetingId = (json.meeting?.id as string | undefined) ?? editingId;
      if (meetingId && pendingFiles.length > 0) {
        await uploadFiles(meetingId, pendingFiles);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY_FORM);
      setFormAttachments([]);
      setPendingFiles([]);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Meeting wirklich löschen?")) return;
    setPending(true);
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
    } finally {
      setPending(false);
    }
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
          <div className="meetings-field">
            <span>Teilnehmer</span>
            <textarea
              rows={4}
              className="meetings-participant-paste"
              value={participantPaste}
              onChange={(e) => setParticipantPaste(e.target.value)}
              placeholder={"Google-Kalender-Teilnehmer hier einfügen, z. B.:\nMax Mustermann <max@firma.de>\nanna.schmidt@partner.com"}
            />
            <p className="muted m-0 text-xs">
              E-Mails werden extrahiert; optional LinkedIn & Firmenwebseite werden gesucht und als Kontakte im Graph gespeichert.
            </p>
            <div className="meetings-participant-actions">
              <button
                type="button"
                className="btn btn-ghost"
                disabled={participantBusy || pending}
                onClick={() => void onProcessParticipants()}
              >
                {participantBusy ? "Verarbeite…" : "Extrahieren & anreichern"}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={participantBusy || pending}
                onClick={() => void onCommitParticipants()}
              >
                Als Kontakte speichern
              </button>
            </div>
            {participantSummary ? (
              <pre className="meetings-participant-summary">{participantSummary}</pre>
            ) : null}
            {participantPreview.length > 0 ? (
              <table className="meetings-participant-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>E-Mail</th>
                    <th>Organisation</th>
                    <th>LinkedIn / Web</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {participantPreview.map((p) => (
                    <tr key={p.email}>
                      <td>{p.name}</td>
                      <td className="mono text-xs">{p.email}</td>
                      <td>{p.org_name ?? "—"}</td>
                      <td className="text-xs">
                        {p.linkedin_url ? (
                          <a href={p.linkedin_url} target="_blank" rel="noreferrer">
                            LinkedIn
                          </a>
                        ) : null}
                        {p.linkedin_url && p.company_website ? " · " : null}
                        {p.company_website ? (
                          <a href={p.company_website} target="_blank" rel="noreferrer">
                            Web
                          </a>
                        ) : null}
                        {!p.linkedin_url && !p.company_website ? "—" : null}
                      </td>
                      <td>{p.status === "existing" ? "bekannt" : "neu"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <input
                value={form.participants}
                onChange={(e) => setForm((f) => ({ ...f, participants: e.target.value }))}
                placeholder="oder manuell: Michael, Juri, …"
              />
            )}
          </div>
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
          <div className="meetings-field">
            <span>Anhänge</span>
            <input
              type="file"
              multiple
              className="meetings-file-input"
              onChange={(e) => {
                void onFilesSelected(e.target.files);
                e.target.value = "";
              }}
            />
            <p className="muted m-0 text-xs">
              {editingId
                ? "Dateien werden sofort hochgeladen (max. 25 MB pro Datei)."
                : "Bei neuem Meeting: Dateien werden nach dem Speichern hochgeladen."}
            </p>
            {pendingFiles.length > 0 ? (
              <ul className="meetings-attach-list">
                {pendingFiles.map((f) => (
                  <li key={`${f.name}-${f.size}`}>
                    {f.name} · {formatBytes(f.size)} (wartet auf Speichern)
                  </li>
                ))}
              </ul>
            ) : null}
            {formAttachments.length > 0 ? (
              <ul className="meetings-attach-list">
                {formAttachments.map((att) => (
                  <li key={att.id} className="meetings-attach-item">
                    <a
                      href={`/api/meetings/${editingId}/attachments/${att.id}`}
                      className="nav-link"
                      download={att.filename}
                    >
                      {att.filename}
                    </a>
                    <span className="mono muted text-xs">
                      {formatBytes(att.size_bytes)}
                    </span>
                    {editingId ? (
                      <button
                        type="button"
                        className="btn-ghost meetings-attach-remove"
                        onClick={() => void removeAttachment(att)}
                      >
                        Entfernen
                      </button>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
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
              {!m.summary?.trim() && (m.source === "calendar" || m.tags?.includes("calendar-import")) ? (
                <span className="badge ml-2" data-variant="curated">Kalender · Summary fehlt</span>
              ) : null}
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
                {m.attachment_count ? (
                  <span className="badge" data-variant="raw">
                    {m.attachment_count} Anhang{m.attachment_count === 1 ? "" : "e"}
                  </span>
                ) : null}
              </div>
              {(m.attachments ?? []).length > 0 ? (
                <ul className="meetings-attach-list mt-2">
                  {(m.attachments ?? []).map((att) => (
                    <li key={att.id}>
                      <a
                        href={`/api/meetings/${m.id}/attachments/${att.id}`}
                        className="nav-link text-sm"
                        download={att.filename}
                      >
                        {att.filename}
                      </a>
                      <span className="mono muted text-xs ml-2">
                        {formatBytes(att.size_bytes)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : null}
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
