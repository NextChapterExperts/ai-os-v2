"use client";

import { useState } from "react";

export function GitPushButton() {
  const [loading, setLoading] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showLogModal, setShowLogModal] = useState(false);

  const handlePush = async () => {
    setLoading(true);
    setOutput(null);
    setError(null);

    try {
      const res = await fetch("/api/git-push", { method: "POST" });
      const data = await res.json();

      if (res.ok && data.ok) {
        setOutput(data.output);
        setShowLogModal(true);
      } else {
        setError(data.error || "Fehler beim Git-Push");
        if (data.output) setOutput(data.output);
        setShowLogModal(true);
      }
    } catch (err: any) {
      setError(err.message || "Netzwerkfehler");
      setShowLogModal(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={handlePush}
        disabled={loading}
        className="btn-ghost text-xs font-mono py-1 px-3 flex items-center gap-2 transition-all cursor-pointer"
        title="Führt git-push-active.sh für alle 9 aktiven Projekte aus"
      >
        {loading ? (
          <>
            <span className="h-2.5 w-2.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
            <span>Pushe Repos…</span>
          </>
        ) : (
          <>
            <svg className="h-3.5 w-3.5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Git Push</span>
          </>
        )}
      </button>

      {/* Log Output Modal */}
      {showLogModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="relative w-full max-w-2xl border border-line bg-paper p-6 shadow-2xl text-ink font-sans">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${error ? "bg-danger" : "bg-signal-bright"}`} />
                <h3 className="section-title text-base m-0">
                  {error ? "Git-Push Status" : "Git-Push Erfolgreich"}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowLogModal(false)}
                className="btn-ghost py-1 px-2 text-xs"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 max-h-96 overflow-y-auto border border-line bg-paper-2 p-4 font-mono text-xs text-ink leading-relaxed">
              {error && (
                <div className="mb-3 text-danger font-semibold">
                  Fehler: {error}
                </div>
              )}
              {output ? (
                <pre className="whitespace-pre-wrap m-0">{output}</pre>
              ) : (
                <p className="muted m-0">Keine Konsolenausgabe vorhanden.</p>
              )}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={() => setShowLogModal(false)}
                className="btn-primary text-xs py-1.5 px-4"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
