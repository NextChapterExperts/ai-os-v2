"use client";

import { FormEvent, useCallback, useState, useTransition } from "react";

type UnifiedHit = {
  id: string;
  score: number;
  source_type: "curated" | "raw-file";
  title: string;
  snippet: string;
  project_slug?: string | null;
  source_path?: string | null;
  collection?: string;
};

type SearchResponse = {
  kind: string;
  query: string;
  sources?: UnifiedHit[];
  sourceCount?: number;
  curatedCount?: number;
  rawFileCount?: number;
  error?: string | object;
};

const SOURCE_LABEL: Record<UnifiedHit["source_type"], string> = {
  curated: "Freigegeben",
  "raw-file": "Rohdatei",
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
            params: { force_intent: "unified_search", query, limit: 10 },
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

  const sources = data?.sources ?? [];
  const curatedCount = data?.curatedCount ?? sources.filter((s) => s.source_type === "curated").length;
  const rawFileCount = data?.rawFileCount ?? sources.filter((s) => s.source_type === "raw-file").length;

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
          {sources.length} Treffer · {curatedCount} freigegeben (Company Brain) ·{" "}
          {rawFileCount} Rohdateien (Projekte/active)
        </p>
      ) : null}

      {error ? <p className="text-danger mt-3">{error}</p> : null}

      {sources.length > 0 ? (
        <div className="row-list mt-6">
          {sources.map((hit) => (
            <div key={hit.id} className="search-hit">
              <div>
                <div className="flex flex-wrap items-baseline gap-2">
                  <span
                    className="badge"
                    data-variant={hit.source_type === "curated" ? "curated" : "raw"}
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
