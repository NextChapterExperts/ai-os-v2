# Offering Pack — SAP API Management Training

**offering_id:** `off-sap-apim-training`  
**phase:** craft → publish

## Contents

- `seed/offering.json` — OrgOffering metadata
- `workflows/` — delivery workflows (stubs)
- `skills/` — versioned skills (empty until Skill-Loop)
- `LICENSE.features` — feature flags for delivery VM

## Delivery VM

```bash
OFFERING_PACK=sap-apim-training \
  docker compose -f deploy/infra.yml -f deploy/monitoring.yml \
  -f deploy/core.yml -f deploy/profiles/delivery.yml --env-file .env up -d
```
