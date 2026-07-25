#!/usr/bin/env python3
"""Führt Memory-Testcases aus testcases/memory/cases/ gegen den Orchestrator aus.

Usage:
  ./scripts/run-memory-testcases.py
  ./scripts/run-memory-testcases.py --category episodic
  ./scripts/run-memory-testcases.py --id mem-episodic-001
  ./scripts/run-memory-testcases.py --fail-fast
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
CASES_DIR = REPO / "testcases" / "memory" / "cases"
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8091").rstrip("/")
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "nextchapter")


def _http(method: str, url: str, body: dict | None = None, timeout: float = 60) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw) if raw else {"detail": str(exc)}
        except json.JSONDecodeError:
            payload = {"detail": raw.decode("utf-8", errors="replace")}
        return exc.code, payload


def _load_cases(
    *,
    category: str | None = None,
    case_id: str | None = None,
    tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            c = yaml.safe_load(f)
        if category and c.get("category") != category:
            continue
        if case_id and c.get("id") != case_id:
            continue
        if tags:
            case_tags = set(c.get("tags") or [])
            if not case_tags.intersection(tags):
                continue
        cases.append(c)
    return cases


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    expect = case.get("expect") or {}
    endpoint = case.get("endpoint", "dispatch")
    method = case.get("method", "POST")
    t0 = time.perf_counter()

    if endpoint == "dispatch":
        body = {
            "intent": case["intent"],
            "tenant_id": DEFAULT_TENANT,
            "params": case.get("params") or {},
        }
        status, data = _http("POST", f"{ORCHESTRATOR_URL}/v1/dispatch", body)
        result = data.get("result") if isinstance(data, dict) else {}
    elif endpoint == "orchestrator":
        path = case.get("path", "")
        body = case.get("body")
        if method == "GET":
            status, data = _http("GET", f"{ORCHESTRATOR_URL}{path}")
        else:
            status, data = _http(method, f"{ORCHESTRATOR_URL}{path}", body)
        result = data
    else:
        return {"id": case["id"], "ok": False, "error": f"Unknown endpoint: {endpoint}"}

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    failures: list[str] = []

    exp_status = expect.get("http_status", 200)
    if status != exp_status:
        failures.append(f"HTTP {status} != {exp_status}")

    if expect.get("result_kind") and result.get("kind") != expect["result_kind"]:
        failures.append(f"kind {result.get('kind')!r} != {expect['result_kind']!r}")

    min_len = expect.get("min_answer_length")
    if min_len is not None:
        answer = str(result.get("answer") or "")
        if len(answer) < min_len:
            failures.append(f"answer length {len(answer)} < {min_len}")

    min_sources = expect.get("min_source_count")
    if min_sources is not None:
        sc = result.get("sourceCount", result.get("count", 0))
        if sc < min_sources:
            failures.append(f"sourceCount {sc} < {min_sources}")

    if expect.get("has_stacks") and not (isinstance(data, dict) and data.get("stacks")):
        failures.append("missing stacks in storage response")

    if expect.get("has_total_chunks") and (data or {}).get("total_chunks") is None:
        failures.append("missing total_chunks in capture stats")

    return {
        "id": case["id"],
        "name": case.get("name"),
        "category": case.get("category"),
        "ok": len(failures) == 0,
        "failures": failures,
        "elapsed_ms": elapsed_ms,
        "http_status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Memory-Testcase-Runner")
    parser.add_argument("--category", help="Nur diese Kategorie")
    parser.add_argument("--id", dest="case_id", help="Einzelner Case")
    parser.add_argument("--tag", action="append", dest="tags", help="Filter nach Tag")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--fast", action="store_true", help="Ohne LLM-lastige Kategorien (episodic, l1_qdrant, …)")
    parser.add_argument("--json", action="store_true", help="JSON-Report")
    args = parser.parse_args()

    if not CASES_DIR.is_dir():
        print(f"Keine Testcases in {CASES_DIR} — zuerst generate-memory-testcases.py ausführen", file=sys.stderr)
        return 2

    cases = _load_cases(category=args.category, case_id=args.case_id, tags=args.tags)
    if args.fast:
        slow = {"episodic", "l1_qdrant", "graph", "episodic_search", "raw_files", "mixed_search", "company_brain"}
        cases = [c for c in cases if c.get("category") not in slow]
    if not cases:
        print("Keine Testcases gefunden.", file=sys.stderr)
        return 2

    results = []
    failed = 0
    for case in cases:
        r = _run_case(case)
        results.append(r)
        if not r["ok"]:
            failed += 1
            if not args.json:
                print(f"FAIL {r['id']}: {r['failures']} ({r['elapsed_ms']}ms)")
            if args.fail_fast:
                break
        elif not args.json:
            print(f"OK   {r['id']} ({r['elapsed_ms']}ms)")

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "orchestrator": ORCHESTRATOR_URL,
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"\n{summary['passed']}/{summary['total']} passed, {summary['failed']} failed")

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
