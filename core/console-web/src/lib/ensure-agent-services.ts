import { spawn } from "child_process";
import fs from "fs";
import path from "path";

export type AgentServiceId = "orchestrator" | "mcp_gateway";

export type EnsureAgentServicesResult = {
  started: AgentServiceId[];
  alreadyRunning: AgentServiceId[];
  failed: Array<{ id: AgentServiceId; error: string }>;
};

type ServiceDef = {
  id: AgentServiceId;
  healthUrl: string;
  script: string;
};

const REPO_ROOT =
  process.env.AIOS_REPO_ROOT?.trim() ||
  path.resolve(process.cwd(), "..", "..");

const ORCHESTRATOR_URL =
  process.env.ORCHESTRATOR_URL?.trim() || "http://127.0.0.1:8091";
const MCP_GATEWAY_URL =
  process.env.MCP_GATEWAY_URL?.trim() || "http://127.0.0.1:8097";

const SERVICES: ServiceDef[] = [
  {
    id: "orchestrator",
    healthUrl: `${ORCHESTRATOR_URL.replace(/\/$/, "")}/health`,
    script: "core/orchestrator/run.sh",
  },
  {
    id: "mcp_gateway",
    healthUrl: `${MCP_GATEWAY_URL.replace(/\/$/, "")}/health`,
    script: "core/mcp_gateway/run.sh",
  },
];

async function probeHealth(url: string, timeoutMs = 2500): Promise<boolean> {
  try {
    const res = await fetch(url, {
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!res.ok) return false;
    const body = (await res.json().catch(() => ({}))) as { status?: string };
    return body.status === "ok" || res.ok;
  } catch {
    return false;
  }
}

function startServiceScript(scriptRel: string, logName: string): void {
  const scriptPath = path.join(REPO_ROOT, scriptRel);
  if (!fs.existsSync(scriptPath)) {
    throw new Error(`Startskript nicht gefunden: ${scriptPath}`);
  }
  const logDir = path.join(REPO_ROOT, ".logs");
  fs.mkdirSync(logDir, { recursive: true });
  const logPath = path.join(logDir, `${logName}.log`);
  const logFd = fs.openSync(logPath, "a");
  const child = spawn("bash", [scriptPath], {
    cwd: REPO_ROOT,
    detached: true,
    stdio: ["ignore", logFd, logFd],
    env: { ...process.env },
  });
  child.unref();
}

async function waitForHealth(
  url: string,
  attempts = 20,
  intervalMs = 500,
): Promise<boolean> {
  for (let i = 0; i < attempts; i += 1) {
    if (await probeHealth(url, 2000)) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

/** Orchestrator + MCP-Gateway vor Agent-Ausführung bereitstellen (DEV). */
export async function ensureAgentServices(): Promise<EnsureAgentServicesResult> {
  const result: EnsureAgentServicesResult = {
    started: [],
    alreadyRunning: [],
    failed: [],
  };

  for (const svc of SERVICES) {
    if (await probeHealth(svc.healthUrl)) {
      result.alreadyRunning.push(svc.id);
      continue;
    }

    try {
      startServiceScript(svc.script, svc.id);
      result.started.push(svc.id);
      const ok = await waitForHealth(svc.healthUrl);
      if (!ok) {
        result.failed.push({
          id: svc.id,
          error: `${svc.id} startete, antwortet aber nicht auf ${svc.healthUrl}`,
        });
      }
    } catch (err) {
      result.failed.push({
        id: svc.id,
        error: err instanceof Error ? err.message : String(err),
      });
    }
  }

  return result;
}

export function formatEnsureServicesError(
  ensure: EnsureAgentServicesResult,
): string | null {
  if (ensure.failed.length === 0) return null;
  const parts = ensure.failed.map((f) => `${f.id}: ${f.error}`);
  return `Backend-Dienste nicht bereit (${parts.join("; ")}). Logs: ${REPO_ROOT}/.logs/`;
}
