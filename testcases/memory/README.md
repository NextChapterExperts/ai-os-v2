# Memory-Testcases

Automatisierte Regressionstests für alle Memory-Arten im AI-OS v2.

## Struktur

```
testcases/memory/
├── README.md           ← diese Datei
├── manifest.yaml       ← Index aller Cases (autogeneriert)
└── cases/
    ├── mem-episodic-001.yaml
    ├── mem-l1-001.yaml
    └── …
```

## Kategorien

| Präfix / Kategorie | Was getestet wird |
|--------------------|-------------------|
| `episodic` | `memory_ask` — temporale Fragen (gestern/heute/Woche) |
| `l1_qdrant` | Unified Search → Qdrant `content` |
| `graph` | Unified Search → Knowledge Graph |
| `episodic_search` | Unified Search → Letta/SQLite episodisch |
| `raw_files` | Unified Search → Qdrant `raw-files` |
| `mixed_search` | Query-Router — mehrere Schichten |
| `storage` / `capture` / `l1_api` | Orchestrator-APIs |
| `l1_curator` / `l2_curator` / `l3_curator` | Curator dry-run |
| `working` / `tactical` / `distill` | Run-Memory + P9-Destillation |
| `company_brain` | Graph/Policies/Claims |
| `edge_cases` | Leere Queries, Ping |

## Ausführen

Orchestrator muss laufen (`http://127.0.0.1:8091`).

```bash
# Cases neu generieren (nach Anpassung der Templates)
python3 scripts/generate-memory-testcases.py

# Alle Cases (~70+)
python3 scripts/run-memory-testcases.py

# Nur episodische Fragen
python3 scripts/run-memory-testcases.py --category episodic

# Einzelner Case
python3 scripts/run-memory-testcases.py --id mem-episodic-001

# JSON-Report für CI
python3 scripts/run-memory-testcases.py --json > /tmp/memory-test-report.json
```

## Wann laufen lassen

- Nach Änderungen an Memory-Gateway, Curators, Capture, Unified Search
- Vor Release / nach VM-Restore
- Optional in CI (Orchestrator + Infra müssen erreichbar sein)

## Case-Format (YAML)

```yaml
id: mem-episodic-001
name: Was haben wir gestern gemacht?
category: episodic
endpoint: dispatch          # dispatch | orchestrator
intent: memory_ask
params:
  question: "Was haben wir gestern gemacht?"
expect:
  http_status: 200
  result_kind: memory_ask
  min_answer_length: 3
tags: [temporal, memory_ask]
```
