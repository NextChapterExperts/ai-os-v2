# Company-Brain-Seed — Vorlage

**Tenant:** `__customer-id__`

Lesereihenfolge (gleiches Schema wie beim NCE-First-Party-Seed unter
`customers/nextchapter/knowledge/seed/`):

1. `00-organization.md` — Wer ist der Kunde
2. `01-offerings.md` — sein Portfolio / seine Leistungen (falls relevant für sein Brain)
3. `02-people.md` · `03-partners.md` · `04-policies.md`
4. `06-projektmap-index.md` — aktive Themen → Verweise auf sein eigenes
   Projektverzeichnis (außerhalb des Repos, siehe ADR 0001)
5. `07-decisions.md` · `08-knowledge-assets.md`

Jede Datei nach `customers/<customer-id>/knowledge/seed/` kopieren und
ausfüllen. Diese Dateien werden vom Ingest gelesen und landen im Knowledge
Graph (`org:*`-Entities) — siehe `docs/09-COMPANY-BRAIN.md`.

**Wichtig:** Front-Door-Frontmatter pro Projekt (`id`, `status`, `priority`,
`customer`, `summary`, `next_step`) lebt direkt im `README.md` des jeweiligen
Projektordners auf dem externen Datenverzeichnis der Kunden-VM — nicht als
Duplikat hier im Seed.
