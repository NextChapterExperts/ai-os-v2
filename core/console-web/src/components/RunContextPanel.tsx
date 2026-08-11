"use client";

import { useEffect, useState } from "react";

type ContextChunk = {
  id?: string;
  role?: string;
  title?: string;
  source?: string;
  chat_id?: string;
  bodyPreview?: string;
  bodyLength?: number;
};

type RunContext = {
  runId?: string;
  tenantId?: string;
  handler?: string;
  createdAt?: string;
  routing?: {
    intent?: string;
    federated?: boolean;
    memoryBackend?: string;
    modelTier?: string;
    model?: string;
  };
  retrieval?: {
    question?: string;
    federatedQuery?: string | null;
    chunkCountTotal?: number;
    chunkCountUsed?: number;
    chunks?: ContextChunk[];
  };
  prompt?: {
    system?: string;
    user?: string;
    messages?: Array<{ role: string; content: string }>;
    contextCharCount?: number;
  };
  orchestratorContext?: Record<string, unknown>;
};

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="muted">{label}</span>
      <span className="mono text-sm">{value}</span>
    </div>
  );
}

export function RunContextPanel({ runId }: { runId: string }) {
  const [data, setData] = useState<RunContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`/api/runs/${encodeURIComponent(runId)}/context`, { cache: "no-store" })
      .then(async (res) => {
        const json = (await res.json()) as RunContext & { detail?: string; error?: string };
        if (!res.ok) {
          throw new Error(json.detail ?? json.error ?? `HTTP ${res.status}`);
        }
        if (!cancelled) setData(json);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (loading) return <p className="muted">Kontext wird geladen…</p>;
  if (error) return <p className="text-danger">{error}</p>;
  if (!data) return <p className="muted">Kein Kontext gefunden.</p>;

  const routing = data.routing ?? {};
  const retrieval = data.retrieval ?? {};
  const prompt = data.prompt ?? {};

  return (
    <div className="context-page">
      <section className="context-section">
        <h2 className="context-section-title">Routing & Modell</h2>
        <div className="row-list">
          <MetaRow label="Handler" value={data.handler ?? "—"} />
          <MetaRow label="Intent" value={routing.intent ?? "—"} />
          <MetaRow label="Modell" value={routing.model ?? "—"} />
          <MetaRow label="Tier" value={routing.modelTier ?? "local"} />
          <MetaRow label="Memory" value={routing.memoryBackend ?? "—"} />
          <MetaRow label="Federated" value={routing.federated ? "ja" : "nein"} />
          <MetaRow label="Tenant" value={data.tenantId ?? "—"} />
          {data.createdAt ? <MetaRow label="Erstellt" value={data.createdAt} /> : null}
        </div>
      </section>

      <section className="context-section">
        <h2 className="context-section-title">Retrieval</h2>
        <p className="muted m-0 text-sm">
          Frage: <span className="text-ink">{retrieval.question ?? "—"}</span>
        </p>
        {retrieval.federatedQuery ? (
          <p className="muted mt-2 mb-0 text-sm">
            Federated Query:{" "}
            <span className="mono text-ink">{retrieval.federatedQuery}</span>
          </p>
        ) : null}
        <p className="mono muted mt-3 mb-0 text-xs">
          {retrieval.chunkCountUsed ?? 0} von {retrieval.chunkCountTotal ?? 0} Chunks im Prompt ·{" "}
          {prompt.contextCharCount ?? 0} Zeichen Kontext
        </p>
        {(retrieval.chunks ?? []).length > 0 ? (
          <div className="row-list mt-4">
            {(retrieval.chunks ?? []).map((chunk, idx) => (
              <div key={`${chunk.id ?? "chunk"}-${idx}`} className="search-hit">
                <div>
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="font-medium">{chunk.title || chunk.role || "Chunk"}</span>
                    <span className="mono muted text-xs">
                      {chunk.source ?? "—"} · {chunk.role ?? "—"}
                      {chunk.bodyLength ? ` · ${chunk.bodyLength} Zeichen` : ""}
                    </span>
                  </div>
                  {chunk.bodyPreview ? (
                    <p className="muted mt-2 mb-0 text-sm leading-relaxed whitespace-pre-wrap">
                      {chunk.bodyPreview}
                    </p>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section className="context-section">
        <h2 className="context-section-title">System-Prompt</h2>
        <pre className="context-pre">{prompt.system ?? "—"}</pre>
      </section>

      <section className="context-section">
        <h2 className="context-section-title">User-Prompt (an Modell gesendet)</h2>
        <pre className="context-pre">{prompt.user ?? "—"}</pre>
      </section>

      {data.orchestratorContext ? (
        <section className="context-section">
          <h2 className="context-section-title">Orchestrator Context Bundle</h2>
          <p className="muted mt-0 mb-3 text-sm">
            Domain-, Task- und Policy-Slices für spätere Fachagenten / Cloud-Modelle.
          </p>
          <pre className="context-pre context-pre-json">
            {JSON.stringify(data.orchestratorContext, null, 2)}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
