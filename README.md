# AI-OS v2

**State-of-the-art souveränes KI-Betriebssystem — eine Implementierung, ein Stack**  
**Basiert auf:** [1000-AI-OS](../1000-AI-OS) (v1, eingefroren Juli 2026)  
**Repo:** [NextChapterExperts/ai-os-v2](https://github.com/NextChapterExperts/ai-os-v2)

**Erstes Lizenzprodukt:** Platform-VM + `AIOS-CORE` — *eine VM · eine Tür · ein Gedächtnis **pro VM***  
→ [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) · **Isolation:** NCE-DEV-Brain ≠ Kunden-PROD-Brain

**Aktueller Bau-Stand (verbindlich für „was läuft?“):** → **[docs/13-IST-STAND.md](docs/13-IST-STAND.md)**

---

## Ist-Stand (2026-07-24)

| Bereich | Status |
|---------|--------|
| Phase 0 — Infra, LangFuse, Schema, DEV-Bootstrap, GitHub | weitgehend erledigt |
| Phase 1 — Orchestrator, Console, MCP-Skeleton | Skeleton lauffähig |
| Phase 1b — Cursor → SQLite Memory | teilweise (Gemini/Antigravity offen) |
| Offerings / Engagements / `daily_open_loops` | Seed + Packs + Intent |
| Phase 2–6 — Platform-Gate, SDK, Fach-Agenten, GraphRAG | geplant |

Auf der DEV-VM: Console `:8092`, Orchestrator `:8091`, MCP-Gateway `:8097`, Compose-Infra, Capture nach `/opt/ai-os/memory/`.

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
| **[docs/13-IST-STAND.md](docs/13-IST-STAND.md)** | **Was heute läuft** (Ist vs. Ziel) |
| **[ROADMAP.md](ROADMAP.md)** | Bauanleitung / Ziel-Spec — für LLMs und Entwickler |
| [docs/00-VISION.md](docs/00-VISION.md) | Plattform-Vision |
| [docs/01-ARCHITEKTUR.md](docs/01-ARCHITEKTUR.md) | Ziel-Architektur |
| [docs/02-AGENT-SDK.md](docs/02-AGENT-SDK.md) | Agent-Contract |
| [docs/03-DATENPRODUKTE.md](docs/03-DATENPRODUKTE.md) | Schema-Catalog + Datenflusskarte |
| [docs/04-DEPLOYMENT.md](docs/04-DEPLOYMENT.md) | Deploy-Modi (Ist + Ziel) |
| [docs/05-CONSOLE-IA.md](docs/05-CONSOLE-IA.md) | 3-Ebenen-UI-Konzept |
| [docs/06-PRODUKT-DEPLOYMENT.md](docs/06-PRODUKT-DEPLOYMENT.md) | Produkt-Deployment & Abnahme |
| [docs/07-LOKALES-MODELL-TESTPROTOKOLL.md](docs/07-LOKALES-MODELL-TESTPROTOKOLL.md) | Capability-Tests Ollama |
| [docs/08-MARKTVERGLEICH.md](docs/08-MARKTVERGLEICH.md) | Markt-/Wettbewerbsvergleich |
| [docs/09-COMPANY-BRAIN.md](docs/09-COMPANY-BRAIN.md) | Company Brain (P18) |
| [docs/10-MEMORY-EINFACH.md](docs/10-MEMORY-EINFACH.md) | Memory-Schichten |
| [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md) | Platform-VM (P19) |
| [docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md) | P1–P19 im Detail |
| [docs/ref/](docs/ref/) | Referenz aus v1 |

---

## Leitprinzipien (P1–P19)

**Vollständig:** [docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md)  
Kurz: [ROADMAP.md](ROADMAP.md) Kap. 1 · [docs/00-VISION.md](docs/00-VISION.md)

Kernauszug:
- **MCP + DataProducts** (P5/P8) — nur `self.mcp`, In/Out typisiert
- **Platform vor Fach-Agenten** (P10) — Gate vor SKU-Deploy
- **Alles in die Datenbank** (P9) — kein Run nur im RAM
- **Search + Memory Gateway** (P11) — eine Suche, eine Inference-Tür
- **FinOps** (P12) — Ollama-Default, Cloud messbar
- **Company Brain** (P18) — [docs/09-COMPANY-BRAIN.md](docs/09-COMPANY-BRAIN.md)
- **Platform-VM first** (P19) — 1 VM = 1 Brain — [docs/11-PLATFORM-VM.md](docs/11-PLATFORM-VM.md)

---

## DEV-VM Bootstrap

Nach Ubuntu-Installation auf `ai-os-dev`: Tools + Dokus — siehe  
[`appliance/BOOTSTRAP-DEV-VM.md`](appliance/BOOTSTRAP-DEV-VM.md)  
Sync vom Host: `./appliance/sync-docs-to-vm.sh peter@VM_IP --with-installers`

---

## Kurzstart (Ist — DEV-VM)

```bash
# Infra + Monitoring
docker compose -f deploy/infra.yml -f deploy/monitoring.yml up -d

# Core-Prozesse (lokal, nicht alles in Compose)
./core/orchestrator/run.sh          # :8091
./core/mcp_gateway/run.sh           # :8097
cd core/console-web && npm run dev  # :8092 → http://localhost:8092

# Optional: Cursor-Capture (systemd user unit oder npm start in core/capture)
# Memory: /opt/ai-os/memory/memory.db
```

Lagebild-Feld → `POST /api/dispatch` → Orchestrator (`daily_open_loops`, `memory_ask`, …).

Details & Smoke-Pfad: [docs/13-IST-STAND.md](docs/13-IST-STAND.md).

---

## Kurzstart (Ziel-Zustand — noch nicht vollständig im Repo)

```bash
# Später: voller Core inkl. Search/Skill/… als Compose
docker compose -f deploy/infra.yml -f deploy/monitoring.yml -f deploy/core.yml up

# Später: Platform-Agenten, dann Gate, dann Fach-Agenten
# docker compose … -f deploy/platform-agents.yml up
# python -m tests.platform_gate --tenant nextchapter
# docker compose … -f deploy/agents/research.yml …
```

Dateien wie `platform-agents.yml` / `tests.platform_gate` sind **Ziel-Spec** — siehe Roadmap Phase 2+.

---

## v1-Referenz

v1 ist eingefroren und bleibt als Read-only-Referenz.  
Repo: [../1000-AI-OS](../1000-AI-OS) — Tag: `v1-freeze`
