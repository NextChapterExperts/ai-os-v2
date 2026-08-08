import { NextResponse } from "next/server";
import {
  ensureAgentServices,
  formatEnsureServicesError,
} from "@/lib/ensure-agent-services";

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || "http://127.0.0.1:8091";

export async function POST(req: Request) {
  try {
    const ensure = await ensureAgentServices();
    const ensureError = formatEnsureServicesError(ensure);
    if (ensureError) {
      return NextResponse.json(
        { error: ensureError, services: ensure },
        { status: 503 },
      );
    }

    const body = await req.json();
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/workflow/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(300_000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json({ ...data, services: ensure });
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Failed to execute agent workflow";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
