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
          <div className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className="font-display text-2xl text-signal">{data.active_label}</span>
            <span className="mono text-sm text-ink-soft">{data.active_model}</span>
          </div>
          {data.active_description ? (
            <p className="muted mt-2 mb-0 text-sm">{data.active_description}</p>
          ) : null}
          {data.updated_at ? (
            <p className="muted mt-2 mb-0 text-xs">
              Geändert: {new Date(data.updated_at).toLocaleString("de-DE")}
            </p>
          ) : (
            <p className="muted mt-2 mb-0 text-xs">
              Standard aus Konfiguration ({data.config_default_mode})
            </p>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            {data.modes.map((mode) => {
              const active = mode.id === data.active_mode;
              return (
                <button
                  key={mode.id}
                  type="button"
                  className={active ? "btn-primary text-sm" : "btn-secondary text-sm"}
                  onClick={() => selectMode(mode.id)}
                  disabled={pending || active}
                  title={mode.description}
                >
                  {mode.label}
                </button>
              );
            })}
          </div>
        </>
      ) : (
        !error && <p className="muted mt-4 mb-0 text-sm">Modellstatus wird geladen…</p>
      )}
    </section>
  );
}
