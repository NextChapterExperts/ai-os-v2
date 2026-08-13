"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { loginUser } from "@/lib/auth";
import {
  IconLock,
  IconUserCheck,
  IconShieldLock,
  IconArrowRight,
  IconAlertTriangle,
} from "@tabler/icons-react";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleLogin = (u: string, p: string) => {
    setError(null);
    const user = loginUser(u, p);
    if (user) {
      if (typeof window !== "undefined") {
        window.location.href = "/";
      } else {
        router.push("/");
      }
    } else {
      setError("Ungültige Anmeldedaten. Bitte verwenden Sie peter/peter oder admin/admin.");
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(username, password);
  };

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)] flex flex-col justify-center items-center px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-[color-mix(in_oklab,var(--signal)_15%,white)] text-[var(--signal)] border border-[var(--signal)] mb-2 shadow-md">
            <IconShieldLock size={32} />
          </div>
          <h1 className="font-mystic text-3xl font-extrabold tracking-wider text-[var(--ink)] uppercase m-0">
            VIRKI <span className="text-[var(--signal)]">AI-OS</span>
          </h1>
          <p className="text-xs text-[var(--ink-soft)] font-sans m-0">
            Souveränes KI-Betriebssystem · Anmelden & Arbeiten
          </p>
        </div>

        {/* Login Form Card */}
        <div className="bg-white border border-[var(--line)] rounded-3xl p-8 shadow-xl space-y-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--ink)] mb-1.5">
                Benutzername
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="peter oder admin"
                className="w-full bg-[color-mix(in_oklab,white_90%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:border-[var(--signal)] font-mono transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--ink)] mb-1.5">
                Passwort
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Passwort eingeben"
                className="w-full bg-[color-mix(in_oklab,white_90%,transparent)] border border-[var(--line)] text-[var(--ink)] rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:border-[var(--signal)] font-mono transition-colors"
                required
              />
            </div>

            {error && (
              <div className="p-3 rounded-xl border border-[var(--danger)] bg-[color-mix(in_oklab,var(--danger)_10%,white)] text-[var(--danger)] text-xs mono flex items-center gap-2">
                <IconAlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="w-full btn-primary rounded-xl py-3 text-xs font-bold inline-flex items-center justify-center gap-2 cursor-pointer shadow-md"
            >
              <span>Anmelden</span>
              <IconArrowRight size={16} />
            </button>
          </form>

          <div className="border-t border-[var(--line)] pt-5 space-y-3">
            <span className="text-[11px] font-mono muted uppercase block text-center tracking-wider">
              Schnellanmeldung (1-Klick)
            </span>

            <div className="grid grid-cols-1 gap-2.5">
              <button
                type="button"
                onClick={() => handleLogin("peter", "peter")}
                className="w-full p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_80%,transparent)] hover:border-[var(--signal)] hover:bg-white text-xs text-left transition-all flex items-center justify-between cursor-pointer group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-[color-mix(in_oklab,var(--signal)_15%,white)] text-[var(--signal)]">
                    <IconUserCheck size={16} />
                  </div>
                  <div>
                    <div className="font-bold text-[var(--ink)] group-hover:text-[var(--signal)]">
                      peter / peter
                    </div>
                    <div className="text-[10px] muted">Endanwender · Navigationsrad & Search Agent</div>
                  </div>
                </div>
                <IconArrowRight size={14} className="text-[var(--ink-soft)] group-hover:text-[var(--signal)]" />
              </button>

              <button
                type="button"
                onClick={() => handleLogin("admin", "admin")}
                className="w-full p-3 rounded-xl border border-[var(--line)] bg-[color-mix(in_oklab,white_80%,transparent)] hover:border-slate-800 hover:bg-slate-900 hover:text-white text-xs text-left transition-all flex items-center justify-between cursor-pointer group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-slate-200 text-slate-800 group-hover:bg-slate-800 group-hover:text-white">
                    <IconLock size={16} />
                  </div>
                  <div>
                    <div className="font-bold text-[var(--ink)] group-hover:text-white">
                      admin / admin
                    </div>
                    <div className="text-[10px] muted group-hover:text-slate-300">Administrator · Entwickler & Plattform Layout</div>
                  </div>
                </div>
                <IconArrowRight size={14} className="text-[var(--ink-soft)] group-hover:text-white" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
