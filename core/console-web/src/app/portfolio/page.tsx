"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { type ProjectSummary } from "@/lib/portfolio-db";

export default function PortfolioPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>("all");

  useEffect(() => {
    fetch("/api/portfolio")
      .then((res) => res.json())
      .then((data) => {
        setProjects(data.projects || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load portfolio data", err);
        setLoading(false);
      });
  }, []);

  const filteredProjects = projects.filter((p) => {
    if (selectedFilter === "all") return true;
    if (selectedFilter === "prio1") return p.priority === "prio1";
    if (selectedFilter === "prio2_3") return p.priority === "prio2" || p.priority === "prio3";
    if (selectedFilter === "continuous") return p.priority === "continuous";
    return true;
  });

  const prio1Project = projects.find((p) => p.priority === "prio1");

  return (
    <div className="rise pt-6">
      {/* Top Header */}
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
        <div>
          <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">
            Datenbank-Portfolio & Dokument-Direktabsprung
          </p>
          <h1 className="section-title m-0">Projekte & Meilensteine</h1>
          <p className="muted mt-1 mb-0 max-w-2xl text-sm">
            Dynamisch aus der AI-OS Datenbank geladen · Direkte Verlinkung zu allen Dokumenten & Artefakten
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/" className="btn-ghost">
            ← Zurück zum Lagebild
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6 flex flex-wrap items-center gap-2 border-b border-line pb-4 text-xs">
        <span className="mono text-ink-soft mr-2 font-semibold">Filter:</span>
        <button
          type="button"
          onClick={() => setSelectedFilter("all")}
          className={`btn-ghost text-xs ${selectedFilter === "all" ? "data-[active=true]:true font-bold" : ""}`}
          data-active={selectedFilter === "all"}
        >
          Alle 10 Projekte ({projects.length})
        </button>
        <button
          type="button"
          onClick={() => setSelectedFilter("prio1")}
          className={`btn-ghost text-xs ${selectedFilter === "prio1" ? "data-[active=true]:true font-bold" : ""}`}
          data-active={selectedFilter === "prio1"}
        >
          🔴 Höchste Priorität (Prio 1)
        </button>
        <button
          type="button"
          onClick={() => setSelectedFilter("prio2_3")}
          className={`btn-ghost text-xs ${selectedFilter === "prio2_3" ? "data-[active=true]:true font-bold" : ""}`}
          data-active={selectedFilter === "prio2_3"}
        >
          📅 Prio 2 & 3
        </button>
        <button
          type="button"
          onClick={() => setSelectedFilter("continuous")}
          className={`btn-ghost text-xs ${selectedFilter === "continuous" ? "data-[active=true]:true font-bold" : ""}`}
          data-active={selectedFilter === "continuous"}
        >
          ♾️ Continuous Engine
        </button>
      </div>

      {loading ? (
        <div className="p-8 text-center muted">Lade Projektdaten aus der Datenbank…</div>
      ) : (
        <>
          {/* Spotlight Box for Prio 1 if selected/all */}
          {prio1Project && (selectedFilter === "all" || selectedFilter === "prio1") && (
            <section className="rise rise-delay-1 mb-8 border border-line bg-paper-2/40 p-6">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="badge" data-variant="raw">
                      🔴 HÖCHSTE PRIORITÄT (Prio 1)
                    </span>
                    <span className="mono text-xs text-ink font-bold">
                      {prio1Project.title}
                    </span>
                  </div>
                  <h2 className="section-title mt-2 mb-0">
                    Ziel-Go-Live: {prio1Project.deadline} (Studenten-Start)
                  </h2>
                  <p className="muted mt-1 mb-0 text-sm">
                    {prio1Project.description}
                  </p>
                </div>
                <div className="text-right">
                  <span className="badge" data-variant="graph">
                    {prio1Project.status}
                  </span>
                </div>
              </div>

              {/* Direct Document Jump Links for Prio 1 */}
              <div className="mt-5">
                <h3 className="mono text-xs uppercase tracking-wider text-ink-soft mb-2 font-semibold">
                  📄 Dokumente & Artefakte (Direktabsprung):
                </h3>
                <div className="flex flex-wrap gap-2">
                  {prio1Project.documents.map((doc) => (
                    <a
                      key={doc.fileUri}
                      href={doc.fileUri}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-ghost text-xs font-mono py-1 px-2.5 flex items-center gap-1.5 hover:border-signal"
                    >
                      <svg className="w-3.5 h-3.5 text-signal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      <span>{doc.label}</span>
                      <span className="muted text-[10px]">({doc.fileName})</span>
                    </a>
                  ))}
                </div>
              </div>

              {/* Milestones Sequence */}
              <div className="mt-6 border-t border-line pt-4">
                <h3 className="mono text-xs uppercase tracking-wider text-ink-soft mb-3 font-semibold">
                  🏁 Meilensteine & Freigabe-Gates:
                </h3>
                <div className="row-list">
                  {prio1Project.milestones.map((m) => (
                    <div key={m.id} className="grid grid-cols-1 md:grid-cols-3 gap-2 items-center py-2.5">
                      <div>
                        <span className="font-semibold text-sm text-ink">{m.title}</span>
                      </div>
                      <div>
                        <span className="mono text-xs text-ink-soft">Termin: {m.targetDate}</span>
                      </div>
                      <div className="flex items-center justify-between md:justify-end gap-3">
                        <span className="badge" data-variant={m.status === "done" ? "graph" : m.status === "in_progress" ? "episodic" : "raw"}>
                          {m.status === "done" ? "✓ Erledigt" : m.status === "in_progress" ? "In Arbeit" : "Geplant"}
                        </span>
                        {m.fileLink && (
                          <a
                            href={m.fileLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mono text-xs text-signal underline hover:text-ink"
                          >
                            Öffnen →
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Full Projects Table / List */}
          <section className="rise rise-delay-2">
            <h2 className="section-title mb-1">Alle 10 Projekte im Detail</h2>
            <p className="muted mb-4 text-sm">
              Inklusive Dokumenten-Links, Abhängigkeiten & Fristen
            </p>

            <div className="space-y-6">
              {filteredProjects.map((proj) => (
                <div
                  key={proj.id}
                  className="border border-line bg-paper/60 p-5 transition-colors hover:border-ink-soft"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className="badge"
                          data-variant={
                            proj.priority === "prio1"
                              ? "raw"
                              : proj.priority === "prio2"
                              ? "episodic"
                              : proj.priority === "continuous"
                              ? "graph"
                              : "curated"
                          }
                        >
                          {proj.priorityLabel}
                        </span>
                        <h3 className="text-base font-bold text-ink m-0">
                          {proj.title}
                        </h3>
                      </div>
                      <p className="muted mt-1 mb-0 text-xs">{proj.description}</p>
                    </div>

                    <div className="text-right">
                      <div className="mono text-xs font-semibold text-ink">
                        Ziel: {proj.deadline}
                      </div>
                      <div className="mono text-xs muted mt-0.5">
                        Status: {proj.status}
                      </div>
                    </div>
                  </div>

                  {/* Documents & Links */}
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="mono text-xs text-ink-soft font-semibold">Dokumente:</span>
                      {proj.documents.map((doc) => (
                        <a
                          key={doc.fileUri}
                          href={doc.fileUri}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mono text-xs text-signal hover:underline flex items-center gap-1 bg-paper px-2 py-0.5 border border-line"
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          <span>{doc.label}</span>
                        </a>
                      ))}
                    </div>

                    <div className="mono text-xs muted">
                      Abhängigkeiten: <span className="text-ink">{proj.dependencies.join(", ")}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
