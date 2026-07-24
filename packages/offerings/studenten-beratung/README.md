# Offering Pack — Studenten-Beratungsprojekt

**offering_id:** `off-studenten-beratung`

## Delivery VM

```bash
OFFERING_PACK=studenten-beratung \
  docker compose -f deploy/infra.yml -f deploy/monitoring.yml \
  -f deploy/core.yml -f deploy/profiles/delivery.yml --env-file .env up -d
```
