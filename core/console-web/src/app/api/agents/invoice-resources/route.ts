import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

/** Sheet- und Drive-Links für Rechnungs-Fachagenten (OAuth/Config, kein Gmail-Scan). */
export async function GET() {
  try {
    const res = await fetch(
      `${ORCHESTRATOR_URL}/v1/email/invoices/status?tenant_id=nextchapter`,
      { cache: "no-store", signal: AbortSignal.timeout(15_000) },
    );
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error ? err.message : "Rechnungs-Ressourcen nicht erreichbar",
      },
      { status: 503 },
    );
  }
}
