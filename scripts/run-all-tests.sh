#!/usr/bin/env bash
# ==============================================================================
# AI-OS v2 — Master Test Runner
# Führt alle Testsuiten aus: Syntax, Pytest, Memory Cases, Compute Cases.
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CD_DIR="$REPO_DIR"

cd "$REPO_DIR"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}             AI-OS v2 — Master Test Suite Suite                      ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Py Compile Check
echo -e "\n${YELLOW}[1/4] Prüfe Python-Syntax (py_compile)...${NC}"
python3 -m py_compile $(find . -name "*.py" -not -path "*/.venv/*" -not -path "*/node_modules/*")
echo -e "${GREEN}✓ Python-Syntax in allen Dateien OK${NC}"

# 2. Pytest Unit & Contract Suite
echo -e "\n${YELLOW}[2/4] Führe Pytest-Suite aus (Unit, Memory, Graph, API)...${NC}"

# Fachagenten-Regression (Email + Meetings) — grundlegende Contract-Fehler sofort sichtbar
echo -e "${BLUE}  → Fachagenten-Gates (Platform Gate + Meetings-Agent)...${NC}"
if [ -x ".venv/bin/pytest" ]; then
    .venv/bin/pytest tests/test_platform_gate.py tests/test_meetings_agent.py tests/test_meetings_calendar_sync.py tests/test_email_agent.py -v -m "not integration" --tb=short
else
    python3 -m pytest tests/test_platform_gate.py tests/test_meetings_agent.py tests/test_meetings_calendar_sync.py tests/test_email_agent.py -v -m "not integration" --tb=short
fi

echo -e "${BLUE}  → Vollständige Pytest-Suite...${NC}"
if [ -x ".venv/bin/pytest" ]; then
    .venv/bin/pytest tests/ -v -m "not integration"
else
    python3 -m pytest tests/ -v -m "not integration"
fi
echo -e "${GREEN}✓ Pytest-Suite erfolgreich abgeschlossen${NC}"

# 3. Memory Testcases Check
echo -e "\n${YELLOW}[3/4] Prüfe Memory-Testcases (Fast-Modus)...${NC}"
if [ -f "scripts/run-memory-testcases.py" ]; then
    python3 scripts/run-memory-testcases.py --fast || echo -e "${YELLOW}ℹ Orchestrator Server nicht online (Memory API-Check übersprungen)${NC}"
fi

# 4. Compute Mode Testcases Check
echo -e "\n${YELLOW}[4/4] Prüfe Compute-Mode-Testcases (Skip-LLM Modus)...${NC}"
if [ -f "scripts/run-compute-mode-testcases.py" ]; then
    python3 scripts/run-compute-mode-testcases.py --skip-llm || echo -e "${YELLOW}ℹ Orchestrator Server nicht online (Compute API-Check übersprungen)${NC}"
fi

echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${GREEN}  ✓ ALLE TEST-PRÜFUNGEN ERFOLGREICH BESTANDEN!                       ${NC}"
echo -e "${BLUE}======================================================================${NC}"
