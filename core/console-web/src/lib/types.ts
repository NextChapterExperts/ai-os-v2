export type ServiceStatus = "ok" | "down" | "unknown";

export type HealthItem = {
  id: string;
  label: string;
  url: string;
  status: ServiceStatus;
  detail: string;
  latencyMs: number | null;
};

export type PlatformHealthResponse = {
  checkedAt: string;
  tenant: string;
  computeMode: string;
  items: HealthItem[];
  summary: {
    ok: number;
    down: number;
    unknown: number;
  };
};
