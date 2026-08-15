# docs/30-CORE-PLATFORM-EXTRACTION-UND-DOCKER-CONTAINER.md — Core Plattform Extraktion & Docker Appliance

> **Architektur-Spezifikation für die autarke AI-OS v2 Core Appliance (Säule 1)**  
> **Status:** Standard für Docker Container Deployments (Google Cloud Run & VM Appliances)

---

## 🎯 1. Ziel & Prinzip der Source-Trennung

Die Plattform existiert als eigenständige, **neutrale Appliance**:

```
┌────────────────────────────────────────────────────────┐
│             AI-OS CORE PLATFORM APPLIANCE              │
├────────────────────────────────────────────────────────┤
│ • 5-Layer Memory Modell (SQLite, Graph, Vektoren)      │
│ • Unternehmens-Identität & Root-Profil (/company)      │
│ • Plattform- & Storage-Health Management (/platform)   │
│ • Universelle Semantische Suche (/search)              │
│ • RBAC Berechtigungsgate (Admin vs. User)              │
│                                                        │
│ ❌ KEINE vorinstallierten Fachagenten                   │
│ ❌ KEINE NextChapter-Demodaten oder Dummy-Projekte     │
│ ❌ KEINE Laufzeit-Compiler (Node-Gyp, npm build)       │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    [ Google Cloud Run ]        [ Lokaler Docker Stack ]
    (Serverless / Demo)         (DSGVO / Kunden-VM)
```

---

## 📦 2. Docker Multi-Stage Architektur

Ein einziges, vorkompiliertes Docker-Image enthält:
1. **Next.js Standalone Bundle:** Vorkompiliertes CSS, Icons und Routen (kein `npm install` auf Zielsystem).
2. **FastAPI Core Orchestrator:** Minimales Python-Image mit sauberer Schnittstelle.
3. **Persistentes Volume (`/app/data`):** Trennung von zustandslosem Code und wachsenden Unternehmensdaten.

---

## 🔒 3. Mandanten-Isolation & Clean Slate

Wird ein neuer Container gestartet:
- Erkennt die Plattform automatisch, ob `/app/data/00-company-profile.yaml` existiert.
- Ist die Datei leer, öffnet sich der **Setup-Assistent für den Kunden-Admin**.
- Keine Datenlecks aus der Entwicklungs-Umgebung NextChapter.
