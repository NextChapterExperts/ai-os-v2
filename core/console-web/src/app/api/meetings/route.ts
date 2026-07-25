import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const qs = searchParams.toString();
  const url = `${ORCHESTRATOR_URL}/v1/meetings${qs ? `?${qs}` : ""}`;
  try {
    const res = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(30_000) });
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Meetings laden fehlgeschlagen" },
      { status: 502 },
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/meetings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Meeting speichern fehlgeschlagen" },
      { status: 502 },
    );
  }
}
