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
    icon: <IconTool size={24} />,
    angle: 270, // Oben
    color: "#00f2fe",
    glowColor: "rgba(0, 242, 254, 0.5)",
  },
  {
    id: "blog",
    name: "Blog Generator",
    category: "Marketing & Media",
    description: "SEO-optimierte Fachartikel & Marketing-Posts",
    icon: <IconEdit size={24} />,
    angle: 342, // Oben-Rechts
    color: "#c084fc",
    glowColor: "rgba(192, 132, 252, 0.5)",
  },
  {
    id: "meetings",
    name: "Meeting Manager",
    category: "Zeitmanagement",
    description: "Kalender-Sync, Terminprüfungen & Meeting-Summaries",
    icon: <IconCalendar size={24} />,
    angle: 54, // Unten-Rechts
    color: "#38bdf8",
    glowColor: "rgba(56, 189, 248, 0.5)",
  },
  {
    id: "email",
    name: "E-Mail & Ingest",
    category: "Finanzen & Dokumente",
    description: "Gmail-Rechnungen, PDF-Beleg-Extraktion & Graph Commit",
    icon: <IconFileText size={24} />,
    angle: 126, // Unten-Links
    color: "#f472b6",
    glowColor: "rgba(244, 114, 182, 0.5)",
  },
  {
    id: "research",
    name: "Deep Research",
    category: "Wissen & Internet",
    description: "SearXNG Anonymer Web-Egress & Company Brain Suche",
    icon: <IconSearch size={24} />,
    angle: 198, // Oben-Links
    color: "#60a5fa",
    glowColor: "rgba(96, 165, 250, 0.5)",
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

  // Radius des Navigationsrads (in px)
  const radius = 230;

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[640px] w-full py-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950 rounded-3xl border border-cyan-500/20 shadow-[0_0_60px_rgba(6,182,212,0.12)] overflow-hidden">
      {/* 1. KONTINUIERLICH ROTIERENDE & PULSIERENDE SVG ORBIT-RINGE */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-visible"
        viewBox="-350 -350 700 700"
      >
        <defs>
          {/* Radial Gradient Background Glow */}
          <radialGradient id="cyberCenterGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#0f172a" stopOpacity="0" />
          </radialGradient>

          {/* Neon Arc Stroke Gradient */}
          <linearGradient id="neonArcGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00f2fe" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
          </linearGradient>

          {/* Laser Glow Filter */}
          <filter id="neonGlowFilter" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Center Glow Aura */}
        <circle cx="0" cy="0" r={radius + 60} fill="url(#cyberCenterGlow)" />

        {/* Outer Pulsing Dashed Orbit Ring */}
        <circle
          cx="0"
          cy="0"
          r={radius + 15}
          fill="none"
          stroke="url(#neonArcGradient)"
          strokeWidth="1.5"
          strokeDasharray="4 8"
          className="opacity-40 animate-[spin_60s_linear_infinite]"
        />

        {/* Main Solid Glowing Orbit Circle */}
        <circle
          cx="0"
          cy="0"
          r={radius}
          fill="none"
          stroke="url(#neonArcGradient)"
          strokeWidth="2"
          filter="url(#neonGlowFilter)"
          className="opacity-80"
        />

        {/* Inner Secondary Dashed Orbit */}
        <circle
          cx="0"
          cy="0"
          r={radius - 40}
          fill="none"
          stroke="#06b6d4"
          strokeWidth="1"
          strokeDasharray="12 12"
          className="opacity-30 animate-[spin_40s_linear_infinite_reverse]"
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
                strokeWidth={isSelected || isSuggested ? "2.5" : "1"}
                strokeOpacity={isSelected ? "0.9" : isSuggested ? "0.8" : "0.4"}
                filter={isSelected || isSuggested ? "url(#neonGlowFilter)" : undefined}
                className="transition-all duration-300"
              />
              {/* Pulsing Energy Dot on Line */}
              {isSelected && (
                <circle
                  cx={x2 * 0.65}
                  cy={y2 * 0.65}
                  r="3"
                  fill={agent.color}
                  filter="url(#neonGlowFilter)"
                  className="animate-ping"
                />
              )}
            </g>
          );
        })}
      </svg>

      {/* 2. ZENTRALES SUCHFELD HUB (Im Zentrum des Rads) */}
      <div className="relative z-20 w-full max-w-xl px-4">{children}</div>

      {/* 3. ORBITAL FACHAGENTEN NODES (Im Ring angeordnet) */}
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
                className={`group relative flex flex-col items-center justify-center p-4 rounded-2xl transition-all duration-300 cursor-pointer backdrop-blur-xl ${
                  isSelected
                    ? "bg-slate-900/95 text-white scale-115 z-30"
                    : isSuggested
                    ? "bg-slate-900/90 text-slate-100 scale-105 animate-pulse"
                    : "bg-slate-900/80 hover:bg-slate-800/90 text-slate-300 hover:text-white hover:scale-110"
                }`}
                style={{
                  border: `1.5px solid ${isSelected ? agent.color : isSuggested ? "#00f2fe" : "rgba(51, 65, 85, 0.6)"}`,
                  boxShadow: isSelected
                    ? `0 0 30px ${agent.glowColor}, inset 0 0 15px ${agent.glowColor}`
                    : isHovered
                    ? `0 0 20px ${agent.glowColor}`
                    : "0 10px 25px rgba(0, 0, 0, 0.5)",
                }}
              >
                {/* Glowing Circular Icon Plaque */}
                <div
                  className="p-3 rounded-xl text-slate-950 font-bold transition-all duration-300 flex items-center justify-center"
                  style={{
                    background: `linear-gradient(135deg, ${agent.color}, #0284c7)`,
                    boxShadow: `0 0 18px ${agent.glowColor}`,
                  }}
                >
                  {agent.icon}
                </div>

                {/* Node Title Label */}
                <span className="text-[11px] font-extrabold mt-2.5 whitespace-nowrap tracking-wider uppercase text-slate-100 group-hover:text-cyan-300 transition-colors">
                  {agent.name}
                </span>

                {/* Intent Smart Suggestion Badge */}
                {isSuggested && (
                  <span className="absolute -top-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-[9px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-widest shadow-[0_0_12px_#06b6d4] inline-flex items-center gap-1 border border-cyan-300">
                    <IconSparkles size={11} />
                    Empfohlen
                  </span>
                )}

                {/* Cyberpunk Hover Info Card */}
                {isHovered && (
                  <div className="absolute top-full mt-3 left-1/2 -translate-x-1/2 w-52 p-3 bg-slate-950/95 text-slate-100 rounded-xl text-[11px] font-sans shadow-[0_10px_40px_rgba(0,0,0,0.8)] z-40 pointer-events-none border border-cyan-500/40 backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-150">
                    <div className="font-bold text-cyan-400 uppercase tracking-wider text-[10px]">
                      {agent.category}
                    </div>
                    <div className="text-[11px] text-slate-300 mt-1 leading-snug">
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
