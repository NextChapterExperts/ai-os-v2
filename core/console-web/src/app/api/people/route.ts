import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const tenant_id = searchParams.get("tenant_id") ?? "nextchapter";

  try {
    const res = await fetch(
      `${ORCHESTRATOR_URL}/v1/brain/people?tenant_id=${encodeURIComponent(tenant_id)}&_t=${Date.now()}`,
      { signal: AbortSignal.timeout(5000) }
    );
    if (!res.ok) {
      throw new Error(`Orchestrator returned ${res.status}`);
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Hardcoded fallback seed if orchestrator is starting up
    return NextResponse.json({
      tenant_id,
      people: [
        {
          id: "person:peter-alexander",
          name: "Peter Alexander",
          email: "peter.alexander@nextchapterexperts.de",
          role: "Founder / Operator",
        },
        {
          id: "person:juri-mustermann",
          name: "Juri Mustermann",
          email: "juri@nextchapterexperts.de",
          role: "Senior Consultant",
        },
        {
          id: "person:michael-sample",
          name: "Michael Sample",
          email: "michael@nextchapterexperts.de",
          role: "Solution Architect",
        },
      ],
    });
  }
}
