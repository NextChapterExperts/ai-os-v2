# AI-OS Console (`core/console-web`)

Next.js 15 Console — 3-Ebenen-IA (Lagebild / Workflows / Plattform).

**Port:** `8092` (nicht 3000)  
**Ist-Stand:** [docs/13-IST-STAND.md](../../docs/13-IST-STAND.md) · **IA-Ziel:** [docs/05-CONSOLE-IA.md](../../docs/05-CONSOLE-IA.md)

## Start

```bash
cd core/console-web
npm install   # einmalig
npm run dev   # → http://localhost:8092
```

Voraussetzungen für volle Lagebild-Fragen: Orchestrator auf `:8091` (`./core/orchestrator/run.sh`).

## Routen

| Pfad | Rolle |
|------|--------|
| `/` | Lagebild — Fragefeld → `/api/dispatch` |
| `/workflows` | Platzhalter (Ziel: Scheduler/LangGraph) |
| `/platform` | Health-Probes |

## Env (Auswahl)

Siehe Root-`.env.example`. Wichtig u. a.: `ORCHESTRATOR_PORT`, Memory-Pfad `/opt/ai-os/memory`, `AIOS_MEMORY_PROJECT`, Ollama-Host.
