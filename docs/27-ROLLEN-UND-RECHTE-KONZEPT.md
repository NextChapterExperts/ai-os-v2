# Rollen- und Rechte-Konzept für isolierte Fachagenten & Multi-User Plattform

> **Dokument-ID:** `docs/27-ROLLEN-UND-RECHTE-KONZEPT.md`  
> **Status:** Verbindliche Spezifikation & Roadmap-Architektur  
> **Gültig für:** AI-OS v2 Plattform, Console Web UI, Orchestrator & Fachagenten (P1, P4, P5, P8, P18)

---

## 1. Executive Summary & Architektur-Fundament

Die Kernphilosophie von **VIRKI / AI-OS v2** basiert auf der strikten Entkopplung von Plattform, Gedächtnis und Agenten:
1. **DataProduct-In / DataProduct-Out:** Fachagenten verarbeiten ausschließlich typisierte Datenprodukte (Pydantic-Schemas) und liefern validierte Datenprodukte ab.
2. **MCP als einzige Konnektivitäts-Schicht (P5):** Fachagenten greifen auf externe Systeme (Dateisystem, E-Mail, Kalender, SAP, Google Workspace) ausschließlich über standardisierte MCP-Server zu.
3. **Isolierte Ausführung:** Jeder Agent läuft in einer kontrollierten Umgebung (Sandboxed Python-Prozess / Docker / LangGraph-State-Machine).

Aufgrund dieser Architektur ist das System **von Natur aus prädestiniert für ein feingranulares Rollen- und Rechte-System (RBAC / ABAC)**: Weder die Benutzeroberfläche noch das LLM entscheiden über Berechtigungen, sondern deterministischer Orchestrator-Code vor dem Dispatch.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BENUTZER-AUTHENTIFIZIERUNG                             │
│       Admin (Peter Schuler)         Werkstudent (Mini-Jobber)         Vertrieb / Partner│
└───────────────────────────┬───────────────────────┬────────────────────────┬───────────┘
                            │                       │                        │
                            ▼                       ▼                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR ACCESS & DISPATCH GATEWAY                          │
│   • Prüft: Darf `user_id` den Agenten `workflow_id` aufrufen?                          │
│   • Baut: `ContextBundle` mit rollenspezifischen Slices & Guardrails                   │
│   • Filtert: MCP-Server-Tools nach Benutzer-Berechtigung (MCP Scoping)                 │
└───────────────────────────┬────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Rechnungs-    │   │ Research- &   │   │ Angebots-     │
│ Agent         │   │ Ingest-Agent  │   │ Agent         │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ Nur Finance & │   │ Alle User &   │   │ Vertrieb &    │
│ Admin         │   │ Werkstudenten │   │ Admin         │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────────────────────────────────────────────┐
│                MCP PERMISSION PROXY (P5)              │
│    • Google Mail MCP (Nur zugewiesene Postfächer)     │
│    • File System MCP (Nur freigegebene Verzeichnisse) │
│    • Knowledge Graph Write Gateway (Commit-Rechte)    │
└───────────────────────────────────────────────────────┘
```

---

## 2. Aktueller Stand (Phase 4 Baseline)

Im aktuellen Entwicklungsstand existiert eine **Zwei-Rollen-Trennung**:

| Rolle | Benutzer-Beispiel | Freigeschaltete Bereiche | UI-Sichtbarkeit (`AppShell`) |
|---|---|---|---|
| **`admin`** | Administrator (`admin`) | **Vollzugriff:** Lagebild (`/`), Unternehmens-Identität (`/company`), Projekte (`/portfolio`), Agenten (`/agents`), Globale Suche (`/search`), Plattform & Speicher (`/platform`). | Vollständige Plattform-Navigation. |
| **`user`** | Peter Alexander (`peter`) | **Ausschließlich Fachagenten:** Darf Fachagenten starten, Inputs eingeben und Ergebnisse entgegennehmen. Kein Zugriff auf Stammdaten, Speichermengen, Health oder Graph-Administration. | Nur Menüpunkt **„Fachagenten“** sichtbar. Direkter Aufruf von Admin-URLs wird geblockt. |

---

## 3. Zukünftiges Multi-User & Agent-Berechtigungskonzept (Roadmap)

Im Zielzustand unterstützt VIRKI **einen Administrator** pro Tenant, aber **beliebig viele Benutzer (Mitarbeiter, Studenten, Partner)** mit individuellen Agenten-Freigaben.

### 3.1 Entitäten & Datenmodell

#### A. Benutzer-Entität (`auth_users`)
```json
{
  "user_id": "user:student-1",
  "username": "niklas.student",
  "name": "Niklas (Werkstudent)",
  "tenant_id": "nextchapter",
  "role": "user",
  "department": "research_and_data",
  "assigned_agents": [
    "research-agent",
    "document-ingest",
    "meeting-prep"
  ],
  "mcp_scopes": [
    "filesystem:read:customers/nextchapter/knowledge",
    "websearch:all"
  ]
}
```

#### B. Agenten-Berechtigungs-Manifest (`agent_manifest.yaml`)
Jeder Fachagent deklariert seine Mindestanforderungen:
```yaml
workflow_id: "handwerk-angebot"
name: "Handwerker Angebots-Agent"
version: "1.0.0"
security:
  required_role: "user"
  allowed_departments: ["sales", "executive", "admin"]
  required_mcp_servers:
    - name: "filesystem"
      access: "read_write"
      path_scope: "customers/{tenant_id}/offers"
  input_dataproducts:
    - "org:Offering"
    - "org:Organization"
  output_dataproducts:
    - "org:Claim"
    - "org:Engagement"
```

---

## 4. Beispiel-Szenario: Agentur Next Chapter Experts

Für das konkrete Unternehmens-Setup von Peter Schuler (1 Senior AI Consultant + Werkstudenten / Mini-Jobber):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PETER SCHULER (Inhaber, Senior AI Architect, Rolle: `admin`)             │
│    • Zugriff auf alle 6 Plattform-Bereiche & alle Fachagenten               │
│    • Kann Stundensätze, Steuerdaten und Mitarbeiter verwalten               │
│    • Kann neue Agenten deployen und MCP-Verbindungen autorisieren           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. WERKSTUDENT / MINI-JOBBER (Rolle: `user`, Dept: `research`)              │
│    • Zugriff NUR auf:                                                       │
│      - Research- & Web-Ingest-Agent                                         │
│      - Meeting-Protokoll- & Audio-Transkriptions-Agent                      │
│    • KEIN Zugriff auf:                                                      │
│      - Rechnungs- & Finance-Agenten                                         │
│      - Angebots-Kalkulation & Unternehmens-Stammdaten                       │
│      - Speicherverbrauch & Server-Konfiguration                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. VERTRIEBS-PARTNER / FREELANCER (Rolle: `user`, Dept: `sales`)            │
│    • Zugriff NUR auf:                                                       │
│      - Angebots-Agent (Handwerk & Enterprise)                               │
│      - CRM- & Kontakt-Agent                                                 │
│    • Sieht automatisch die freigegebenen Stundensätze aus dem SSOT-Profil   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Durchsetzung der Berechtigungen (Enforcement Points)

Berechtigungen werden an **drei unabhängigen Schranken** geprüft (Defense in Depth):

1. **Frontend-Ebene (Console Web UI):**
   - Filterung der sichtbaren Menüpunkte in `AppShell.tsx`.
   - Auf der Fachagenten-Startseite werden nur diejenigen Kacheln/Agenten angezeigt, die in `user.assigned_agents` enthalten sind.
   - Routen-Guard blockiert nicht autorisierte URL-Sprünge.

2. **Orchestrator Dispatch Gateway (`POST /v1/workflow/execute` & `/v1/dispatch`):**
   - Bevor ein LangGraph-Run oder Agent gestartet wird, validiert der Orchestrator:
     `assert current_user.has_agent_access(workflow_id)`.
   - Bei fehlender Berechtigung erfolgt ein sofortiger HTTP 403 Forbidden Fehlerabbruch ohne LLM-Kosten.

3. **MCP Proxy Gateway (P5):**
   - Der MCP-Client initialisiert für den Run nur diejenigen Tools, die im `mcp_scopes` des Benutzers freigegeben sind.
   - Ein Werkstudent kann über den MCP-Server keine E-Mails aus dem Inhaber-Postfach abrufen.

---

## 6. Zusammenfassung der Leitprinzipien-Konformität

- **P1 (Kontextsystem vor Agenten):** Rollen und Benutzer-Einschränkungen fließen in den `guardrail`-Slice des ContextBundles ein.
- **P4 (Determinismus in der Hülle):** Zugriffskontrolle ist 100% deterministischer Python-Code, kein Prompt-Engineering.
- **P5 (MCP als einzige Konnektivität):** Rechte steuern die Tool-Verfügbarkeit auf MCP-Ebene.
- **P18 (Company Brain):** Das Unternehmens-Profil und die Mitarbeiterdaten in `00-company-profile.yaml` bilden die kanonische Grundlage für alle Benutzer und Rechte.
