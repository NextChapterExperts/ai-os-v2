"use client";

import { FormEvent, useCallback, useEffect, useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";

type Source = {
  id: string;
  role: string;
  title: string;
  snippet: string;
  chat_id: string;
  source: string;
  ingested_at: string;
};

type Stats = {
  chunks: number;
  chats: number;
  trackedFiles: number;
  lastRunAt: string | null;
  projectId?: string;
  projectLabel?: string;
};

type AskResponse = {
  kind: string;
  query: string;
  answer?: string;
  mode?: string;
  dayLabel?: string;
  detail?: boolean;
  projectId?: string;
  model?: string;
  sourceCount?: number;
  sources?: Source[];
  results?: Source[];
  error?: string;
  stats?: Stats;
};

export function MemorySearch({
  autofocus = false,
  compact = false,
}: {
  autofocus?: boolean;
  compact?: boolean;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const initial = params.get("q") ?? "";
  const [q, setQ] = useState(initial);
  const [data, setData] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSources, setShowSources] = useState(false);
  const [pending, startTransition] = useTransition();

  const run = useCallback((query: string) => {
    startTransition(async () => {
      try {
        setError(null);
        setData(null);
        setShowSources(false);
        const res = await fetch("/api/dispatch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
          cache: "no-store",
        });
        const json = (await res.json()) as AskResponse & {
          error?: string | object;
          intent?: string;
        };
        if (!res.ok) {
          const errMsg =
            typeof json.error === "string"
              ? json.error
              : json.error
                ? JSON.stringify(json.error)
                : `HTTP ${res.status}`;
          setError(errMsg);
          setData(json);
          return;
        }
        setData(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Dispatch fehlgeschlagen");
      }
    });
  }, []);

  useEffect(() => {
    if (initial) run(initial);
    else {
      fetch("/api/memory/stats", { cache: "no-store" })
        .then((r) => r.json())
        .then((stats) => setData({ kind: "empty", query: "", stats }))
        .catch(() => undefined);
    }
  }, [initial, run]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const next = q.trim();
    router.replace(next ? `/?q=${encodeURIComponent(next)}` : "/");
    if (next) run(next);
  }

  const sources = data?.sources ?? data?.results ?? [];
  const stats = data?.stats;
  const sourceCount = data?.sourceCount ?? sources.length;

  return (
    <section className={compact ? "" : "rise"}>
      <form onSubmit={onSubmit} className="search-bar">
        <label className="sr-only" htmlFor="memory-q">
          Orchestrator steuern
        </label>
        <input
          id="memory-q"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder='z. B. „Was muss ich heute noch machen?“'
          autoFocus={autofocus}
          autoComplete="off"
        />
        <button type="submit" className="btn-primary" disabled={pending}>
          {pending ? "Orchestriere…" : "Fragen"}
        </button>
      </form>

      {stats ? (
        <p className="muted mono mt-3 mb-0 text-xs">
          Orchestrator · Projekt {stats.projectLabel ?? "—"} · {stats.chunks} Chunks
          {data?.kind === "ask" && data.mode ? ` · ${data.mode}` : null}
          {data && "intent" in data && (data as { intent?: string }).intent
            ? ` · intent ${(data as { intent?: string }).intent}`
            : null}
        </p>
      ) : null}

      {error ? <p className="text-danger mt-3">{error}</p> : null}

      {data?.kind === "ask" && data.answer ? (
        <article className="answer-panel mt-6 rise">
          <h2 className="section-title">Zusammenfassung</h2>
          <div className="answer-body">{data.answer}</div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <p className="mono muted m-0 text-xs">
              {data.model} · {sourceCount} Quellen
            </p>
            {sources.length > 0 ? (
              <button
                type="button"
                className="btn-ghost"
                style={{ padding: "0.4rem 0.75rem", fontSize: "0.85rem" }}
                onClick={() => setShowSources((v) => !v)}
                aria-expanded={showSources}
              >
                {showSources ? "Quellen ausblenden" : "Quellen einblenden"}
              </button>
            ) : null}
          </div>
        </article>
      ) : null}

      {showSources && sources.length > 0 ? (
        <div className="mt-6">
          <h2 className="mb-2 text-sm uppercase tracking-[0.16em] text-ink-soft">
            Quellen
          </h2>
          <div className="row-list">
            {sources.map((r) => (
              <div key={r.id} className="search-hit">
                <div>
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="font-medium">{r.title || r.role}</span>
                    <span className="mono muted text-xs">
                      {r.source} · {r.role}
                      {r.chat_id ? ` · ${r.chat_id.slice(0, 8)}` : ""}
                      {r.ingested_at
                        ? ` · ${new Date(r.ingested_at).toLocaleTimeString("de-DE")}`
                        : ""}
                    </span>
                  </div>
                  <p className="muted mt-2 mb-0 text-sm leading-relaxed">
                    {r.snippet}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {data?.kind === "search" && q.trim() && !pending ? (
        <div className="mt-6">
          <button
            type="button"
            className="btn-ghost"
            style={{ padding: "0.4rem 0.75rem", fontSize: "0.85rem" }}
            onClick={() => setShowSources((v) => !v)}
          >
            {showSources
              ? "Treffer ausblenden"
              : `${sources.length} Treffer einblenden`}
          </button>
          {showSources ? (
            <div className="row-list mt-4">
              {sources.length === 0 ? (
                <div>
                  <span className="muted">Keine Treffer</span>
                  <span />
                </div>
              ) : null}
              {sources.map((r) => (
                <div key={r.id} className="search-hit">
                  <div>
                    <div className="font-medium">{r.title || r.role}</div>
                    <p className="muted mt-2 mb-0 text-sm">{r.snippet}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
