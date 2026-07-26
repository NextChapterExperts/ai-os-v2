# Compute-Modus & LLM-Routing — Testcases

Automatisierte Tests für Modus-Umschalten und Inference-Routing.

## Ausführen

Orchestrator + LiteLLM müssen laufen (`8091`, `4000`). OpenRouter-Key für Cloud-Modi.

```bash
# Alle Tests (Modus-API + LLM-Inference)
./scripts/run-compute-mode-testcases.py

# Nur Modus-API (schnell, ohne OpenRouter)
./scripts/run-compute-mode-testcases.py --skip-llm

# Einzelner Case
./scripts/run-compute-mode-testcases.py --id compute-llm-003

# JSON-Report
./scripts/run-compute-mode-testcases.py --json
```

## Kategorien

| Kategorie | Was getestet wird |
|---|---|
| `mode_api` | GET/POST `/v1/compute/mode` — Persistenz & Validierung |
| `llm_inference` | `/v1/chat/completions` — Routing nach Modus/Modell |
| `litellm_direct` | LiteLLM-Aliase direkt |

## Ablauf der LLM-Cases

1. Modus setzen (`POST /v1/compute/mode`)
2. Chat ohne Override → prüft aktiven Modus
3. Am Ende: Restore auf `sovereign` (außer `--no-restore`)
