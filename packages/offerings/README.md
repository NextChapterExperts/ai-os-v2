# Publish path for Offerings → Delivery VM

Offerings are crafted on the NCE DEV-VM Company Brain, then published as packs:

```text
packages/offerings/<pack-id>/
  README.md
  seed/offering.json
  workflows/
  skills/
  LICENSE.features
```

## Activate delivery profile

```bash
export OFFERING_PACK=sap-apim-training   # or studenten-beratung
docker compose -f deploy/infra.yml -f deploy/monitoring.yml \
  -f deploy/core.yml -f deploy/profiles/delivery.yml \
  --profile core-docker --env-file .env up -d --build
```

No Cursor tools. No auto-sync of raw chats from DEV.
