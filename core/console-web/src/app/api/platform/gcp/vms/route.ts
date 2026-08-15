import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET() {
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/platform/gcp/vms`, {
      cache: "no-store",
      signal: AbortSignal.timeout(20_000),
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

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const action = body.action || "create";

    if (action === "delete") {
      const instanceName = body.instance_name;
      const res = await fetch(`${ORCHESTRATOR_URL}/v1/platform/gcp/vms/${instanceName}`, {
        method: "DELETE",
        signal: AbortSignal.timeout(60_000),
      });
      const data = await res.json();
      if (!res.ok) return NextResponse.json({ error: data }, { status: res.status });
      return NextResponse.json(data);
    }

    let endpoint = "/v1/platform/gcp/vms/create";
    if (action === "stop") endpoint = "/v1/platform/gcp/vms/stop";
    if (action === "start") endpoint = "/v1/platform/gcp/vms/start";

    const res = await fetch(`${ORCHESTRATOR_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
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
