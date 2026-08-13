# VIRKI AI-OS v2 — Integration von Docker MCP Catalog/Gateway & Docker Sandboxes

> **Stand:** 2026-08-13 · **Status:** Konzeptionell freigabebereit (Warten auf Go)  
> **Bezug:** [12-LEITPRINZIPIEN.md](12-LEITPRINZIPIEN.md) (P5, P15, P19) · [ROADMAP.md](../ROADMAP.md) (Kap. 11 & 13)

---

## 🎯 1. Übersicht & Zielsetzung

Um die Entwicklung von **VIRKI AI-OS v2** zu beschleunigen und die Sicherheit bei der Tool-Ausführung auf Enterprise-Niveau zu heben, integriert VIRKI zwei Kern-Funktionen aus dem **Docker AI Ecosystem**:

1. **Option 1: Docker MCP Catalog & Gateway Integration (Prinzip P5)**  
   Nutzung von 300+ fertigen, verifizierten und containerisierten MCP-Servern (Postgres, GitHub, Slack, Google, Grafana etc.) über das Docker MCP Gateway, anstatt jeden MCP-Adapter manuell in Python zu schreiben.
2. **Option 2: Docker Sandboxes / MicroVMs für den PGE-Trinity Executor (Prinzip P15)**  
   Verwendung von ephemeren MicroVM-Sandboxes zur isolierten Ausführung von Code und risikoreichen Tools durch den Executor, um das Host-System vor Prompt-Injections, schädlichem Code oder Ressourcen-Overload zu schützen.

---

## 🔌 2. Option 1: Docker MCP Catalog & Gateway Integration (P5)

### 2.1 Architektur & Prinzip-Treue

VIRKIs Prinzip **P5 (MCP als einzige Konnektivität)** fordert:
* Jeder Tool-Aufruf läuft über `self.mcp`.
* Das Gateway erzwingt **Allowlist**, **Caps (Rate-Limits)** und **Audit-Logs (P17 Hash-Chain)**.

Durch die Docker-Integration bleibt VIRKIs Governance-Schicht als Oberboss erhalten, während Docker die Ausführungsschicht übernimmt:

```text
 Agent (Huginn)
       │
       ▼ (self.mcp.call)
┌─────────────────────────────────────────────────────────┐
│ VIRKI mcp-gateway (core/mcp_gateway/server.py)           │
│  • Tenant-Allowlist Check                               │
│  • PGE Gatekeeper Check (GREEN/YELLOW/RED)              │
│  • P17 Hash-Chain Audit Entry                           │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼ (Inter-Service / stdio)
┌─────────────────────────────────────────────────────────┐
│ Docker MCP Gateway (docker-mcp / Container Environment) │
│  • Managt Container Lifecycle & OAuth                    │
│  • Führt MCP-Server isoliert im Container aus            │
└────────────────────────────┬────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       [MCP GitHub]   [MCP Postgres]  [MCP Slack]
```

### 2.2 Vorteile
* **Reduktion des Entwicklungsaufwands um ~90 %:** Kein manuelles Schreiben von Python-Adaptern für Drittanbieter-APIs.
* **Isolierte Runtimes:** Jedes MCP-Tool bringt sein eigenes Umfeld (Node.js, Go, Python) im Container mit — null Abweichungen ("Dependency-Hell") auf dem Server.

---

## 🛡️ 3. Option 2: Docker Sandboxes (MicroVMs) für PGE Trinity Executor (P15)

### 3.1 PGE Trinity Erweiterung

Gemäß Prinzip **P15 (PGE Trinity)** gliedert sich die Arbeitsweise in:
1. **Planner (LLM - Huginn):** Erstellt den Arbeitsplan und schlägt Schritte / Skripte vor.
2. **Gatekeeper (Code):** Evaluierte Risk-Klasse (`GREEN`, `YELLOW`, `ORANGE`, `RED`).
3. **Executor (Code):** Führt den freigegebenen Schritt aus.

Bei Risikoklassen `YELLOW` und `ORANGE` (Code-Generierung, Shell-Skripte, unvertraute Datenverarbeitung) startet der Executor eine **ephemere Docker MicroVM Sandbox**:

```text
[ Planner schlägt Python-Skript vor ]
                 │
                 ▼
[ Gatekeeper erteilt Freigabe (YELLOW) ]
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ EPHEMERE DOCKER MICROVM SANDBOX                         │
│                                                         │
│ 1. Startet in < 0,2s komplett isoliert                  │
│ 2. Führt Skript ohne Zugriff auf Host-Dateien aus       │
│ 3. Gibt fertiges Ergebnis (z.B. Markdown/JSON) zurück  │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ SANDBOX WIRD VERNICHTET (0,0s Spuren am Host)           │
└─────────────────────────────────────────────────────────┘
                             │
                             ▼
[ Ergebnis wird im Company Brain (Muninn) gespeichert ]
```

### 3.2 Sicherheits-Gewinn für VIRKI
* **Schutz vor Prompt Injection:** Bösartige Befehle in gelesenen Dokumenten können niemals den Server oder das Host-Dateisystem beschädigen.
* **Zero-Leakage von Secrets:** Die Sandbox besitzt keine SSH-Keys, `.env`-Dateien oder Host-Anmeldedaten.
* **Leistungs-Schutz:** CPU-/RAM-Limits verhindern, dass fehlerhafte Skripte die Platform-VM lahmlegen.

---

## 📋 4. Roadmap-Integration & Meilensteine

Die Integration wird wie folgt in `ROADMAP.md` verankert:

* **Phase 1 (Core & MCP M1):** Anbindung von `docker-mcp` an `core/mcp_gateway/server.py` als optionaler Backend-Driver für Catalog-Server.
* **Phase 2 (Platform-Gate & Guardrails):** Integration der Docker MicroVM Sandbox in den PGE-Trinity Executor Hook.
* **Phase 3 (Contract & Abnahme):** Erweiterung der Contract-Tests `tests/contract/test_mcp_isolation.py` & `tests/contract/test_sandbox_executor.py`.

---

## 🛠️ 5. Nächster Schritt (Nach Freigabe / "Go")

Nach dem Go durch den User werden die folgenden Aufgaben in `task.md` abgearbeitet:
1. `core/mcp_gateway/docker_adapter.py` zur Ansteuerung von containerisierten MCP-Servern erstellen.
2. `core/orchestrator/sandbox_executor.py` zur Einbindung von Docker MicroVM Sandboxes für PGE Trinity erstellen.
3. Testfälle in `tests/test_mcp_docker.py` und `tests/test_sandbox_executor.py` schreiben und `./scripts/run-all-tests.sh` durchführen.
4. Git Commit + Update Changelog.
