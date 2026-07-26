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
          <p className="muted mt-4 mb-0 text-sm">
            <Link href="/platform/storage" className="underline underline-offset-2">
              Speicherverbrauch aller Memory-Stacks →
            </Link>
          </p>
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
        </>
      ) : (
        <p className="muted">Services werden abgefragt…</p>
      )}
    </section>
  );
}
