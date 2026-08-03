# AGENTS.md — Verbindlicher Entwicklungs-Workflow für KI-Agenten

> **GILT FÜR ALLE KI-AGENTEN (Antigravity, Gemini, Cursor, Claude, etc.) UND MENSCHLICHE ENTWICKLER**  
> Jede Änderung in diesem Repository **MUSS** strikt in der unten angegebenen Reihenfolge ausgeführt werden.

---

## 📋 Der 6-Schritte-Arbeitsablauf (Strikte Reihenfolge)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. ROADMAP LESEN                                                        │
│    Vor jeglicher Arbeit ROADMAP.md & docs/12-LEITPRINZIPIEN.md lesen.  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. ROADMAP ABGLEICHEN / ANPASSEN                                        │
│    Falls geplante Änderung noch nicht in ROADMAP.md steht: Vorab         │
│    dort eintragen und spezifizieren.                                    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. CODE-ÄNDERUNG UMSETZEN                                              │
│    Code sauber gemäß den Leitprinzipien (P1–P19) implementieren.        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. TESTFÄLLE ERSTELLEN                                                  │
│    Neue Testfälle für die Änderung schreiben und im Verzeichnis tests/ │
│    ablegen.                                                             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. TESTSUITE AUSFÜHREN & VERIFIZIEREN                                   │
│    Master-Testskript ausführen: ./scripts/run-all-tests.sh              │
│    Prüfung: Muss zu 100% fehlerfrei durchlaufen (0 Failed).             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. ROADMAP · TAG · DOKU · GIT CHECK-IN                                  │
│    - ROADMAP abhaken + Release-Tag setzen (§24) + Fachagent-Doku.         │
│    - Code, Tests & Dokumente committen, taggen & pushen.                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailbeschreibung der Schritte

### Schritt 1: Roadmap lesen
- Vor Beginn jeder Aufgabe liest der Agent zuerst [ROADMAP.md](ROADMAP.md) und [docs/12-LEITPRINZIPIEN.md](docs/12-LEITPRINZIPIEN.md).
- Ziel: Den Kontext, den festgelegten Stack und bestehende Vorgaben vollständig verstehen.

### Schritt 2: Roadmap abgleichen & anpassen
- Der Agent prüft, ob die geforderte Aufgabe / Änderung bereits in `ROADMAP.md` enthalten ist.
- **Wenn nein:** Der Agent trägt das Vorhaben vorab in `ROADMAP.md` ein, damit die Roadmap immer die Single Source of Truth für alle Anforderungen bleibt.

### Schritt 3: Code ändern
- Der Agent setzt die Code-Änderungen im Projekt um.
- Keine Abweichungen vom Technologiestack oder den Leitprinzipien P1–P19.

### Schritt 4: Testfälle erstellen
- Für jede neue Logik oder jeden Bugfix erstellt der Agent entsprechende automatisierte Testfälle.
- Die Testdateien werden unter `tests/` abgelegt (z. B. `tests/test_*.py`).

### Schritt 5: Testsuite ausführen
- Der Agent führt das zentrale Testskript aus:
  ```bash
  ./scripts/run-all-tests.sh
  ```
- **Bedingung:** Der Schritt gilt erst als bestanden, wenn alle Tests grün sind (`0 Failed`).

### Schritt 6: Roadmap updaten, Release-Tag setzen & GitHub-Repository aktualisieren
- Der Agent aktualisiert den Bereich **Stand / Changelog** in [ROADMAP.md](ROADMAP.md) und hakt erledigte Punkte ab.
- **Release-Tag (Pflicht bei Meilenstein-Abschluss):** Format `roadmap/YYYY-MM-DD-<phase>-<slug>` — siehe [docs/22-RELEASE-TAGS.md](docs/22-RELEASE-TAGS.md) und ROADMAP §24. Tag im Release-Register eintragen und in den betroffenen Roadmap-Abschnitten referenzieren.
- Fachagent-/Feature-Doku in `docs/` ergänzen (detektivisch, nicht oberflächlich).
- Abschließend werden alle Änderungen committet, getaggt und zu GitHub gepusht:
  ```bash
  git add .
  git commit -m "..."
  git tag -a roadmap/YYYY-MM-DD-p4-slug -m "Roadmap §X.Y: Kurzbeschreibung"
  git push origin main --tags
  ```
