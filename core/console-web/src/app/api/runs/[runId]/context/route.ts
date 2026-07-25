import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

type RouteParams = { params: Promise<{ runId: string }> };

export async function GET(_req: Request, { params }: RouteParams) {
  const { runId } = await params;
  if (!runId?.trim()) {
    return NextResponse.json({ error: "runId required" }, { status: 400 });
  }

  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/runs/${encodeURIComponent(runId)}/context`, {
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      {
        error: err instanceof Error ? err.message : "Kontext konnte nicht geladen werden",
      },
      { status: 502 },
    );
  }
}
