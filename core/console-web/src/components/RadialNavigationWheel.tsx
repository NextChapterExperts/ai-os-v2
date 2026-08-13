"use client";

import React, { useState } from "react";
import {
  IconSearch,
  IconTool,
  IconEdit,
  IconCalendar,
  IconFileText,
  IconSparkles,
} from "@tabler/icons-react";

export interface AgentNode {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: React.ReactNode;
  angle: number; // Grad auf dem Kreis (0 = Oben, 72, 144, 216, 288)
  color: string;
}

export const RADIAL_AGENTS: AgentNode[] = [
  {
    id: "handwerker",
    name: "Handwerker Angebot",
    category: "Handwerk & Bau",
    description: "Erstellt kalkulierte Angebote, Leistungsbeschreibungen & Kundenanschreiben",
    icon: <IconTool size={22} />,
    angle: 270, // Oben
    color: "var(--signal)",
  },
  {
    id: "blog",
    name: "Blog Generator",
    category: "Marketing & Media",
    description: "Generiert SEO-optimierte Artikel & Unternehmens-News",
    icon: <IconEdit size={22} />,
    angle: 342, // Oben-Rechts
    color: "#a855f7",
  },
  {
    id: "meetings",
    name: "Meeting Manager",
    category: "Zeitmanagement",
    description: "Syncht Kalender, prüft Termine & generiert Meeting-Summaries",
    icon: <IconCalendar size={22} />,
    angle: 54, // Unten-Rechts
    color: "#06b6d4",
  },
  {
    id: "email",
    name: "E-Mail & Ingest",
    category: "Finanzen & Dokumente",
    description: "Syncht Gmail-Rechnungen, extrahiert PDFs & committet in den Knowledge Graph",
    icon: <IconFileText size={22} />,
    angle: 126, // Unten-Links
    color: "#ec4899",
  },
  {
    id: "research",
    name: "Deep Research",
    category: "Wissen & Internet",
    description: "Durchsucht Company Brain & SearXNG Web via Anonymem Egress",
    icon: <IconSearch size={22} />,
    angle: 198, // Oben-Links
    color: "#3b82f6",
  },
];

interface RadialNavigationWheelProps {
  activeAgentId: string;
  suggestedAgentId?: string | null;
  onSelectAgent: (agentId: string) => void;
  children?: React.ReactNode; // Der zentrale Inhalt (z. B. das Suchfeld)
}

export const RadialNavigationWheel: React.FC<RadialNavigationWheelProps> = ({
  activeAgentId,
  suggestedAgentId,
  onSelectAgent,
  children,
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Radius des Navigationsrads (in px)
  const radius = 210;

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[580px] w-full py-8">
      {/* SVG Hintergrund-Ringe und Orbital-Linien */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-visible"
        viewBox="-300 -300 600 600"
      >
        <defs>
          <radialGradient id="radialGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--signal)" stopOpacity="0.12" />
            <stop offset="100%" stopColor="var(--signal)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Hintergrunde-Glow */}
        <circle cx="0" cy="0" r={radius + 40} fill="url(#radialGlow)" />

        {/* Äußerer gestrichelter Kreisring */}
        <circle
          cx="0"
          cy="0"
          r={radius}
          fill="none"
          stroke="var(--line)"
          strokeWidth="1.5"
          strokeDasharray="6 6"
          className="opacity-70"
        />

        {/* Verbindungs-Strahlen vom Zentrum zu den Knoten */}
        {RADIAL_AGENTS.map((agent) => {
          const rad = (agent.angle * Math.PI) / 180;
          const x2 = Math.cos(rad) * radius;
          const y2 = Math.sin(rad) * radius;
          const isSelected = agent.id === activeAgentId;
          const isSuggested = agent.id === suggestedAgentId;

          return (
            <line
              key={`line-${agent.id}`}
              x1="0"
              y1="0"
              x2={x2}
              y2={y2}
              stroke={isSelected ? agent.color : isSuggested ? "var(--signal)" : "var(--line)"}
              strokeWidth={isSelected || isSuggested ? "2.5" : "1"}
              strokeOpacity={isSelected ? "0.9" : isSuggested ? "0.8" : "0.35"}
              className="transition-all duration-300"
            />
          );
        })}
      </svg>

      {/* Zentrierter Content (z. B. das erweiterte Suchfeld) */}
      <div className="relative z-10 w-full max-w-xl px-4">{children}</div>

      {/* Orbit-Buttons für die Fachagenten */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        {RADIAL_AGENTS.map((agent) => {
          const rad = (agent.angle * Math.PI) / 180;
          const x = Math.cos(rad) * radius;
          const y = Math.sin(rad) * radius;
          const isSelected = agent.id === activeAgentId;
          const isSuggested = agent.id === suggestedAgentId;
          const isHovered = agent.id === hoveredId;

          return (
            <div
              key={agent.id}
              style={{
                transform: `translate(${x}px, ${y}px)`,
              }}
              className="absolute pointer-events-auto transition-all duration-300 ease-out"
            >
              <button
                type="button"
                onClick={() => onSelectAgent(agent.id)}
                onMouseEnter={() => setHoveredId(agent.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`group relative flex flex-col items-center justify-center rounded-2xl p-3.5 transition-all duration-300 cursor-pointer backdrop-blur-md ${
                  isSelected
                    ? "bg-white text-[var(--ink)] shadow-xl ring-2 scale-110"
                    : isSuggested
                    ? "bg-white/90 text-[var(--ink)] shadow-lg ring-2 ring-[var(--signal)] animate-pulse"
                    : "bg-white/80 hover:bg-white text-[var(--ink-soft)] hover:text-[var(--ink)] shadow-md hover:scale-105 border border-[var(--line)]"
                }`}
                style={{
                  borderColor: isSelected ? agent.color : undefined,
                  boxShadow: isSelected
                    ? `0 10px 25px -5px ${agent.color}40, 0 0 15px 0 ${agent.color}30`
                    : undefined,
                }}
              >
                {/* Visual Accent Dot / Icon */}
                <div
                  className="p-2 rounded-xl text-white transition-all duration-300"
                  style={{
                    backgroundColor: agent.color,
                  }}
                >
                  {agent.icon}
                </div>

                <span className="text-[11px] font-bold mt-1.5 whitespace-nowrap tracking-tight">
                  {agent.name}
                </span>

                {/* Intent Highlight Badge */}
                {isSuggested && (
                  <span className="absolute -top-3.5 bg-[var(--signal)] text-white text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider shadow-md inline-flex items-center gap-1">
                    <IconSparkles size={10} />
                    Empfehlung
                  </span>
                )}

                {/* Hover Tooltip Card */}
                {isHovered && (
                  <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-48 p-2.5 bg-slate-900 text-white rounded-xl text-[11px] font-sans shadow-2xl z-30 pointer-events-none animate-in fade-in zoom-in-95 duration-150 border border-slate-700">
                    <div className="font-bold text-indigo-300">{agent.category}</div>
                    <div className="text-[10px] text-slate-300 mt-0.5 leading-tight">
                      {agent.description}
                    </div>
                  </div>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
