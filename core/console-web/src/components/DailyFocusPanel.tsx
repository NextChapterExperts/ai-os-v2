"use client";

import { useState, useEffect } from "react";

type MilestoneState = "pending" | "active" | "completed";

interface PhaseGate {
  id: string;
  phaseNumber: string;
  title: string;
  subtitle: string;
  dateRange: string;
  deliverableFile: string;
  description: string;
  keyActions: string[];
  defaultState: MilestoneState;
}

const V2_REPO_PATH = "/home/peter/Projekte/active/studentenprojekt_v2";
const PHASE_STORAGE_KEY = "aios_waqam_v2_phase_states";

const PHASES: PhaseGate[] = [
  {
    id: "saeule-1",
    phaseNumber: "01",
    title: "Säule 1: Enablement",
    subtitle: "Demystifizieren & Abholen",
    dateRange: "Mo. – Di.",
    deliverableFile: "saeule_1_enablement/00_AP_Uebersicht_Saeule1.md",
    description:
      "Master-Index, KI-Grundbegriffe (Tokens, RAG, Agents), 5 KI-Modi, 4 Strategie-Typen und A3-Übersetzer-Canvas für den Workshop-Einstieg.",
    keyActions: [
      "Fact-Sheets zu KI-Basics & Enterprise-Modi finalisieren",
      "A3-Übersetzer-Canvas (4 Perspektiven) freigeben",
      "Kickoff-Leitfaden & Rollenverteilung verknüpfen",
    ],
    defaultState: "completed",
  },
  {
    id: "saeule-2",
    phaseNumber: "02",
    title: "Säule 2: KI-Herausforderungen",
    subtitle: "11 Risiken & Live-Blog-Simulator",
    dateRange: "Mi.",
    deliverableFile: "saeule_2_herausforderungen_simulator/00_AP_Uebersicht_Saeule2.md",
    description:
      "11 stochastische KI-Risiken aus den Realpessimismus-Blogs erfassen und Live-Blog-Simulator für Bot-Provokation im Workshop spezifizieren (TRICUS-Verstöße).",
    keyActions: [
      "11 Risiken mit Blog-Belegen dokumentieren (Failing Silently, RAG-Drift, …)",
      "Live-Simulator für 6–7 Kern-Blogs spezifizieren",
      "TRICUS-Regeln als Workshop-Nachweis verankern",
    ],
    defaultState: "active",
  },
  {
    id: "saeule-3",
    phaseNumber: "03",
    title: "Säule 3: SAP-Lösungsarchitektur",
    subtitle: "Gegenmittel & AI Stack",
    dateRange: "Do.",
    deliverableFile: "saeule_3_sap_loesungsarchitektur/00_AP_Uebersicht_Saeule3.md",
    description:
      "SAP-Gegenmittel zu allen 11 Herausforderungen aus Säule 2 — BTP Validation Gates, GenAI Hub, Loop-Breaker, Event Mesh, HITL — plus SAP AI Stack entlang IA-AI-Framework.",
    keyActions: [
      "1:1-Mapping Risiko → SAP-Gegenmittel erstellen",
      "Joule Suite, AI Hub, Knowledge Graph & Clean Core dokumentieren",
      "Referenzhandbuch Säule 3 als Berater-Artefakt abschließen",
    ],
    defaultState: "pending",
  },
  {
    id: "saeule-4",
    phaseNumber: "04",
    title: "Säule 4: Use-Case & Simulation",
    subtitle: "Datenblatt & WAQAM PCS",
    dateRange: "Fr.",
    deliverableFile: "saeule_4_use_case_simulation/00_AP_Uebersicht_Saeule4.md",
    description:
      "Use-Case-Datenblätter (10 Dimensionen) für 1–3 Kunden-Workflows (z. B. EXT-01) und WAQAM PCS-Simulation über 4 Betriebsarten vorbereiten.",
    keyActions: [
      "Datenblatt-Vorlage mit Parametern V, Q, U, C, L, N, P ausfüllen",
      "WAQAM Board PCS-Simulation (Deterministisch → Agentenmodus) testen",
      "EXT-01 Szenario als Referenz-Use-Case durchspielen",
    ],
    defaultState: "pending",
  },
  {
    id: "lcc-release",
    phaseNumber: "05",
    title: "LCC-Release V2",
    subtitle: "Projektpaket abgabebereit",
    dateRange: "Fr. (Release)",
    deliverableFile: "01_ROADMAP.md",
    description:
      "Komplettes 4-Säulen-Projektpaket V2 im LCC (Landshut Competence Center) abgabe- und startbereit — inklusive aller Säulen-Artefakte und Studenten-Kit.",
    keyActions: [
      "Dry Run aus Studierenden-Perspektive durchführen",
      "Alle Säulen-Ordner & Fact-Sheets auf Vollständigkeit prüfen",
      "LCC-Upload & Freigabe für Studierenden-Start",
    ],
    defaultState: "pending",
  },
];

const OTHER_PROJECTS = [
  { name: "ai-sap-videos", date: "Ende Aug. 2026", scope: "Wissensaufbau & SAP AI Enablement (Lernen)", tag: "W-Unterstützung" },
  { name: "redrays-btp", date: "Anfang Sept. 2026", scope: "Alignment BTP Security Scanner", tag: "Security" },
  { name: "lizenz-simulation", date: "Oktober 2026", scope: "BTP Lizenz- & Kosten-Simulator", tag: "Tooling" },
  { name: "website-nce", date: "Continuous", scope: "VIRKI Landingpage & Prototyp", tag: "Web" },
  { name: "1100-AI-OS-V2", date: "Continuous", scope: "Platform Engine & Governance", tag: "Platform" },
];

export function DailyFocusPanel() {
  const [phaseStates, setPhaseStates] = useState<Record<string, MilestoneState>>({});
  const [selectedPhaseId, setSelectedPhaseId] = useState<string>("saeule-2");

  useEffect(() => {
    const saved = localStorage.getItem(PHASE_STORAGE_KEY);
    if (saved) {
      try {
        setPhaseStates(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse phase states", e);
      }
    }
  }, []);

  const setPhaseState = (id: string, state: MilestoneState) => {
    const updated = { ...phaseStates, [id]: state };
    setPhaseStates(updated);
    localStorage.setItem(PHASE_STORAGE_KEY, JSON.stringify(updated));
  };

  const getPhaseState = (phase: PhaseGate): MilestoneState => {
    return phaseStates[phase.id] || phase.defaultState;
  };

  const completedCount = PHASES.filter((p) => getPhaseState(p) === "completed").length;
  const progressPct = Math.round((completedCount / PHASES.length) * 100);
  const activePhase = PHASES.find((p) => p.id === selectedPhaseId) || PHASES[0];
  const activeState = getPhaseState(activePhase);

  return (
    <div className="relative overflow-hidden rounded-3xl border border-indigo-500/20 bg-[#0B0F17] p-8 shadow-2xl text-slate-100 font-sans">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute -top-32 -left-32 h-96 w-96 rounded-full bg-indigo-600/10 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-amber-500/10 blur-[120px]" />

      {/* Top Banner Header */}
      <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-400 border border-amber-500/20">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
              Priorität 1 · Höchste Dringlichkeit
            </span>
            <span className="text-xs font-mono text-indigo-400 tracking-wide uppercase">
              studentenprojekt_v2
            </span>
          </div>

          <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            4-Säulen-Sprint · LCC-Readiness
          </h2>
          <p className="mt-1 text-sm text-slate-400 max-w-2xl leading-relaxed">
            Meilenstein-Fahrplan für das Beratungsmodell V2 (Enablement → Risiken → SAP-Architektur →
            Simulation). Ziel:{" "}
            <span className="font-semibold text-slate-200">LCC-Release V2 diese Woche (Fr.)</span>
          </p>
        </div>

        {/* Executive Overall Progress Card */}
        <div className="flex items-center gap-5 rounded-2xl border border-slate-800/80 bg-slate-900/50 p-4 backdrop-blur-md shrink-0">
          <div className="text-right">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Release Readiness
            </div>
            <div className="text-2xl font-black text-white mt-0.5">
              {completedCount} / {PHASES.length}{" "}
              <span className="text-sm font-semibold text-indigo-400">({progressPct}%)</span>
            </div>
          </div>
          <div className="relative flex h-14 w-14 items-center justify-center rounded-full border-2 border-slate-700 bg-slate-950">
            <svg className="h-12 w-12 -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-800"
                strokeWidth="3"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-indigo-500 transition-all duration-500"
                strokeDasharray={`${progressPct}, 100`}
                strokeWidth="3"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-xs font-bold text-white">{progressPct}%</span>
          </div>
        </div>
      </div>

      {/* Interactive Timeline Track */}
      <div className="relative z-10 mt-8">
        <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
          <span>📍 4-Säulen-Sprint (Mo. – Fr.)</span>
          <span className="text-slate-500 font-normal">Phase anklicken für Detail-Ansicht</span>
        </div>

        {/* Timeline Grid */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {PHASES.map((phase) => {
            const state = getPhaseState(phase);
            const isSelected = phase.id === selectedPhaseId;

            return (
              <button
                key={phase.id}
                type="button"
                onClick={() => setSelectedPhaseId(phase.id)}
                className={`relative flex flex-col justify-between rounded-2xl border p-4 text-left transition-all duration-200 ${
                  isSelected
                    ? "border-indigo-500 bg-indigo-950/30 ring-2 ring-indigo-500/20 shadow-lg shadow-indigo-950/50"
                    : state === "completed"
                    ? "border-emerald-500/30 bg-emerald-950/10 hover:border-emerald-500/50"
                    : state === "active"
                    ? "border-amber-500/40 bg-amber-950/20 hover:border-amber-500/60"
                    : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-indigo-400">
                      SÄULE {phase.phaseNumber}
                    </span>
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${
                        state === "completed"
                          ? "bg-emerald-400 shadow-sm shadow-emerald-400"
                          : state === "active"
                          ? "bg-amber-400 animate-pulse shadow-sm shadow-amber-400"
                          : "bg-slate-700"
                      }`}
                    />
                  </div>

                  <h3 className="mt-2 text-sm font-bold text-white leading-snug">
                    {phase.title}
                  </h3>
                  <p className="mt-0.5 text-xs text-slate-400 truncate">
                    {phase.subtitle}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-slate-800/60 pt-2.5 text-[11px]">
                  <span className="font-mono text-slate-400">{phase.dateRange}</span>
                  <span
                    className={`font-semibold uppercase tracking-wider ${
                      state === "completed"
                        ? "text-emerald-400"
                        : state === "active"
                        ? "text-amber-300"
                        : "text-slate-500"
                    }`}
                  >
                    {state === "completed" ? "Abgenommen" : state === "active" ? "In Arbeit" : "Offen"}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Phase Detail Panel (Executive Drilldown) */}
      <div className="relative z-10 mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800/80 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-indigo-400">
                Säule {activePhase.phaseNumber} · Details
              </span>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-amber-300 font-medium">
                {activePhase.dateRange}
              </span>
            </div>
            <h3 className="text-xl font-bold text-white mt-1">
              {activePhase.title} — {activePhase.subtitle}
            </h3>
          </div>

          {/* Interactive State Toggle Buttons */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPhaseState(activePhase.id, "pending")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeState === "pending"
                  ? "bg-slate-700 text-white border border-slate-600"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Offen
            </button>
            <button
              type="button"
              onClick={() => setPhaseState(activePhase.id, "active")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeState === "active"
                  ? "bg-amber-500 text-slate-950 font-bold border border-amber-400"
                  : "bg-slate-900 text-slate-400 hover:text-amber-300 border border-slate-800"
              }`}
            >
              In Arbeit
            </button>
            <button
              type="button"
              onClick={() => setPhaseState(activePhase.id, "completed")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeState === "completed"
                  ? "bg-emerald-500 text-slate-950 font-bold border border-emerald-400"
                  : "bg-slate-900 text-slate-400 hover:text-emerald-300 border border-slate-800"
              }`}
            >
              ✓ Abgenommen
            </button>
          </div>
        </div>

        {/* Phase Details Content Grid */}
        <div className="mt-5 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="md:col-span-2 space-y-4">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Beschreibung & Zielsetzung
              </h4>
              <p className="mt-1.5 text-sm text-slate-300 leading-relaxed">
                {activePhase.description}
              </p>
            </div>

            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Konkrete Handlungsschritte
              </h4>
              <ul className="space-y-2 text-sm text-slate-200">
                {activePhase.keyActions.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2.5">
                    <span className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-300">
                      {idx + 1}
                    </span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Zentrales Deliverable-Artefakt
            </h4>
            <div className="flex items-center gap-2.5 rounded-lg border border-slate-800 bg-slate-900 p-2.5 text-xs font-mono text-indigo-300">
              <svg className="h-4 w-4 shrink-0 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="truncate">{activePhase.deliverableFile}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Liegt im Repository <span className="font-mono text-slate-300">{V2_REPO_PATH}/</span>
            </p>
          </div>
        </div>
      </div>

      {/* Portfolio Horizon (Sleek Bottom Cards) */}
      <div className="relative z-10 mt-8 border-t border-slate-800/80 pt-6">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
          🌌 Portfolio Horizont (Weitere aktive Projekte)
        </h4>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-5 text-xs">
          {OTHER_PROJECTS.map((item) => (
            <div
              key={item.name}
              className="group rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4 transition-all hover:border-indigo-500/40 hover:bg-slate-900/70"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-white group-hover:text-indigo-300 transition-colors">
                  {item.name}
                </span>
                <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-semibold text-slate-300">
                  {item.tag}
                </span>
              </div>
              <div className="mt-1.5 text-xs font-medium text-amber-300">
                {item.date}
              </div>
              <div className="mt-1 text-[11px] text-slate-400 leading-normal line-clamp-2">
                {item.scope}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
