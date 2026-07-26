import { Suspense } from "react";
import Link from "next/link";
import { checkPlatformHealth } from "@/lib/platform-health";
import { memoryStats } from "@/lib/memory";
import { StatusDot } from "@/components/StatusDot";
import { MemorySearch } from "@/components/MemorySearch";
import { LagebildRibbon } from "@/components/LagebildRibbon";
import { ComputeModePanel } from "@/components/ComputeModePanel";
import { DailyFocusPanel } from "@/components/DailyFocusPanel";

export const dynamic = "force-dynamic";

function formatToday() {
  return new Intl.DateTimeFormat("de-DE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());
}

export default async function LagebildPage() {
  const [health, mem] = await Promise.all([
    checkPlatformHealth(),
    Promise.resolve(memoryStats()),
  ]);
  const online = health.summary.ok;
  const total = health.items.length;

  return (
    <>
      <LagebildRibbon />

      <section className="lagebild-top rise pt-6">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">
              {formatToday()}
            </p>
            <h1 className="section-title m-0">Lagebild</h1>
            <p className="muted mt-1 mb-0 max-w-xl text-sm">
              Tenant <span className="mono text-ink">nextchapter</span> · {online}/{total}{" "}
              Services · {mem.chunks} Memory-Chunks
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/platform" className="btn-ghost">
              Plattform
            </Link>
            <Link href="/workflows" className="btn-ghost">
              Workflows
            </Link>
          </div>
        </div>

        <Suspense fallback={<p className="muted">Suche lädt…</p>}>
          <MemorySearch autofocus />
        </Suspense>
      </section>

      <section className="rise rise-delay-1 mt-6">
        <DailyFocusPanel />
      </section>

      <section className="rise rise-delay-1 mt-8">
        <ComputeModePanel />
      </section>

      <section className="rise rise-delay-1 mt-10 grid gap-10 border-t border-line pt-8 lg:grid-cols-2">
        <div>
          <h2 className="section-title">Briefing</h2>
          <p className="m-0 text-ink-soft leading-relaxed">
            Cursor-Chats landen im Gedächtnis; das Feld oben steuert den{" "}
            <span className="mono text-ink">Orchestrator</span> (Intent →
            Engagements / Memory / Mail-Stub).
          </p>
        </div>
        <div>
          <h2 className="section-title">Infra</h2>
          <div className="row-list">
            {health.items.map((item) => (
              <div key={item.id}>
                <div className="flex items-center gap-3">
                  <StatusDot status={item.status} />
                  <span>{item.label}</span>
                </div>
                <span className="mono text-xs text-ink-soft">
                  {item.status === "ok" ? `${item.latencyMs ?? "—"} ms` : "offline"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
