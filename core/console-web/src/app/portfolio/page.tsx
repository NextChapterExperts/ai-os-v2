"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

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

const PHASES: PhaseGate[] = [
  {
    id: "phase-1",
    phaseNumber: "01",
    title: "Kickoff & Rollen",
    subtitle: "Studenten-Pitch & Freigabe",
    dateRange: "Mo. 27.07.",
    deliverableFile: "projekt_pitch_studenten_de.md",
    description: "Studenten-Pitch sichten, Anforderungsprofil für 2–3 Studierende freigeben und Aufgabenverteilung zuteilen.",
    keyActions: [
      "Pitch-Unterlagen (DE/EN) prüfen & freigeben",
      "Rollenverteilung (rollenverteilung_studenten.md) festlegen",
    ],
    defaultState: "active",
  },
  {
    id: "phase-2a",
    phaseNumber: "02",
    title: "Paket 1: Portfolio",
    subtitle: "SAP AI Scoping & Features",
    dateRange: "Di. 28.07.",
    deliverableFile: "paket1_sap_ai_portfolio.md",
    description: "Grundlagen des Autonomous Enterprise definieren und existierende SAP AI Features bewerten.",
    keyActions: [
      "SAP Business AI Scope abstimmen",
      "Feature-Matrix für Studenten aufbereiten",
    ],
    defaultState: "pending",
  },
  {
    id: "phase-2b",
    phaseNumber: "03",
    title: "Paket 2: Stochastik",
    subtitle: "Risiko & Simulator",
    dateRange: "Mi. 29.07. – Fr. 31.07.",
    deliverableFile: "paket2_stochastik_risiko.md",
    description: "KI-Halluzinationsrisiken & Realpessimismus-Bloghürden mit dem Störungs-Handbuch & Simulator koppeln.",
    keyActions: [
      "Störungs- & Manipulations-Handbuch integrieren",
      "Simulator-Testfälle für Stresstest definieren",
    ],
    defaultState: "pending",
  },
  {
    id: "phase-3",
    phaseNumber: "04",
    title: "Paket 3: WAQAM Board",
    subtitle: "Use Case & UI Overhaul",
    dateRange: "Mo. 03.08. – Di. 04.08.",
    deliverableFile: "paket3_use_case_simulation.md",
    description: "EXT-01 Lieferanten-Onboarding Szenario im WAQAM Board überarbeiten und Vorstandsslides vorbereiten.",
    keyActions: [
      "Board UI auf neusten Stand bringen",
      "Lieferanten-Onboarding Testfall durchspielen",
    ],
    defaultState: "pending",
  },
  {
    id: "phase-4",
    phaseNumber: "05",
    title: "Final Release",
    subtitle: "Go-Live & Briefing Kit",
    dateRange: "Fr. 07.08. (RELEASE)",
    deliverableFile: "projekt_overview.canvas",
    description: "Pakete 1–3 als fertiges Studenten-Kit (PDF & Repository) übergeben. Offizieller Projektstart!",
    keyActions: [
      "Dry Run aus Studenten-Perspektive durchführen",
      "GitHub Repo & Unterlagen für Studenten freigeben",
    ],
    defaultState: "pending",
  },
];

const ALL_PROJECTS = [
  { id: "waqam-project", name: "waqam-project / waqamboard", priority: "Prio 1 (Höchste)", deadline: "07.08.2026", status: "In Arbeit", dep: "Fließt in sap-consultant-package" },
  { id: "ai-sap-videos", name: "ai-sap-videos", priority: "Prio 2", deadline: "Ende Aug. 2026", status: "Geplant", dep: "Autonom (Wissen für SAP)" },
  { id: "redrays-btp", name: "redrays-btp", priority: "Prio 3", deadline: "Anfang Sept. 2026", status: "Wartet auf BTP-Kollegen", dep: "BTP Partner Alignment" },
  { id: "lizenz-simulation", name: "lizenz-simulation", priority: "Prio 4", deadline: "Ende Sept. / Okt. 2026", status: "Geplant", dep: "Partner-Projekt Fortschritt" },
  { id: "website-nce", name: "website-nce", priority: "Continuous", deadline: "Permanente Evolution", status: "Prototyp Aktiv (Port 3001)", dep: "Content aus sap-consultant-package" },
  { id: "1100-AI-OS-V2", name: "1100-AI-OS-V2", priority: "Continuous", deadline: "Permanente Engine", status: "Core Operating System", dep: "Plattform-Basis für alle Demos" },
  { id: "sap-consultant-package", name: "sap-consultant-package", priority: "Continuous", deadline: "Laufend", status: "Realpessimismus-Serie", dep: "Liefert Content für website-nce" },
  { id: "btc-apim-training", name: "btc-apim-training", priority: "Prio 3", deadline: "Mitte Aug. 2026", status: "Curriculum Vorbereitung", dep: "Abhängig von AI-OS Demos" },
  { id: "steuer-2025", name: "steuer-2025 / 2026", priority: "Governance", deadline: "Laufend", status: "Verwaltung & Buchhaltung", dep: "Keine" },
];

export default function PortfolioPage() {
  const [phaseStates, setPhaseStates] = useState<Record<string, MilestoneState>>({});
  const [selectedPhaseId, setSelectedPhaseId] = useState<string>("phase-1");

  useEffect(() => {
    const saved = localStorage.getItem("aios_waqam_phase_states");
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
    localStorage.setItem("aios_waqam_phase_states", JSON.stringify(updated));
  };

  const getPhaseState = (phase: PhaseGate): MilestoneState => {
    return phaseStates[phase.id] || phase.defaultState;
  };

  const completedCount = PHASES.filter((p) => getPhaseState(p) === "completed").length;
  const progressPct = Math.round((completedCount / PHASES.length) * 100);
  const activePhase = PHASES.find((p) => p.id === selectedPhaseId) || PHASES[0];
  const activeState = getPhaseState(activePhase);

  return (
    <div className="rise pt-6">
      {/* Page Header */}
      <div className="mb-8 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-6">
        <div>
          <p className="muted mb-1 text-xs uppercase tracking-[0.16em]">
            Portfolio & Zeitplan
          </p>
          <h1 className="section-title m-0">Projekte</h1>
          <p className="muted mt-1 mb-0 max-w-xl text-sm">
            Gesamtfahrplan aller 10 aktiven Projekte · Kritischer Pfad & Meilensteine
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/" className="btn-ghost">
            ← Lagebild
          </Link>
        </div>
      </div>

      {/* Critical Path Header Card: WAQAM Studentenprojekt */}
      <section className="rise rise-delay-1 mb-10 border border-line bg-paper-2/40 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="badge" data-variant="raw">
                🔴 HÖCHSTE PRIORITÄT (Prio 1)
              </span>
              <span className="mono text-xs text-ink-soft">waqam-project</span>
            </div>
            <h2 className="section-title mt-2 mb-0">WAQAM Studenten-Start</h2>
            <p className="muted mt-1 mb-0 text-sm">
              Ziel-Go-Live: <strong className="text-ink font-semibold">Freitag, 07. August 2026</strong> (Startbereit für Studierende)
            </p>
          </div>
          <div className="text-right">
            <div className="mono text-xs text-ink-soft">RELEASE READINESS</div>
            <div className="font-display text-2xl font-bold text-ink">
              {completedCount} / {PHASES.length} <span className="text-sm font-normal text-signal">({progressPct}%)</span>
            </div>
          </div>
        </div>

        {/* Phase Track Grid */}
        <div className="mt-6">
          <p className="muted mb-3 text-xs uppercase tracking-wider">
            Phasen-Fahrplan (Woche 1 & Woche 2) · Klicken für Details
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {PHASES.map((phase) => {
              const state = getPhaseState(phase);
              const isSelected = phase.id === selectedPhaseId;

              return (
                <button
                  key={phase.id}
                  type="button"
                  onClick={() => setSelectedPhaseId(phase.id)}
                  className={`flex flex-col justify-between border p-3.5 text-left transition-all ${
                    isSelected
                      ? "border-signal bg-paper text-ink shadow-sm ring-1 ring-signal"
                      : state === "completed"
                      ? "border-line bg-paper/80"
                      : "border-line bg-paper-2/20 hover:border-ink-soft"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="mono font-semibold text-ink-soft">PHASE {phase.phaseNumber}</span>
                      <span
                        className={`status-dot ${
                          state === "completed" ? "ok" : state === "active" ? "unknown" : "muted"
                        }`}
                      />
                    </div>
                    <div className="mt-2 font-semibold text-sm text-ink leading-snug">{phase.title}</div>
                    <div className="muted mt-0.5 text-xs truncate">{phase.subtitle}</div>
                  </div>

                  <div className="mt-3 flex items-center justify-between border-t border-line pt-2 text-xs">
                    <span className="mono text-ink-soft">{phase.dateRange}</span>
                    <span className="mono text-xs font-medium">
                      {state === "completed" ? "✓ Done" : state === "active" ? "In Arbeit" : "Offen"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Phase Details */}
        <div className="mt-6 border-t border-line pt-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="mono text-xs text-signal font-semibold">PHASE {activePhase.phaseNumber} DETAILS</span>
              <h3 className="section-title text-lg mt-1 mb-0">{activePhase.title} — {activePhase.subtitle}</h3>
              <p className="muted mt-0.5 text-xs">Termin: {activePhase.dateRange}</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPhaseState(activePhase.id, "pending")}
                className={`btn-ghost text-xs ${activeState === "pending" ? "data-[active=true]:true" : ""}`}
                data-active={activeState === "pending"}
              >
                Offen
              </button>
              <button
                type="button"
                onClick={() => setPhaseState(activePhase.id, "active")}
                className={`btn-ghost text-xs ${activeState === "active" ? "data-[active=true]:true" : ""}`}
                data-active={activeState === "active"}
              >
                In Arbeit
              </button>
              <button
                type="button"
                onClick={() => setPhaseState(activePhase.id, "completed")}
                className={`btn-ghost text-xs ${activeState === "completed" ? "data-[active=true]:true" : ""}`}
                data-active={activeState === "completed"}
              >
                ✓ Abgenommen
              </button>
            </div>
          </div>

          <div className="mt-4 grid gap-6 md:grid-cols-3">
            <div className="md:col-span-2 space-y-3">
              <p className="m-0 text-sm text-ink leading-relaxed">{activePhase.description}</p>
              <div>
                <span className="mono text-xs text-ink-soft font-semibold">Schritte:</span>
                <ul className="mt-1 space-y-1 text-sm text-ink list-disc pl-5">
                  {activePhase.keyActions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="border border-line bg-paper/60 p-3">
              <span className="mono text-xs text-ink-soft uppercase tracking-wider block mb-1">Artefakt</span>
              <div className="mono text-xs text-ink font-semibold break-all">{activePhase.deliverableFile}</div>
              <p className="muted mt-1 mb-0 text-xs">Pfad: /home/peter/Projekte/active/waqam-project/</p>
            </div>
          </div>
        </div>
      </section>

      {/* Portfolio Horizon Table Section */}
      <section className="rise rise-delay-2">
        <h2 className="section-title">Alle 10 Projekte im Überblick</h2>
        <p className="muted mb-4 text-sm">Übersicht der Prioritäten, Fristen und Abhängigkeiten</p>

        <div className="row-list">
          {ALL_PROJECTS.map((proj) => (
            <div key={proj.id} className="grid grid-cols-1 md:grid-cols-4 gap-2 items-baseline py-3">
              <div>
                <span className="font-semibold text-ink">{proj.name}</span>
                <span className="block mono text-xs text-ink-soft">{proj.priority}</span>
              </div>
              <div>
                <span className="mono text-xs text-ink">{proj.deadline}</span>
              </div>
              <div>
                <span className="badge" data-variant={proj.id === "waqam-project" ? "raw" : "curated"}>
                  {proj.status}
                </span>
              </div>
              <div className="text-right">
                <span className="mono text-xs muted">{proj.dep}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
