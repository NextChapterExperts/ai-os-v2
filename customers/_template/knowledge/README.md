# Knowledge — Tenant-Vorlage

Struktur für den Company-Brain-Seed eines neuen Kunden. Beim Tenant-Bootstrap
(`aios bootstrap --config customer-config.yaml`, siehe
`docs/06-PRODUKT-DEPLOYMENT.md` § Kunden-Onboarding-Flow) wird dieser Ordner
nach `customers/<customer-id>/knowledge/` kopiert und ausgefüllt.

- `seed/` — kuratiertes Firmenwissen (Organisation, Offerings, Partner,
  Policies, Projektmap, Decisions, KnowledgeAsset-Index). **Klein und
  strukturiert halten** — keine Rohdateien/Deliverables hier ablegen (siehe
  ADR 0001).
- `offerings/` — Offering-Packs, die der Kunde lizenziert hat.

Rohe Projektarbeit des Kunden (Deliverables, Verträge, Code, …) lebt
**außerhalb** dieses Repos in einem eigenen Datenverzeichnis auf der
Kunden-VM — Details: [`../../../docs/adr/0001-customer-data-isolation.md`](../../../docs/adr/0001-customer-data-isolation.md).
