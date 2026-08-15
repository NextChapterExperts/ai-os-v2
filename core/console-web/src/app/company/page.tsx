"use client";

import { useEffect, useState } from "react";
import {
  IconBuilding,
  IconCheck,
  IconClock,
  IconCoin,
  IconDeviceFloppy,
  IconPlus,
  IconReload,
  IconSparkles,
  IconTrash,
  IconUsers,
  IconWorld,
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

  useEffect(() => {
    loadProfile();
  }, []);

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

  if (loading) {
    return (
      <div className="flex min-h-[600px] items-center justify-center">
        <div className="flex items-center gap-3 text-cyan-400">
          <IconReload className="h-6 w-6 animate-spin" />
          <span className="text-sm font-medium">Lade Unternehmens-Identität...</span>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-8 text-center text-rose-400">
        <p>Profil konnte nicht geladen werden.</p>
        <button onClick={loadProfile} className="mt-4 rounded bg-slate-800 px-4 py-2 text-xs text-white">
          Erneut versuchen
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-8 p-4 sm:p-8">
      {/* Header Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-cyan-500/20 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-cyan-500/10 p-2.5 text-cyan-400 ring-1 ring-cyan-500/30">
              <IconBuilding size={28} />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
                Unternehmens-Identität
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
                  Company Brain SSOT
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400">
                Die zentrale DNA & Stammparameter für alle KI-Agenten, Angebote, Chats und Workflows.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {savedSuccess && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 animate-pulse">
              <IconCheck size={16} /> Im Company Brain gespeichert!
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            {saving ? <IconReload size={18} className="animate-spin" /> : <IconDeviceFloppy size={18} />}
            {saving ? "Speichere..." : "Profil speichern"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          ⚠️ {error}
        </div>
      )}

      {/* Grid Sections */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* 1. Basis-Identität & Rechtliches (7 Spalten) */}
        <div className="space-y-6 lg:col-span-7">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <IconWorld className="text-cyan-400" size={20} />
              Basisdaten & Rechtliche Identität
            </h2>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">Offizieller Firmenname / Inhaber</label>
                <input
                  type="text"
                  value={profile.legal_name}
                  onChange={(e) => setProfile({ ...profile, legal_name: e.target.value })}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">Markenname / Brand</label>
                <input
                  type="text"
                  value={profile.brand_name}
                  onChange={(e) => setProfile({ ...profile, brand_name: e.target.value })}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">USt-IdNr. / Steuernummer</label>
                <input
                  type="text"
                  value={profile.tax_id ?? ""}
                  onChange={(e) => setProfile({ ...profile, tax_id: e.target.value })}
                  placeholder="DE..."
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">Webseite / URL</label>
                <input
                  type="text"
                  value={profile.website ?? ""}
                  onChange={(e) => setProfile({ ...profile, website: e.target.value })}
                  placeholder="https://..."
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-slate-400 block mb-1">Gründer, Inhaber & Geschäftsführung</label>
                <input
                  type="text"
                  value={profile.founder_or_owner ?? ""}
                  onChange={(e) => setProfile({ ...profile, founder_or_owner: e.target.value })}
                  placeholder="Name & Rolle"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-slate-400 block mb-1">Branche & Tätigkeitsfeld</label>
                <input
                  type="text"
                  value={profile.industry ?? ""}
                  onChange={(e) => setProfile({ ...profile, industry: e.target.value })}
                  placeholder="z.B. KI-Consulting & Agenten-Workflows"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-slate-400 block mb-1">Unternehmensbeschreibung (Agenten-Kontext)</label>
                <textarea
                  rows={3}
                  value={profile.description ?? ""}
                  onChange={(e) => setProfile({ ...profile, description: e.target.value })}
                  placeholder="Kurze Zusammenfassung des Geschäftsmodells..."
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Kernangebote */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <IconSparkles className="text-amber-400" size={20} />
              Kernangebote & Spezialisierungen
            </h2>

            <div className="flex flex-wrap gap-2">
              {profile.core_services.map((srv, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200"
                >
                  {srv}
                  <button
                    onClick={() => removeService(idx)}
                    className="text-slate-500 hover:text-rose-400 cursor-pointer ml-1"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            <div className="flex gap-2 pt-2">
              <input
                type="text"
                placeholder="Neues Angebot (z.B. KI-Workshops)..."
                value={newService}
                onChange={(e) => setNewService(e.target.value)}
                className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              />
              <button
                onClick={addService}
                className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-cyan-400 hover:bg-slate-700 cursor-pointer"
              >
                + Hinzufügen
              </button>
            </div>
          </div>
        </div>

        {/* 2. Stundensätze, Team & Abrechnung (5 Spalten) */}
        <div className="space-y-6 lg:col-span-5">
          {/* Stundensätze */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <IconCoin className="text-emerald-400" size={20} />
              Stundensätze & Abrechnungskonditionen
            </h2>

            <div className="space-y-2">
              {Object.entries(profile.hourly_rates).map(([key, val]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm"
                >
                  <span className="font-mono text-xs text-cyan-300 capitalize">{key.replace(/_/g, " ")}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-emerald-400">{val} €</span>
                    <button
                      onClick={() => removeHourlyRate(key)}
                      className="text-slate-500 hover:text-rose-400 cursor-pointer"
                      title="Löschen"
                    >
                      <IconTrash size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-12 gap-2 pt-2 border-t border-slate-800">
              <input
                type="text"
                placeholder="Rollenname..."
                value={newRateKey}
                onChange={(e) => setNewRateKey(e.target.value)}
                className="col-span-7 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              />
              <input
                type="number"
                value={newRateVal}
                onChange={(e) => setNewRateVal(Number(e.target.value))}
                className="col-span-3 rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              />
              <button
                onClick={addHourlyRate}
                className="col-span-2 flex items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 cursor-pointer"
                title="Hinzufügen"
              >
                <IconPlus size={16} />
              </button>
            </div>

            <div className="pt-2 text-xs text-slate-400">
              <label className="block mb-1">Standard-Zahlungsziel (Tage)</label>
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
                className="w-24 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Team & Mitarbeiter */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <IconUsers className="text-indigo-400" size={20} />
              Team & Mitarbeiter-Kapazitäten
            </h2>

            <div className="space-y-3">
              {profile.team_members.map((m, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{m.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/30 uppercase">
                        {m.type}
                      </span>
                      <button
                        onClick={() => removeTeamMember(idx)}
                        className="text-slate-500 hover:text-rose-400 cursor-pointer"
                      >
                        <IconTrash size={14} />
                      </button>
                    </div>
                  </div>
                  <div className="text-slate-400">{m.role}</div>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {m.skills.map((s, i) => (
                      <span key={i} className="rounded bg-slate-900 px-1.5 py-0.5 text-[10px] text-slate-300 border border-slate-800">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Add Team Member */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="text-xs font-semibold text-slate-300">+ Mitarbeiter/Rolle erfassen</div>
              <input
                type="text"
                placeholder="Name (z.B. Studentischer Mitarbeiter)..."
                value={newMemberName}
                onChange={(e) => setNewMemberName(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="Rolle (z.B. Mini-Jobber)..."
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
                />
                <select
                  value={newMemberType}
                  onChange={(e) => setNewMemberType(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
                >
                  <option value="freelancer">Freelancer / Inhaber</option>
                  <option value="minijobber">Mini-Jobber / Student</option>
                  <option value="angestellter">Angestellter</option>
                  <option value="partner">Partner</option>
                </select>
              </div>
              <input
                type="text"
                placeholder="Skills (kommagetrennt, z.B. Python, Research, Ingest)..."
                value={newMemberSkills}
                onChange={(e) => setNewMemberSkills(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
              />
              <button
                onClick={addTeamMember}
                className="w-full rounded-lg bg-indigo-500/20 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/30 cursor-pointer"
              >
                + Mitglied speichern
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
