# ADR 0001 — Trennung von Produkt-Code, Tenant-Seed und Rohdaten

**Status:** angenommen · **Datum:** 2026-07-24 · **Autor:** Peter / NCE
**Verwandt:** [11-PLATFORM-VM.md](../11-PLATFORM-VM.md) (P19, Isolationsmodell) ·
[06-PRODUKT-DEPLOYMENT.md](../06-PRODUKT-DEPLOYMENT.md) ·
[09-COMPANY-BRAIN.md](../09-COMPANY-BRAIN.md) ·
[12-LEITPRINZIPIEN.md](../12-LEITPRINZIPIEN.md) (P18, P19)

---

## Kontext

Beim Aufbau der Company-Brain-Seed-Struktur für den First-Party-Tenant
`nextchapter` stellte sich die Frage: Wo leben die **Rohdaten** eines
Projekts (Deliverables, Verträge, Code, Entwürfe, PDFs — bei Peter unter
`Projekte/active/<slug>/`) im Verhältnis zum AI-OS-Produkt-Repo
(`1100-AI-OS-V2`, Remote `github.com/NextChapterExperts/ai-os-v2`)?

Das ist keine kosmetische Frage, sobald ein zweiter Kunde dazukommt: Das
Produkt-Repo wird identisch auf **jede** Kunden-VM ausgerollt
(`aios update` / `git pull`). Läge Kundenmaterial im selben Baum, entstünde:

- ein Datenleck-Risiko (Repo-/Update-Zugriff = Zugriff auf Kundengeheimnisse),
- eine Vermischung von Produkt-Versionierung und Kundendaten beim Update,
- ein Verstoß gegen die bereits bestehende Leitentscheidung **P19**
  („eine Welt = eine VM = ein Company Brain", keine geteilte DB/kein
  geteiltes Repo zwischen Kunden).

## Entscheidung

Drei Ebenen werden strikt getrennt:

| Ebene | Inhalt | Ort | Versionierung |
|---|---|---|---|
| **1. Produkt-Code** | Orchestrator, Console, MCP-Gateway, Compose-Files, Skills — alles außer `customers/` | `1100-AI-OS-V2/` (Git-Repo) | ✅ geteiltes Repo, identisch für alle VMs |
| **2. Tenant-Seed/Config** | Kuratiertes Firmenwissen: Organisation, Offerings, Partner, Policies, Projektmap, Decisions, KnowledgeAsset-Index | `1100-AI-OS-V2/customers/<tenant>/` | ⚠️ liegt im Repo-*Baum*, ist aber **pro VM nur ein Ordner** und wird **nicht** committed (siehe unten) |
| **3. Rohe Projektarbeit** | Deliverables, Code, PDFs, Verträge, Steuerbelege, node_modules, … | außerhalb des Repos — bei Peter: `Projekte/active/<slug>/` (Sibling-Ordner von `1100-AI-OS-V2/`) | ❌ nie im Produkt-Repo, eigenes Backup/Datenverzeichnis pro VM |

Konkret umgesetzt:

- `.gitignore` im Produkt-Repo ignoriert `customers/*` vollständig, mit
  **einer** Ausnahme: `customers/_template/` bleibt versioniert (Vorlage für
  neue Kunden, siehe Referenzstruktur in
  [06-PRODUKT-DEPLOYMENT.md](../06-PRODUKT-DEPLOYMENT.md#referenz-verzeichnisstruktur-produktions-ready)).
- Jede VM (DEV wie PROD) legt ihren eigenen `customers/<tenant>/`-Ordner
  lokal an (Tenant-Bootstrap kopiert aus `_template/`) — er wird nie ins
  gemeinsame GitHub-Repo gepusht, auch nicht der NCE-eigene
  (`customers/nextchapter/`).
- Rohe Projektdateien (Tier 3) werden **nie** nach `customers/<tenant>/`
  kopiert. Nur kuratierte Auszüge (Front-Door-Frontmatter, ausgewählte
  KnowledgeAssets) fließen per Ingest in Tier 2.

## Konsequenzen

**Positiv**

- Ein Kunde kann angelegt werden, ohne Kunde 1 anzufassen (Leitfrage aus
  06-PRODUKT-DEPLOYMENT.md) — sein `customers/<id>/` existiert nur auf
  seiner eigenen VM.
- Produkt-Updates (`aios update` / `git pull`) berühren nie Kundendaten.
- Kein Repo-Zugriff (Support, Dritt-Entwickler, CI) legt automatisch
  Kundengeheimnisse offen.

**Zu beachten / Trade-offs**

- `customers/nextchapter/` (NCE First-Party) ist ab jetzt ebenfalls
  ungetrackt — kein Git-Verlauf für Peters eigenen Seed mehr in diesem
  Repo. Backup läuft separat (Dateisystem-Backup der VM bzw. der
  `Projekte/`-Tarball). Falls Versionierung des eigenen Seeds gewünscht
  ist: optional ein **separates, privates** Git-Repo nur für
  `customers/nextchapter/` einrichten (nicht Teil dieser Entscheidung).
- Rohe Projektdateien (Tier 3) brauchen ein eigenes Backup-/Sync-Konzept
  pro VM — sind nicht durch das Produkt-Repo abgedeckt.
- Der Tenant-Bootstrap-Mechanismus (`aios bootstrap --config …`,
  `_template/` → `customers/<id>/`) muss existieren, bevor ein zweiter
  echter Kunde onboarded wird (aktuell: Skeleton, siehe
  [13-IST-STAND.md](../13-IST-STAND.md)).

## Alternativen (verworfen)

- **Alles im selben Repo, geteilt über alle Kunden:** verworfen — verletzt
  P19 direkt, Kundendaten wären für jeden mit Repo-Zugriff sichtbar.
- **Kundendaten in separatem Repo pro Kunde, als Submodule eingebunden:**
  technisch möglich, aber unnötige Komplexität für den ersten Kunden;
  `.gitignore` + lokaler Ordner pro VM reicht, solange P19 (eigene VM pro
  Kunde) eingehalten wird. Kann bei Bedarf später nachgezogen werden.
