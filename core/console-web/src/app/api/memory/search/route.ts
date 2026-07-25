import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get("q") ?? "").trim();
  const mode = searchParams.get("mode") ?? "auto";
  const limit = Math.min(Number(searchParams.get("limit") ?? 20), 50);

  if (!q) {
    return NextResponse.json({ query: q, kind: "empty", results: [] });
  }

  const wantAsk = mode === "ask" || (mode === "auto" && q.includes("?"));

  try {
    if (wantAsk) {
      const res = await fetch(`${ORCHESTRATOR_URL}/v1/dispatch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent: "memory_ask",
          tenant_id: "nextchapter",
          params: { query: q, force_intent: "memory_ask" },
        }),
        signal: AbortSignal.timeout(120_000),
      });
      if (!res.ok) {
        throw new Error(`Orchestrator ${res.status}`);
      }
      const data = await res.json();
      const result = data.result ?? {};
      return NextResponse.json({
        query: q,
        kind: "ask",
        answer: result.answer,
        mode: result.mode,
        memoryBackend: result.memoryBackend,
        model: result.model,
        sources: result.sources ?? [],
        sourceCount: result.sourceCount ?? 0,
      });
    }

    const res = await fetch(`${ORCHESTRATOR_URL}/v1/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, tenant_id: "nextchapter", limit }),
      signal: AbortSignal.timeout(60_000),
    });
    if (!res.ok) {
      throw new Error(`Orchestrator search ${res.status}`);
    }
    const data = await res.json();
    return NextResponse.json({
      query: q,
      kind: "search",
      results: data.sources ?? [],
      episodicCount: data.episodicCount ?? 0,
      sourceCount: data.sourceCount ?? 0,
    });
  } catch (err) {
    return NextResponse.json(
      {
        query: q,
        kind: "error",
        error: err instanceof Error ? err.message : "Suche fehlgeschlagen",
      },
      { status: 502 },
    );
  }
}
