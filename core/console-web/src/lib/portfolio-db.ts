import fs from "fs/promises";
import path from "path";

export interface ProjectMilestone {
  id: string;
  title: string;
  targetDate: string;
  status: "done" | "in_progress" | "planned";
  fileLink?: string;
  fileName?: string;
}

export interface ProjectSummary {
  id: string;
  title: string;
  path: string;
  roadmapFile: string;
  priority: "prio1" | "prio2" | "prio3" | "continuous";
  priorityLabel: string;
  deadline: string;
  status: string;
  description: string;
  dependencies: string[];
  documents: { label: string; fileUri: string; fileName: string }[];
  milestones: ProjectMilestone[];
}

const ACTIVE_ROOT = "/home/peter/Projekte/active";
const AIOS_ROOT = "/home/peter/Projekte/1100-AI-OS-V2";

export async function getPortfolioData(): Promise<ProjectSummary[]> {
  const projects: ProjectSummary[] = [
    {
      id: "studentenprojekt",
      title: "WAQAM Studentenprojekt & Board",
      path: `${ACTIVE_ROOT}/studentenprojekt`,
      roadmapFile: `${ACTIVE_ROOT}/studentenprojekt/ROADMAP.md`,
      priority: "prio1",
      priorityLabel: "🔴 Prio 1 (Höchste)",
      deadline: "07.08.2026",
      status: "In Arbeit",
      description: "Studentisches Praxisprojekt: SAP S/4HANA & BTP — AI Scoping, Stochastik, Risiko & Board Overhaul.",
      dependencies: ["sap-consultant-package", "1100-AI-OS-V2"],
      documents: [
        { label: "Roadmap", fileUri: `file://${ACTIVE_ROOT}/studentenprojekt/ROADMAP.md`, fileName: "ROADMAP.md" },
        { label: "Studenten-Pitch DE", fileUri: `file://${ACTIVE_ROOT}/studentenprojekt/projekt_pitch_studenten_de.md`, fileName: "projekt_pitch_studenten_de.md" },
        { label: "Paket 1: Portfolio", fileUri: `file://${ACTIVE_ROOT}/studentenprojekt/paket1_sap_ai_portfolio.md`, fileName: "paket1_sap_ai_portfolio.md" },
        { label: "Paket 2: Stochastik", fileUri: `file://${ACTIVE_ROOT}/studentenprojekt/paket2_stochastik_risiko.md`, fileName: "paket2_stochastik_risiko.md" },
        { label: "Paket 3: Board Use Case", fileUri: `file://${ACTIVE_ROOT}/studentenprojekt/paket3_use_case_simulation.md`, fileName: "paket3_use_case_simulation.md" },
        { label: "Störungs-Handbuch", fileUri: `file://${ACTIVE_ROOT}/studentenprojekt/stoerung_manipulation_handbuch.md`, fileName: "stoerung_manipulation_handbuch.md" },
      ],
      milestones: [
        { id: "m1", title: "Gate 1: Studenten-Pitch & Rollen vergeben", targetDate: "27.07.2026", status: "in_progress", fileName: "projekt_pitch_studenten_de.md", fileLink: `file://${ACTIVE_ROOT}/studentenprojekt/projekt_pitch_studenten_de.md` },
        { id: "m2", title: "Gate 2A: Paket 1 SAP AI Portfolio & Scoping", targetDate: "28.07.2026", status: "planned", fileName: "paket1_sap_ai_portfolio.md", fileLink: `file://${ACTIVE_ROOT}/studentenprojekt/paket1_sap_ai_portfolio.md` },
        { id: "m3", title: "Gate 2B: Paket 2 Stochastik & Simulator-Kopplung", targetDate: "31.07.2026", status: "planned", fileName: "paket2_stochastik_risiko.md", fileLink: `file://${ACTIVE_ROOT}/studentenprojekt/paket2_stochastik_risiko.md` },
        { id: "m4", title: "Gate 3: Paket 3 WAQAM Board Overhaul & EXT-01", targetDate: "04.08.2026", status: "planned", fileName: "paket3_use_case_simulation.md", fileLink: `file://${ACTIVE_ROOT}/studentenprojekt/paket3_use_case_simulation.md` },
        { id: "m5", title: "Gate 4: Final Release & Go-Live Briefing Kit", targetDate: "07.08.2026", status: "planned", fileName: "projekt_overview.canvas", fileLink: `file://${ACTIVE_ROOT}/studentenprojekt/projekt_overview.canvas` },
      ],
    },
    {
      id: "ai-sap-videos",
      title: "AI SAP Videos (Projekt Zorro)",
      path: `${ACTIVE_ROOT}/projekt-zorro/ai-sap-videos`,
      roadmapFile: `${ACTIVE_ROOT}/projekt-zorro/ai-sap-videos/README.md`,
      priority: "prio2",
      priorityLabel: "📚 Projekt Zorro (Lokal)",
      deadline: "Mitte/Ende Aug. 2026",
      status: "Lern- & Wissenspipeline (Lokal)",
      description: "Projekt Zorro: Interne Wissensunterstützung zum Lernen (Video-Transkripte & Enablement).",
      dependencies: ["Keine (Autonom)"],
      documents: [
        { label: "Projekt-Ordner (Lokal)", fileUri: `file://${ACTIVE_ROOT}/projekt-zorro/ai-sap-videos`, fileName: "projekt-zorro/ai-sap-videos/" },
      ],
      milestones: [
        { id: "v1", title: "Video 1: Autonomous Enterprise Basics", targetDate: "10.08.2026", status: "planned" },
        { id: "v2", title: "Video 2: BTP Integration & Agenten", targetDate: "17.08.2026", status: "planned" },
        { id: "v3", title: "Video 3: VIRKI Architecture Deep Dive", targetDate: "25.08.2026", status: "planned" },
      ],
    },
    {
      id: "redrays-btp",
      title: "RedRays BTP Security Scanner",
      path: `${ACTIVE_ROOT}/redrays-btp`,
      roadmapFile: `${ACTIVE_ROOT}/redrays-btp/README.md`,
      priority: "prio3",
      priorityLabel: "🛡️ Prio 3",
      deadline: "Anfang Sept. 2026",
      status: "Wartet auf BTP Partner",
      description: "Sicherheits- und Vulnerability-Scanner Integration für SAP BTP Umgebungen.",
      dependencies: ["BTP Partner Alignment"],
      documents: [
        { label: "Projekt-Ordner", fileUri: `file://${ACTIVE_ROOT}/redrays-btp`, fileName: "redrays-btp/" },
      ],
      milestones: [
        { id: "r1", title: "BTP Security Audit Alignment", targetDate: "01.09.2026", status: "planned" },
      ],
    },
    {
      id: "lizenz-simulation",
      title: "SAP BTP Lizenz-Simulator",
      path: `${ACTIVE_ROOT}/lizenz-simulation`,
      roadmapFile: `${ACTIVE_ROOT}/lizenz-simulation/README.md`,
      priority: "prio3",
      priorityLabel: "🧮 Prio 3",
      deadline: "Ende Sept. / Okt. 2026",
      status: "Geplant",
      description: "Interaktive Simulation für SAP BTP Lizenzen, Verbrauchskalkulation und TCO-Vergleich.",
      dependencies: ["Partner-Projekt Fortschritt"],
      documents: [
        { label: "Projekt-Ordner", fileUri: `file://${ACTIVE_ROOT}/lizenz-simulation`, fileName: "lizenz-simulation/" },
      ],
      milestones: [
        { id: "l1", title: "Lizenz-Modellierung & Partner-Kickoff", targetDate: "25.09.2026", status: "planned" },
      ],
    },
    {
      id: "website-nce",
      title: "Next Chapter Experts Website",
      path: `${ACTIVE_ROOT}/website-nce`,
      roadmapFile: `${ACTIVE_ROOT}/website-nce/README.md`,
      priority: "continuous",
      priorityLabel: "🌐 Continuous",
      deadline: "Permanente Evolution",
      status: "Prototyp Aktiv (Port 3001)",
      description: "Corporate Website mit interaktivem VIRKI-Prototyp, Beratung, Blogs und Kontakt.",
      dependencies: ["sap-consultant-package", "1100-AI-OS-V2"],
      documents: [
        { label: "Website Repo", fileUri: `file://${ACTIVE_ROOT}/website-nce`, fileName: "website-nce/" },
        { label: "Prototyp Subnav", fileUri: `file://${ACTIVE_ROOT}/website-nce/src/components/prototype/PrototypeSubnav.tsx`, fileName: "PrototypeSubnav.tsx" },
        { label: "VIRKI Page", fileUri: `file://${ACTIVE_ROOT}/website-nce/src/components/prototype/VirkiPage.tsx`, fileName: "VirkiPage.tsx" },
      ],
      milestones: [
        { id: "w1", title: "VIRKI Landingpage & Clean Nav", targetDate: "26.07.2026", status: "done" },
        { id: "w2", title: "LinkedIn Kampagne & Live Launch", targetDate: "05.08.2026", status: "in_progress" },
      ],
    },
    {
      id: "1100-AI-OS-V2",
      title: "AI-OS v2 Platform Engine",
      path: AIOS_ROOT,
      roadmapFile: `${AIOS_ROOT}/ROADMAP.md`,
      priority: "continuous",
      priorityLabel: "🏰 Continuous (Core)",
      deadline: "Permanente Plattform",
      status: "Core Engine Aktiv",
      description: "Souveränes Enterprise KI-Betriebssystem — Muninn Memory, Huginn Workflows, Odin Console.",
      dependencies: ["Keine (Fundament)"],
      documents: [
        { label: "Master Roadmap", fileUri: `file://${AIOS_ROOT}/ROADMAP.md`, fileName: "ROADMAP.md" },
        { label: "12 Leitprinzipien", fileUri: `file://${AIOS_ROOT}/docs/12-LEITPRINZIPIEN.md`, fileName: "12-LEITPRINZIPIEN.md" },
        { label: "Workaround Doku", fileUri: `file://${AIOS_ROOT}/docs/20-WEBSITE-PROTOTYPE-WORKAROUND.md`, fileName: "20-WEBSITE-PROTOTYPE-WORKAROUND.md" },
      ],
      milestones: [
        { id: "os1", title: "Knowledge Graph & Ingest Engine", targetDate: "26.07.2026", status: "done" },
        { id: "os2", title: "Multi-User Isolation & Saga Compensations", targetDate: "15.08.2026", status: "in_progress" },
      ],
    },
    {
      id: "sap-consultant-package",
      title: "SAP Consultant Package & Blogs",
      path: `${ACTIVE_ROOT}/sap-consultant-package`,
      roadmapFile: `${ACTIVE_ROOT}/sap-consultant-package/README.md`,
      priority: "continuous",
      priorityLabel: "📚 Content Core",
      deadline: "Laufend",
      status: "Aktiv",
      description: "10 Realpessimismus-Blogbeiträge zu KI-Enterprise-Herausforderungen & Workshop-Materialien.",
      dependencies: ["Keine"],
      documents: [
        { label: "Blog-Ordner", fileUri: `file://${ACTIVE_ROOT}/sap-consultant-package/blogs`, fileName: "blogs/" },
      ],
      milestones: [
        { id: "c1", title: "10 Realpessimismus Blogs verfasst", targetDate: "25.07.2026", status: "done" },
      ],
    },
    {
      id: "btc-apim-training",
      title: "BTC APIM Training & Curriculum",
      path: `${ACTIVE_ROOT}/btc-apim-training`,
      roadmapFile: `${ACTIVE_ROOT}/btc-apim-training/README.md`,
      priority: "prio3",
      priorityLabel: "🎓 Prio 3",
      deadline: "Mitte Aug. 2026",
      status: "In Arbeit",
      description: "BTP Solution Architect Curriculum & Schulungsmaterialien.",
      dependencies: ["1100-AI-OS-V2"],
      documents: [
        { label: "Projekt-Ordner", fileUri: `file://${ACTIVE_ROOT}/btc-apim-training`, fileName: "btc-apim-training/" },
      ],
      milestones: [
        { id: "t1", title: "APIM Architecture Agenda & Labs", targetDate: "15.08.2026", status: "planned" },
      ],
    },
    {
      id: "waqamboard",
      title: "WAQAM Board Simulator",
      path: `${ACTIVE_ROOT}/waqam/waqamboard`,
      roadmapFile: `${ACTIVE_ROOT}/waqam/waqamboard/ROADMAP.md`,
      priority: "prio1",
      priorityLabel: "🔴 Prio 1",
      deadline: "04.08.2026",
      status: "In Entwicklung",
      description: "React-basierter Stochastik- & TCO-Simulator für SAP AI Szenarien.",
      dependencies: ["waqam-doku", "studentenprojekt"],
      documents: [
        { label: "Simulator Repo", fileUri: `file://${ACTIVE_ROOT}/waqam/waqamboard`, fileName: "waqam/waqamboard/" },
        { label: "Roadmap", fileUri: `file://${ACTIVE_ROOT}/waqam/waqamboard/ROADMAP.md`, fileName: "ROADMAP.md" },
      ],
      milestones: [
        { id: "wb1", title: "UI Overhaul & EXT-01 Onboarding", targetDate: "04.08.2026", status: "in_progress" },
      ],
    },
    {
      id: "waqam-doku",
      title: "WAQAM Dokumentation",
      path: `${ACTIVE_ROOT}/waqam/waqam-doku`,
      roadmapFile: `${ACTIVE_ROOT}/waqam/waqam-doku/ROADMAP.md`,
      priority: "prio1",
      priorityLabel: "🔴 Prio 1",
      deadline: "Laufend",
      status: "Aktiv",
      description: "Fachliche Dokumentation, Prüfprotokolle und Berater-Handbuch für WAQAM.",
      dependencies: ["sap-consultant-package"],
      documents: [
        { label: "Berater-Handbuch", fileUri: `file://${ACTIVE_ROOT}/waqam/waqam-doku/SAP_AI_Governance_WAQAM_Berater_Handbuch.md`, fileName: "SAP_AI_Governance_WAQAM_Berater_Handbuch.md" },
        { label: "Roadmap", fileUri: `file://${ACTIVE_ROOT}/waqam/waqam-doku/ROADMAP.md`, fileName: "ROADMAP.md" },
      ],
      milestones: [
        { id: "wd1", title: "Validation Gate Spec & Doku", targetDate: "01.08.2026", status: "done" },
      ],
    },
  ];

  // Try to enrich status dynamically from file system if ROADMAP.md exists
  for (const proj of projects) {
    try {
      const content = await fs.readFile(proj.roadmapFile, "utf-8");
      if (content.includes("HÖCHSTE PRIORITÄT")) {
        proj.priority = "prio1";
      }
    } catch {
      // Keep static defaults if file read fails
    }
  }

  return projects;
}
