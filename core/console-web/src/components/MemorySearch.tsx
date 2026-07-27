"use client";

import Link from "next/link";
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
  runId?: string;
  hasContext?: boolean;
  federated?: boolean;
  memoryBackend?: string;
  error?: string;
  stats?: Stats;
};

const STANDARD_PROMPTS = [
  { label: "— Standard-Abfrage wählen —", value: "" },
  { label: "Was ist noch offen?", value: "Was ist noch offen?" },
  { label: "Was steht noch aus?", value: "Was steht noch aus?" },
  { label: "Was liegt an?", value: "Was liegt an?" },
  { label: "Was müsste gemacht werden?", value: "Was müsste gemacht werden?" },
  { label: "Was sind wichtige Punkte für heute?", value: "Was sind wichtige Punkte für heute?" },
  { label: "Wie ist der Stand zu welchem Projekt?", value: "Wie ist der Stand zu welchem Projekt?" },
  { label: "Gibt es offene Punkte aus Meetings?", value: "Gibt es offene Punkte aus Meetings?" },
  { label: "ich suche nach : Agenda", value: "ich suche nach : Agenda" },
] as const;

function renderFormattedAnswer(text: string) {
  const lines = text.split("\n");
  return lines.map((line, lineIdx) => {
    const tokens: React.ReactNode[] = [];
    let lastIdx = 0;
    const regex = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*/g;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(line)) !== null) {
      if (match.index > lastIdx) {
        tokens.push(line.slice(lastIdx, match.index));
      }
      if (match[1] !== undefined && match[2] !== undefined) {
        const label = match[1];
        const href = match[2];
        tokens.push(
          <Link
            key={`${lineIdx}-${match.index}`}
            href={href}
            className="text-signal hover:text-signal-bright underline font-semibold transition-colors"
          >
            {label}
          </Link>
        );
      } else if (match[3] !== undefined) {
        tokens.push(
          <strong key={`${lineIdx}-${match.index}`} className="font-semibold text-ink">
            {match[3]}
          </strong>
        );
      }
      lastIdx = regex.lastIndex;
    }

    if (lastIdx < line.length) {
      tokens.push(line.slice(lastIdx));
    }

    return (
      <div key={lineIdx} className={line.trim() === "" ? "h-2" : ""}>
        {tokens}
      </div>
    );
  });
}

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
        const activeUserId = typeof window !== "undefined" ? localStorage.getItem("aios_active_user_id") ?? "person:peter-alexander" : "person:peter-alexander";
        const res = await fetch("/api/dispatch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, params: { user_id: activeUserId } }),
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
        if (json.answer && typeof window !== "undefined") {
          try {
            sessionStorage.setItem("aios_last_summary", JSON.stringify({ q: query, data: json }));
          } catch (e) {}
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Dispatch fehlgeschlagen");
      }
    });
  }, []);

  useEffect(() => {
    if (initial) {
      run(initial);
    } else {
      if (typeof window !== "undefined") {
        try {
          const saved = sessionStorage.getItem("aios_last_summary");
          if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed && parsed.data && parsed.data.answer) {
              setQ(parsed.q || "");
              setData(parsed.data);
              return;
            }
          }
        } catch (e) {}
      }
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

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="muted text-xs">Standard-Abfragen:</span>
        <select
          aria-label="Standard-Abfrage wählen"
          className="bg-card text-ink border border-line rounded-lg px-2.5 py-1.5 text-xs font-sans focus:outline-none focus:border-signal transition-colors cursor-pointer"
          onChange={(e) => {
            const val = e.target.value;
            if (val) {
              setQ(val);
              router.replace(`/?q=${encodeURIComponent(val)}`);
              run(val);
            }
          }}
          defaultValue=""
        >
          {STANDARD_PROMPTS.map((p) => (
            <option key={p.label} value={p.value} className="bg-card text-ink">
              {p.label}
            </option>
          ))}
        </select>
      </div>

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
          <div className="answer-body">{renderFormattedAnswer(data.answer)}</div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <p className="mono muted m-0 text-xs">
              {data.model} · {sourceCount} Quellen
              {data.memoryBackend ? ` · ${data.memoryBackend}` : null}
              {data.federated ? " · federated" : null}
            </p>
            {data.runId && data.hasContext !== false ? (
              <Link
                href={`/context/${data.runId}`}
                className="btn-ghost"
                style={{ padding: "0.4rem 0.75rem", fontSize: "0.85rem" }}
              >
                LLM-Kontext anzeigen
              </Link>
            ) : null}
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
