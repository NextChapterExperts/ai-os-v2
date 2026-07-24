import Link from "next/link";

const SCHEDULED = [
  { name: "Daily Briefing", when: "täglich 07:00", state: "geplant" },
  { name: "Memory-Curation", when: "täglich 02:00", state: "geplant" },
] as const;

const MANUAL = [
  { name: "Recherche", note: "nach Platform-Gate" },
  { name: "Blog", note: "nach Platform-Gate" },
  { name: "E-Mail Export", note: "nach Platform-Gate" },
] as const;

export default function WorkflowsPage() {
  return (
    <section className="rise pt-10">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="section-title">Workflows</h1>
          <p className="muted m-0 max-w-xl">
            Ebene 2 — Scheduler und manuelle Starts. Noch Platzhalter, bis LangGraph angebunden
            ist.
          </p>
        </div>
        <Link href="/platform" className="btn-ghost">
          Zur Plattform
        </Link>
      </div>

      <h2 className="mb-2 text-sm uppercase tracking-[0.16em] text-ink-soft">Automatisch</h2>
      <div className="row-list mb-10">
        {SCHEDULED.map((job) => (
          <div key={job.name}>
            <span>{job.name}</span>
            <span className="mono text-sm text-ink-soft">
              {job.when} · {job.state}
            </span>
          </div>
        ))}
      </div>

      <h2 className="mb-2 text-sm uppercase tracking-[0.16em] text-ink-soft">Manuell</h2>
      <div className="row-list">
        {MANUAL.map((job) => (
          <div key={job.name}>
            <span>{job.name}</span>
            <span className="muted text-sm">{job.note}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
