# AI-OS v2 — Console: 3-Ebenen-Information-Architecture

**Stand:** Juli 2026 · **Verwandt:** [01-ARCHITEKTUR.md](01-ARCHITEKTUR.md)  
**Tech:** Next.js 15 · TypeScript · Tailwind CSS

---

## Das Problem mit v1

v1-Console versucht alles zu zeigen:
- Pipeline-Innenleben auf der Hauptseite
- Agent-Logs direkt sichtbar
- MCP-Server-Details prominent
- Config-Dumps in Hauptrouten
- Gleiche visuelle Gewichtung für täglich-relevante und selten-gebrauchte Infos

**Ergebnis:** Nutzer sieht bei jedem Öffnen Infrastruktur-Details, die er 19 von 20 Tagen nicht braucht.

---

## Das Designprinzip: 80/15/5-Regel

```
80 % der täglichen Nutzung → Ebene 1 — Lagebild
  Was ist heute passiert? Was brauche ich jetzt?
  → maximal simpel, kein Infrastruktur-Detail

15 % der Nutzung → Ebene 2 — Workflows
  Welche Workflows laufen? Was muss ich freigeben?
  → Task-orientiert, nicht Agent-orientiert

5 % der Nutzung → Ebene 3 — Plattform
  Agenten-Config, MCP-Server, Knowledge Graph, Skills
  → Nur wenn etwas kaputt ist oder neu konfiguriert wird
```

**Konsequenz:** Alles was heute in Ebene-1-Screens steht, aber eigentlich Ebene-3-Information ist — fliegt raus.

---

## Ebene 1 — Lagebild (`/`)

**Öffnungsfrequenz:** täglich  
**Ladezeit-Ziel:** < 1s  
**Inhalt:** Nur das, was morgens relevant ist.

```
┌──────────────────────────────────────────────────────────┐
│  AI-OS — Lagebild         Sonntag, 12. Juli 2026         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  BRIEFING                                                │
│  "3 E-Mails, 2 Termine heute. Fokusblock 14–16 Uhr."    │
│  → Vollständiges Briefing ansehen                        │
│                                                          │
│  OFFENE AUFGABEN           2 ausstehend                  │
│  ● Blog-Draft «KI-Trends» wartet auf Review             │
│  ● Steuer-Export 2025 wartet auf Freigabe               │
│                                                          │
│  AKTIVE WORKFLOWS           1 laufend                    │
│  ● Recherche: «LangGraph vs CrewAI» — 40% abgeschlossen  │
│                                                          │
│  LETZTE OUTPUTS             Heute                        │
│  → Daily Briefing — 07:03                               │
│  → Recherche: «MCP-Standards» — Gestern 19:41           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Was NICHT gezeigt wird:**
- Agent-Logs
- Pipeline-Status
- MCP-Server-Liste
- Alle Alerts (nur 1 wenn vorhanden)
- Rohdaten

```typescript
// src/app/page.tsx — nur diese 4 API-Calls
const briefing = await getBriefingSummary(tenant)      // 1 Satz + Link
const pendingReviews = await getPendingReviews(tenant)  // Zahl + Titel
const activeWorkflows = await getActiveWorkflows(tenant) // Zahl + Fortschritt
const recentOutputs = await getRecentOutputs(tenant, 3)  // Letzte 3 DPs
```

---

## Ebene 2 — Workflows (`/workflows`)

**Öffnungsfrequenz:** mehrmals wöchentlich  
**Inhalt:** Alle Workflows starten, Status verfolgen, Human-Review-Gate bedienen.

### Routen

```
/workflows                  Übersicht aller Workflows
/workflows/briefing         Daily Briefing — starten, History
/workflows/research         Recherche starten
/workflows/blog             Blog-Workflow — mit Review-Gate
/workflows/email            E-Mail / Steuer-Export
/workflows/[id]             Generischer Workflow-Status + Output
```

### Workflow-Übersicht (`/workflows`)

```
┌──────────────────────────────────────────────────────────┐
│  Workflows                              + Neuer Workflow  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  AUTOMATISCH (Scheduler)                                 │
│  ● Daily Briefing        täglich 07:00  ● aktiv         │
│  ● Memory-Curation       täglich 02:00  ● aktiv         │
│                                                          │
│  MANUELL                                                 │
│  [Recherche starten]  [Blog erstellen]  [E-Mail Export]  │
│                                                          │
│  LETZTE LÄUFE                                            │
│  Daily Briefing     heute 07:03   ✓ erfolgreich          │
│  Recherche          gestern 19:30  ✓ erfolgreich         │
│  Blog-Workflow      12.07 14:20   ⏳ wartet auf Review   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Blog-Workflow mit Human-Review-Gate (`/workflows/blog`)

```
┌──────────────────────────────────────────────────────────┐
│  Blog-Workflow                                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Schritt 1 ✓  Recherche abgeschlossen                   │
│  Schritt 2 ✓  Draft erstellt (850 Wörter)               │
│  Schritt 3 ✓  Compliance: freigegeben                   │
│  Schritt 4 ⏳  REVIEW ERFORDERLICH                      │
│  Schritt 5 …  Publish (ausstehend)                      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ «KI-Trends im Mittelstand: Was 2026 wirklich zählt»│  │
│  │                                                    │  │
│  │ [Volltext ansehen]                                 │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  [✓ Freigeben + Publizieren]    [✗ Ablehnen + Notiz]    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Wichtig:** Der Review-Screen zeigt NUR den Draft und die Freigabe-Buttons.  
**Nicht gezeigt:** Agent-Logs, MCP-Calls, Pipeline-Steps, Token-Counts.

---

## Ebene 3 — Plattform (`/platform`)

**Öffnungsfrequenz:** selten — nur bei Konfiguration oder Fehler  
**Inhalt:** Alle Infrastruktur-Details, Agenten-Config, KG, Skills, Monitor.

### Routen

```
/platform                   Übersicht — Services-Status kompakt
/platform/agents            Alle Agenten + Contract-Status
/platform/mcp               MCP-Gateway — Server, Caps, Audit-Log
/platform/kg                Knowledge Graph Visualisierung
/platform/skills            Skill-Bibliothek
/platform/monitor           Services + FinOps + Logs
/platform/tenants           Tenant-Management (Multi-Tenant)
```

### Platform-Übersicht (`/platform`)

```
┌──────────────────────────────────────────────────────────┐
│  Plattform                                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  SERVICES                                                │
│  ● Orchestrator    ✓   ● LiteLLM      ✓                 │
│  ● MCP-Gateway     ✓   ● Qdrant       ✓                 │
│  ● Skill-Service   ✓   ● Letta        ✓                 │
│  ● Scheduler       ✓   ● SearXNG      ✓                 │
│                                                          │
│  HEUTE                                                   │
│  12 Workflows gelaufen · 847 Tokens · 3 Skills verfeinert│
│                                                          │
│  SCHNELL-NAVIGATION                                      │
│  [Agenten]  [MCP-Server]  [Knowledge Graph]  [Skills]   │
│  [Monitor]  [Tenants]                                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Knowledge Graph (`/platform/kg`)

Interaktive Visualisierung des Knowledge Graph — inkl. **Company Brain**-Filter (`org:*`, P18):

- Default-Ansicht Tenant `nextchapter`: Offerings, Decisions (active), Policies
- Decision-Inbox: `org:Decision` mit Status `proposed` → Human-Gate → `active`
- Keine „Pretty Graph only“-Ansicht ohne Abnahmefragen (siehe [09-COMPANY-BRAIN.md](09-COMPANY-BRAIN.md) §8)

Interaktive Visualisierung des Knowledge Graph:
- Filter nach Entity-Typ (Dropdown)
- Filter nach Zeitraum (Datumsauswahl)
- Filter nach Tenant
- Klick auf Node → Detail-Panel mit allen Beziehungen
- Suche: «Welche Artikel beziehen sich auf Compliance?»

```typescript
// Technologie: vis-network oder cytoscape.js
// Daten: GET /v1/kg/graph?tenant=nextchapter&type=blog:BlogDraft&days=30
```

### Skill-Bibliothek (`/platform/skills`)

```
┌──────────────────────────────────────────────────────────┐
│  Skills                                    12 Skills     │
├──────────────────────────────────────────────────────────┤
│  Suche: [________________]                               │
│                                                          │
│  blog-research-to-draft  v3  ★ 89%  12 Nutzungen        │
│  «Blog-Artikel aus Research-Brief erstellen»             │
│                                                          │
│  daily-briefing-synthesis  v2  ★ 95%  47 Nutzungen      │
│  «Tages-Briefing aus E-Mails und Kalender erstellen»     │
│                                                          │
│  compliance-check-article  v1  ★ 78%  8 Nutzungen       │
│  «Blog-Artikel auf Compliance prüfen»                    │
│                                                          │
│  [Skill ansehen]  [Skill bearbeiten]  [Skill exportieren]│
└──────────────────────────────────────────────────────────┘
```

---

## Navigationsprinzip

```typescript
// src/lib/navigation.ts

export const navigation = [
  {
    label: "Lagebild",
    href: "/",
    level: 1,
    // Immer sichtbar, prominent
  },
  {
    label: "Workflows",
    href: "/workflows",
    level: 2,
    children: [
      { label: "Briefing", href: "/workflows/briefing" },
      { label: "Recherche", href: "/workflows/research" },
      { label: "Blog", href: "/workflows/blog" },
      { label: "E-Mail", href: "/workflows/email" },
    ],
  },
  {
    label: "Plattform",
    href: "/platform",
    level: 3,
    // Weniger prominent — z.B. kleinere Schrift, anderer Stil
    children: [
      { label: "Agenten", href: "/platform/agents" },
      { label: "MCP", href: "/platform/mcp" },
      { label: "Knowledge Graph", href: "/platform/kg" },
      { label: "Skills", href: "/platform/skills" },
      { label: "Monitor", href: "/platform/monitor" },
    ],
  },
]
```

**Navigation-Design:**
- Ebene 1 und 2: Hauptnavigation, volle Größe
- Ebene 3 (`/platform`): visuell abgesetzt — z.B. kleiner, weniger prominent
- Kein Badge/Alert auf Plattform-Links (Alerts nur auf Ebene 1 sichtbar)

---

## API-Design (BFF)

```typescript
// src/app/api/lagebild/route.ts
// Aggregiert 4 Calls zu einem Response für Ebene 1
export async function GET(req: Request) {
  const tenant = getTenant(req)
  const [briefing, reviews, workflows, outputs] = await Promise.all([
    orchestratorClient.getBriefingSummary(tenant),
    orchestratorClient.getPendingReviews(tenant),
    orchestratorClient.getActiveWorkflows(tenant),
    orchestratorClient.getRecentOutputs(tenant, 3),
  ])
  return Response.json({ briefing, reviews, workflows, outputs })
}
// → 1 API-Call statt 4 für die Hauptseite
```

---

## Was aus v1 nicht übernommen wird

| v1-Route | Grund für Entfernung |
|---------|---------------------|
| `/email` direkt in Hauptnav | → unter `/workflows/email` (Ebene 2) |
| `/werkstatt-sync` prominent | → unter `/platform/` oder CLI-only |
| `/assistants` als eigene Route | → in `/workflows` integriert |
| `/chat-capture` prominent | → in `/workflows` oder `/platform` |
| `/monitor` in Hauptnav | → `/platform/monitor` |
| Pipeline-Details in Workflow-View | → nur Status + Output, kein Innenleben |
| MCP-Call-Details im Workflow | → nur in `/platform/mcp` audit-log |
