# AI-OS v2 — Lokales Modell: Capability-Test

**Datum:** 2026-07-12 (18:19 UTC+2)  
**Skript:** `1000-AI-OS/stack/scripts/tools/test_qwen_capabilities.py` (v1, wiederverwendet für Baseline)  
**Host:** `http://192.168.178.64:11434` (Ollama LAN)  
**Modell:** `qwen3.6-64k:latest`  
**SearXNG:** `http://127.0.0.1:8888`

## Zusammenfassung

| Kennzahl | Wert |
|----------|------|
| Tests gesamt | 8 |
| Bestanden | 6 |
| Fehlgeschlagen | 2 |
| Erfolgsquote | 75 % |
| Durchschnittliche Latenz | 3,11 s |

**Gesamtergebnis:** ⚠️ TEILBESTANDEN — lokales Modell für strukturierte AI-OS-Tasks grundsätzlich nutzbar; Tool-Calling und Fakten ohne Kontext noch offen.

## Ergebnisse

| ID | Status | Use Case | Dauer | Nachricht |
|----|--------|----------|-------|-----------|
| QWEN-01 | ✅ PASS | E-Mail: Suchfilter JSON | 2,19 s | `from='Michael Dorn'`, `date_from='2026-06-01'`, `task='summarize'` |
| QWEN-02 | ✅ PASS | Kalender: Tages-Briefing | 3,90 s | Termine 09:00 / 11:30 / 14:00 / 16:30 korrekt zusammengefasst |
| QWEN-03 | ✅ PASS | Agent-Job: Workflow-Routing | 1,66 s | `intent=daily_briefing`, `steps=['mail','calendar','synthesis']` |
| QWEN-04 | ❌ FAIL | Tool-Calling: Kalender + E-Mail | — | Exception im Testskript: `slice(None, 120, None)` — `arguments` war Dict, kein String |
| QWEN-05 | ✅ PASS | Übersetzung DE→EN | 0,97 s | Geschäftstext korrekt übersetzt |
| QWEN-06 | ✅ PASS | Datenprodukt: `email:MailSummary` | 2,89 s | `dp_id`, `count=3`, `storage_target=L2` korrekt |
| QWEN-07 | ❌ FAIL | Recherche ohne Web-Kontext | 8,96 s | Ubuntu 26.04 Fakten (23. April 2026, Resolute Raccoon) nicht zuverlässig aus Modellwissen |
| QWEN-08 | ✅ PASS | Recherche mit SearXNG-Kontext | 1,21 s | Datum + Codename korrekt aus Web-Kontext |

## Bewertung für v2

| Fähigkeit | Eignung | Hinweis |
|-----------|---------|---------|
| JSON-Extraktion (E-Mail, Routing, DP) | ✅ Gut | Deterministische Hülle + `temperature=0` ausreichend |
| Natürlichsprachige Zusammenfassung | ✅ Gut | Kalender-Briefing, Übersetzung stabil |
| Tool-Calling (Multi-Step) | ⚠️ Unklar | Testlauf abgebrochen — Skript-Bug; erneut prüfen |
| Fakten ohne Kontext | ❌ Schwach | Halluzinationsrisiko — Web-Kontext oder RAG Pflicht |
| Fakten mit SearXNG-Kontext | ✅ Gut | Recherche-Pipeline mit Kontext-Injection funktioniert |

## Bekannte Grenzen (aus Skript)

- Thinking-Tokens verlangsamen kurze JSON-Antworten
- Tool-Calling: beide Aktionen müssen zuverlässig getrennt werden
- Recherche ohne Kontext: Halluzinationsrisiko bei aktuellen Fakten

## Nächste Schritte (v2)

1. Testskript `test_qwen_capabilities.py` nach v2 portieren (`tests/capability/`)
2. QWEN-04: `arguments`-Handling im Skript fixen und Tool-Calling erneut messen
3. QWEN-07: als Negativtest behalten — bestätigt RAG/SearXNG-Pflicht in der Pipeline
4. Baseline bei Modellwechsel (`qwen2.5:32b` → `qwen3.6-64k`) wiederholen und hier dokumentieren

## Ausführung

```bash
python3 ../1000-AI-OS/stack/scripts/tools/test_qwen_capabilities.py
```
