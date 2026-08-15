"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import type { PlatformHealthResponse } from "@/lib/types";
import { StatusDot } from "./StatusDot";

type MemStats = {
  chunks: number;
  chats: number;
  trackedFiles: number;
  lastRunAt: string | null;
  dbPath: string;
};

export function PlatformHealthPanel() {
  const [data, setData] = useState<PlatformHealthResponse | null>(null);
  const [mem, setMem] = useState<MemStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    setPending(true);
    try {
      setError(null);
      const ts = Date.now();
      const [healthRes, memRes] = await Promise.all([
        fetch(`/api/platform/health?_t=${ts}`, { cache: "no-store" }),
        fetch(`/api/memory/stats?_t=${ts}`, { cache: "no-store" }),
      ]);
      if (!healthRes.ok) throw new Error(`HTTP ${healthRes.status}`);
      setData((await healthRes.json()) as PlatformHealthResponse);
      if (memRes.ok) setMem((await memRes.json()) as MemStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Probe fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = window.setInterval(load, 15000);
    return () => window.clearInterval(id);
  }, [load]);

  return (
    <section className="rise rise-delay-1">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="section-title">Plattform</h1>
          <p className="muted m-0 max-w-xl">
            Live-Health der Phase-0-Infra und Cursor-Capture-Status.
          </p>
        </div>
        <button type="button" className="btn-ghost" onClick={load} disabled={pending}>
          {pending ? "Prüfe…" : "Erneut prüfen"}
        </button>
      </div>

      {error ? <p className="text-danger m-0 mb-4">{error}</p> : null}

      {mem ? (
        <div className="mb-10 border-b border-line pb-8">
          <h2 className="section-title">Cursor → Gedächtnis</h2>
          <div className="row-list">
            <div>
              <span>Chunks</span>
              <span className="mono">{mem.chunks}</span>
            </div>
            <div>
              <span>Chats</span>
              <span className="mono">{mem.chats}</span>
            </div>
            <div>
              <span>Dateien getrackt</span>
              <span className="mono">{mem.trackedFiles}</span>
            </div>
            <div>
              <span>Letzter Capture</span>
              <span className="mono">
                {mem.lastRunAt
                  ? new Date(mem.lastRunAt).toLocaleString("de-DE")
                  : "—"}
              </span>
            </div>
            <div>
              <span>DB</span>
              <span className="mono text-xs">{mem.dbPath}</span>
            </div>
          </div>
          <div className="muted mt-4 mb-0 flex flex-wrap gap-4 text-sm">
            <Link href="/platform/storage" className="underline underline-offset-2">
              Speicherverbrauch aller Memory-Stacks →
            </Link>
            <Link href="/platform/vms" className="underline underline-offset-2 text-signal font-semibold">
              Kunden-VMs & Google Cloud Hosting (GCP) →
            </Link>
          </div>
        </div>
      ) : null}

      {data ? (
        <>
          <div className="mb-8 flex flex-wrap gap-6 text-sm">
            <div>
              <div className="muted text-xs uppercase tracking-wider">Online</div>
              <div className="font-display text-3xl text-signal">{data.summary.ok}</div>
            </div>
            <div>
              <div className="muted text-xs uppercase tracking-wider">Offline</div>
              <div className="font-display text-3xl text-danger">{data.summary.down}</div>
            </div>
            <div>
              <div className="muted text-xs uppercase tracking-wider">Modus</div>
              <div className="mono mt-1">{data.computeMode}</div>
            </div>
            <div>
              <div className="muted text-xs uppercase tracking-wider">Geprüft</div>
              <div className="mono mt-1">
                {new Date(data.checkedAt).toLocaleTimeString("de-DE")}
              </div>
            </div>
          </div>

          <div className="row-list">
            {data.items.map((item) => (
              <div key={item.id}>
                <div className="flex items-center gap-3">
                  <StatusDot status={item.status} />
                  <div>
                    <div className="font-medium">{item.label}</div>
                    <div className="mono muted text-xs">{item.url}</div>
                  </div>
                </div>
                <div className="text-right text-sm">
                  <div className={item.status === "ok" ? "text-signal" : "text-danger"}>
                    {item.status === "ok" ? "ok" : "down"}
                  </div>
                  <div className="mono muted text-xs">
                    {item.latencyMs != null ? `${item.latencyMs} ms` : "—"} · {item.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Release Changelog & Revisionssicherheit */}
          <div className="mt-10 rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-4 mb-4">
              <div>
                <h2 className="text-base font-bold text-ink m-0">Plattform Release-Changelog & Audit</h2>
                <p className="text-xs muted m-0 mt-1">Revisionssicherer Änderungsverlauf zur vorherigen Version.</p>
              </div>
              <span className="badge" data-variant="graph">v1.0.0-core-appliance</span>
            </div>

            <div className="space-y-4">
              <div className="border border-line/60 rounded-xl p-4 bg-paper/30">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="font-bold text-signal">Release v1.0.0</span>
                  <span className="muted">2026-08-15 · Commit bd2a74c</span>
                </div>
                <p className="text-xs font-semibold text-ink mb-2">
                  AI-OS Core Platform Appliance Initial Release
                </p>
                <ul className="text-xs text-ink-soft space-y-1 pl-4 list-disc">
                  <li>Autarkes Distributions-Repository <code>virgi-platform-dist</code></li>
                  <li>5-Schichten-Memory-Modell (L1 Working Memory bis L5 Enterprise Core)</li>
                  <li>Hybrid Graph-RAG mit Reciprocal Rank Fusion & Wissensgraph-Traversal</li>
                  <li>Unternehmensprofil-Verwaltung (<code>/company</code>) mit Blanko-Formular für Neukunden</li>
                  <li>Sovereign Multi-Stage Dockerfile & Docker Compose Stack</li>
                  <li>CLI-Management Toolbox (Suche, Memory-Status, Batch-Ingest, Profil)</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      ) : (
        <p className="muted">Services werden abgefragt…</p>
      )}
    </section>
  );
}
