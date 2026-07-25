import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

type RouteParams = { params: Promise<{ meetingId: string }> };

export async function POST(req: Request, { params }: RouteParams) {
  const { meetingId } = await params;
  try {
    const formData = await req.formData();
    const res = await fetch(
      `${ORCHESTRATOR_URL}/v1/meetings/${encodeURIComponent(meetingId)}/attachments`,
      {
        method: "POST",
        body: formData,
        signal: AbortSignal.timeout(120_000),
      },
    );
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Upload fehlgeschlagen" },
      { status: 502 },
    );
  }
}
