"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStoredAuth, AuthUser } from "@/lib/auth";
import {
  IconBuilding,
  IconCheck,
  IconClock,
  IconCoin,
  IconDeviceFloppy,
  IconLock,
  IconPlus,
  IconReload,
  IconSparkles,
  IconTrash,
  IconUsers,
  IconWorld,
  IconShieldLock,
} from "@tabler/icons-react";

interface TeamMember {
  name: string;
  role: string;
  type: string;
  skills: string[];
}

interface CompanyProfile {
  legal_name: string;
  brand_name: string;
  tax_id?: string;
  website?: string;
  industry?: string;
  description?: string;
  founder_or_owner?: string;
  hourly_rates: Record<string, number>;
  team_members: TeamMember[];
  core_services: string[];
  standard_terms: {
    payment_terms_days?: number;
    travel_policy?: string;
  };
}

export default function CompanyProfilePage() {
  const [auth, setAuth] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New item inputs
  const [newRateKey, setNewRateKey] = useState("");
  const [newRateVal, setNewRateVal] = useState<number>(100);
  const [newMemberName, setNewMemberName] = useState("");
  const [newMemberRole, setNewMemberRole] = useState("");
  const [newMemberType, setNewMemberType] = useState("freelancer");
  const [newMemberSkills, setNewMemberSkills] = useState("");
  const [newService, setNewService] = useState("");

  useEffect(() => {
    const currentAuth = getStoredAuth();
    setAuth(currentAuth);

    if (currentAuth.role === "admin") {
      loadProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/company/profile?tenant_id=nextchapter");
      if (!res.ok) throw new Error("Fehler beim Laden des Unternehmensprofils");
      const data = await res.json();
      setProfile(data.profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    setSavedSuccess(false);
    setError(null);
    try {
      const res = await fetch("/api/company/profile?tenant_id=nextchapter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) throw new Error("Fehler beim Speichern");
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  };

  const addHourlyRate = () => {
    if (!newRateKey.trim() || !profile) return;
    setProfile({
      ...profile,
      hourly_rates: {
        ...profile.hourly_rates,
        [newRateKey.trim().toLowerCase().replace(/\s+/g, "_")]: Number(newRateVal),
      },
    });
    setNewRateKey("");
    setNewRateVal(100);
  };

  const removeHourlyRate = (key: string) => {
    if (!profile) return;
    const next = { ...profile.hourly_rates };
    delete next[key];
    setProfile({ ...profile, hourly_rates: next });
  };

  const addTeamMember = () => {
    if (!newMemberName.trim() || !profile) return;
    const skills = newMemberSkills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const newMember: TeamMember = {
      name: newMemberName.trim(),
      role: newMemberRole.trim() || "Team Member",
      type: newMemberType,
      skills,
    };
    setProfile({
      ...profile,
      team_members: [...profile.team_members, newMember],
    });
    setNewMemberName("");
    setNewMemberRole("");
    setNewMemberSkills("");
  };

  const removeTeamMember = (idx: number) => {
    if (!profile) return;
    setProfile({
      ...profile,
      team_members: profile.team_members.filter((_, i) => i !== idx),
    });
  };

  const addService = () => {
    if (!newService.trim() || !profile) return;
    setProfile({
      ...profile,
      core_services: [...profile.core_services, newService.trim()],
    });
    setNewService("");
  };

  const removeService = (idx: number) => {
    if (!profile) return;
    setProfile({
      ...profile,
      core_services: profile.core_services.filter((_, i) => i !== idx),
    });
  };

  // 1. Check Role Permission: Only Admin allowed!
  if (auth && auth.role !== "admin") {
    return (
      <div className="rise mx-auto max-w-3xl space-y-6 py-12 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 border border-amber-500/30">
          <IconLock size={32} />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-ink">Zugriff verweigert (Administrator erforderlich)</h1>
          <p className="text-sm text-ink-soft max-w-lg mx-auto">
            Die Unternehmens-Identität, Stundensätze und Plattform-Stammdaten dürfen ausschließlich vom <strong>Administrator</strong> eingesehen und verändert werden.
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

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="flex items-center gap-3 text-signal">
          <IconReload className="h-6 w-6 animate-spin" />
          <span className="text-sm font-medium">Lade Unternehmens-Identität...</span>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="card text-center text-danger p-8">
        <p className="m-0 mb-4">Profil konnte nicht geladen werden.</p>
        <button onClick={loadProfile} className="btn-secondary text-xs">
          Erneut versuchen
        </button>
      </div>
    );
  }

  return (
    <section className="rise space-y-8">
      {/* Header Bar im Admin-Design */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="tag-signal flex items-center gap-1 font-mono text-[11px]">
              <IconShieldLock size={12} /> ADMIN SSOT
            </span>
            <span className="text-xs text-ink-soft">Wurzel im Company Brain</span>
          </div>
          <h1 className="section-title text-3xl m-0 flex items-center gap-2">
            Unternehmens-Identität
          </h1>
          <p className="muted m-0 max-w-2xl text-sm pt-1">
            Zentrale Stammdaten, Stundensätze und Kapazitäten. Wird automatisch als <code>enterprise</code> Context-Slice in alle KI-Agenten injiziert.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {savedSuccess && (
            <span className="flex items-center gap-1.5 text-xs font-semibold text-signal animate-pulse">
              <IconCheck size={16} /> Im Company Brain gespeichert!
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary flex items-center gap-2 shadow-md cursor-pointer disabled:opacity-50"
          >
            {saving ? <IconReload size={16} className="animate-spin" /> : <IconDeviceFloppy size={16} />}
            {saving ? "Speichere..." : "Profil im Brain speichern"}
          </button>
        </div>
      </div>

      {error && (
        <div className="card border-danger/30 bg-danger/10 p-4 text-sm text-danger">
          ⚠️ {error}
        </div>
      )}

      {/* Grid Layout nach Admin-Spezifikation */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Linke Spalte: Basisdaten & Rechtliches (7 Cols) */}
        <div className="space-y-6 lg:col-span-7">
          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink flex items-center gap-2 m-0">
                <IconBuilding className="text-signal" size={18} />
                Basisdaten & Rechtliche Identität
              </h2>
              <span className="tag text-[11px] font-mono">org:EnterpriseProfile</span>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">Offizieller Firmenname / Inhaber</label>
                <input
                  type="text"
                  value={profile.legal_name}
                  onChange={(e) => setProfile({ ...profile, legal_name: e.target.value })}
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">Markenname / Brand</label>
                <input
                  type="text"
                  value={profile.brand_name}
                  onChange={(e) => setProfile({ ...profile, brand_name: e.target.value })}
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">USt-IdNr. / Steuernummer</label>
                <input
                  type="text"
                  value={profile.tax_id ?? ""}
                  onChange={(e) => setProfile({ ...profile, tax_id: e.target.value })}
                  placeholder="DE..."
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink font-mono focus:outline-none focus:border-signal"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-ink-soft block mb-1">Webseite / URL</label>
                <input
                  type="text"
                  value={profile.website ?? ""}
                  onChange={(e) => setProfile({ ...profile, website: e.target.value })}
                  placeholder="https://..."
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-ink-soft block mb-1">Gründer, Inhaber & Geschäftsführung</label>
                <input
                  type="text"
                  value={profile.founder_or_owner ?? ""}
                  onChange={(e) => setProfile({ ...profile, founder_or_owner: e.target.value })}
                  placeholder="Name & Rolle"
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-ink-soft block mb-1">Branche & Tätigkeitsfeld</label>
                <input
                  type="text"
                  value={profile.industry ?? ""}
                  onChange={(e) => setProfile({ ...profile, industry: e.target.value })}
                  placeholder="z.B. KI-Consulting & Agenten-Workflows"
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-ink-soft block mb-1">Unternehmensbeschreibung (Globaler KI-Kontext)</label>
                <textarea
                  rows={3}
                  value={profile.description ?? ""}
                  onChange={(e) => setProfile({ ...profile, description: e.target.value })}
                  placeholder="Kurze Zusammenfassung des Geschäftsmodells..."
                  className="w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink focus:outline-none focus:border-signal"
                />
              </div>
            </div>
          </div>

          {/* Kernangebote & Spezialisierungen */}
          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink flex items-center gap-2 m-0">
                <IconSparkles className="text-warn" size={18} />
                Kernangebote & Spezialisierungen
              </h2>
              <span className="text-xs text-ink-soft">{profile.core_services.length} Bereiche</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {profile.core_services.map((srv, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-paper-2 px-2.5 py-1 text-xs text-ink"
                >
                  <span>{srv}</span>
                  <button
                    onClick={() => removeService(idx)}
                    className="text-ink-soft hover:text-danger cursor-pointer ml-1"
                    title="Entfernen"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            <div className="flex gap-2 pt-2">
              <input
                type="text"
                placeholder="Neues Angebot (z.B. KI-Architektur-Audit)..."
                value={newService}
                onChange={(e) => setNewService(e.target.value)}
                className="flex-1 rounded-lg border border-line bg-paper px-3 py-1.5 text-xs text-ink focus:outline-none focus:border-signal"
              />
              <button
                onClick={addService}
                className="btn-ghost text-xs cursor-pointer"
              >
                + Hinzufügen
              </button>
            </div>
          </div>
        </div>

        {/* Rechte Spalte: Stundensätze & Team (5 Cols) */}
        <div className="space-y-6 lg:col-span-5">
          {/* Stundensätze */}
          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink flex items-center gap-2 m-0">
                <IconCoin className="text-signal" size={18} />
                Stundensätze & Abrechnung
              </h2>
              <span className="tag-signal text-[11px] font-mono">EUR NETTO</span>
            </div>

            <div className="row-list">
              {Object.entries(profile.hourly_rates).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <span className="font-mono text-xs text-ink-soft capitalize">{key.replace(/_/g, " ")}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-signal mono">{val} €</span>
                    <button
                      onClick={() => removeHourlyRate(key)}
                      className="text-ink-soft hover:text-danger cursor-pointer p-1"
                      title="Löschen"
                    >
                      <IconTrash size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-12 gap-2 pt-2 border-t border-line">
              <input
                type="text"
                placeholder="Rollenname..."
                value={newRateKey}
                onChange={(e) => setNewRateKey(e.target.value)}
                className="col-span-7 rounded-lg border border-line bg-paper px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-signal"
              />
              <input
                type="number"
                value={newRateVal}
                onChange={(e) => setNewRateVal(Number(e.target.value))}
                className="col-span-3 rounded-lg border border-line bg-paper px-2 py-1.5 text-xs text-ink font-mono focus:outline-none focus:border-signal"
              />
              <button
                onClick={addHourlyRate}
                className="col-span-2 btn-secondary flex items-center justify-center text-signal cursor-pointer"
                title="Hinzufügen"
              >
                <IconPlus size={15} />
              </button>
            </div>

            <div className="pt-2 text-xs text-ink-soft border-t border-line">
              <label className="block mb-1 font-semibold">Standard-Zahlungsziel (Tage)</label>
              <input
                type="number"
                value={profile.standard_terms?.payment_terms_days ?? 14}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    standard_terms: {
                      ...profile.standard_terms,
                      payment_terms_days: Number(e.target.value),
                    },
                  })
                }
                className="w-24 rounded-lg border border-line bg-paper px-3 py-1 text-xs text-ink font-mono focus:outline-none focus:border-signal"
              />
            </div>
          </div>

          {/* Team & Mitarbeiter */}
          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h2 className="text-base font-bold text-ink flex items-center gap-2 m-0">
                <IconUsers className="text-signal" size={18} />
                Team & Mitarbeiter
              </h2>
              <span className="text-xs text-ink-soft">{profile.team_members.length} Personen</span>
            </div>

            <div className="space-y-2.5">
              {profile.team_members.map((m, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-line bg-paper p-2.5 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-ink text-sm">{m.name}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="tag text-[10px] font-mono uppercase">
                        {m.type}
                      </span>
                      <button
                        onClick={() => removeTeamMember(idx)}
                        className="text-ink-soft hover:text-danger cursor-pointer p-0.5"
                        title="Entfernen"
                      >
                        <IconTrash size={13} />
                      </button>
                    </div>
                  </div>
                  <div className="text-ink-soft text-[11px]">{m.role}</div>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {m.skills.map((s, i) => (
                      <span key={i} className="rounded bg-paper-2 px-1.5 py-0.2 text-[10px] text-ink-soft">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Mitarbeiter hinzufügen */}
            <div className="space-y-2 pt-2 border-t border-line">
              <div className="text-xs font-semibold text-ink">+ Person erfassen</div>
              <input
                type="text"
                placeholder="Name (z.B. Studentischer Mitarbeiter)..."
                value={newMemberName}
                onChange={(e) => setNewMemberName(e.target.value)}
                className="w-full rounded-lg border border-line bg-paper px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-signal"
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="Rolle (z.B. Mini-Jobber)..."
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value)}
                  className="rounded-lg border border-line bg-paper px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-signal"
                />
                <select
                  value={newMemberType}
                  onChange={(e) => setNewMemberType(e.target.value)}
                  className="rounded-lg border border-line bg-paper px-2 py-1.5 text-xs text-ink focus:outline-none focus:border-signal"
                >
                  <option value="freelancer">Freelancer / Inhaber</option>
                  <option value="minijobber">Mini-Jobber / Student</option>
                  <option value="angestellter">Angestellter</option>
                  <option value="partner">Partner</option>
                </select>
              </div>
              <input
                type="text"
                placeholder="Skills (z.B. Python, Research, Ingest)..."
                value={newMemberSkills}
                onChange={(e) => setNewMemberSkills(e.target.value)}
                className="w-full rounded-lg border border-line bg-paper px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-signal"
              />
              <button
                onClick={addTeamMember}
                className="w-full btn-secondary text-xs py-1.5 cursor-pointer"
              >
                + Person zum Team hinzufügen
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
