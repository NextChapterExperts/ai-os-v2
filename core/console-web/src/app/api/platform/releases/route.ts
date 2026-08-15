import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET() {
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/platform/releases`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({
      releases: [
        {
          version: "v1.0.0",
          tag: "v1.0.0-core-appliance",
          date: "2026-08-15",
          title: "AI-OS Core Platform Appliance Initial Release",
          description: "Erste offizielle Verteilung der autarken Core Platform Appliance.",
          changes: ["Autarkes Distributions-Projekt virgi-platform-dist", "5-Schichten-Memory-Modell", "Hybrid Graph-RAG", "Multi-Stage Docker Stack"],
          git_commit: "bd2a74c"
        }
      ],
      current_version: "v1.0.0"
    });
  }
}
