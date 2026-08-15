# Plattform-Core vs. Mandanten-Fachagenten (Das 2-Säulen-Produktmodell)

> **Dokument-ID:** `docs/28-PLATFORM-VS-CUSTOM-AGENTS-MODELL.md`  
> **Status:** Verbindliche Architektur & Produkt-Spezifikation  
> **Gültig für:** AI-OS v2 Multi-Tenant Appliance, Orchestrator, Console Web UI & Tenant-Provisioning (P1, P4, P5, P10, P18, P19)

---

## 1. Executive Summary: Das Produktversprechen

VIRKI / AI-OS v2 wird als **lizenzierbare Multi-User AI-OS VM-Appliance** an Unternehmen vertrieben. Das Produkt teilt sich in zwei strikt voneinander getrennte Schichten:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               SÄULE 1: DIE LIZENZIERBARE PLATTFORM (AI-OS VM APPLIANCE)                │
│                         (Neutraler Kern für den Kunden-Admin)                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • 5-Schichten Memory-Modell (L1 Working, L2 Letta/Episodic, L3 KG, L4 Skills, L5 Audit)│
│ • Hybrid Graph-RAG Engine & LLM-freier Intent-Router (Unified Search)                  │
│ • Company Brain Root & Stammdatenverwaltung (00-company-profile.yaml)                 │
│ • Docker Compose Orchestration, FastEmbed, LiteLLM, Qdrant/SQLite                      │
│ • Admin Web-Konsole: Lagebild, Plattform-Health, Speicherverbrauch, Audit-Logs         │
│ • Multi-User & RBAC-Gateway (Admin richtet Mitarbeiter und Berechtigungen ein)         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ APIs / Slices / Tool-Registry
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│             SÄULE 2: DIE MANDANTENSPEZIFISCHEN FACHAGENTEN (CUSTOM SKUs)               │
│                        (Individuell für den Kunden entwickelt)                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ • Tenant "nextchapter":                                                                │
│   └── Rechnungs-Agent, Meeting/Calendar-Agent, Web-Ingest-Agent                        │
│                                                                                        │
│ • Tenant "kunde_kanzlei_schmidt":                                                      │
│   └── Schriftsatz-Analyse-Agent, Akten-Zusammenfassungs-Agent, Fristen-Wächter        │
│                                                                                        │
│ • Tenant "kunde_metallbau_meier":                                                      │
│   └── CAD-Zeichnungs-Ingest, Material-Kalkulations-Agent, Lieferanten-Anfrage-Agent    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Abgrenzung: Was gehört zur Plattformlizenz, was ist Customizing?

| Merkmal | Säule 1: Plattform-Kern (Core Appliance) | Säule 2: Mandanten-Fachagenten (Custom SKUs) |
|---|---|---|
| **Zielgruppe** | Kunden-Administrator (IT / Geschäftsführung) | Fachanwender (Sachbearbeiter, Berater, Vertrieb) |
| **Enthaltene Features** | • Vollständiges 5-Ebenen-Memory-System<br>• Knowledge Graph & Vektorsuche<br>• Company-Brain Root-Verwaltung<br>• Hardware-/Docker-Monitoring<br>• RBAC Multi-User Management<br>• MCP Proxy Gateway | • Fachliche LangGraph-Workflows<br>• Spezifische Prompt-Pipelines<br>• Kundenspezifische MCP-Adapter (z.B. Branchen-ERP)<br>• Fachliche DataProducts |
| **Auslieferungszustand** | Jungfräulich, neutral, keine vorinstallierten Branchenagenten | Maßgeschneidert oder aus NextChapter-Agenten-Katalog zugesteckt |
| **Abrechnungsmodell** | VM-Lizenz / Subscription (Hosting & Plattform) | Einrichtungsgebühr / Custom Development / SKU-Lizenz |

---

## 3. Mandanten-Isolation & Dateisystem-Struktur

Jeder Mandant (`tenant_id`) ist im Dateisystem und in allen Datenbanken strikt isoliert:

```
/opt/ai-os/ (oder Repo-Wurzel)
├── customers/
│   ├── nextchapter/                     <-- Mandant 1 (Next Chapter Experts)
│   │   ├── config.json                  <-- Mandanten-Konfiguration & Agenten-Aktivierung
│   │   └── knowledge/
│   │       ├── 00-company-profile.yaml  <-- Eigene Unternehmens-DNA (SSOT)
│   │       └── ...                      <-- Kundenwissen, Notizen, Seed-Dateien
│   │
│   ├── kunde_acme/                      <-- Mandant 2 (Neuer Lizenzkunde ACME Corp)
│   │   ├── config.json                  <-- Eigene Mitarbeiter & aktivierte Agenten
│   │   └── knowledge/
│   │       ├── 00-company-profile.yaml  <-- ACME Stammdaten, Stundensätze, Steuernummer
│   │       └── ...                      <-- ACME Dokumente & Fachwissen
│   │
│   └── ...
```

---

## 4. Tenant Provisioning Lifecycle (Day-1 Inbetriebnahme)

Wenn ein neuer Kunde die Plattform lizenziert, läuft das **Tenant-Provisioning** automatisiert ab (`POST /v1/platform/tenant/provision` bzw. `./scripts/provision-tenant.sh <tenant_id> <company_name>`):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TENANT PROVISIONING PIPELINE                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DATEISYSTEM-INITIALISIERUNG                                         │
│    Erstellt `customers/<tenant_id>/knowledge/`                         │
│    Erstellt `customers/<tenant_id>/config.json`                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. COMPANY BRAIN INITIALISIERUNG                                       │
│    Erstellt neutrales `00-company-profile.yaml` mit Kundenname         │
│    Legt kanonischen `org:EnterpriseProfile`-Knoten im Graph an         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ADMIN-BENUTZER INITIALISIERUNG                                      │
│    Erstellt initialen Administrator-Zugang für den Kunden              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. AGENTEN-FREISCHALTUNG (PLUG-IN)                                     │
│    Aktiviert die vom Kunden gebuchten Fachagenten                      │
│    (Default: Leer / Keine Beispieldaten)                               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Entflechtungs-Leitlinien für Entwickler

1. **Keine hardcodierten Tenant-Defaults:**  
   Im Platform-Core darf kein starrer Fallback auf `"nextchapter"` erzwungen werden. Fehlende Mandanten-Angaben werfen einen Validierungsfehler oder nutzen die konfigurierte Default-Instanz.
2. **Dynamische Agenten-Registry:**  
   Das Frontend lädt Agenten ausschließlich per API (`GET /v1/workflows/registry?tenant_id=XYZ`). Es gibt keine fest einprogrammierten Mock-Agenten (wie Handwerker-Angebote) in der UI.
3. **Plattform-Reinheit:**  
   Tests verifizieren, dass ein neu angelegter Mandant sofort funktionsfähig ist, ohne dass Daten oder Profile von anderen Mandanten einfließen.
