import { NextResponse } from "next/server";
import { memoryStats } from "@/lib/memory";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

type DispatchBody = {
  intent?: string;
  query?: string;
  tenant_id?: string;
  params?: Record<string, unknown>;
};

export async function POST(req: Request) {
  const body = (await req.json()) as DispatchBody;
  const query = (body.query ?? body.intent ?? "").toString().trim();
  if (!query) {
    return NextResponse.json({ error: "query required" }, { status: 400 });
  }

  const payload = {
    intent: query,
    tenant_id: body.tenant_id ?? "nextchapter",
    params: {
      query,
      intent_text: query,
      ...(body.params ?? {}),
    },
  };

  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/dispatch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(120_000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(
        { kind: "dispatch_error", error: data, stats: memoryStats() },
        { status: 502 },
      );
    }

    const result = data.result ?? {};
    return NextResponse.json({
      query,
      kind: result.kind ?? "ask",
      answer: result.answer,
      mode: result.mode ?? data.intent,
      detail: result.detail ?? false,
      projectId: result.projectId,
      model: result.model,
      sources: result.sources ?? [],
      sourceCount: result.sourceCount ?? 0,
      curatedCount: result.curatedCount,
      rawFileCount: result.rawFileCount,
      intent: data.intent,
      context_bundle: data.context_bundle,
      stats: memoryStats(),
    });
  } catch (err) {
    // Fallback: local memory search API path if orchestrator down
    const msg = err instanceof Error ? err.message : "orchestrator unreachable";
    return NextResponse.json(
      {
        kind: "dispatch_error",
        error: `Orchestrator nicht erreichbar (${ORCHESTRATOR_URL}): ${msg}. Starte ./core/orchestrator/run.sh`,
        stats: memoryStats(),
      },
      { status: 503 },
    );
  }
}
