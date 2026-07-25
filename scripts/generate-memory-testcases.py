#!/usr/bin/env python3
"""Generiert Memory-Testcases unter testcases/memory/cases/."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CASES_DIR = REPO / "testcases" / "memory" / "cases"


def _case(
    case_id: str,
    name: str,
    category: str,
    endpoint: str,
    *,
    method: str = "POST",
    intent: str | None = None,
    path: str | None = None,
    params: dict | None = None,
    body: dict | None = None,
    expect: dict | None = None,
    tags: list[str] | None = None,
) -> dict:
    c: dict = {
        "id": case_id,
        "name": name,
        "category": category,
        "endpoint": endpoint,
        "method": method,
    }
    if intent:
        c["intent"] = intent
    if path:
        c["path"] = path
    if params:
        c["params"] = params
    if body:
        c["body"] = body
    if expect:
        c["expect"] = expect
    if tags:
        c["tags"] = tags
    return c


def build_cases() -> list[dict]:
    cases: list[dict] = []

    temporal_questions = [
        ("Was haben wir gestern gemacht?", "gestern-allgemein"),
        ("Was haben wir gestern besprochen?", "gestern-besprochen"),
        ("Was war gestern das Hauptthema?", "gestern-hauptthema"),
        ("Was haben wir heute gemacht?", "heute-allgemein"),
        ("Was haben wir diese Woche gemacht?", "woche-allgemein"),
        ("Was haben wir letzte Woche gemacht?", "letzte-woche"),
        ("Gibt es etwas von gestern zu Memory oder Letta?", "gestern-memory"),
        ("Was haben wir gestern an AI-OS implementiert?", "gestern-aios"),
        ("Welche Entscheidungen gab es gestern?", "gestern-entscheidungen"),
        ("Was haben wir gestern am Company Brain gemacht?", "gestern-brain"),
        ("Was lief gestern mit Cursor Capture?", "gestern-cursor"),
        ("Was haben wir gestern mit Antigravity gemacht?", "gestern-antigravity"),
        ("Zusammenfassung der Aktivitäten von gestern", "gestern-zusammenfassung"),
        ("Was war gestern der Fortschritt?", "gestern-fortschritt"),
        ("Erinnerst du dich an gestern?", "gestern-erinnerung"),
    ]
    for i, (q, slug) in enumerate(temporal_questions, 1):
        cases.append(
            _case(
                f"mem-episodic-{i:03d}",
                q,
                "episodic",
                "dispatch",
                intent="memory_ask",
                params={"question": q},
                expect={
                    "http_status": 200,
                    "result_kind": "ask",
                    "min_answer_length": 3,
                },
                tags=["temporal", "memory_ask", "sqlite", "letta"],
            )
        )

    search_l1 = [
        ("Company Brain Architektur", "brain-arch"),
        ("AI-OS Roadmap Memory", "roadmap-memory"),
        ("SAP APIM Training Angebot", "sap-apim"),
        ("OrgOffering consulting", "offering-consulting"),
        ("Knowledge Asset published", "ka-published"),
        ("NCE Organization Policies", "org-policies"),
        ("Engagement Front-Door README", "engagement-readme"),
        ("DataProduct commit Regeln", "dp-commit"),
    ]
    for i, (q, slug) in enumerate(search_l1, 1):
        cases.append(
            _case(
                f"mem-l1-{i:03d}",
                f"L1 Qdrant: {q}",
                "l1_qdrant",
                "dispatch",
                intent="unified_search",
                params={"query": q, "limit": 8},
                expect={
                    "http_status": 200,
                    "result_kind": "search",
                    "min_source_count": 0,
                },
                tags=["l1", "qdrant", "content"],
            )
        )

    search_graph = [
        "Welche Offerings gibt es?",
        "Decision consulting Governance",
        "OrgPerson Peter",
        "OrgPolicy Datenschutz",
        "Engagement active Projekte",
        "Knowledge Graph org nodes",
    ]
    for i, q in enumerate(search_graph, 1):
        cases.append(
            _case(
                f"mem-graph-{i:03d}",
                f"Graph: {q}",
                "graph",
                "dispatch",
                intent="unified_search",
                params={"query": q, "limit": 6},
                expect={"http_status": 200, "result_kind": "search"},
                tags=["graph", "kg"],
            )
        )

    search_episodic = [
        "Worüber haben wir letzte Woche gesprochen?",
        "Episoden Memory Gateway",
        "Letta Archival Chat",
        "Cursor Capture Transkript",
        "Tagesdigest Letta",
        "Antigravity Session Brain",
        "Gemini Chat Import",
        "Episodisches Gedächtnis AI-OS",
    ]
    for i, q in enumerate(search_episodic, 1):
        cases.append(
            _case(
                f"mem-letta-{i:03d}",
                f"Episodisch: {q}",
                "episodic_search",
                "dispatch",
                intent="unified_search",
                params={"query": q, "limit": 10},
                expect={"http_status": 200, "result_kind": "search"},
                tags=["letta", "episodic", "search"],
            )
        )

    search_raw = [
        "README redrays BTP",
        "package.json dependencies",
        "typescript config tsconfig",
        "docker compose infra",
        "pytest test memory",
    ]
    for i, q in enumerate(search_raw, 1):
        cases.append(
            _case(
                f"mem-raw-{i:03d}",
                f"Raw-files: {q}",
                "raw_files",
                "dispatch",
                intent="unified_search",
                params={"query": q, "limit": 5},
                expect={"http_status": 200, "result_kind": "search"},
                tags=["raw-files", "file-ingest"],
            )
        )

    search_mixed = [
        "Was wissen wir über AI-OS Memory und Offerings?",
        "Company Brain und gestern besprochen",
        "Roadmap Phase 2 Platform Gate",
        "Unified Search Graph Qdrant Letta",
        "Ingest Agent Qdrant content",
        "Memory Flywheel L1 L2 L3",
    ]
    for i, q in enumerate(search_mixed, 1):
        cases.append(
            _case(
                f"mem-mixed-{i:03d}",
                f"Mixed: {q}",
                "mixed_search",
                "dispatch",
                intent="unified_search",
                params={"query": q, "limit": 12},
                expect={"http_status": 200, "result_kind": "search"},
                tags=["mixed", "router"],
            )
        )

    for i, q in enumerate(
        [
            "ping health check",
            "memory ask empty",
            "search ohne query",
        ],
        1,
    ):
        intent = "ping" if i == 1 else "memory_ask" if i == 2 else "unified_search"
        params: dict = {}
        if intent == "memory_ask":
            params = {"question": ""}
        elif intent == "unified_search":
            params = {"query": ""}
        cases.append(
            _case(
                f"mem-edge-{i:03d}",
                f"Edge: {q}",
                "edge_cases",
                "dispatch",
                intent=intent,
                params=params,
                expect={"http_status": 200},
                tags=["edge"],
            )
        )

    api_cases = [
        ("mem-api-storage", "Storage stats", "storage", "GET", "/v1/memory/storage", None, {"http_status": 200, "has_stacks": True}),
        ("mem-api-l1-stats", "L1 stats", "l1_api", "GET", "/v1/memory/l1/stats", None, {"http_status": 200}),
        ("mem-api-capture", "Capture stats", "capture", "GET", "/v1/capture/stats", None, {"http_status": 200, "has_total_chunks": True}),
        ("mem-api-search", "Direct search API", "search_api", "POST", "/v1/search", {"query": "Memory Gateway", "tenant_id": "nextchapter", "limit": 5}, {"http_status": 200}),
        ("mem-api-rebuild-fts", "Rebuild FTS", "sqlite", "POST", "/v1/memory/rebuild-fts", None, {"http_status": 200}),
        ("mem-api-sync-letta-dry", "Letta sync dry-run", "letta", "POST", "/v1/memory/sync-letta", {"tenant_id": "nextchapter", "dry_run": True, "limit": 5}, {"http_status": 200}),
    ]
    for case_id, name, cat, method, path, body, expect in api_cases:
        cases.append(
            _case(
                case_id,
                name,
                cat,
                "orchestrator",
                method=method,
                path=path,
                body=body or {},
                expect=expect,
                tags=["api"],
            )
        )

    curator_items: list[tuple] = [
        ("mem-curator-l1", "L1 curate dry-run stats", "l1_curator", "POST", "/v1/memory/curate/l1", {"dry_run": True, "modes": ["stats"]}),
        ("mem-curator-l1-dedup", "L1 exact dedup dry", "l1_curator", "POST", "/v1/memory/curate/l1", {"dry_run": True, "modes": ["exact_dedup"]}),
        ("mem-curator-l2", "L2 curate dry-run", "l2_curator", "POST", "/v1/memory/curate/l2", {"tenant_id": "nextchapter", "dry_run": True}),
        ("mem-curator-l3", "L3 curate dry-run", "l3_curator", "POST", "/v1/memory/curate/l3", {"tenant_id": "nextchapter", "dry_run": True}),
        ("mem-curator-l3-pending", "L3 pending claims", "l3_curator", "GET", "/v1/memory/curate/l3/pending", {}),
        ("mem-curator-l1-rolling", "L1 rolling dry", "l1_curator", "POST", "/v1/memory/curate/l1", {"dry_run": True, "modes": ["rolling"]}),
    ]
    for case_id, name, cat, method, path, body in curator_items:
        cases.append(
            _case(
                case_id,
                name,
                cat,
                "orchestrator",
                method=method,
                path=path,
                body=body,
                expect={"http_status": 200},
                tags=["curator", "dry_run"],
            )
        )

    working_cases = [
        ("mem-working-note", "Working note + dispatch", "working", "dispatch", "memory_ask", {"question": "Kurzer Working-Memory Test", "run_id": "testcase-working-001"}),
        ("mem-tactical-wf", "Tactical workflow step", "tactical", "dispatch", "ping", {"workflow_run_id": "testcase-wf-001", "step": 1, "step_label": "probe"}),
        ("mem-distill-empty", "Empty run distill audit", "distill", "dispatch", "ping", {"run_id": "testcase-empty-001"}),
        ("mem-dispatch-session", "Dispatch with session_id", "working", "dispatch", "memory_ask", {"question": "Session test", "session_id": "testcase-session-001"}),
    ]
    for case_id, name, cat, ep, intent, params in working_cases:
        cases.append(
            _case(
                case_id,
                name,
                cat,
                ep,
                intent=intent,
                params=params,
                expect={"http_status": 200},
                tags=["working", "tactical", "p9"],
            )
        )

    policy_questions = [
        "Welche Policy gilt für PII?",
        "Decision org:Decision consulting",
        "Claim Human Gate supports_refs",
        "Leitprinzip P9 Destillation",
        "Company Brain SSOT Regel",
    ]
    for i, q in enumerate(policy_questions, 1):
        cases.append(
            _case(
                f"mem-policy-{i:03d}",
                f"Policy/Brain: {q}",
                "company_brain",
                "dispatch",
                intent="unified_search",
                params={"query": q, "limit": 8},
                expect={"http_status": 200, "result_kind": "search"},
                tags=["graph", "policy", "p18"],
            )
        )

    return cases


def main() -> None:
    cases = build_cases()
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    for old in CASES_DIR.glob("*.yaml"):
        old.unlink()
    for c in cases:
        path = CASES_DIR / f"{c['id']}.yaml"
        path.write_text(yaml.dump(c, allow_unicode=True, sort_keys=False), encoding="utf-8")
    manifest = {"version": 1, "count": len(cases), "cases": [c["id"] for c in cases]}
    (REPO / "testcases" / "memory" / "manifest.yaml").write_text(
        yaml.dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Generated {len(cases)} testcases in {CASES_DIR}")


if __name__ == "__main__":
    main()
