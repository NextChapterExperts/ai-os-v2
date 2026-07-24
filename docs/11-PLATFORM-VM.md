# AI-OS v2 — Platform-VM (erstes Lizenzprodukt)

**Stand:** 2026-07-24 · **Status:** verbindlich (nachgezogen aus v1 „Plattform-VM first“)  
**Operativ:** [ROADMAP.md](../ROADMAP.md) · **Lizenz:** [06-PRODUKT-DEPLOYMENT.md](06-PRODUKT-DEPLOYMENT.md) · **Deployment:** [04-DEPLOYMENT.md](04-DEPLOYMENT.md)  
**Quelle der Entscheidung:** [1000-AI-OS ROADMAP § v2](../../1000-AI-OS/ROADMAP.md) · [21-ZIELARCHITEKTUR-V2](../../1000-AI-OS/docs/platform/21-ZIELARCHITEKTUR-V2.md)

---

## Leitentscheidung

> **Eine VM für die Platform. Eine Tür für alle KI-Anfragen. Ein Gedächtnis für alles.**

| Was | Bedeutung |
|-----|-----------|
| **Eine VM** | AI-OS läuft als **Linux-Appliance** (DEV oder PROD) — Stack + (DEV) Werkzeuge in einer Maschine |
| **Eine Tür** | Alle LLM-Anfragen (Ollama, Gemini, ChatGPT/OpenRouter) gehen durch das **Memory Gateway** — nichts umgeht es |
| **Ein Gedächtnis** | Pro **Appliance/VM**: jeder Chat in dieser Welt landet im **Company Brain dieser VM** (L1/L2/G + Audit) — nicht über VM-Grenzen hinweg |

**Erstes Lizenzprodukt** = **Platform-VM + `AIOS-CORE`** (ohne Pflicht-Fachagenten).  
Fach-SKUs kommen erst nach Platform-Gate.

**Ziel-Frage an die Platform:** *„Was habe ich letzte Woche zu SAP besprochen?“* — egal ob in AI-OS, Gemini oder ChatGPT **auf derselben VM**.

---

## Isolationsmodell (verbindlich): eine Welt = eine VM = ein Company Brain

**Entscheidung:** Physische Trennung (nicht nur Config-Flags auf einer gemeinsamen DB).

```text
┌─────────────────────────────────────┐     ┌─────────────────────────────────────┐
│  NCE Werkstatt-VM (DEV)             │     │  Kunden-VM (PROD) — je Kunde eine   │
│  Ubuntu Desktop + Cursor/Antigrav. │     │  Ubuntu Server, nur Browser         │
│  Docker: AI-OS Core + Memory        │     │  Docker: AI-OS Core + Memory        │
│  Company Brain = NCE (nextchapter / │     │  Company Brain = NUR dieser Kunde   │
│  NCE-Org) — selbst genutzt          │     │                                     │
└─────────────────────────────────────┘     └─────────────────────────────────────┘
         eigene Volumes/DB                           eigene Volumes/DB
         kein Auto-Sync ───────────────────────────► kein Zugriff auf NCE-Brain
```

| Welt | Wer nutzt das Company Brain? | Was fließt rein? |
|------|------------------------------|------------------|
| **NCE DEV-VM** | **Peter / NCE selbst** (First-Party) | Cursor, Antigravity, Gemini, Console, Plattform-Entwicklung, eigene Firma/Angebote |
| **Kunden-PROD-VM** | nur der Kunde | Console, seine Captures, seine Agenten — **kein** NCE-Dev-Kram |

**Konsequenzen**
- NCE **ist** der erste Company-Brain-Nutzer — auf der Werkstatt-VM, nicht „erst wenn ein Kunde kommt“.
- Kundendaten und NCE-Wissen teilen **keine** Postgres/Qdrant/Letta-Instanz.
- Kein automatischer Sync DEV → Kunden-Image. Bewusste Übergabe nur als **Seed/Doku/SKU**, nie als Roh-Chat-Dump.
- Optional später: zweite NCE-VM „PROD-like“ für eigenen Betrieb ohne Cursor — gleiche Isolation, anderer Profil-Mix.
- Tenant-IDs *innerhalb* einer VM bleiben möglich (z. B. Demo-Sandbox), ersetzen aber **nicht** die VM-Grenze zu Kunden.

---

## DEV-VM vs. PROD-VM

| | **DEV-VM** (Werkstatt) | **PROD-VM** (Kunde / Lizenz) |
|--|------------------------|------------------------------|
| Platform (`AIOS-CORE`) | ✅ | ✅ |
| Cursor + Antigravity | ✅ **in** der VM | ❌ |
| Fachagenten entwickeln & testen | ✅ | nur deployte / lizenzierte Version |
| Gemini / ChatGPT (eigene Accounts) | ✅ über Memory Gateway + Chat Capture | ✅ über Memory Gateway + Capture |
| Nutzung | Arbeit **in** der VM | Kunde nur **Browser** |
| Host-Rolle | nur KVM/libvirt-Manager | Hetzner/On-Prem Hypervisor |

```text
v1 heute:   Host (Cursor, Antigravity)  →  Incus-Container (AI-OS)
v2 Ziel:    Host (nur KVM/libvirt)      →  DEV-VM (Cursor + Antigravity + AI-OS)
            Kunde:                      →  PROD-VM (Platform + Agents, Browser)
```

**Kein** Hypervisor *inside* der Appliance. Compose-Files sind VM-agnostisch (brauchen Docker).

---

## Zwei Wege, ein Speicher

```text
Weg 1 — durch AI-OS (automatisch)
  Mensch / Agent → Console / Orchestrator → Memory Gateway → Ollama | OpenRouter
                                         ↓
                         immer: L1/L2/G + A + LangFuse (P9 / P18)

Weg 2 — Browser / IDE außerhalb des Orchestrators
  Gemini-Web · ChatGPT-Web · Antigravity-Transkripte · (Cursor-Exports)
       → Chat Capture Service (in der VM)
       → gleicher Normalizer (/v1/chat-import) → gleicher Speicher
```

| Komponente | Aufgabe |
|------------|---------|
| **Memory Gateway** | „Eine Tür“: ruft Modelle auf **und** schreibt **immer** Memory-Trail + Audit + LangFuse |
| **Chat Capture Service** | Sammelt externe Chats (Gemini-Export, Antigravity `transcript.jsonl`, später ChatGPT) |
| **chat_import** (aus v1) | Normalisiert Quellen → L1 Qdrant + L2 Letta (+ Claims nur via L3-Curator / DP) |

**Regel:** Kein Chat ohne Memory-Trail — Platform-Chats sofort, Browser-/IDE-Chats über Capture (Polling oder manueller Import; Echtzeit später).

---

## Was das erste Produkt enthält (`AIOS-CORE` auf VM)

- Appliance-Image / Installer-Pfad (qcow2 bzw. `install.ai-os.app`)
- Infra: Postgres+pgvector, Qdrant, Letta, LiteLLM, SearXNG, LangFuse
- Core: Orchestrator, MCP-Gateway, Console Shell, Unified Search
- **Memory Gateway** (Model Gateway + Persist-Hook)
- **Chat Capture** (mindestens Gemini + Antigravity)
- Guardrails-Skeleton, Audit (hash-chained ab Schema), Agent Registry
- `license.yaml` — nur Core; Packs optional

**Explizit nicht nötig für den ersten Verkauf:** Research/Blog/Email-Fachagenten, Whisper/Piper in der VM, Ollama *in* der VM (Default: Ollama LAN/remote), Mega-Console mit Domänen-UIs.

---

## Antigravity / Cursor in der DEV-VM

```text
Antigravity / Cursor  →  /opt/ai-os/ingest/inbox/  oder Capture-Pfad
Ingest-Agent / chat_import  →  L1/L2/G (+ Audit)
Console / Unified Search   →  Wissen auffindbar
```

Ein Dateisystem, ein Git-Root, ein AI-OS-Stack — kein Host→Container-Poller mehr wie in v1.

---

## Abgrenzung Company Brain

- Capture + Gateway **füllen** den Speicher **dieser** VM; **Company Brain (P18)** bleibt SSOT-Regeln: Roh-Chat ≠ Decision; Claims nur über DP-Commit / L3-Curator.
- Isolation zwischen NCE und Kunde = **eigene Appliance** (siehe oben), nicht Shared-SaaS-DB.
- Details: [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) · [10-MEMORY-EINFACH.md](10-MEMORY-EINFACH.md)

---

## Build-Reihenfolge (Produkt-Sicht)

| Phase | Deliverable |
|-------|-------------|
| **0** | Repo + `appliance/` + Infra/Monitoring Compose + DB-Schema + DEV-VM-Bootstrap |
| **1** | Core OS + **Memory Gateway** + Unified Search + LangFuse-Traces |
| **1b** | **Chat Capture** (Gemini, Antigravity; ChatGPT-Export) + Console „Chat-Erfassung“ |
| **2** | Platform-Agenten → Platform-Gate (inkl. Ingest für Capture-Inbox) |
| **3+** | SDK, Fach-SKUs, volle Console — erst nach Gate |

Technische Details und Akzeptanztests: [ROADMAP.md](../ROADMAP.md) Kap. 5–7 und §19.
