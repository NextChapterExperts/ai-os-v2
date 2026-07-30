import { NextResponse } from "next/server";

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || "http://127.0.0.1:8091";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/workflow/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to execute agent workflow" }, { status: 502 });
  }
}
