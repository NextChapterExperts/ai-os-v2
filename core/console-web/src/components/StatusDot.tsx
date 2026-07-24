import type { ServiceStatus } from "@/lib/types";

export function StatusDot({ status }: { status: ServiceStatus }) {
  const cls =
    status === "ok" ? "ok" : status === "down" ? "down" : "unknown";
  const label = status === "ok" ? "online" : status === "down" ? "offline" : "unbekannt";
  return <span className={`status-dot ${cls}`} title={label} aria-label={label} />;
}
