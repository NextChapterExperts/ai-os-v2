"use client";

import { useCallback, useEffect, useState } from "react";

type CaptureStats = {
  sources?: Record<string, number>;
  total_chunks?: number;
  inbox_path?: string;
  capture_meta?: Record<string, string>;
  antigravity?: { updated_at?: string; sessions?: Record<string, unknown> };
  gemini_inbox?: { updated_at?: string; files?: Record<string, unknown> };
  error?: string;
};

export function ChatCapturePanel() {
  const [data, setData] = useState<CaptureStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/capture/stats", { cache: "no-store" });
      const json = (await res.json()) as CaptureStats & { error?: string };
      if (!res.ok) throw new Error(json.error ?? `HTTP ${res.status}`);
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const agSessions = data?.antigravity?.sessions
    ? Object.keys(data.antigravity.sessions).length
    : 0;
  const inboxFiles = data?.gemini_inbox?.files
    ? Object.keys(data.gemini_inbox.files).length
    : 0;

  return (
    <section className="rise">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Chat-Erfassung</h2>
          <p className="muted mb-0 text-sm">
            Cursor, Antigravity und Gemini-Inbox → gemeinsames Gedächtnis (memory.db)
          </p>
        </div>
        <button type="button" className="btn-secondary" onClick={load} disabled={pending}>
          {pending ? "Aktualisiere…" : "Aktualisieren"}
        </button>
      </div>

      {error ? <p className="text-danger mt-4">{error}</p> : null}

      {data ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="card p-4">
            <h3 className="text-sm font-medium">Chunks nach Quelle</h3>
            <p className="mono muted mt-1 text-xs">Gesamt: {data.total_chunks ?? 0}</p>
            <ul className="mt-3 space-y-1 text-sm">
              {Object.entries(data.sources ?? {}).map(([src, n]) => (
                <li key={src} className="flex justify-between gap-4">
                  <span>{src}</span>
                  <span className="mono">{n}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="card p-4">
            <h3 className="text-sm font-medium">Poller-Status</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li>
                <span className="font-medium">Cursor</span>
                <span className="muted ml-2 text-xs">
                  letzter Lauf: {data.capture_meta?.last_run_at ?? "—"}
                </span>
              </li>
              <li>
                <span className="font-medium">Antigravity</span>
                <span className="muted ml-2 text-xs">
                  {agSessions} Sessions · {data.antigravity?.updated_at ?? "—"}
                </span>
              </li>
              <li>
                <span className="font-medium">Gemini-Inbox</span>
                <span className="muted ml-2 text-xs">
                  {inboxFiles} Dateien · {data.gemini_inbox?.updated_at ?? "—"}
                </span>
              </li>
            </ul>
          </div>

          <div className="card p-4 md:col-span-2">
            <h3 className="text-sm font-medium">Gemini / manueller Import</h3>
            <p className="muted mt-2 mb-0 text-sm leading-relaxed">
              Markdown-Exporte nach{" "}
              <code className="mono text-xs">{data.inbox_path}/gemini/</code> oder{" "}
              <code className="mono text-xs">{data.inbox_path}/chats/</code> ablegen
              (YAML-Frontmatter mit <code>source: gemini</code>). Der Inbox-Poller
              importiert automatisch.
            </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
