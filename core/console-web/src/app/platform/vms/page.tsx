"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStoredAuth, AuthUser } from "@/lib/auth";
import {
  IconCloud,
  IconServer,
  IconPlus,
  IconReload,
  IconPlayerStop,
  IconTrash,
  IconExternalLink,
  IconShieldLock,
  IconCoin,
  IconCheck,
  IconLock,
  IconWorld,
} from "@tabler/icons-react";

interface GcpVm {
  name: string;
  zone: string;
  status: string;
  machine_type: string;
  ip_address: string;
  console_url: string | null;
  tenant_id: string;
  created_at: string;
}

export default function VmManagementPage() {
  const [auth, setAuth] = useState<AuthUser | null>(null);
  const [vms, setVms] = useState<GcpVm[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form inputs
  const [tenantId, setTenantId] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [machineType, setMachineType] = useState("e2-standard-4");

  useEffect(() => {
    const currentAuth = getStoredAuth();
    setAuth(currentAuth);
    if (currentAuth.role === "admin") {
      loadVms();
    } else {
      setLoading(false);
    }
  }, []);

  const loadVms = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/platform/gcp/vms");
      if (!res.ok) throw new Error("Fehler beim Laden der VM-Liste");
      const data = await res.json();
      setVms(data.vms || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verbindungsfehler");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenantId.trim() || !companyName.trim()) return;

    setCreating(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await fetch("/api/platform/gcp/vms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "create",
          tenant_id: tenantId.trim(),
          company_name: companyName.trim(),
          admin_email: adminEmail.trim() || "admin@example.com",
          machine_type: machineType,
          zone: "europe-west3-a",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error?.detail || data.error || "VM-Erstellung fehlgeschlagen");

      setSuccessMsg(`VM für '${companyName}' wird in Frankfurt bereitgestellt!`);
      setTenantId("");
      setCompanyName("");
      setAdminEmail("");
      await loadVms();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erstellung fehlgeschlagen");
    } finally {
      setCreating(false);
    }
  };

  const handleStopVm = async (instanceName: string) => {
    try {
      const res = await fetch("/api/platform/gcp/vms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "stop", instance_name: instanceName }),
      });
      if (!res.ok) throw new Error("Fehler beim Stoppen der VM");
      await loadVms();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Aktion fehlgeschlagen");
    }
  };

  if (auth && auth.role !== "admin") {
    return (
      <div className="rise mx-auto max-w-3xl space-y-6 py-12 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 border border-amber-500/30">
          <IconLock size={32} />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-ink">Zugriff verweigert (Administrator erforderlich)</h1>
          <p className="text-sm text-ink-soft max-w-lg mx-auto">
            Das VM- und Hosting-Management ist ausschließlich für Plattform-Administratoren freigegeben.
          </p>
        </div>
        <div>
          <Link href="/agents" className="btn-primary inline-flex items-center gap-2">
            Zu den Fachagenten wechseln →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <section className="rise space-y-8">
      {/* Header Bar */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="tag-signal flex items-center gap-1 font-mono text-[11px]">
              <IconCloud size={12} /> GOOGLE CLOUD COMPUTE ENGINE
            </span>
            <span className="text-xs text-ink-soft">Projekt: strong-zephyr-505611-k4 (Frankfurt europe-west3-a)</span>
          </div>
          <h1 className="section-title text-3xl m-0 flex items-center gap-2">
            Kunden-VMs & Hosting
          </h1>
          <p className="muted m-0 max-w-2xl text-sm pt-1">
            Erstelle und verwalte isolierte, dedizierte AI-OS v2 VM-Appliances für externe Kunden direkt in Google Cloud.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="https://console.cloud.google.com/billing"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost flex items-center gap-2 text-xs border border-line"
          >
            <IconCoin size={15} className="text-warn" />
            <span>Google Billing Dashboard</span>
            <IconExternalLink size={13} />
          </a>
          <button
            type="button"
            onClick={loadVms}
            disabled={loading}
            className="btn-secondary flex items-center gap-2 text-xs cursor-pointer"
          >
            <IconReload size={14} className={loading ? "animate-spin" : ""} />
            <span>Aktualisieren</span>
          </button>
        </div>
      </div>

      {/* Cost & Info Card */}
      <div className="card-glass flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-signal/30 bg-signal/5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-semibold text-sm text-ink">
            <IconShieldLock className="text-signal" size={18} />
            <span>DSGVO-konformes Cloud-Hosting in Frankfurt am Main</span>
          </div>
          <p className="text-xs text-ink-soft m-0">
            Jede VM läuft autark mit eigener IP, eigenem Company Brain und isoliertem Docker-Stack. <strong>300 € Startguthaben aktiv</strong> · Bei Inaktivität pausierbar (0 € Compute-Kosten).
          </p>
        </div>
        <a
          href="https://console.cloud.google.com/billing"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary text-xs shrink-0"
        >
          Kosten & Rechnungen prüfen →
        </a>
      </div>

      {error && (
        <div className="card border-danger/30 bg-danger/10 p-4 text-sm text-danger">
          ⚠️ {error}
        </div>
      )}

      {successMsg && (
        <div className="card border-signal/30 bg-signal/10 p-4 text-sm text-signal flex items-center gap-2">
          <IconCheck size={18} /> {successMsg}
        </div>
      )}

      {/* Grid: Formular + Liste */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Neue VM erstellen (5 Spalten) */}
        <div className="space-y-6 lg:col-span-5">
          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink flex items-center gap-2 m-0">
                <IconServer className="text-signal" size={18} />
                Neue Kunden-VM provisionieren
              </h2>
              <span className="tag text-[11px] font-mono">SÄULE 1</span>
            </div>

            <form onSubmit={handleCreateVm} className="space-y-3.5">
              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">
                  Mandanten-ID (Slug)
                </label>
                <input
                  type="text"
                  placeholder="z.B. kanzlei_schmidt"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  required
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink font-mono focus:outline-none focus:border-signal"
                />
                <span className="text-[10px] text-ink-soft">Wird als VM-Name <code>aios-{tenantId || "slug"}</code> genutzt.</span>
              </div>

              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">
                  Kunden-Firmenname
                </label>
                <input
                  type="text"
                  placeholder="z.B. Kanzlei Schmidt & Kollegen"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">
                  Admin E-Mail-Adresse
                </label>
                <input
                  type="email"
                  placeholder="admin@kunde.de"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">
                  Hardware-Größe (Compute Engine)
                </label>
                <select
                  value={machineType}
                  onChange={(e) => setMachineType(e.target.value)}
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                >
                  <option value="e2-standard-4">e2-standard-4 (4 vCPUs, 16 GB RAM) — Empfohlen (~0,14 €/h)</option>
                  <option value="e2-standard-2">e2-standard-2 (2 vCPUs, 8 GB RAM) — Minimal (~0,07 €/h)</option>
                  <option value="n2-standard-4">n2-standard-4 (4 vCPUs, 16 GB RAM, High-Perf) (~0,20 €/h)</option>
                </select>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={creating}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-2.5 cursor-pointer disabled:opacity-50"
                >
                  {creating ? <IconReload size={16} className="animate-spin" /> : <IconPlus size={16} />}
                  {creating ? "Erstelle Google Cloud VM..." : "Kunden-VM in Google Cloud starten"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Aktive Kunden-VMs (7 Spalten) */}
        <div className="space-y-6 lg:col-span-7">
          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink flex items-center gap-2 m-0">
                <IconWorld className="text-signal" size={18} />
                Instanzen in Google Cloud ({vms.length})
              </h2>
              <span className="tag-signal text-[11px] font-mono">europe-west3-a</span>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12 text-signal gap-2 text-sm">
                <IconReload className="animate-spin" size={18} />
                <span>Lade Instanzen aus Google Cloud...</span>
              </div>
            ) : vms.length === 0 ? (
              <div className="text-center py-12 space-y-3">
                <IconCloud size={40} className="mx-auto text-ink-soft opacity-40" />
                <p className="text-sm text-ink-soft m-0">
                  Noch keine Kunden-VMs in Google Cloud gestartet.
                </p>
                <p className="text-xs text-ink-soft m-0">
                  Nutze das Formular links, um die erste isolierte VM in Frankfurt hochzufahren.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {vms.map((vm) => (
                  <div
                    key={vm.name}
                    className="rounded-lg border border-line bg-paper p-4 space-y-2 text-sm"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-ink font-mono">{vm.name}</span>
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            vm.status === "RUNNING"
                              ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/30"
                              : "bg-slate-500/10 text-slate-600 border border-slate-500/30"
                          }`}
                        >
                          {vm.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {vm.status === "RUNNING" && (
                          <button
                            onClick={() => handleStopVm(vm.name)}
                            className="btn-ghost text-xs text-amber-600 flex items-center gap-1 cursor-pointer"
                            title="VM pausieren um Kosten zu sparen"
                          >
                            <IconPlayerStop size={13} />
                            <span>Pausieren</span>
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs text-ink-soft pt-1">
                      <div>
                        <span className="block font-semibold">Öffentliche IP:</span>
                        <span className="font-mono">{vm.ip_address}</span>
                      </div>
                      <div>
                        <span className="block font-semibold">Maschinen-Typ:</span>
                        <span className="font-mono">{vm.machine_type}</span>
                      </div>
                    </div>

                    {vm.console_url && vm.status === "RUNNING" && (
                      <div className="pt-2 border-t border-line flex items-center justify-between">
                        <span className="text-xs text-ink-soft">Web-Konsole:</span>
                        <a
                          href={vm.console_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-primary text-xs flex items-center gap-1.5 py-1 px-3"
                        >
                          <span>Kunden-Konsole öffnen</span>
                          <IconExternalLink size={12} />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
