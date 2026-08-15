# docs/31-CORE-PLATFORM-DISTRIBUTION-REPO.md — Autarkes Core Plattform Distributions-Projekt

> **Architektur-Spezifikation für die Trennung von R&D (v2) und Distribution (`1110-AI-OS-Core-Platform`)**  
> **Status:** Standard für Docker Appliance Releases & Kunden-Provisionierung

---

## 🎯 1. Das 2-Repository-Modell

```
┌────────────────────────────────────────────────────────┐
│             1100-AI-OS-V2 (R&D WORKSTATION)            │
├────────────────────────────────────────────────────────┤
│ • Master-Entwicklung mit Cursor & Antigravity          │
│ • Forschung an neuen Fachagenten & Prototypen          │
│ • Umfassende Testsuite (248+ automatisierte Tests)     │
│ • NextChapter Ur-Tenant Daten                          │
└───────────────────────────┬────────────────────────────┘
                            │
              ./scripts/export-core-appliance.sh
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│        1110-AI-OS-Core-Platform (DISTRIBUTION REPO)    │
├────────────────────────────────────────────────────────┤
│ • 100% autark, ohne Entwicklungs-Artefakte             │
│ • 5-Schichten Memory Modell (L1–L5)                    │
│ • Unternehmens-Identität (/company) & Suche (/search)  │
│ • Vollständige Kunden- & Architektur-Dokumentation     │
│ • Docker Multi-Stage Image & Compose Appliance         │
│ • Bereit für Google Cloud Run / Dedicated VMs          │
└────────────────────────────────────────────────────────┘
```

---

## 📂 2. Struktur des Distributions-Projekts

Das neue Projekt `/home/peter/Projekte/1110-AI-OS-Core-Platform` umfasst:

1. **`core/orchestrator/`:** Reiner Plattform-Orchestrator, Enterprise Profile Store, Context Resolution, Memory Storage Manager, GCP VM Engine.
2. **`core/console-web/`:** Nordisches Admin-Frontend (`/`, `/company`, `/platform`, `/platform/storage`, `/platform/vms`, `/search`).
3. **`docs/`:** Umfassende, hochpräzise Dokumentation aller Plattform-Prinzipien.
4. **`deploy/docker/`:** Multi-Stage Dockerfile und docker-compose.yml.
5. **`scripts/`:** Start- und Wartungs-Skripte für Admins.
