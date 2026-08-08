"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { type ProjectMilestone, type ProjectSummary } from "@/lib/portfolio-db";
import { GitPushButton } from "@/components/GitPushButton";

type PriorityFilter = "all" | "prio1" | "prio2_3" | "continuous";

const PRIORITY_SECTIONS: {
  key: PriorityFilter;
  title: string;
  subtitle: string;
  match: (p: ProjectSummary) => boolean;
}[] = [
  {
    key: "prio1",
    title: "Prio 1 — Höchste Dringlichkeit",
    subtitle: "Aktuelle Sprint-Ziele & LCC-Readiness",
    match: (p) => p.priority === "prio1",
  },
  {
    key: "prio2_3",
    title: "Prio 2 & 3 — Geplant & Partner-abhängig",
    subtitle: "Nebenprojekte mit festem Zeitfenster",
    match: (p) => p.priority === "prio2" || p.priority === "prio3",
  },
  {
    key: "continuous",
    title: "Continuous — Plattform & Content",
    subtitle: "Laufende Evolution ohne harten Release-Termin",
    match: (p) => p.priority === "continuous",
  },
];

function getViewerUrl(uri: string) {
  if (!uri) return "#";
  if (uri.startsWith("http://") || uri.startsWith("https://")) return uri;
  const cleanPath = uri.replace("file://", "");
  return `/api/view-file?path=${encodeURIComponent(cleanPath)}`;
}

function getOpenLocalUrl(uri: string) {
  if (!uri) return "#";
  const cleanPath = uri.replace("file://", "");
  return `/api/open-local?path=${encodeURIComponent(cleanPath)}`;
}

function milestoneProgress(milestones: ProjectMilestone[]) {
  if (milestones.length === 0) return { done: 0, total: 0, pct: 0 };
  const done = milestones.filter((m) => m.status === "done").length;
  return { done, total: milestones.length, pct: Math.round((done / milestones.length) * 100) };
}

function milestoneStatusLabel(status: ProjectMilestone["status"]) {
  switch (status) {
    case "done":
      return "Erledigt";
    case "in_progress":
      return "In Arbeit";
    case "planned":
      return "Geplant";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

function milestoneBadgeVariant(status: ProjectMilestone["status"]) {
  switch (status) {
    case "done":
      return "graph";
    case "in_progress":
      return "episodic";
    case "planned":
      return "raw";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

function priorityBadgeVariant(priority: ProjectSummary["priority"]) {
  switch (priority) {
    case "prio1":
      return "raw";
    case "prio2":
      return "episodic";
    case "continuous":
      return "graph";
    case "prio3":
      return "curated";
    default: {
      const _exhaustive: never = priority;
      return _exhaustive;
    }
  }
}

function DocumentChip({ label, fileUri, fileName }: { label: string; fileUri: string; fileName: string }) {
  return (
    <div className="inline-flex items-center rounded border border-line bg-paper text-xs font-mono overflow-hidden">
      <a
        href={getViewerUrl(fileUri)}
        target="_blank"
        rel="noopener noreferrer"
        className="py-1 px-2 flex items-center gap-1 text-signal hover:bg-paper-2 transition-colors"
        title="Im Browser-Viewer anzeigen"
      >
        <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
        <span>{label}</span>
        <span className="muted text-[10px] hidden sm:inline">({fileName})</span>
      </a>
      <a
        href={getOpenLocalUrl(fileUri)}
        target="_blank"
        rel="noopener noreferrer"
        className="py-1 px-1.5 text-ink-soft border-l border-line hover:bg-paper-2 hover:text-ink"
        title="Direkt im System / Editor öffnen"
      >
        💻
      </a>
    </div>
  );
}

function ProjectCard({ proj, expanded }: { proj: ProjectSummary; expanded?: boolean }) {
  const progress = milestoneProgress(proj.milestones);
  const [showAllDocs, setShowAllDocs] = useState(false);
  const visibleDocs = showAllDocs || expanded ? proj.documents : proj.documents.slice(0, 3);
  const hiddenDocCount = proj.documents.length - visibleDocs.length;

  return (
    <article className="border border-line bg-paper/60 p-4 transition-colors hover:border-ink-soft flex flex-col h-full">
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-line pb-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge shrink-0" data-variant={priorityBadgeVariant(proj.priority)}>
              {proj.priorityLabel}
            </span>
            <h3 className="text-sm font-bold text-ink m-0 leading-snug">{proj.title}</h3>
          </div>
          <p className="muted mt-1.5 mb-0 text-xs leading-relaxed">{proj.description}</p>
        </div>
        <div className="text-right shrink-0">
          <div className="mono text-xs font-semibold text-ink">{proj.deadline}</div>
          <div className="mono text-[11px] muted mt-0.5">{proj.status}</div>
        </div>
      </div>

      {proj.milestones.length > 0 ? (
        <div className="mt-3">
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <span className="mono text-[11px] text-ink-soft font-semibold uppercase tracking-wide">
              Meilensteine
            </span>
            <span className="mono text-[11px] text-ink-soft">
              {progress.done}/{progress.total} · {progress.pct}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-paper-2 overflow-hidden">
            <div
              className="h-full rounded-full bg-signal transition-all"
              style={{ width: `${progress.pct}%` }}
            />
          </div>
          <ul className="mt-2 space-y-1">
            {proj.milestones.slice(0, expanded ? undefined : 3).map((m) => (
              <li key={m.id} className="flex items-center justify-between gap-2 text-xs">
                <span className="text-ink truncate">{m.title}</span>
                <span className="badge shrink-0" data-variant={milestoneBadgeVariant(m.status)}>
                  {milestoneStatusLabel(m.status)}
                </span>
              </li>
            ))}
            {!expanded && proj.milestones.length > 3 ? (
              <li className="mono text-[11px] muted">+{proj.milestones.length - 3} weitere</li>
            ) : null}
          </ul>
        </div>
      ) : null}

      <div className="pt-3 border-t border-line mt-auto">
        <div className="flex flex-wrap gap-1.5">
          {visibleDocs.map((doc) => (
            <DocumentChip key={doc.fileUri} label={doc.label} fileUri={doc.fileUri} fileName={doc.fileName} />
          ))}
        </div>
        {!expanded && hiddenDocCount > 0 ? (
          <button
            type="button"
            className="btn-ghost text-[11px] mt-2 py-0.5"
            onClick={() => setShowAllDocs(true)}
          >
            +{hiddenDocCount} weitere Dokumente
          </button>
        ) : null}
        {proj.dependencies.length > 0 ? (
          <p className="mono text-[11px] muted mt-2 mb-0">
            Abhängigkeiten: <span className="text-ink">{proj.dependencies.join(", ")}</span>
          </p>
        ) : null}
      </div>
    </article>
  );
}

function SpotlightSection({ project }: { project: ProjectSummary }) {
  const progress = milestoneProgress(project.milestones);

  return (
    <section className="rise rise-delay-1 mb-8 border border-line bg-paper-2/40 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge" data-variant="raw">
              🔴 Fokus · Prio 1
            </span>
            <span className="mono text-xs text-ink-soft">{project.id}</span>
          </div>
          <h2 className="section-title mt-2 mb-0">{project.title}</h2>
          <p className="muted mt-1 mb-0 text-sm max-w-3xl">{project.description}</p>
        </div>
        <div className="text-right">
          <div className="mono text-sm font-bold text-ink">{project.deadline}</div>
          <span className="badge mt-1" data-variant="graph">
            {project.status}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <h3 className="mono text-xs uppercase tracking-wider text-ink-soft mb-3 font-semibold">
            4-Säulen-Sprint · Meilensteine
          </h3>
          <div className="space-y-2">
            {project.milestones.map((m) => (
              <div
                key={m.id}
                className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2 items-center py-2 border-b border-line/60 last:border-0"
              >
                <span className="font-semibold text-sm text-ink">{m.title}</span>
                <span className="mono text-xs text-ink-soft">{m.targetDate}</span>
                <div className="flex items-center gap-2 md:justify-end">
                  <span className="badge" data-variant={milestoneBadgeVariant(m.status)}>
                    {milestoneStatusLabel(m.status)}
                  </span>
                  {m.fileLink ? (
                    <>
                      <a
                        href={getViewerUrl(m.fileLink)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mono text-xs text-signal underline hover:text-ink"
                      >
                        Öffnen
                      </a>
                      <a
                        href={getOpenLocalUrl(m.fileLink)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mono text-xs text-ink-soft hover:text-ink"
                        title="Im Editor öffnen"
                      >
                        💻
                      </a>
                    </>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded border border-line bg-paper/80 p-4">
          <div className="mono text-xs text-ink-soft uppercase tracking-wide font-semibold">
            Fortschritt
          </div>
          <div className="text-3xl font-bold text-ink mt-1">
            {progress.pct}
            <span className="text-base font-normal muted">%</span>
          </div>
          <div className="h-2 rounded-full bg-paper-2 mt-2 overflow-hidden">
            <div className="h-full rounded-full bg-signal" style={{ width: `${progress.pct}%` }} />
          </div>
          <p className="mono text-xs muted mt-2 mb-4">
            {progress.done} von {progress.total} Säulen/Gates abgeschlossen
          </p>
          <h4 className="mono text-[11px] uppercase tracking-wider text-ink-soft font-semibold mb-2">
            Kern-Dokumente
          </h4>
          <div className="flex flex-col gap-1.5">
            {project.documents.map((doc) => (
              <DocumentChip key={doc.fileUri} label={doc.label} fileUri={doc.fileUri} fileName={doc.fileName} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function PortfolioPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<PriorityFilter>("all");

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

  const counts = useMemo(() => {
    const prio1 = projects.filter((p) => p.priority === "prio1").length;
    const prio23 = projects.filter((p) => p.priority === "prio2" || p.priority === "prio3").length;
    const continuous = projects.filter((p) => p.priority === "continuous").length;
    return { all: projects.length, prio1, prio23, continuous };
  }, [projects]);

  const spotlightProject = projects.find((p) => p.id === "studentenprojekt_v2");

  const visibleSections = PRIORITY_SECTIONS.filter((section) => {
    if (selectedFilter !== "all" && selectedFilter !== section.key) return false;
    return projects.some(section.match);
  });

  return (
    <div className="rise pt-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
        <div>
          <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">Portfolio</p>
          <h1 className="section-title m-0">Projekte & Meilensteine</h1>
          <p className="muted mt-1 mb-0 max-w-2xl text-sm">
            {counts.all} aktive Projekte · gruppiert nach Priorität · Direktsprung zu Dokumenten
          </p>
        </div>
        <div className="flex items-center gap-3">
          <GitPushButton />
          <Link href="/" className="btn-ghost">
            ← Zurück zum Lagebild
          </Link>
        </div>
      </div>

      {!loading && projects.length > 0 ? (
        <div className="mb-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {(
            [
              { key: "all" as const, label: "Gesamt", count: counts.all },
              { key: "prio1" as const, label: "Prio 1", count: counts.prio1 },
              { key: "prio2_3" as const, label: "Prio 2 & 3", count: counts.prio23 },
              { key: "continuous" as const, label: "Continuous", count: counts.continuous },
            ] as const
          ).map((stat) => (
            <button
              key={stat.key}
              type="button"
              onClick={() => setSelectedFilter(stat.key)}
              className="rounded border border-line bg-paper/60 p-3 text-left transition-colors hover:border-ink-soft"
              data-active={selectedFilter === stat.key}
            >
              <div className="mono text-[11px] text-ink-soft uppercase tracking-wide">{stat.label}</div>
              <div className="text-2xl font-bold text-ink mt-0.5">{stat.count}</div>
            </button>
          ))}
        </div>
      ) : null}

      {loading ? (
        <div className="p-8 text-center muted">Lade Projektdaten…</div>
      ) : (
        <>
          {spotlightProject && (selectedFilter === "all" || selectedFilter === "prio1") ? (
            <SpotlightSection project={spotlightProject} />
          ) : null}

          {visibleSections.map((section) => {
            const sectionProjects = projects.filter(section.match);
            if (sectionProjects.length === 0) return null;

            return (
              <section key={section.key} className="rise rise-delay-2 mb-10">
                <div className="mb-4 flex flex-wrap items-end justify-between gap-2 border-b border-line pb-3">
                  <div>
                    <h2 className="section-title mb-0 text-lg">{section.title}</h2>
                    <p className="muted m-0 text-sm">{section.subtitle}</p>
                  </div>
                  <span className="mono text-xs text-ink-soft">
                    {sectionProjects.length} Projekt{sectionProjects.length === 1 ? "" : "e"}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {sectionProjects
                    .filter((p) => {
                      const showSpotlight =
                        spotlightProject &&
                        (selectedFilter === "all" || selectedFilter === "prio1");
                      return !(showSpotlight && p.id === "studentenprojekt_v2");
                    })
                    .map((proj) => (
                      <ProjectCard key={proj.id} proj={proj} />
                    ))}
                </div>
              </section>
            );
          })}

          {projects.length === 0 ? (
            <p className="muted mt-4">Keine Projekte geladen.</p>
          ) : null}
        </>
      )}
    </div>
  );
}
