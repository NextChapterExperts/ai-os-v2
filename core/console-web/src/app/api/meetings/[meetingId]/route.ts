import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

type RouteParams = { params: Promise<{ meetingId: string }> };

export async function GET(_req: Request, { params }: RouteParams) {
  const { meetingId } = await params;
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/meetings/${encodeURIComponent(meetingId)}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Meeting laden fehlgeschlagen" },
      { status: 502 },
    );
  }
}

export async function PATCH(req: Request, { params }: RouteParams) {
  const { meetingId } = await params;
  try {
    const body = await req.json();
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/meetings/${encodeURIComponent(meetingId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Meeting aktualisieren fehlgeschlagen" },
      { status: 502 },
    );
  }
}

export async function DELETE(_req: Request, { params }: RouteParams) {
  const { meetingId } = await params;
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/meetings/${encodeURIComponent(meetingId)}`, {
      method: "DELETE",
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Meeting löschen fehlgeschlagen" },
      { status: 502 },
    );
  }
}
