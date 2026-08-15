# Release-Tags & Roadmap-Zuordnung

**Zweck:** Jeder größere Check-in (Feature-Abschluss, Fachagent, Plattform-Meilenstein) erhält einen **Git-Tag**, der in der [ROADMAP.md](../ROADMAP.md) referenziert wird. So lässt sich jederzeit rekonstruieren, welcher Code-Stand welchem Roadmap-Punkt entspricht.

---

## Tag-Format (verbindlich)

```
roadmap/YYYY-MM-DD-<phase>-<slug>
```

| Segment | Bedeutung | Beispiel |
|---------|-----------|----------|
| `YYYY-MM-DD` | Abschluss-Datum (UTC+2 DEV-VM) | `2026-08-03` |
| `<phase>` | Roadmap-Kapitel-Kürzel | `p4` = Phase 4, `p1b` = Phase 1b, `p2` = Phase 2 |
| `<slug>` | kebab-case, max. 4 Wörter | `email-invoices` |

**Beispiel:** `roadmap/2026-08-03-p4-email-invoices`

---

## Workflow bei jedem Release-Check-in

1. **Roadmap** — betroffene Punkte abhaken / Implementierungsstand-Tabelle aktualisieren  
2. **Doku** — Fachagent-/Feature-Doc in `docs/` (detektivisch, nicht oberflächlich)  
3. **Tests** — relevante Suite grün (`tests/test_*.py`)  
4. **Commit** — Conventional Commit mit Roadmap-Referenz im Body  
5. **Tag** setzen und in ROADMAP **Release-Register** eintragen  
6. **Push** — `git push origin main --tags` (wenn explizit gewünscht)

```bash
git tag -a roadmap/2026-08-03-p4-email-invoices -m "Phase 4: Gmail-Rechnungen Fachagent (§9.3)"
git push origin roadmap/2026-08-03-p4-email-invoices
```

---

## Release-Register

| Tag | Datum | Roadmap | Kurzbeschreibung | Commit |
|-----|-------|---------|------------------|--------|
| `roadmap/2026-08-15-p4-formal-memory-mapping-doc` | 2026-08-15 | §9, §12, Memory | 5-Schichten-Memory-Modell Referenz-Doku & Code-Mapping (docs/25) mit Paper-Verknüpfung | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-fluid-viewport-fit-wheel` | 2026-08-13 | §9, §10, UI | Fluide 100% Viewport-Einpassung des Rads (relativer 37.5% Radius) ohne Scrollbalken | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-giant-wheel-mega-search` | 2026-08-13 | §9, §10, UI | 520px Mega-Navigationsrad (Full Screen) & Riesiges 850px Webrecherche-Suchfenster | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-expansive-radial-wheel` | 2026-08-13 | §9, §10, UI | Großzügiges Raumausfüllendes Navigationsrad (Radius 380px, Pill Searchbar max-w-2xl) | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-pure-harmonious-radial-page` | 2026-08-13 | §9, §10, UI | Harmonisierte puristische Startseite (280px Radius), 100% frei von Unter-Boxen | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-radial-wheel-fullwidth` | 2026-08-13 | §9, §10, UI | Full-Width Screen Layout (440px Radius) & Hover-Erklärungen mit Klick-Absprung | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-radial-wheel-fullscreen` | 2026-08-13 | §9, §10, UI | Fullscreen Navigationsrad (Radius 370px) & Entfernung der unteren festen Websearch-Box | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-radial-navigation-dark-neon` | 2026-08-13 | §9, §10, UI | 1:1 High-End Dark Neon Refactoring des Navigationsrads gemäß Konzept-Mockup | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-console-port-8090` | 2026-08-13 | §9, §10, Port | Port-Umstellung der Console Web UI auf Port 8090 (http://localhost:8090) | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-role-based-login` | 2026-08-13 | §9, §10, Auth | Rollenbasiertes Login: peter/peter (Endanwender) vs. admin/admin (Admin-Layout) | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-radial-navigation-prototype` | 2026-08-13 | §9, §10, UI | Isolierter Prototyp /prototype mit Anwendermodus & Navigationsrad | *(siehe `git show`)* |
| `roadmap/2026-08-13-p4-tabler-icons-searxng-ux` | 2026-08-13 | §9, §10, UI | Systemweite Tabler-Icons, SearXNG UI Refactoring & IP-Schutz-Klarstellung | *(siehe `git show`)* |
| `roadmap/2026-08-13-p1-docker-mcp-sandbox` | 2026-08-13 | §13.3, P5, P15 | Docker MCP Catalog & Gateway Adapter, Docker MicroVM Sandboxes für PGE Trinity Executor | *(siehe `git show`)* |
| `roadmap/2026-08-08-p1-model-gateway-context-fix` | 2026-08-08 | §6, §11, P11/P12/P19 | Ollama 60s Timeout & qwen3.6:27b Model Fix, Console UI Kontext-Länge & Link Restoration, FTS5 Stop-Word Filter & CAP Search Verification | *(siehe `git show`)* |
| `roadmap/2026-08-03-p4-email-invoices` | 2026-08-03 | §9.3, §13 (mail MCP), §6b (Gemini-Drive teilw.), Gate 6–12 | Google-Plattformkern, email-agent, Console `/agents`, PDF/OCR-Extraktion, Backfill-Skript | *(siehe `git show`)* |


---

## Tag ↔ Roadmap nachschlagen

```bash
# Welcher Tag gehört zu welchem Commit?
git tag -l 'roadmap/*'

# Was war in einem Tag enthalten?
git show roadmap/2026-08-03-p4-email-invoices --stat

# Roadmap-Stand zum Tag lesen
git show roadmap/2026-08-03-p4-email-invoices:ROADMAP.md | head -20
```

---

## Regeln

- **Ein Tag pro abgeschlossenem Roadmap-Meilenstein** — keine Tags für WIP oder reine Docs-Fixes ohne Meilenstein  
- Tag-Name **muss** im ROADMAP Release-Register stehen  
- Breaking Changes: Zusatz `-breaking` im Slug oder neues Major-Segment vermerken  
- Tags sind **annotated** (`-a`) mit Message = Roadmap-Abschnitt + 1-Zeiler  

Siehe auch [AGENTS.md](../AGENTS.md) Schritt 6 (Roadmap + Tag + Check-in).
