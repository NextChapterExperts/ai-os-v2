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
  let body: DispatchBody = {};
  try {
    body = (await req.json()) as DispatchBody;
  } catch {
    return NextResponse.json({ error: "Ungültiges JSON-Format" }, { status: 400 });
  }

  const activeParams = body.params ?? {};
  const query = (activeParams.query ?? body.query ?? body.intent ?? "").toString().trim();
  const intent = body.intent || query;
  if (!query) {
    return NextResponse.json({ error: "query required" }, { status: 400 });
  }

  const payload = {
    intent,
    tenant_id: body.tenant_id ?? "nextchapter",
    params: {
      query,
      intent_text: query,
      ...activeParams,
    },
  };

  let res: Response;
  try {
    res = await fetch(`${ORCHESTRATOR_URL}/v1/dispatch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(120_000),
    });
  } catch (firstErr) {
    try {
      res = await fetch("http://localhost:8091/v1/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(120_000),
      });
    } catch {
      throw firstErr;
    }
  }
    const rawText = await res.text();
    let data: Record<string, unknown> = {};
    try {
      data = JSON.parse(rawText) as Record<string, unknown>;
    } catch {
      data = { message: rawText || `HTTP ${res.status}` };
    }
    if (!res.ok) {
      const errorStr = typeof data.detail === "string" ? data.detail : typeof data.message === "string" ? data.message : JSON.stringify(data);
      return NextResponse.json(
        { kind: "dispatch_error", error: errorStr, stats: memoryStats() },
        { status: res.status },
      );
    }

    const resultObj = typeof data.result === "object" && data.result !== null ? (data.result as Record<string, unknown>) : {};
    return NextResponse.json({
      query: resultObj.query ?? query,
      kind: resultObj.kind ?? "ask",
      summary: resultObj.summary ?? resultObj.answer ?? "",
      answer: resultObj.answer ?? resultObj.summary ?? "",
      mode: resultObj.mode ?? data.intent,
      detail: resultObj.detail ?? false,
      projectId: resultObj.projectId,
      model: resultObj.model ?? resultObj.model_used,
      model_used: resultObj.model_used ?? resultObj.model,
      sources: resultObj.sources ?? [],
      sourceCount: resultObj.sourceCount ?? (Array.isArray(resultObj.sources) ? resultObj.sources.length : 0),
      confidence: resultObj.confidence,
      anonymity_active: resultObj.anonymity_active,
      sub_questions: resultObj.sub_questions,
      llmContext: resultObj.llmContext,
      saved_to_brain: resultObj.saved_to_brain,
      curatedCount: resultObj.curatedCount,
      rawFileCount: resultObj.rawFileCount,
      graphCount: resultObj.graphCount,
      episodicCount: resultObj.episodicCount,
      federated: resultObj.federated,
      memoryBackend: resultObj.memoryBackend,
      intent: data.intent,
      runId: data.run_id ?? resultObj.runId,
      hasContext: resultObj.hasContext ?? Boolean(data.run_id),
      contextCharCount: resultObj.contextCharCount,
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
