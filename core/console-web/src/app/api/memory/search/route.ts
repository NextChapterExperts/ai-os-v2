import { NextResponse } from "next/server";
import { askMemory, isNarrativeQuestion } from "@/lib/memory-ask";
import { memoryStats, searchMemory } from "@/lib/memory";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get("q") ?? "").trim();
  const mode = searchParams.get("mode") ?? "auto"; // auto | ask | search
  const limit = Math.min(Number(searchParams.get("limit") ?? 20), 50);

  if (!q) {
    return NextResponse.json({
      query: q,
      kind: "empty",
      results: [],
      stats: memoryStats(),
    });
  }

  const wantAsk =
    mode === "ask" || (mode === "auto" && isNarrativeQuestion(q));

  if (wantAsk) {
    try {
      const asked = await askMemory(q);
      return NextResponse.json({
        query: q,
        kind: "ask",
        ...asked,
        stats: memoryStats(),
      });
    } catch (err) {
      return NextResponse.json(
        {
          query: q,
          kind: "ask_error",
          error: err instanceof Error ? err.message : "Ask fehlgeschlagen",
          stats: memoryStats(),
        },
        { status: 502 },
      );
    }
  }

  const results = searchMemory(q, limit).map((r) => ({
    ...r,
    snippet: r.body.slice(0, 280) + (r.body.length > 280 ? "…" : ""),
  }));

  return NextResponse.json({
    query: q,
    kind: "search",
    results,
    stats: memoryStats(),
  });
}
