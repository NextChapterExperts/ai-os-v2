"use client";

import { useState, useEffect } from "react";

type MilestoneState = "queued" | "in_execution" | "released";

interface StrategicMilestone {
  id: string;
  project: string;
  gate: string;
  title: string;
  deliverable: string;
  targetDate: string;
  isCriticalPath?: boolean;
  defaultState: MilestoneState;
}

const STRATEGIC_MILESTONES: StrategicMilestone[] = [
  {
    id: "waqam-gate-1",
    project: "waqam-project",
    gate: "Gate 1 · Kickoff",
    title: "Studenten-Pitch & Rollenvergabe",
    deliverable: "Projekt-Pitch (projekt_pitch_studenten_de.md) freigeben & Rollen zuweisen.",
    targetDate: "27.07.2026 (Montag)",
    isCriticalPath: true,
    defaultState: "queued",
  },
  {
    id: "waqam-gate-2a",
    project: "waqam-project",
    gate: "Gate 2A · Scoping",
    title: "Paket 1: SAP AI Portfolio & Scoping",
    deliverable: "Grundlagen Autonomous Enterprise & Feature-Bewertung finalisieren.",
    targetDate: "28.07.2026 (Dienstag)",
    isCriticalPath: true,
    defaultState: "queued",
  },
  {
    id: "waqam-gate-2b",
    project: "waqam-project",
    gate: "Gate 2B · Simulator",
    title: "Paket 2: Stochastik, Risiko & Simulator-Kopplung",
    deliverable: "Realpessimismus-Blog-Hürden mit Störungs-Handbuch & Simulator koppeln.",
    targetDate: "31.07.2026 (Freitag)",
    isCriticalPath: true,
    defaultState: "queued",
  },
  {
    id: "waqam-gate-3",
    project: "waqam-project",
    gate: "Gate 3 · Board UI",
    title: "Paket 3: WAQAM Board Overhaul & EXT-01",
    deliverable: "Waqamboard UI & Lieferanten-Onboarding Störungs-Szenario überarbeiten.",
    targetDate: "04.08.2026 (Dienstag)",
    isCriticalPath: true,
    defaultState: "queued",
  },
  {
    id: "waqam-gate-4",
    project: "waqam-project",
    gate: "Gate 4 · Go-Live",
    title: "🎉 Go-Live Release: Studenten-Projekt Startklar",
    deliverable: "Paket 1–3 als PDF & GitHub-Repository für Studenten freigeben.",
    targetDate: "07.08.2026 (Freitag)",
    isCriticalPath: true,
    defaultState: "queued",
  },
];

const PORTFOLIO_HORIZON = [
  { name: "ai-sap-videos", target: "Ende Aug. 2026", status: "3 Video-Skripte & Clips" },
  { name: "redrays-btp", target: "Anfang Sept. 2026", status: "Alignment BTP-Security" },
  { name: "lizenz-simulation", target: "Oktober 2026", status: "BTP Lizenz-Simulator" },
  { name: "website-nce", target: "Continuous", status: "Live-Prototyp & Branding" },
  { name: "1100-AI-OS-V2", target: "Continuous", status: "Platform Engine & Muninn" },
];

export function DailyFocusPanel() {
  const [states, setStates] = useState<Record<string, MilestoneState>>({});

  useEffect(() => {
    const saved = localStorage.getItem("aios_portfolio_milestone_states");
    if (saved) {
      try {
        setStates(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse milestone states", e);
      }
    }
  }, []);

  const cycleState = (id: string, currentState: MilestoneState) => {
    const next: Record<MilestoneState, MilestoneState> = {
      queued: "in_execution",
      in_execution: "released",
      released: "queued",
    };
    const updated = { ...states, [id]: next[currentState] };
    setStates(updated);
    localStorage.setItem("aios_portfolio_milestone_states", JSON.stringify(updated));
  };

  const getState = (m: StrategicMilestone): MilestoneState => {
    return states[m.id] || m.defaultState;
  };

  const releasedCount = STRATEGIC_MILESTONES.filter((m) => getState(m) === "released").length;
  const totalCount = STRATEGIC_MILESTONES.length;
  const progressPct = Math.round((releasedCount / totalCount) * 100);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 shadow-2xl backdrop-blur-md text-slate-100">
      {/* Ambient background glow */}
      <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-amber-500/10 blur-3xl" />

      {/* Executive Header */}
      <div className="relative z-10 flex flex-col gap-4 border-b border-slate-800/80 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/15 px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider text-rose-300 border border-rose-500/30">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-pulse" />
              Critical Path Prio 1
            </span>
            <span className="mono text-xs font-medium text-cyan-400">
              waqam-project · Release Readiness
            </span>
          </div>
          <h2 className="mt-1.5 text-2xl font-black tracking-tight text-white">
            Portfolio Control Radar
          </h2>
          <p className="mt-0.5 text-xs text-slate-400">
            Meilenstein-Steuerung für den Studenten-Start · Ziel-Go-Live: <strong className="text-slate-200">07.08.2026</strong>
          </p>
        </div>

        {/* Executive Progress Ring / Metric */}
        <div className="flex items-center gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-3 backdrop-blur-sm">
          <div className="text-right">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Target Progress</div>
            <div className="text-lg font-black text-white">
              {releasedCount} / {totalCount} <span className="text-xs font-medium text-cyan-400">({progressPct}%)</span>
            </div>
          </div>
          <div className="h-10 w-10 rounded-full border-2 border-slate-700 p-0.5 flex items-center justify-center">
            <div
              className="h-full w-full rounded-full bg-gradient-to-tr from-amber-400 to-cyan-400 transition-all duration-500"
              style={{ opacity: progressPct > 0 ? 1 : 0.2 }}
            />
          </div>
        </div>
      </div>

      {/* Critical Path Milestone Pipeline */}
      <div className="relative z-10 mt-6 space-y-3">
        <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-amber-300">
          <span>🎯 Meilenstein-Pipeline (Freigabe-Roadmap bis 07.08.)</span>
          <span className="text-[11px] font-normal text-slate-400">Klick auf Karte ändert Status</span>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {STRATEGIC_MILESTONES.map((m) => {
            const state = getState(m);
            return (
              <div
                key={m.id}
                onClick={() => cycleState(m.id, state)}
                className={`group cursor-pointer rounded-xl border p-4 transition-all duration-200 hover:-translate-y-0.5 ${
                  state === "released"
                    ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-100 shadow-emerald-950/50"
                    : state === "in_execution"
                    ? "border-amber-500/60 bg-amber-950/30 text-amber-100 shadow-amber-950/50"
                    : "border-slate-800 bg-slate-950/70 hover:border-cyan-500/40"
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-bold">
                  <span className="mono text-cyan-400">{m.gate}</span>
                  <span
                    className={`rounded px-1.5 py-0.5 uppercase tracking-wider ${
                      state === "released"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : state === "in_execution"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}
                  >
                    {state === "released" ? "RELEASED" : state === "in_execution" ? "IN EXECUTION" : "QUEUED"}
                  </span>
                </div>

                <h4 className="mt-2 text-xs font-bold leading-snug text-white group-hover:text-cyan-300 transition-colors">
                  {m.title}
                </h4>

                <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400 line-clamp-3">
                  {m.deliverable}
                </p>

                <div className="mt-3 border-t border-slate-800/60 pt-2 text-[10px] font-mono text-slate-400">
                  {m.targetDate}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Strategic Horizon Radar */}
      <div className="relative z-10 mt-6 border-t border-slate-800/80 pt-4">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
          🌌 Portfolio Horizon (Strategischer Ausblick)
        </div>

        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3 lg:grid-cols-5 text-xs">
          {PORTFOLIO_HORIZON.map((item) => (
            <div
              key={item.name}
              className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-3 transition-colors hover:border-slate-700"
            >
              <div className="font-bold text-slate-200">{item.name}</div>
              <div className="mt-0.5 text-[11px] font-medium text-amber-300">{item.target}</div>
              <div className="mt-1 text-[10px] text-slate-400 truncate">{item.status}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
