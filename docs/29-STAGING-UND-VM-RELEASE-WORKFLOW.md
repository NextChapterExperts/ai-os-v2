# docs/29-STAGING-UND-VM-RELEASE-WORKFLOW.md — 3-Stufen Entwicklungs- & VM-Release-Workflow

> **Architektur- und Betriebsdokumentation für die AI-OS v2 Multi-Tenant Appliance**  
> **Status:** Verbindlicher Standard für NextChapter R&D und Kunden-VM Deployments

---

## 🎯 1. Das Kernprinzip

```
┌───────────────────────────────┐
│   1. NEXTCHAPTER EXPERTS      │  • Ur-Entwicklungs-Tenant & Forschungs-Labor
│      (Lokale Workstation)     │  • Erstellung neuer Agenten, Prototypen, Memory-Tests
└───────────────┬───────────────┘
                │
                │ Release-Tagging (z.B. roadmap/YYYY-MM-DD-p4-...)
                ▼
┌───────────────────────────────┐
│   2. GCP STAGING TEST-VM      │  • Identische, isolierte Ubuntu-VM in Frankfurt
│      (aios-staging-test)      │  • Verifikation von Zero-Touch Setup, Port 8090, Clean State
│                               │  • Prüfung der Plattform-Updatefähigkeit (Migrationen)
└───────────────┬───────────────┘
                │
                │ Abnahme & Go (0 Fehler, saubere UI & neutrale Identität)
                ▼
┌───────────────────────────────┐
│   3. KUNDEN-PRODUKTION        │  • Dedizierte, DSGVO-konforme Mandanten-VM
│      (aios-<tenant_id>)       │  • 100% autark: Eigene IP, eigenes Company-Profil,
│                               │    eigene Custom SKUs, keine fremden Daten
└───────────────────────────────┘
```

---

## 🔄 2. Der Update- und Lifecycle-Mechanismus

### A. Warum kein manuelles VM-Patching?
Eine Kunden-VM ist eine **declarative Infrastructure-as-Code (IaC) Appliance**:
- Alle persistenten Kundendaten (Firmendaten, Mitarbeiter, Wissensgraph, Vektor-Chunks) liegen geschützt im Daten-Layer (`customers/<tenant_id>/`).
- Die Engine und das Web-Frontend sind reine Software-Layer.
- Schlägt ein Staging-Test fehl, wird die Test-VM **kostenlos gelöscht** und nach Behebung des Codes in NextChapter neu hochgezogen.

### B. Update-Prozess für bestehende Kunden-Appliances:
1. **Core-Update bereitstellen:** Der Admin der Kunden-VM erhält in der Konsole den Hinweis: *„AI-OS Core v2.x verfügbar“*.
2. **One-Click Update:** Der Orchestrator zieht das getaggte Release-Paket, kompiliert das Frontend neu und startet die Systemd-Dienste neu.
3. **Rollback-Sicherheit:** Vor jedem Update wird ein automatischer Snapshot des lokalen SQLite/Graph-Speichers angelegt.

---

## 🛑 3. Kostenkontrolle & Pausieren (0 € Rechenkosten)

| Zustand | Google Compute Engine Kosten | Daten & IP Status |
|---|---|---|
| **RUNNING** | ca. 0,14 € / Stunde (e2-standard-4) | Voll erreichbar unter `http://<IP>:8090` |
| **TERMINATED (Pausiert)** | **0,00 €** Rechenkosten (nur minimale Disk-Kosten ~0,04 € / Monat) | Zustand eingefroren, kann sofort wieder gestartet werden |
| **DELETED (Gelöscht)** | **0,00 €** (Keinerlei Kosten) | Vollständig entfernt |

---

## 📋 4. Staging-Prüfmatrix vor Kunden-Rollout

Vor Freigabe an einen echten Kunden muss die Test-VM folgende Kriterien erfüllen:
- [x] **Zero-Touch Provisioning:** VM startet ohne manuelle SSH-Befehle komplett durch.
- [x] **Firewall & Security:** Externe Ports 8090 (Console Web) und 8091 (Orchestrator) sind per GCP Firewall geschützt.
- [x] **Clean-Slate Compliance:** Keine NextChapter-Projekte, keine Standard-Agenten vorinstalliert.
- [x] **Nordic/Sovereign UI:** Pixelgenaue, gestochen scharfe Web-Oberfläche mit 100% Funktionsfähigkeit.
