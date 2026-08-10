"use client";

import { useCallback, useEffect, useState } from "react";

type ComputeModeEntry = {
  id: string;
  default_model: string;
  label: string;
  description: string;
  is_active: boolean;
  is_config_default: boolean;
};

type ComputeModeResponse = {
  active_mode: string;
  active_model: string;
  active_label: string;
  active_description: string;
  config_default_mode: string;
  updated_at: string | null;
  modes: ComputeModeEntry[];
  error?: string;
};

export function ComputeModePanel() {
  const [data, setData] = useState<ComputeModeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const res = await fetch(`/api/compute/mode?_t=${Date.now()}`, { cache: "no-store" });
      const json = (await res.json()) as ComputeModeResponse;
      if (!res.ok) {
        throw new Error(json.error ?? `HTTP ${res.status}`);
      }
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Modus laden fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function selectMode(mode: string) {
    if (pending || data?.active_mode === mode) return;
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/compute/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      const json = (await res.json()) as ComputeModeResponse;
      if (!res.ok) {
        throw new Error(json.error ?? `HTTP ${res.status}`);
      }
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Moduswechsel fehlgeschlagen");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="compute-mode-panel card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">Inference</p>
          <h2 className="section-title m-0 text-base">Aktives Modell</h2>
        </div>
        <button type="button" className="btn-ghost text-sm" onClick={load} disabled={pending}>
          {pending ? "…" : "Aktualisieren"}
        </button>
      </div>

      {error ? <p className="text-danger mt-3 mb-0 text-sm">{error}</p> : null}

      {data ? (
        <>
          <div className="mt-4 flex flex-col gap-3">
            <label htmlFor="compute-mode-select" className="sr-only">
              Modell auswählen
            </label>
            <div className="relative">
              <select
                id="compute-mode-select"
                className="w-full appearance-none rounded-lg border border-slate-700 bg-slate-900/90 px-4 py-2.5 pr-10 text-sm font-medium text-slate-100 shadow-sm transition-colors hover:border-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                value={data.active_mode}
                onChange={(e) => selectMode(e.target.value)}
                disabled={pending}
              >
                {data.modes.map((mode) => (
                  <option key={mode.id} value={mode.id} className="bg-slate-900 text-slate-100 py-1">
                    {mode.label} {mode.id === data.active_mode ? " (Aktiv)" : ""}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                </svg>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-display text-lg font-semibold text-emerald-400">{data.active_label}</span>
                <span className="mono rounded bg-slate-800/80 px-2 py-0.5 text-xs text-slate-300">{data.active_model}</span>
              </div>
              {data.active_description ? (
                <p className="muted mt-1.5 mb-0 text-xs leading-relaxed text-slate-400">{data.active_description}</p>
              ) : null}
              {data.updated_at ? (
                <p className="muted mt-2 mb-0 text-[11px] text-slate-500">
                  Geändert: {new Date(data.updated_at).toLocaleString("de-DE")}
                </p>
              ) : (
                <p className="muted mt-2 mb-0 text-[11px] text-slate-500">
                  Standard aus Konfiguration ({data.config_default_mode})
                </p>
              )}
            </div>
          </div>
        </>
      ) : (
        !error && <p className="muted mt-4 mb-0 text-sm">Modellstatus wird geladen…</p>
      )}
    </section>
  );
}
