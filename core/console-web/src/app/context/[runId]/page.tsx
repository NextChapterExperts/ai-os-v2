import Link from "next/link";
import { RunContextPanel } from "@/components/RunContextPanel";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ runId: string }>;
};

export default async function RunContextPage({ params }: PageProps) {
  const { runId } = await params;

  return (
    <section className="rise pt-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">Lagebild · Kontext</p>
          <h1 className="section-title m-0">LLM-Kontext</h1>
          <p className="muted mt-1 mb-0 max-w-2xl text-sm">
            Vollständiger Prompt und Retrieval-Kontext für Run{" "}
            <span className="mono text-ink">{runId}</span>
          </p>
        </div>
        <Link href="/" className="btn-ghost">
          Zurück zum Lagebild
        </Link>
      </div>

      <RunContextPanel runId={runId} />
    </section>
  );
}
