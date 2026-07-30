# 16-VM-PACKAGING.md — Platform-VM Appliance Packaging & Onboarding

> **Zweck:** Anleitung und Spezifikation für das automatische Erstellen, Paketieren und Initialisieren von schlüsselfertigen AI-OS Platform-VMs für Kunden (P19 / [docs/11-PLATFORM-VM.md](11-PLATFORM-VM.md)).

---

## 1. Architektur & Isolationsmodell

AI-OS v2 folgt dem Prinzip **Eine VM · ein Company Brain · ein Mandant**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Kunden Platform-VM (Appliance)                 │
│                                                                        │
│  Ubuntu 26.04 LTS · Docker Compose · systemd                           │
│  /opt/ai-os/ (Code, Config, Memory DB, Ingest Inbox, State)           │
│                                                                        │
│  ┌───────────────────────┐  ┌───────────────────────┐                  │
│  │ aios-orchestrator.service │  │ aios-mcp-gateway.service │           │
│  │ (FastAPI Port :8091)   │  │ (Node.js Port :8097)  │                  │
│  └───────────────────────┘  └───────────────────────┘                  │
│  ┌──────────────────────────────────────────────────┐                  │
│  │ Next.js Console Web UI (Port :8092)              │                  │
│  └──────────────────────────────────────────────────┘                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Image Build Workflow (`appliance/image-build.sh`)

Das Skript `appliance/image-build.sh` baut das schlüsselfertige QCOW2-Image:

```bash
# Bildet das Produktions-Image:
./appliance/image-build.sh --output /pfad/zu/ai-os-appliance.qcow2

# Dry-Run Prüfung:
./appliance/image-build.sh --dry-run
```

### Schritte des Build-Prozesses:
1. Validiert cloud-init Konfiguration (`appliance/cloud-init.yaml`).
2. Paketiert AI-OS Core, SDK, Deploy & Scripts nach `/opt/ai-os`.
3. Richtet systemd-Units (`aios-orchestrator.service`, `aios-mcp-gateway.service`) ein.
4. Generiert QCOW2 VM-Disk.

---

## 3. Mandanten Onboarding & VM Initialisierung

Nach der Bereitstellung der VM beim Kunden wird die Instanz mit dem Onboarding-Skript initialisiert:

```bash
./appliance/init-tenant-vm.sh \
  --tenant malerbetrieb-schulze \
  --domain schulze.ai-os.local \
  --openrouter-key sk-or-v1-...
```

### Was das Skript ausführt:
1. Erstellt `.env` Konfiguration mit `TENANT_ID`, `DOMAIN` und API-Keys.
2. Initialisiert `tenant-info.json` und die SQLite Memory DB (`memory.db`).
3. Aktiviert den Sovereign Computemodus (Ollama LAN) mit optionalen Cloud-Fallbacks.

---

## 4. Verifizierung & Status-Check

```bash
# Service Health prüfen
systemctl status aios-orchestrator.service
systemctl status aios-mcp-gateway.service

# API Health Call
curl http://localhost:8091/health
```

---

*Dieses Dokument gehört zur offiziellen AI-OS v2 Dokumentationsserie.*
