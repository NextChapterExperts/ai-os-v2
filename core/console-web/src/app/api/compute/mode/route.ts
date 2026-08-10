import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";

export async function GET() {
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/compute/mode`, {
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      {
        active_mode: "sovereign",
        active_model: "ai-os-sovereign",
        active_label: "Lokal (LAN)",
        active_description: "Ollama auf LAN — Fallback (Orchestrator beschäftigt)",
        config_default_mode: "sovereign",
        updated_at: null,
        modes: [
          {
            id: "sovereign",
            default_model: "ai-os-sovereign",
            label: "Qwen 2.5 Coder 32B (Default)",
            description: "Code, Webseiten, JSON & Tool-Calling (128k Kontext)",
            is_active: true,
            is_config_default: true,
          },
          {
            id: "sovereign_r1",
            default_model: "ai-os-deepseek-r1",
            label: "DeepSeek-R1 32B (Lokal)",
            description: "Logik, Reasoning & komplexe Problemlösung (128k Kontext)",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "sovereign_coder",
            default_model: "ai-os-qwen-coder",
            label: "Qwen 2.5 Coder 32B (Lokal)",
            description: "Code, Webseiten, JSON & Tool-Calling (128k Kontext)",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "sovereign_nemo",
            default_model: "ai-os-mistral-nemo",
            label: "Mistral Nemo 12B (Lokal)",
            description: "E-Mails, Blogs & deutsche Texte (128k Kontext)",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "sovereign_hermes",
            default_model: "ai-os-hermes3",
            label: "Hermes 3 8B (Lokal)",
            description: "Multi-Agenten Orchestrierung & Tool-Calling",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "sovereign_vision",
            default_model: "ai-os-llama-vision",
            label: "Llama 3.2 Vision 11B (Lokal)",
            description: "OCR, Bild-, PDF- & Dokumentenanalyse",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "sovereign_vllm",
            default_model: "ai-os-vllm",
            label: "vLLM Qwen2.5-14B (vLLM Server)",
            description: "High-Throughput Agenten Inferenz (Port 8001)",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "balanced",
            default_model: "ai-os-balanced",
            label: "Cloud (Free)",
            description: "Nemotron Super 120B — OpenRouter :free, 262K, Tools",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "premium",
            default_model: "ai-os-premium",
            label: "Frontier (Free)",
            description: "Nemotron Ultra 550B — OpenRouter :free, 1M Context, Tools",
            is_active: false,
            is_config_default: false,
          },
          {
            id: "coding",
            default_model: "ai-os-coding",
            label: "Coding (Free)",
            description: "Poolside Laguna M.1 — OpenRouter :free, agentic coding",
            is_active: false,
            is_config_default: false,
          },
        ],
        error:
          err instanceof Error
            ? err.message
            : "Compute-Modus nicht erreichbar",
      },
      { status: 200 },
    );
  }
}

export async function POST(req: Request) {
  let body: { mode?: string };
  try {
    body = (await req.json()) as { mode?: string };
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }
  const mode = body.mode?.trim();
  if (!mode) {
    return NextResponse.json({ error: "mode required" }, { status: 400 });
  }

  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/compute/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
      signal: AbortSignal.timeout(15000),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error
            ? err.message
            : "Compute-Modus nicht erreichbar",
      },
      { status: 503 },
    );
  }
}
