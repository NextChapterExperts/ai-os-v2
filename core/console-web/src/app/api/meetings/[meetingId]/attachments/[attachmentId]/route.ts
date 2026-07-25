import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

type RouteParams = { params: Promise<{ meetingId: string; attachmentId: string }> };

export async function GET(_req: Request, { params }: RouteParams) {
  const { meetingId, attachmentId } = await params;
  try {
    const res = await fetch(
      `${ORCHESTRATOR_URL}/v1/meetings/${encodeURIComponent(meetingId)}/attachments/${encodeURIComponent(attachmentId)}`,
      { cache: "no-store", signal: AbortSignal.timeout(60_000) },
    );
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: res.statusText }));
      return NextResponse.json(data, { status: res.status });
    }
    const blob = await res.blob();
    const headers = new Headers();
    const ct = res.headers.get("content-type");
    const cd = res.headers.get("content-disposition");
    if (ct) headers.set("Content-Type", ct);
    if (cd) headers.set("Content-Disposition", cd);
    return new NextResponse(blob, { status: 200, headers });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Download fehlgeschlagen" },
      { status: 502 },
    );
  }
}

export async function DELETE(_req: Request, { params }: RouteParams) {
  const { meetingId, attachmentId } = await params;
  try {
    const res = await fetch(
      `${ORCHESTRATOR_URL}/v1/meetings/${encodeURIComponent(meetingId)}/attachments/${encodeURIComponent(attachmentId)}`,
      { method: "DELETE", signal: AbortSignal.timeout(30_000) },
    );
    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Löschen fehlgeschlagen" },
      { status: 502 },
    );
  }
}
