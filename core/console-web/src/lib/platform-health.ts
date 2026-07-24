import type { HealthItem, PlatformHealthResponse, ServiceStatus } from "./types";

type Probe = {
  id: string;
  label: string;
  url: string;
  okWhen: (res: Response, body: string) => boolean;
};

const PROBES: Probe[] = [
  {
    id: "qdrant",
    label: "Qdrant",
    url: "http://127.0.0.1:6333/readyz",
    okWhen: (res) => res.ok,
  },
  {
    id: "langfuse",
    label: "LangFuse",
    url: "http://127.0.0.1:3000/api/public/health",
    okWhen: (res, body) => res.ok && body.includes("OK"),
  },
  {
    id: "letta",
    label: "Letta",
    url: "http://127.0.0.1:8283/v1/health",
    okWhen: (res) => res.ok || res.status === 404,
  },
  {
    id: "litellm",
    label: "LiteLLM / Memory Gateway",
    url: "http://127.0.0.1:4000/health/liveliness",
    okWhen: (res) => res.ok,
  },
  {
    id: "searxng",
    label: "SearXNG",
    url: "http://127.0.0.1:8888",
    okWhen: (res) => res.ok,
  },
];

async function probeOne(probe: Probe): Promise<HealthItem> {
  const started = Date.now();
  try {
    const res = await fetch(probe.url, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });
    const body = await res.text().catch(() => "");
    const latencyMs = Date.now() - started;
    const ok = probe.okWhen(res, body);
    const status: ServiceStatus = ok ? "ok" : "down";
    return {
      id: probe.id,
      label: probe.label,
      url: probe.url,
      status,
      detail: ok ? `HTTP ${res.status}` : `HTTP ${res.status} · ${body.slice(0, 80) || "no body"}`,
      latencyMs,
    };
  } catch (err) {
    return {
      id: probe.id,
      label: probe.label,
      url: probe.url,
      status: "down",
      detail: err instanceof Error ? err.message : "unreachable",
      latencyMs: Date.now() - started,
    };
  }
}

export async function checkPlatformHealth(): Promise<PlatformHealthResponse> {
  const items = await Promise.all(PROBES.map(probeOne));

  // LiteLLM fallback paths
  const litellm = items.find((i) => i.id === "litellm");
  if (litellm && litellm.status === "down") {
    const alt = await probeOne({
      ...PROBES.find((p) => p.id === "litellm")!,
      url: "http://127.0.0.1:4000/health",
      okWhen: (res) => res.ok || res.status === 401,
    });
    if (alt.status === "ok") {
      litellm.status = "ok";
      litellm.detail = alt.detail;
      litellm.latencyMs = alt.latencyMs;
      litellm.url = alt.url;
    }
  }

  // Letta: root may work if /v1/health 404s with empty app
  const letta = items.find((i) => i.id === "letta");
  if (letta && letta.status === "down") {
    const alt = await probeOne({
      id: "letta",
      label: "Letta",
      url: "http://127.0.0.1:8283/",
      okWhen: (res) => res.status < 500,
    });
    Object.assign(letta, alt);
  }

  const summary = {
    ok: items.filter((i) => i.status === "ok").length,
    down: items.filter((i) => i.status === "down").length,
    unknown: items.filter((i) => i.status === "unknown").length,
  };

  return {
    checkedAt: new Date().toISOString(),
    tenant: process.env.DEFAULT_TENANT ?? "nextchapter",
    computeMode: process.env.DEFAULT_COMPUTE_MODE ?? "sovereign",
    items,
    summary,
  };
}
