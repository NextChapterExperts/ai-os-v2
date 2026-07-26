"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

type MemoryStack = {
  id: string;
  label: string;
  bytes: number;
  path?: string;
  detail?: string;
  status?: string;
  meta?: Record<string, unknown>;
};

type StorageResponse = {
  ok?: boolean;
  checkedAt?: string;
  vm?: {
    totalBytes: number;
    usedBytes: number;
    freeBytes: number;
    usedPercent: number;
  };
  memoryStacksTotalBytes?: number;
  stacks?: MemoryStack[];
  budget?: {
    vmTotalGb: number;
    memoryStacksGb: number;
    warningPercent: number;
    criticalPercent: number;
  };
  error?: string;
};

function fmtBytes(n: number): string {
  if (n >= 1024 ** 3) return `${(n / 1024 ** 3).toFixed(2)} GB`;
  if (n >= 1024 ** 2) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  if (n >= 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${n} B`;
}

function barColor(percent: number, warn: number, crit: number): string {
  if (percent >= crit) return "bg-red-500";
  if (percent >= warn) return "bg-amber-500";
  return "bg-emerald-500";
}

export function MemoryStoragePanel() {
  const [data, setData] = useState<StorageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const res = await fetch(`/api/memory/storage?_t=${Date.now()}`, { cache: "no-store" });
      const json = (await res.json()) as StorageResponse;
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
    const id = window.setInterval(load, 30000);
    return () => window.clearInterval(id);
  }, [load]);

  const vm = data?.vm;
  const stacks = data?.stacks ?? [];
  const memTotal = data?.memoryStacksTotalBytes ?? 0;
  const vmUsedPct = vm?.usedPercent ?? 0;
  const warn = data?.budget?.warningPercent ?? 70;
  const crit = data?.budget?.criticalPercent ?? 85;
  const maxStack = Math.max(...stacks.map((s) => s.bytes), 1);

  return (
    <section className="rise">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Memory-Speicher</h2>
          <p className="muted mb-0 text-sm">
            VM-Budget (~300 GB) · alle Memory-Stacks (SQLite, Qdrant, Letta, State, Inbox)
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/platform/capture" className="btn-ghost text-sm">
            Chat-Erfassung
          </Link>
          <button type="button" className="btn-secondary" onClick={load} disabled={pending}>
            {pending ? "Aktualisiere…" : "Aktualisieren"}
          </button>
        </div>
      </div>

      {error ? <p className="text-danger mt-4">{error}</p> : null}

      {data && vm ? (
        <div className="mt-6 space-y-6">
          <div className="card p-5">
            <h3 className="text-sm font-medium">VM Festplatte</h3>
            <div className="mt-3 flex flex-wrap items-baseline gap-4">
              <span className="mono text-2xl font-semibold">{vmUsedPct}%</span>
              <span className="muted text-sm">
                {fmtBytes(vm.usedBytes)} belegt · {fmtBytes(vm.freeBytes)} frei ·{" "}
                {fmtBytes(vm.totalBytes)} gesamt
              </span>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-line">
              <div
                className={`h-full transition-all ${barColor(vmUsedPct, warn, crit)}`}
                style={{ width: `${Math.min(vmUsedPct, 100)}%` }}
              />
            </div>
            {vmUsedPct >= warn ? (
              <p className="muted mt-2 mb-0 text-xs">
                {vmUsedPct >= crit
                  ? "Kritisch — Speicher freimachen oder Retention prüfen (L1-Curator rolling)."
                  : "Warnung — Memory-Stacks und Qdrant-Volumen im Blick behalten."}
              </p>
            ) : null}
          </div>

          <div className="card p-5">
            <h3 className="text-sm font-medium">Memory-Stacks gesamt</h3>
            <p className="mono mt-2 text-xl font-semibold">{fmtBytes(memTotal)}</p>
            <p className="muted mt-1 mb-0 text-xs">
              Stand: {data.checkedAt ? new Date(data.checkedAt).toLocaleString("de-DE") : "—"}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {stacks.map((stack) => {
              const pct = memTotal > 0 ? (stack.bytes / memTotal) * 100 : 0;
              const barW = stack.bytes > 0 ? (stack.bytes / maxStack) * 100 : 0;
              return (
                <div key={stack.id} className="card p-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-medium">{stack.label}</h3>
                    <span
                      className="mono text-xs"
                      data-status={stack.status === "missing" ? "down" : "ok"}
                    >
                      {stack.status ?? "ok"}
                    </span>
                  </div>
                  <p className="mono mt-2 text-lg font-semibold">{fmtBytes(stack.bytes)}</p>
                  {stack.detail ? (
                    <p className="muted mt-1 text-xs">{stack.detail}</p>
                  ) : null}
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line">
                    <div
                      className="h-full bg-accent"
                      style={{ width: `${barW}%` }}
                      title={`${pct.toFixed(1)}% der Memory-Stacks`}
                    />
                  </div>
                  {stack.path ? (
                    <p className="mono muted mt-2 mb-0 truncate text-[10px]" title={stack.path}>
                      {stack.path}
                    </p>
                  ) : null}
                  {stack.meta && stack.id === "sqlite_episodic" && stack.meta.sources ? (
                    <ul className="mt-3 space-y-0.5 text-xs">
                      {Object.entries(stack.meta.sources as Record<string, number>).map(
                        ([src, n]) => (
                          <li key={src} className="flex justify-between gap-2">
                            <span>{src}</span>
                            <span className="mono">{n}</span>
                          </li>
                        ),
                      )}
                    </ul>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </section>
  );
}
