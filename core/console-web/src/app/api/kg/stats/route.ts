import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET() {
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/kg/stats`, {
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ error: data }, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Orchestrator nicht erreichbar";
    return NextResponse.json({ error: msg }, { status: 503 });
  }
}
