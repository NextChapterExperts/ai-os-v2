# Ingest-Agent (Phase 2 — Company-Brain-Seed)

Materialisiert die kuratierten Seed-Quellen unter
`customers/nextchapter/knowledge/seed/` (+ Front-Door-READMEs unter
`Projekte/active/*/README.md`) als typisierte `org:*`-DataProducts im
Knowledge Graph (`kg_nodes`/`kg_edges` in Postgres) — über den DP-Service
(`POST /v1/dataproduct/commit`), nie per Direktzugriff auf Postgres/Qdrant.
Spec: [docs/09-COMPANY-BRAIN.md](../../docs/09-COMPANY-BRAIN.md) ·
[docs/03-DATENPRODUKTE.md](../../docs/03-DATENPRODUKTE.md).

Damit ist dies der Unterschied zu `core/file_ingest_watcher/`
([ADR 0002](../../docs/adr/0002-file-ingest-watcher-und-rolle-von-cursor.md)):
Der File-Ingest-Watcher indexiert **rohe, ungeprüfte** Projektdateien
(`raw-files`, kein Graph). Der Ingest-Agent hier verarbeitet **kuratierte**
Company-Brain-Seed-Dokumente, schreibt Graph-Knoten + -Kanten + Audit
(Hash-Chain) und embedded veröffentlichte `OrgKnowledgeAsset`s zusätzlich in
die Qdrant-Collection `content`.

## Quellen -> DataProduct-Typ

| Quelle | DP-Typ |
|---|---|
| `00-organization.md` (Frontmatter) | `OrgOrganization` |
| `03-partners.md` (Fenced-YAML-Blöcke) | `OrgOrganization` |
| `02-people.md` | `OrgPerson` |
| `01-offerings.md` | `OrgOffering` |
| `04-policies.md` | `OrgPolicy` |
| `07-decisions.md` | `OrgDecision` |
| `08-knowledge-assets.md` (Markdown-Tabelle) | `OrgKnowledgeAsset` |
| `brain.json` | `OrgOffering` + `OrgEngagement` + `OrgOrganization` |
| `Projekte/active/*/README.md` (Frontmatter `id: eng:*`) | `OrgEngagement` |

`OrgMeeting`/`OrgClaim` sind im DP-Service vollständig implementiert
(Commit-Mapping, Edges), haben aber aktuell **keine Datenquelle** — es gibt
noch kein Calendar-MCP (`time-agent`) und keinen L3-Curator. Das ist
beabsichtigt (kein Massen-Ingest ohne echte Quelle).

## Betrieb

Läuft täglich per systemd-Timer (Seed ändert sich selten):

```bash
systemctl --user status aios-ingest-agent.timer
systemctl --user list-timers aios-ingest-agent.timer
journalctl --user -u aios-ingest-agent.service -f
```

Manuell:

```bash
cd core/ingest_agent
./run.sh                 # committen + L1-Ingest (idempotent, sicher mehrfach)
./run.sh --dry-run       # nur parsen + validieren, nichts schreiben
./run.sh --skip-l1       # Knoten committen, aber nicht in Qdrant content ingesten
```

## Verifikation (DoD laut 09-COMPANY-BRAIN.md §7)

```bash
curl -s "http://127.0.0.1:8091/v1/kg/stats?tenant_id=nextchapter" | python3 -m json.tool
# Erwartung: >= 10 Nodes mit Prefix org:, >= 5 Edges
```

Unified Search (`/search` in der Console) sollte danach `curatedCount > 0`
zeigen, nicht mehr nur Rohdateien.

## Bekannte Grenzen (MVP)

- Referenz-Auflösung (`about`/`documents`/`applies_to`) ist best-effort:
  Ziel-Refs, die zum Zeitpunkt des Commits noch nicht als Knoten existieren,
  werden übersprungen und im Response als `edges_skipped` gemeldet — kein
  Fehler, aber ggf. fehlende Kante bis zum nächsten Lauf.
- `brain.json` (`org-internal-nce`, `eng-sap-apim-kw-next`, …) und die
  Seed-Markdown-IDs (`org:nce`, `eng:redrays-btp`, …) verwenden **unterschiedliche
  ID-Konventionen** für inhaltlich verwandte Dinge — bewusst nicht
  automatisch zusammengeführt (keine geratenen Merges). Spätere Bereinigung:
  eine Konvention für beide Quellen.
- Nur Markdown als L1-Quelle (kein PDF/Office) — analog zu
  `file_ingest_watcher`, aber hier für kuratierte Assets.
