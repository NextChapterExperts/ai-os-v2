---
id: eng:aios-v2-build
title: "AI-OS v2 — Platform-VM & Company Brain"
kind: product
status: active
priority: normal
customer: "NCE First-Party (DEV-VM) + spätere Kunden (PROD-VM)"
offering: offering:ai-os
summary: >
  Souveränes KI-Betriebssystem: Platform-VM + AIOS-CORE, Company Brain als
  SSOT, Memory Gateway, Chat Capture, MCP-Konnektivität.
next_step: "Siehe ROADMAP.md"
tags: [ai-os, platform, company-brain]
---

# AI-OS v2

**State-of-the-art souveränes KI-Betriebssystem — eine Implementierung, ein Stack**  
**Basiert auf:** [archive/ai-os-v1](../archive/ai-os-v1) (v1, eingefroren Juli 2026)

**Erstes Lizenzprodukt:** Platform-VM + `AIOS-CORE` — *eine VM · eine Tür · ein Gedächtnis **pro VM***  
→ [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) · **Isolation:** NCE-DEV-Brain ≠ Kunden-PROD-Brain; NCE nutzt Company Brain First-Party auf der Werkstatt-VM

---

## Die vier Ziele

| Ziel | Wie |
|------|-----|
| **Kosten sparen** | Ollama-Default · OpenRouter `:floor` · Skill-Loop · LangFuse-FinOps |
| **Qualität** | Context Bundle · GraphRAG · Unified Search · Guardrails · Human-in-the-Loop |
| **Skalierbar** | Layered Deployment · Tenant-Isolation · Compose-Profile |
| **Erweiterbar** | MCP · SDK-Contract · SKU-Fach-Agenten · versionierte Skills |

---

## Warum v2?

v1 hat die Konzepte bewiesen. v2 baut **genau einen** production-grade Stack:

| | v1 | v2 |
|---|---|---|
| Agent-Contract | Optional | Pflicht — SDK |
| Datenprodukte | Umgehbar | Einziger Datenpfad |
| Multi-Tenant | Ordnerstruktur | Runtime-Isolation |
| Deployment | Monolith | Core → Platform → Fach (Gate) |
| Workflow-Engine | Eigener Runner | LangGraph |
| Skill-Loop | Offen | Tag 1 |
| Scheduler | P2-Blocker | Phase 2 |
| Monitoring | Spät | LangFuse Tag 1 |
| Suche + Modelle | Verstreut | Platform-Services |
| Inference | Gemischt | Ollama + OpenRouter |

---

## Kern-Prinzip

> **Jeder Agent ist ein Contract, kein Skript.**

Ein Agent, der keinen typisierten Datenprodukt-Output liefert, keine MCP-Adapter nutzt und keinen Tenant-Kontext trägt — ist kein gültiger AI-OS-Agent.

---

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| **[ROADMAP.md](ROADMAP.md)** | **Sehr detaillierte Bauanleitung** — für LLMs und Entwickler |
| [docs/00-VISION.md](docs/00-VISION.md) | Plattform-Vision (aus v1 aktualisiert) |
| [docs/01-ARCHITEKTUR.md](docs/01-ARCHITEKTUR.md) | Vollständige v2-Architektur |
| [docs/02-AGENT-SDK.md](docs/02-AGENT-SDK.md) | Agent-Contract — wie schreibt man einen Agenten? |
| [docs/03-DATENPRODUKTE.md](docs/03-DATENPRODUKTE.md) | Schema-Catalog + Datenflusskarte |
| [docs/04-DEPLOYMENT.md](docs/04-DEPLOYMENT.md) | 3 Deployment-Modi |
| [docs/05-CONSOLE-IA.md](docs/05-CONSOLE-IA.md) | 3-Ebenen-UI-Konzept |
| [docs/06-PRODUKT-DEPLOYMENT.md](docs/06-PRODUKT-DEPLOYMENT.md) | Produkt-Deployment & Abnahme |
| [docs/07-LOKALES-MODELL-TESTPROTOKOLL.md](docs/07-LOKALES-MODELL-TESTPROTOKOLL.md) | Capability-Tests lokales Modell (Ollama) |
| [docs/08-MARKTVERGLEICH.md](docs/08-MARKTVERGLEICH.md) | Markt-/Wettbewerbsvergleich |
| [docs/09-COMPANY-BRAIN.md](docs/09-COMPANY-BRAIN.md) | **Company Brain** (SSOT, org:*, MCP/DP-Regeln, P18) |
| [docs/10-MEMORY-EINFACH.md](docs/10-MEMORY-EINFACH.md) | **Memory einfach** — alle Speicher + Art (Datei/Graph/Vektor/…) |
| [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) | **Platform-VM** — erstes Produkt, Memory Gateway, Chat Capture |
| [docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md) | **P1–P19 im Detail** — Regeln, Verbote, Abnahme |
| [docs/13-IST-STAND.md](docs/13-IST-STAND.md) | **Ist-Stand** — was heute läuft vs. Roadmap-Ziel |
| [docs/14-KONTEXT.md](docs/14-KONTEXT.md) | **Kontext Lagebild→LLM** — Retrieval, Prompt, Context Bundle |
| [docs/ref/](docs/ref/) | Referenz-Dokumente aus v1 |

---

## Leitprinzipien (P1–P19)

**Vollständig:** [docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md) (Intent · Regeln · Verboten · Abnahme)  
Kurz: [ROADMAP.md](ROADMAP.md) Kap. 1 · [docs/00-VISION.md](docs/00-VISION.md)

Kernauszug:
- **MCP + DataProducts** (P5/P8) — nur `self.mcp`, In/Out typisiert
- **Platform vor Fach-Agenten** (P10) — Gate vor SKU-Deploy
- **Alles in die Datenbank** (P9) — kein Run nur im RAM
- **Search + Memory Gateway** (P11) — eine Suche, eine Inference-Tür
- **FinOps** (P12) — Ollama-Default, Cloud messbar
- **Company Brain** (P18) — [docs/09-COMPANY-BRAIN.md](docs/09-COMPANY-BRAIN.md)
- **Platform-VM first** (P19) — 1 VM = 1 Brain; NCE First-Party — [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md)

---

## DEV-VM Bootstrap (jetzt)

Nach Ubuntu-Installation auf `ai-os-dev`: Tools + Dokus — siehe  
[`appliance/BOOTSTRAP-DEV-VM.md`](appliance/BOOTSTRAP-DEV-VM.md)  
Sync vom Host: `./appliance/sync-docs-to-vm.sh peter@VM_IP --with-installers`

## Company-Brain-Seed (NCE First-Party)

Organisation, Offerings, Projekte, Policies — Obsidian-tauglich:

[`customers/nextchapter/knowledge/seed/`](customers/nextchapter/knowledge/seed/)  
Start: `seed/README.md` → `00-organization.md` → `06-projektmap-index.md`

---

## Kurzstart (Ziel-Zustand)

```bash
# Core OS + LangFuse starten
docker compose -f deploy/infra.yml -f deploy/monitoring.yml -f deploy/core.yml up

# + Platform-Agenten (vor Fach-Agenten Pflicht)
docker compose -f deploy/infra.yml -f deploy/monitoring.yml \
  -f deploy/core.yml -f deploy/platform-agents.yml up

# Platform-Gate, dann Fach-Agenten
python -m tests.platform_gate --tenant nextchapter
docker compose ... -f deploy/agents/research.yml -f deploy/agents/blog.yml up
```

---

## v1-Referenz

v1 ist eingefroren und bleibt vollständig lauffähig als Read-only-Referenz.  
Repo: [../1000-AI-OS](../1000-AI-OS) — Tag: `v1-freeze`
