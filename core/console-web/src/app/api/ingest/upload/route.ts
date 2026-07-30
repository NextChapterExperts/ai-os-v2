import { NextResponse } from "next/server";

const ORCHESTRATOR_URL = process.env.AIOS_ORCHESTRATOR_URL || "http://127.0.0.1:8091";

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");

    if (!file) {
      return NextResponse.json({ error: "Keine Datei im Request" }, { status: 400 });
    }

    const proxyFormData = new FormData();
    proxyFormData.append("file", file);
    proxyFormData.append("tenant_id", (formData.get("tenant_id") as string) || "nextchapter");

    const response = await fetch(`${ORCHESTRATOR_URL}/v1/ingest/upload`, {
      method: "POST",
      body: proxyFormData,
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json(
      { error: "Upload Proxy Error", detail: err.message },
      { status: 500 }
    );
  }
}
