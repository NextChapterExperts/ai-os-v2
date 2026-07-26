import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET() {
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/compute/mode`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error
            ? err.message
            : "Compute-Modus nicht erreichbar",
      },
      { status: 503 },
    );
  }
}

export async function POST(req: Request) {
  let body: { mode?: string };
  try {
    body = (await req.json()) as { mode?: string };
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }
  const mode = body.mode?.trim();
  if (!mode) {
    return NextResponse.json({ error: "mode required" }, { status: 400 });
  }

  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/compute/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error
            ? err.message
            : "Compute-Modus nicht erreichbar",
      },
      { status: 503 },
    );
  }
}
