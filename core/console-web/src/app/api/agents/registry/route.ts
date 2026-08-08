import { NextResponse } from "next/server";
import {
  ensureAgentServices,
  formatEnsureServicesError,
} from "@/lib/ensure-agent-services";

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || "http://127.0.0.1:8091";

export async function GET() {
  try {
    const ensure = await ensureAgentServices();
    const ensureError = formatEnsureServicesError(ensure);
    if (ensureError) {
      return NextResponse.json(
        { error: ensureError, services: ensure },
        { status: 503 },
      );
    }

    const res = await fetch(`${ORCHESTRATOR_URL}/v1/workflows/registry`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ error: "Orchestrator unavailable" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to connect to Orchestrator" }, { status: 502 });
  }
}
