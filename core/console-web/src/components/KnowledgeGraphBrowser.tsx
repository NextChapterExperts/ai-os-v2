"use client";

import { FormEvent, useCallback, useEffect, useState, useTransition } from "react";

type KgStats = {
  tenant_id: string;
  total_nodes: number;
  total_edges: number;
  nodes_by_type: Record<string, number>;
  edges_by_type: Record<string, number>;
};

type KgNodeSummary = {
  id: string;
  node_type: string;
  external_id: string;
  title: string;
  snippet: string;
  k_path: string | null;
};

type KgEdgeRef = {
  edge_type: string;
  node_id?: string;
  node_type?: string;
  external_id?: string;
  title?: string;
  to?: string;
  from?: string;
};

type KgSearchHit = KgNodeSummary & {
  edges_out: KgEdgeRef[];
  edges_in: KgEdgeRef[];
};

type KgNodeDetail = {
  id: string;
  node_type: string;
  external_id: string;
  payload: Record<string, unknown>;
  k_path: string | null;
  edges_out: KgEdgeRef[];
  edges_in: KgEdgeRef[];
};

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });
  const json = await res.json();
  if (!res.ok) throw new Error(typeof json.error === "string" ? json.error : JSON.stringify(json.error));
  return json as T;
}

function titleOf(payload: Record<string, unknown>, externalId: string): string {
  return String(payload.title ?? payload.name ?? externalId);
}

export function KnowledgeGraphBrowser() {
  const [stats, setStats] = useState<KgStats | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);

  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [nodesOfType, setNodesOfType] = useState<KgNodeSummary[] | null>(null);

  const [q, setQ] = useState("");
  const [searchHits, setSearchHits] = useState<KgSearchHit[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [selectedNode, setSelectedNode] = useState<KgNodeDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [pending, startTransition] = useTransition();

  const loadStats = useCallback(() => {
    startTransition(async () => {
      try {
        setStatsError(null);
        setStats(await getJson<KgStats>("/api/kg/stats"));
      } catch (err) {
        setStatsError(err instanceof Error ? err.message : "Stats fehlgeschlagen");
      }
    });
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const openType = useCallback((nodeType: string) => {
    setSelectedType(nodeType);
    setSelectedNode(null);
    setSearchHits(null);
    startTransition(async () => {
      try {
        const data = await getJson<{ results: KgNodeSummary[] }>(
          `/api/kg/nodes?node_type=${encodeURIComponent(nodeType)}`,
        );
        setNodesOfType(data.results);
      } catch (err) {
        setDetailError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
      }
    });
  }, []);

  const openNode = useCallback((id: string) => {
    startTransition(async () => {
      try {
        setDetailError(null);
        const node = await getJson<KgNodeDetail>(`/api/kg/resolve/${id}`);
        setSelectedNode(node);
      } catch (err) {
        setDetailError(err instanceof Error ? err.message : "Knoten nicht gefunden");
      }
    });
  }, []);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    setSelectedType(null);
    setNodesOfType(null);
    setSelectedNode(null);
    startTransition(async () => {
      try {
        setSearchError(null);
        const data = await getJson<{ results: KgSearchHit[] }>(
          `/api/kg/search?q=${encodeURIComponent(query)}`,
        );
        setSearchHits(data.results);
      } catch (err) {
        setSearchError(err instanceof Error ? err.message : "Suche fehlgeschlagen");
      }
    });
  }

  return (
    <section className="rise">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="section-title">Knowledge Graph</h1>
          <p className="muted m-0 max-w-xl">
            Speicherverwaltung des Company Brain — Knoten, Kanten, Herkunft je Eintrag.
          </p>
        </div>
        <button type="button" className="btn-ghost" onClick={loadStats} disabled={pending}>
          {pending ? "Lädt…" : "Aktualisieren"}
        </button>
      </div>

      {statsError ? <p className="text-danger">{statsError}</p> : null}

      {stats ? (
        <div className="mb-8 border-b border-line pb-6">
          <div className="mb-4 flex flex-wrap gap-6 text-sm">
            <div>
              <div className="muted text-xs uppercase tracking-wider">Knoten</div>
              <div className="font-display text-3xl text-signal">{stats.total_nodes}</div>
            </div>
            <div>
              <div className="muted text-xs uppercase tracking-wider">Kanten</div>
              <div className="font-display text-3xl text-signal">{stats.total_edges}</div>
            </div>
            <div>
              <div className="muted text-xs uppercase tracking-wider">Tenant</div>
              <div className="mono mt-1">{stats.tenant_id}</div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.nodes_by_type).map(([type, count]) => (
              <button
                key={type}
                type="button"
                className="badge"
                data-variant={selectedType === type ? "graph" : undefined}
                onClick={() => openType(type)}
              >
                {type} · {count}
              </button>
            ))}
          </div>
          <p className="muted mono mt-3 mb-0 text-xs">
            Kanten: {Object.entries(stats.edges_by_type).map(([t, n]) => `${t} (${n})`).join(" · ")}
          </p>
        </div>
      ) : !statsError ? (
        <p className="muted">Graph-Stats werden geladen…</p>
      ) : null}

      <form onSubmit={onSearch} className="search-bar mb-6">
        <label className="sr-only" htmlFor="kg-search-q">
          Graph durchsuchen
        </label>
        <input
          id="kg-search-q"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder='z. B. „Welche Policy gilt für consulting?“'
          autoComplete="off"
        />
        <button type="submit" className="btn-primary" disabled={pending}>
          Graph durchsuchen
        </button>
      </form>

      {searchError ? <p className="text-danger">{searchError}</p> : null}

      <div className="grid gap-8 md:grid-cols-2">
        <div>
          {searchHits ? (
            <>
              <h2 className="section-title text-lg">Suchtreffer ({searchHits.length})</h2>
              <div className="row-list">
                {searchHits.map((hit) => (
                  <div key={hit.id} className="search-hit" style={{ cursor: "pointer" }} onClick={() => openNode(hit.id)}>
                    <div>
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="badge" data-variant="graph">
                          {hit.node_type}
                        </span>
                        <span className="font-medium">{hit.title}</span>
                      </div>
                      {hit.snippet ? (
                        <p className="muted mt-1 mb-0 text-sm">{hit.snippet}</p>
                      ) : null}
                      {hit.edges_out.length + hit.edges_in.length > 0 ? (
                        <p className="mono muted mt-1 mb-0 text-xs">
                          {[...hit.edges_out, ...hit.edges_in]
                            .slice(0, 4)
                            .map((e) => `${e.edge_type} → ${e.external_id}`)
                            .join(" · ")}
                        </p>
                      ) : null}
                    </div>
                  </div>
                ))}
                {searchHits.length === 0 ? <p className="muted py-4">Keine Treffer.</p> : null}
              </div>
            </>
          ) : selectedType && nodesOfType ? (
            <>
              <h2 className="section-title text-lg">
                {selectedType} ({nodesOfType.length})
              </h2>
              <div className="row-list">
                {nodesOfType.map((n) => (
                  <div key={n.id} className="search-hit" style={{ cursor: "pointer" }} onClick={() => openNode(n.id)}>
                    <div>
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="font-medium">{n.title}</span>
                        <span className="mono muted text-xs">{n.external_id}</span>
                      </div>
                      {n.snippet ? <p className="muted mt-1 mb-0 text-sm">{n.snippet}</p> : null}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="muted">Knoten-Typ oben wählen oder den Graph durchsuchen.</p>
          )}
        </div>

        <div>
          <h2 className="section-title text-lg">Detail</h2>
          {detailError ? <p className="text-danger">{detailError}</p> : null}
          {selectedNode ? (
            <div>
              <div className="mb-2 flex flex-wrap items-baseline gap-2">
                <span className="badge" data-variant="graph">
                  {selectedNode.node_type}
                </span>
                <span className="font-medium">
                  {titleOf(selectedNode.payload, selectedNode.external_id)}
                </span>
              </div>
              <p className="mono muted mb-3 text-xs">{selectedNode.external_id}</p>
              {selectedNode.k_path ? (
                <p className="mono muted mb-3 text-xs">K-Pfad: {selectedNode.k_path}</p>
              ) : null}

              <h3 className="mb-1 text-sm font-medium">Ausgehende Kanten</h3>
              <ul className="mb-4 list-none p-0">
                {selectedNode.edges_out.length === 0 ? (
                  <li className="muted text-sm">—</li>
                ) : (
                  selectedNode.edges_out.map((e, i) => (
                    <li key={i} className="mono text-sm">
                      {e.edge_type} →{" "}
                      <button
                        type="button"
                        className="cursor-pointer border-none bg-transparent p-0 text-signal underline"
                        onClick={() => e.to && openNode(e.to)}
                      >
                        {e.title ?? e.external_id ?? e.to}
                      </button>
                    </li>
                  ))
                )}
              </ul>

              <h3 className="mb-1 text-sm font-medium">Eingehende Kanten</h3>
              <ul className="mb-4 list-none p-0">
                {selectedNode.edges_in.length === 0 ? (
                  <li className="muted text-sm">—</li>
                ) : (
                  selectedNode.edges_in.map((e, i) => (
                    <li key={i} className="mono text-sm">
                      {e.edge_type} ←{" "}
                      <button
                        type="button"
                        className="cursor-pointer border-none bg-transparent p-0 text-signal underline"
                        onClick={() => e.from && openNode(e.from)}
                      >
                        {e.title ?? e.external_id ?? e.from}
                      </button>
                    </li>
                  ))
                )}
              </ul>

              <details>
                <summary className="cursor-pointer text-sm">Rohdaten (payload)</summary>
                <pre className="mono mt-2 whitespace-pre-wrap text-xs">
                  {JSON.stringify(selectedNode.payload, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <p className="muted">Knoten aus der Liste links auswählen.</p>
          )}
        </div>
      </div>
    </section>
  );
}
