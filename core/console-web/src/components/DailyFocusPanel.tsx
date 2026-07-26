"use client";

import { useState, useEffect } from "react";

type TaskStatus = "todo" | "in_progress" | "done";

interface TaskItem {
  id: string;
  project: string;
  period: "today" | "this_week" | "next_week";
  title: string;
  desc: string;
  deadline: string;
  defaultStatus: TaskStatus;
}

const INITIAL_TASKS: TaskItem[] = [
  {
    id: "waqam-pitch",
    project: "waqam-project (Prio 1)",
    period: "today",
    title: "Studenten-Pitch & Rollen vergeben",
    desc: "Pitch-Unterlagen (projekt_pitch_studenten_de.md) prüfen & Rollen zuweisen.",
    deadline: "27.07. (Morgen)",
    defaultStatus: "todo",
  },
  {
    id: "waqam-p1",
    project: "waqam-project (Prio 1)",
    period: "this_week",
    title: "Paket 1: SAP AI Portfolio & Scoping",
    desc: "Grundlagen Autonomous Enterprise & Feature-Bewertung finalisieren.",
    deadline: "28.07. (Dienstag)",
    defaultStatus: "todo",
  },
  {
    id: "waqam-p2",
    project: "waqam-project (Prio 1)",
    period: "this_week",
    title: "Paket 2: Stochastik, Risiko & Simulator-Kopplung",
    desc: "Realpessimismus-Blog-Hürden mit dem Störungs-Handbuch & Simulator koppeln.",
    deadline: "31.07. (Freitag)",
    defaultStatus: "todo",
  },
  {
    id: "waqam-p3",
    project: "waqam-project (Prio 1)",
    period: "next_week",
    title: "Paket 3: Waqamboard Overhaul & EXT-01",
    desc: "Waqamboard UI & Lieferanten-Onboarding Szenario überarbeiten.",
    deadline: "04.08. (Dienstag)",
    defaultStatus: "todo",
  },
  {
    id: "waqam-release",
    project: "waqam-project (Prio 1)",
    period: "next_week",
    title: "🎉 Go-Live: Studenten-Projekt Startklar",
    desc: "Paket 1–3 als PDF & GitHub Repository an Studenten übergeben.",
    deadline: "07.08. (Freitag)",
    defaultStatus: "todo",
  },
];

const OTHER_PROJECTS = [
  { name: "ai-sap-videos", deadline: "Mitte/Ende August 2026", status: "3 Videos anschauen / Skripte" },
  { name: "redrays-btp", deadline: "Anfang September 2026", status: "Alignment mit BTP-Kollegen" },
  { name: "lizenz-simulation", deadline: "Ende Sept. / Okt. 2026", status: "Partner-Projekt Start" },
  { name: "website-nce", deadline: "Kontinuierlich", status: "Prototyp & Live-Ausbau" },
  { name: "1100-AI-OS-V2", deadline: "Kontinuierlich", status: "Plattform-Engine Core" },
];

export function DailyFocusPanel() {
  const [taskStates, setTaskStates] = useState<Record<string, TaskStatus>>({});

  useEffect(() => {
    const saved = localStorage.getItem("aios_daily_focus_tasks");
    if (saved) {
      try {
        setTaskStates(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse saved task states", e);
      }
    }
  }, []);

  const toggleTask = (id: string, currentStatus: TaskStatus) => {
    const nextStatus: Record<TaskStatus, TaskStatus> = {
      todo: "in_progress",
      in_progress: "done",
      done: "todo",
    };
    const newStates = {
      ...taskStates,
      [id]: nextStatus[currentStatus],
    };
    setTaskStates(newStates);
    localStorage.setItem("aios_daily_focus_tasks", JSON.stringify(newStates));
  };

  const getStatus = (task: TaskItem): TaskStatus => {
    return taskStates[task.id] || task.defaultStatus;
  };

  const doneCount = INITIAL_TASKS.filter((t) => getStatus(t) === "done").length;
  const totalCount = INITIAL_TASKS.length;
  const progressPct = Math.round((doneCount / totalCount) * 100);

  return (
    <div className="space-y-6 rounded-2xl border border-sky-500/30 bg-slate-900/90 p-6 shadow-xl text-slate-100">
      {/* Header & Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-rose-500/20 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider text-rose-300 border border-rose-500/30">
              🔴 Priorität 1
            </span>
            <span className="mono text-xs text-sky-400">waqam-project · Studenten-Start</span>
          </div>
          <h2 className="text-xl font-extrabold text-white mt-1">
            Fokus-Lagebild: Was ist wann zu tun?
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ziel: <strong>07.08.2026</strong> (Ende nächster Woche startbereit für Studierende)
          </p>
        </div>

        {/* Progress Bar */}
        <div className="sm:text-right min-w-[160px]">
          <div className="text-xs font-bold text-slate-300">
            Fortschritt: {doneCount}/{totalCount} ({progressPct}%)
          </div>
          <div className="mt-1.5 h-2.5 w-full rounded-full bg-slate-800 overflow-hidden border border-slate-700">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-emerald-400 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Task Sections */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Today & This Week */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-amber-300 flex items-center gap-2">
            ⚡ Morgen & Diese Woche (bis 31.07.)
          </h3>
          <div className="space-y-2.5">
            {INITIAL_TASKS.filter((t) => t.period === "today" || t.period === "this_week").map((task) => {
              const status = getStatus(task);
              return (
                <div
                  key={task.id}
                  onClick={() => toggleTask(task.id, status)}
                  className={`cursor-pointer rounded-xl border p-3.5 transition-all hover:scale-[1.01] ${
                    status === "done"
                      ? "border-emerald-500/40 bg-emerald-950/20 opacity-75"
                      : status === "in_progress"
                      ? "border-amber-500/50 bg-amber-950/30"
                      : "border-slate-800 bg-slate-950/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <button className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border font-mono text-xs">
                        {status === "done" ? "✓" : status === "in_progress" ? "▸" : ""}
                      </button>
                      <div>
                        <div className={`text-sm font-bold ${status === "done" ? "line-through text-slate-400" : "text-white"}`}>
                          {task.title}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                          {task.desc}
                        </p>
                      </div>
                    </div>
                    <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-300 border border-slate-700">
                      {task.deadline}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Next Week (Target Release) */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-sky-300 flex items-center gap-2">
            🎯 Nächste Woche (bis 07.08. — Go-Live)
          </h3>
          <div className="space-y-2.5">
            {INITIAL_TASKS.filter((t) => t.period === "next_week").map((task) => {
              const status = getStatus(task);
              return (
                <div
                  key={task.id}
                  onClick={() => toggleTask(task.id, status)}
                  className={`cursor-pointer rounded-xl border p-3.5 transition-all hover:scale-[1.01] ${
                    status === "done"
                      ? "border-emerald-500/40 bg-emerald-950/20 opacity-75"
                      : status === "in_progress"
                      ? "border-amber-500/50 bg-amber-950/30"
                      : "border-slate-800 bg-slate-950/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <button className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border font-mono text-xs">
                        {status === "done" ? "✓" : status === "in_progress" ? "▸" : ""}
                      </button>
                      <div>
                        <div className={`text-sm font-bold ${status === "done" ? "line-through text-slate-400" : "text-white"}`}>
                          {task.title}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                          {task.desc}
                        </p>
                      </div>
                    </div>
                    <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-sky-300 border border-sky-800">
                      {task.deadline}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Portfolio Overview Footer */}
      <div className="border-t border-slate-800 pt-4 mt-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          📅 Weitere Portfolio-Termine im Überblick
        </h4>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 lg:grid-cols-5 text-xs">
          {OTHER_PROJECTS.map((item) => (
            <div key={item.name} className="rounded-lg border border-slate-800 bg-slate-950/60 p-2.5">
              <div className="font-bold text-slate-200">{item.name}</div>
              <div className="text-[11px] text-amber-300 mt-0.5">{item.deadline}</div>
              <div className="text-[10px] text-slate-400 mt-1 truncate">{item.status}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
