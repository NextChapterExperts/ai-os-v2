import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET() {
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/capture/stats`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: `Orchestrator ${res.status}` },
        { status: 502 },
      );
    }
    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error ? err.message : "Capture-Stats nicht erreichbar",
      },
      { status: 503 },
    );
  }
}
