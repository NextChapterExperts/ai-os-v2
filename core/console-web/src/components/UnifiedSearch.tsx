"use client";

import Link from "next/link";
import { FormEvent, useCallback, useState, useTransition } from "react";

type UnifiedHit = {
  id: string;
  score: number;
  source_type: "graph" | "curated" | "raw-file" | "episodic";
  title: string;
  snippet: string;
  project_slug?: string | null;
  source_path?: string | null;
  collection?: string;
  relations?: string[];
};

type SearchResponse = {
  kind: string;
  query: string;
  answer?: string;
  sources?: UnifiedHit[];
  sourceCount?: number;
  curatedCount?: number;
  rawFileCount?: number;
  graphCount?: number;
  episodicCount?: number;
  error?: string | object;
  result?: {
    sources?: UnifiedHit[];
    answer?: string;
    sourceCount?: number;
    curatedCount?: number;
    rawFileCount?: number;
    graphCount?: number;
    episodicCount?: number;
  };
};

const SOURCE_LABEL: Record<UnifiedHit["source_type"], string> = {
  graph: "Graph (gesichert)",
  curated: "Freigegeben",
  "raw-file": "Rohdatei",
  episodic: "Cursor-Chat (episodisch)",
};

export function UnifiedSearch() {
  const [q, setQ] = useState("");
  const [data, setData] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const run = useCallback((query: string) => {
    startTransition(async () => {
      try {
        setError(null);
        const res = await fetch("/api/dispatch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            params: { force_intent: "unified_search", query, intent_text: query, limit: 12 },
          }),
          cache: "no-store",
        });
        const json = (await res.json()) as SearchResponse;
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
        setError(err instanceof Error ? err.message : "Suche fehlgeschlagen");
      }
    });
  }, []);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const next = q.trim();
    if (next) run(next);
  }

  const sources = data?.sources ?? data?.result?.sources ?? [];
  const answer = data?.answer ?? data?.result?.answer;
  const graphCount = data?.graphCount ?? data?.result?.graphCount ?? sources.filter((s) => s.source_type === "graph").length;
  const curatedCount = data?.curatedCount ?? data?.result?.curatedCount ?? sources.filter((s) => s.source_type === "curated").length;
  const rawFileCount = data?.rawFileCount ?? data?.result?.rawFileCount ?? sources.filter((s) => s.source_type === "raw-file").length;
  const episodicCount =
    data?.episodicCount ?? data?.result?.episodicCount ?? sources.filter((s) => s.source_type === "episodic").length;

  return (
    <section className="rise">
      <form onSubmit={onSubmit} className="search-bar">
        <label className="sr-only" htmlFor="unified-search-q">
          Alles durchsuchen
        </label>
        <input
          id="unified-search-q"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder='z. B. „WAQAM Engine Berechnung“ oder „RedRays iFlow Parser“'
          autoFocus
          autoComplete="off"
        />
        <button type="submit" className="btn-primary" disabled={pending}>
          {pending ? "Suche…" : "Suchen"}
        </button>
      </form>

      {data ? (
        <p className="muted mono mt-3 mb-0 text-xs">
          {sources.length} Treffer · {graphCount} aus dem Graph (gesichert) ·{" "}
          {curatedCount} freigegeben (Company Brain) · {rawFileCount} Rohdateien (Projekte/active) ·{" "}
          {episodicCount} aus Cursor-Chats (episodisch)
        </p>
      ) : null}

      {error ? <p className="text-danger mt-3">{error}</p> : null}

      {answer ? (
        <article className="answer-panel mt-6 rise">
          <h2 className="section-title">Zusammenfassung</h2>
          <div className="answer-body whitespace-pre-wrap leading-relaxed">{answer}</div>
        </article>
      ) : null}

      {sources.length > 0 ? (
        <div className="row-list mt-6">
          {sources.map((hit) => (
            <div key={hit.id} className="search-hit">
              <div>
                <div className="flex flex-wrap items-baseline gap-2">
                  <span
                    className="badge"
                    data-variant={
                      hit.source_type === "graph"
                        ? "graph"
                        : hit.source_type === "curated"
                          ? "curated"
                          : hit.source_type === "episodic"
                            ? "episodic"
                            : "raw"
                    }
                  >
                    {SOURCE_LABEL[hit.source_type]}
                  </span>
                  <span className="font-medium">{hit.title}</span>
                  <span className="mono muted text-xs">
                    Score {hit.score.toFixed(2)}
                    {hit.project_slug ? ` · ${hit.project_slug}` : ""}
                  </span>
                </div>
                <p className="muted mt-2 mb-0 text-sm leading-relaxed">{hit.snippet}</p>
                {hit.source_path ? (
                  <p className="mono muted mt-1 mb-0 text-xs">{hit.source_path}</p>
                ) : null}
                {hit.relations && hit.relations.length > 0 ? (
                  <p className="mono muted mt-1 mb-0 text-xs">
                    {hit.relations.join(" · ")}
                  </p>
                ) : null}
                {hit.source_type === "graph" ? (
                  <Link
                    href={`/platform/kg?node=${hit.id}`}
                    className="mono mt-1 inline-block text-xs text-signal underline"
                  >
                    Im Graph öffnen →
                  </Link>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {data && !pending && sources.length === 0 && !error ? (
        <p className="muted mt-6">Keine Treffer.</p>
      ) : null}
    </section>
  );
}
