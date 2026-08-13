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
  angle: number; // Grad auf dem Kreis (270 = Oben, 342, 54, 126, 198)
  color: string;
  glowColor: string;
}

export const RADIAL_AGENTS: AgentNode[] = [
  {
    id: "handwerker",
    name: "Handwerker Angebot",
    category: "Handwerk & Bau",
    description: "Kalkulierte Angebote, Leistungsbeschreibungen & Kundenanschreiben",
    icon: <IconTool size={32} />,
    angle: 270, // Oben
    color: "#00f2fe",
    glowColor: "rgba(0, 242, 254, 0.65)",
  },
  {
    id: "blog",
    name: "Blog Generator",
    category: "Marketing & Media",
    description: "SEO-optimierte Fachartikel, Content-Synthese & Marketing-Posts",
    icon: <IconEdit size={32} />,
    angle: 342, // Oben-Rechts
    color: "#c084fc",
    glowColor: "rgba(192, 132, 252, 0.65)",
  },
  {
    id: "meetings",
    name: "Meeting Manager",
    category: "Zeitmanagement",
    description: "Kalender-Sync, Terminprüfungen & KI-Meeting-Summaries",
    icon: <IconCalendar size={32} />,
    angle: 54, // Unten-Rechts
    color: "#38bdf8",
    glowColor: "rgba(56, 189, 248, 0.65)",
  },
  {
    id: "email",
    name: "E-Mail & Ingest",
    category: "Finanzen & Dokumente",
    description: "Gmail-Rechnungen, PDF-Beleg-Extraktion & Knowledge Graph Commit",
    icon: <IconFileText size={32} />,
    angle: 126, // Unten-Links
    color: "#f472b6",
    glowColor: "rgba(244, 114, 182, 0.65)",
  },
  {
    id: "research",
    name: "Deep Research",
    category: "Wissen & Internet",
    description: "SearXNG Anonymer Web-Egress & Company Brain Suche",
    icon: <IconSearch size={32} />,
    angle: 198, // Oben-Links
    color: "#60a5fa",
    glowColor: "rgba(96, 165, 250, 0.65)",
  },
];

interface RadialNavigationWheelProps {
  activeAgentId: string;
  suggestedAgentId?: string | null;
  onSelectAgent: (agentId: string) => void;
  children?: React.ReactNode;
}

export const RadialNavigationWheel: React.FC<RadialNavigationWheelProps> = ({
  activeAgentId,
  suggestedAgentId,
  onSelectAgent,
  children,
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Vergrößerter Radius (440px) für maximale Ausnutzung auf großen Desktop-Bildschirmen
  const radius = 440;

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[920px] w-full py-16 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950 rounded-3xl border border-cyan-500/30 shadow-[0_0_90px_rgba(6,182,212,0.2)] overflow-hidden">
      {/* 1. ROTIERENDE & PULSIERENDE SVG ORBIT-RINGE (GIANT SCALE) */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-visible"
        viewBox="-600 -600 1200 1200"
      >
        <defs>
          {/* Radial Gradient Background Glow */}
          <radialGradient id="cyberCenterGlowGiant" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#0f172a" stopOpacity="0" />
          </radialGradient>

          {/* Neon Arc Stroke Gradient */}
          <linearGradient id="neonArcGradientGiant" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00f2fe" stopOpacity="0.95" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.95" />
          </linearGradient>

          {/* Laser Glow Filter */}
          <filter id="neonGlowFilterGiant" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Center Glow Aura */}
        <circle cx="0" cy="0" r={radius + 100} fill="url(#cyberCenterGlowGiant)" />

        {/* Outer Pulsing Dashed Orbit Ring */}
        <circle
          cx="0"
          cy="0"
          r={radius + 30}
          fill="none"
          stroke="url(#neonArcGradientGiant)"
          strokeWidth="2.5"
          strokeDasharray="8 16"
          className="opacity-60 animate-[spin_90s_linear_infinite]"
        />

        {/* Main Solid Glowing Orbit Circle */}
        <circle
          cx="0"
          cy="0"
          r={radius}
          fill="none"
          stroke="url(#neonArcGradientGiant)"
          strokeWidth="3"
          filter="url(#neonGlowFilterGiant)"
          className="opacity-90"
        />

        {/* Inner Secondary Dashed Orbit */}
        <circle
          cx="0"
          cy="0"
          r={radius - 80}
          fill="none"
          stroke="#06b6d4"
          strokeWidth="2"
          strokeDasharray="20 20"
          className="opacity-40 animate-[spin_60s_linear_infinite_reverse]"
        />

        {/* Rays from Hub to Node Bulbs */}
        {RADIAL_AGENTS.map((agent) => {
          const rad = (agent.angle * Math.PI) / 180;
          const x2 = Math.cos(rad) * radius;
          const y2 = Math.sin(rad) * radius;
          const isSelected = agent.id === activeAgentId;
          const isSuggested = agent.id === suggestedAgentId;

          return (
            <g key={`ray-${agent.id}`}>
              <line
                x1="0"
                y1="0"
                x2={x2}
                y2={y2}
                stroke={isSelected ? agent.color : isSuggested ? "#00f2fe" : "#334155"}
                strokeWidth={isSelected || isSuggested ? "3.5" : "1.5"}
                strokeOpacity={isSelected ? "0.95" : isSuggested ? "0.85" : "0.4"}
                filter={isSelected || isSuggested ? "url(#neonGlowFilterGiant)" : undefined}
                className="transition-all duration-300"
              />
              {/* Pulsing Energy Dot on Line */}
              {isSelected && (
                <circle
                  cx={x2 * 0.65}
                  cy={y2 * 0.65}
                  r="5"
                  fill={agent.color}
                  filter="url(#neonGlowFilterGiant)"
                  className="animate-ping"
                />
              )}
            </g>
          );
        })}
      </svg>

      {/* 2. ZENTRALES SUCHFELD HUB (Im Zentrum des riesigen Rads) */}
      <div className="relative z-20 w-full max-w-3xl px-6">{children}</div>

      {/* 3. RIESIGE ORBITAL FACHAGENTEN NODES (Ausschlaggebend für Klick-Absprung & Hover-Tooltip) */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-10">
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
                className={`group relative flex flex-col items-center justify-center p-6 rounded-3xl transition-all duration-300 cursor-pointer backdrop-blur-2xl ${
                  isSelected
                    ? "bg-slate-900/95 text-white scale-125 z-30 ring-2 ring-cyan-400"
                    : isSuggested
                    ? "bg-slate-900/90 text-slate-100 scale-110 animate-pulse border-cyan-400"
                    : "bg-slate-900/85 hover:bg-slate-800/95 text-slate-100 hover:text-white hover:scale-115"
                }`}
                style={{
                  border: `2.5px solid ${isSelected ? agent.color : isSuggested ? "#00f2fe" : "rgba(51, 65, 85, 0.7)"}`,
                  boxShadow: isSelected
                    ? `0 0 50px ${agent.glowColor}, inset 0 0 25px ${agent.glowColor}`
                    : isHovered
                    ? `0 0 35px ${agent.glowColor}`
                    : "0 15px 40px rgba(0, 0, 0, 0.7)",
                }}
              >
                {/* Glowing Circular Icon Plaque */}
                <div
                  className="p-4 rounded-2xl text-slate-950 font-extrabold transition-all duration-300 flex items-center justify-center shadow-xl"
                  style={{
                    background: `linear-gradient(135deg, ${agent.color}, #0284c7)`,
                    boxShadow: `0 0 28px ${agent.glowColor}`,
                  }}
                >
                  {agent.icon}
                </div>

                {/* Node Title Label */}
                <span className="text-xs sm:text-sm font-black mt-3.5 whitespace-nowrap tracking-wider uppercase text-slate-100 group-hover:text-cyan-300 transition-colors">
                  {agent.name}
                </span>

                {/* Intent Smart Suggestion Badge */}
                {isSuggested && (
                  <span className="absolute -top-5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-[10px] font-black px-3.5 py-1 rounded-full uppercase tracking-widest shadow-[0_0_20px_#06b6d4] inline-flex items-center gap-1 border border-cyan-300">
                    <IconSparkles size={12} />
                    Empfohlen
                  </span>
                )}

                {/* ERKLÄRUNG BLASE BEIM HOVERN */}
                {isHovered && (
                  <div className="absolute top-full mt-4 left-1/2 -translate-x-1/2 w-64 p-4 bg-slate-950/95 text-slate-100 rounded-2xl text-xs font-sans shadow-[0_20px_60px_rgba(0,0,0,0.95)] z-50 pointer-events-none border border-cyan-400/60 backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-150">
                    <div className="flex items-center justify-between font-extrabold text-cyan-400 uppercase tracking-wider text-[11px] border-b border-slate-800 pb-1.5 mb-1.5">
                      <span>{agent.category}</span>
                      <span className="text-[10px] text-slate-400 font-mono">Klick ➔ Absprung</span>
                    </div>
                    <div className="text-xs text-slate-200 leading-relaxed font-normal">
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
