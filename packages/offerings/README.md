# Offerings → Delivery-VM

Offerings werden auf der NCE-DEV-VM (Company Brain) gepflegt und als Packs veröffentlicht:

```text
packages/offerings/<pack-id>/
  README.md
  seed/offering.json
  workflows/          # noch Stub
  skills/             # noch Stub
  LICENSE.features
```

**Ist:** Packs `sap-apim-training` und `studenten-beratung` mit Seed; Orchestrator liest Tenant-Seed aus `customers/nextchapter/knowledge/seed/brain.json`.  
**Details:** [docs/13-IST-STAND.md](../../docs/13-IST-STAND.md)

## Delivery-Profil (Ziel-Pfad)

```bash
export OFFERING_PACK=sap-apim-training   # oder studenten-beratung
docker compose -f deploy/infra.yml -f deploy/monitoring.yml \
  -f deploy/core.yml -f deploy/profiles/delivery.yml \
  --profile core-docker --env-file .env up -d --build
```

Kein Cursor auf Delivery-VMs. Kein Auto-Sync von Roh-Chats aus DEV.
