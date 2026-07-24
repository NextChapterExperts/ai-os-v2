# AI-OS v2 — Produkt-Deployment & Lizenzmodell

**Stand:** Juli 2026 (Platform-VM first 2026-07-24) · **Autor:** Peter / NCE  
**Verwandt:** [04-DEPLOYMENT.md](04-DEPLOYMENT.md) · [11-PLATFORM-VM.md](11-PLATFORM-VM.md) · [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md) · [ROADMAP.md](../ROADMAP.md)

---

## Leitgedanke

> Jede Architektur-Entscheidung in v2 muss mit dieser Frage vereinbar sein:  
> **«Kann das für einen zweiten Kunden deployed werden, ohne v1-Code anzufassen?»**

Das ist der Unterschied zwischen einem Prototyp und einem Produkt.

### Erstes Lizenzprodukt (verbindlich)

**Platform-VM + `AIOS-CORE`** — auslieferbare Appliance mit:

- Memory Gateway (eine Tür für alle LLM-Calls)
- Chat Capture (Gemini, Antigravity, … → zentrales Gedächtnis)
- Console Shell, Orchestrator, MCP, Unified Search, LangFuse
- Company-Brain-fähige Datenschicht (ohne Pflicht-Fachagenten)

Spec: [11-PLATFORM-VM.md](11-PLATFORM-VM.md). Fach-Packs sind Upsell nach Platform-Gate.

---

## Produkt-Tiers & Lizenzmodell

### Tier-Übersicht

| SKU | Name | Enthält | Deployment |
|-----|------|---------|-----------|
| `AIOS-CORE` | **AI-OS Platform (VM)** | Appliance · Orchestrator · MCP-Gateway · Console · **Memory Gateway** · **Chat Capture** · Memory-Curators · Guardrails · Monitor · Skill-Service · Scheduler | Pflicht, immer — **erstes Produkt** |
| `AIOS-PACK-RESEARCH` | Research Pack | Research-Agent · Recherche-Workflow · Deep-Search | optional |
| `AIOS-PACK-CONTENT` | Content Pack | Blog-Agent · Compliance-Agent · Content-Workflow · LinkedIn-Teaser | optional |
| `AIOS-PACK-COMMS` | Communications Pack | Email-Agent · Calendar-Integration · Time-Agent · Briefing-Erweiterung | optional |
| `AIOS-PACK-ENTERPRISE` | Enterprise Add-on | Guardrails L3 PII · GraphRAG · Monitor 24/7 · SLA · Prioritäts-Support | optional |
| `AIOS-CUSTOM` | Custom Agent | Kundenspezifischer Agent nach Spec | Projektbasis |

### Was «Platform Core» alleine kann

Ein Kunde mit nur `AIOS-CORE` (auf der Platform-VM) hat bereits:
- **Alle LLM-Chats** über Memory Gateway im zentralen Gedächtnis
- **Gemini-/Browser-Chats** über Chat Capture im selben Speicher
- Dokumente ingesten (Inbox → Qdrant-Index → Knowledge Graph)
- Knowledge Graph aufbauen (Entities, Beziehungen, Provenienz)
- Daily Briefing (aus E-Mail + Kalender via MCP)
- Skill-Loop (System lernt aus jeder Nutzung)
- Console (Lagebild, Plattform-Monitor, Chat-Erfassung)
- Guardrails (L1/L2 Policies)
- MCP-Gateway (mail, calendar, web, cms)
- Scheduler (Cron-Workflows)

Das ist bereits demonstrierbar und verkaufbar — **ohne** Research/Blog-Fachagenten.

### Lizenz-Datei pro Kunde

```yaml
# /opt/ai-os/license.yaml
customer_id: abc-gmbh
customer_name: ABC GmbH
license_key: AIOS-2026-XXXX-XXXX-XXXX
issued_by: NextChapter Experts
valid_from: 2026-07-01
valid_until: 2027-07-01
tier: starter

licensed_packages:
  - platform-core       # immer dabei
  - research-agent      # Tier 1

# Was die Platform-Runtime prüft:
# - Vor jedem Agent-Start: ist der SKU in licensed_packages?
# - Täglich: ist license valid_until in der Zukunft?
# - Offline-Check: Signatur-Validierung (kein Cloud-Callback nötig)
```

---

## Deployment-Modelle

### Modell A — Managed (Empfehlung für erste Kunden)

**Wer betreibt:** Peter / NCE auf Hetzner  
**Wer zahlt Hetzner:** NCE (in Lizenzpreis eingerechnet)  
**Kunde sieht:** Browser-URL, Console, keine Infrastruktur

```
NCE-Hetzner-Account
  ├── VM «abc-gmbh»         → https://abc.ai-os.app
  │     ├── AI-OS v2 (Docker Compose)
  │     ├── license.yaml    → AIOS-CORE + AIOS-PACK-RESEARCH
  │     └── customers/abc-gmbh/
  │
  ├── VM «xyz-ag»           → https://xyz.ai-os.app
  │     ├── AI-OS v2 (Docker Compose)
  │     ├── license.yaml    → AIOS-CORE only
  │     └── customers/xyz-ag/
  │
  └── VM «demo»             → https://demo.ai-os.app
        └── Demo-Tenant für Vertrieb
```

**Vorteile:**
- NCE kontrolliert die Infrastruktur vollständig
- Updates zentralisiert ausrollbar
- Kein technisches Setup beim Kunden nötig
- Backup, Monitoring, Security in NCE-Hand

**Nachteile:**
- Hetzner-Kosten liegen bei NCE
- Latenz wenn Kunde in anderer Region

### Modell B — Self-Hosted (für technisch affine Kunden)

**Wer betreibt:** Kunde selbst  
**Infrastruktur:** Kunde-eigener Server oder VM  
**Installer:** Einzeiliger Befehl + Lizenz-Key

```bash
# Kunde führt aus (einmalig):
curl -fsSL https://install.ai-os.app | bash \
  --license AIOS-2026-XXXX-XXXX-XXXX \
  --customer-id abc-gmbh \
  --customer-name "ABC GmbH"

# Installer macht automatisch:
# 1. Docker + Dependencies prüfen/installieren
# 2. AI-OS v2 herunterladen
# 3. Lizenz validieren (offline-fähig)
# 4. .env generieren
# 5. Tenant-Profil anlegen
# 6. Docker Compose starten (nur lizensierte Pakete)
# 7. Bootstrap ausführen
# 8. Gibt Console-URL aus
```

### Modell C — On-Premise Air-Gap (Enterprise)

Kein Internet-Zugang, vollständig isoliert. Für Kunden mit strengen Compliance-Anforderungen (Behörden, Gesundheit, Finanz).

```bash
# Installer als offline-Bundle bereitgestellt
# Docker Images als .tar-Archiv
# Lizenz-Key mit Offline-Signatur
aios-installer --offline --bundle ./ai-os-bundle-v2.tar.gz \
  --license AIOS-2026-XXXX-XXXX-XXXX-OFFLINE
```

---

## VM-Strategie: KVM statt Incus/LXC

### Warum für Kunden-Deployments KVM, nicht Incus

| | Incus/LXC | KVM-VM |
|---|---|---|
| Cursor + Docker im selben OS | Nein (Sync nötig) | **Ja** |
| Portabilität (Hetzner ↔ Kunde) | Incus-spezifisch | **qcow2-Image, universell** |
| Isolation | Shared Kernel | **Eigener Kernel** |
| GPU-Passthrough | Komplex | **VFIO — Standard** |
| Snapshot/Backup | Incus-Snapshot | **QEMU-Snapshot, oder Hetzner-Snapshot** |
| Für Kunde selbsterklärend | Nein | **Ja — «das ist eine VM»** |

**Konsequenz für v2:** Kein Incus-Layer in der Produkt-Architektur. Jede Kunden-Deployment läuft als:
- KVM-VM (lokal beim Kunden)
- Hetzner-VM (Managed-Modus)
- Bare-Metal-Server + Docker direkt (GEX44)

Die `deploy/`-Compose-Files sind VM-agnostisch — sie brauchen nur Docker.

---

## Package-Manager CLI

```bash
# Neues Paket installieren (nach Lizenz-Erweiterung)
aios install research-agent
# → Prüft license.yaml: ist research-agent lizensiert?
# → Fügt deploy/agents/research.yml zu aktiven Compose-Files hinzu
# → docker compose up -d research-agent
# → Bootstrap: Tenant-Profil um Research-Skills erweitern
# → Console: Research-Route freigeschaltet

# Paket deinstallieren
aios uninstall blog-agent
# → docker compose stop blog-agent
# → Daten bleiben erhalten (nur Service gestoppt)
# → Console: Blog-Route gesperrt

# Lizenz erweitern (nach Kauf)
aios license update --key AIOS-2026-XXXX-XXXX-YYYY
# → Neue licensed_packages validieren
# → Neue Pakete sofort installierbar

# Status anzeigen
aios status
# Platform Core        ✓  aktiv  (v2.1.0)
# Research Agent       ✓  aktiv  (v2.0.3)
# Blog Agent           ✗  nicht lizensiert
# Email Agent          ✗  nicht lizensiert
# License: abc-gmbh · gültig bis 01.07.2027

# Updates einspielen
aios update
# → Zieht neue Docker Images
# → Führt Datenbankmigrationen aus
# → Rolling restart (kein Downtime)
```

---

## Kunden-Onboarding-Flow

```
1. VERTRAG / LIZENZ
   NCE erstellt license.yaml + Lizenz-Key
   Entscheidung: Managed oder Self-Hosted

2. INFRASTRUCTURE (Managed: NCE, Self-Hosted: Kunde)
   VM anlegen (Ubuntu 24.04, mind. 16 GB RAM, 100 GB NVMe)
   → Für GEX44: GPU vorhanden, Ollama lokal
   → Für kleinere VM: LiteLLM → externe API (OpenAI/Anthropic)

3. INSTALLATION
   curl -fsSL https://install.ai-os.app | bash --license AIOS-...
   → ~10 Minuten bis Console erreichbar

4. TENANT-BOOTSTRAP
   aios bootstrap --config customer-config.yaml
   → Tenant-Profil mit Kundendaten
   → Brand Voice + Style Guides hochladen
   → Seed-Wissen indexieren (Firmen-Dokumente, Handbücher)
   → LiteLLM-Budget setzen

5. ABNAHME-TEST
   → Console öffnen: Lagebild zeigt Tenant-Daten
   → Daily Briefing triggern
   → Test-Recherche durchführen
   → Alle lizensierte Pakete prüfen

6. ÜBERGABE
   → Zugangsdaten + Console-URL
   → Kurz-Schulung (1h): Console bedienen, Workflows starten
   → SLA-Dokument (bei Enterprise)
```

---

## Update-Strategie (kein Breaking Change für Kunden)

```
Versioning:
  Platform-Core:   Semantic Versioning (2.1.0)
  Pakete:          Eigene Versionen (research-agent 2.0.3)
  Datenbank:       Migrationen mit Alembic (rückwärtskompatibel)

Update-Rollout:
  1. NCE testet neue Version auf Demo-Tenant
  2. Canary: 1 Managed-Kunde als First-Mover (mit Zustimmung)
  3. Rollout alle Managed-Kunden
  4. Self-Hosted: aios update (Kunde führt selbst aus)

Rollback:
  aios rollback --version 2.0.1
  → Vorherige Docker Images reaktivieren
  → DB-Migrationen rückgängig (wenn vorhanden)
```

---

## Compute-Strategie pro Kunden-Tier

```
Starter (Managed, kleine VM):
  LiteLLM → Anthropic Claude Haiku (günstig, schnell)
  Kein GPU nötig
  ~€80–120/Monat Hetzner-VM
  Modell: sovereign_mode: false, external API

Professional (Managed, GEX44 oder größere VM):
  LiteLLM → Ollama lokal (qwen2.5:14b)
  Fallback: Claude Haiku
  ~€184/Monat GEX44
  Modell: sovereign_mode: true

Enterprise (On-Premise, Kunde-eigene Hardware):
  LiteLLM → lokales Ollama (eigene GPU)
  Kein externer API-Traffic
  Infrastruktur beim Kunden
  Modell: air_gap: true
```

---

## Was das für die ROADMAP.md bedeutet

Phase 0 (Fundament) bekommt einen zusätzlichen Schritt:

```
Phase 0.5 — Produkt-Struktur validieren
  □ aios CLI als Einstiegspunkt (install, uninstall, status, update, bootstrap)
  □ license.yaml Schema + Validator
  □ Package-Aktivierung via Docker Compose Profiles
  □ deploy/core.yml = Modus 0 (Platform ohne Agenten) lauffähig + testbar
  □ Demo-Tenant einrichten
  □ Installer-Skript Proof-of-Concept
```

**Leitfrage für jeden Architektur-Entscheid:**  
*«Kann dieser Entscheid für Kunde 2 repliziert werden, ohne Kunde 1 anzufassen?»*

---

## Referenz: Verzeichnisstruktur (produktions-ready)

```
ai-os-v2/
├── installer/
│   ├── install.sh          ← curl | bash Einstiegspunkt
│   ├── install.py          ← Installer-Logik (Python)
│   ├── license_validator.py
│   └── bootstrap.py
│
├── aios                    ← CLI-Einstiegspunkt
│   (symlink → installer/aios_cli.py)
│
├── deploy/
│   ├── core.yml            ← Modus 0: Platform ohne Agenten
│   ├── platform-agents.yml ← Modus 1: + Platform-Agenten
│   └── agents/
│       ├── research.yml
│       ├── blog.yml
│       ├── email.yml
│       └── ...
│
└── customers/
    ├── _template/          ← Vorlage für neue Kunden
    ├── nextchapter/        ← Entwicklungs-Tenant
    ├── demo/               ← Demo für Vertrieb
    └── {customer-id}/      ← Pro Kunde ein Ordner
```
