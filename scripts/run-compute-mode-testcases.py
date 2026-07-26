#!/usr/bin/env python3
"""Testet Compute-Modus-Umschalten und LLM-Routing über Orchestrator + LiteLLM.

Usage:
  ./scripts/run-compute-mode-testcases.py
  ./scripts/run-compute-mode-testcases.py --id compute-llm-003
  ./scripts/run-compute-mode-testcases.py --json
  ./scripts/run-compute-mode-testcases.py --skip-llm   # nur Modus-API, ohne Inference
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
CASES_DIR = REPO / "testcases" / "compute" / "cases"
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8091").rstrip("/")
LITELLM_URL = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000").rstrip("/")
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "nextchapter")
RESTORE_MODE = os.environ.get("COMPUTE_TEST_RESTORE_MODE", "sovereign")


def _http(
    method: str,
    url: str,
    body: dict | None = None,
    timeout: float = 120,
) -> tuple[int, Any]:
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


def _load_cases(*, case_id: str | None = None, skip_llm: bool = False) -> list[dict[str, Any]]:
    order = {"mode_api": 0, "llm_inference": 1, "litellm_direct": 2}
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            case = yaml.safe_load(f)
        if case_id and case.get("id") != case_id:
            continue
        if skip_llm and case.get("category") in {"llm_inference", "litellm_direct"}:
            continue
        cases.append(case)
    cases.sort(key=lambda c: (order.get(c.get("category", ""), 9), c.get("id", "")))
    return cases


def _check_expect(data: Any, expect: dict[str, Any], failures: list[str], prefix: str = "") -> None:
    if not isinstance(data, dict):
        failures.append(f"{prefix}response is not an object")
        return

    for key, expected in expect.items():
        if key == "http_status":
            continue
        if key == "source_in":
            actual = data.get("source")
            if actual not in expected:
                failures.append(f"{prefix}source {actual!r} not in {expected!r}")
            continue
        if key == "has_content_or_raw":
            content = str(data.get("content") or "").strip()
            raw = data.get("raw") or {}
            choices = raw.get("choices") or data.get("choices") or []
            msg = (choices[0].get("message") if choices else {}) or {}
            alt = str(msg.get("content") or msg.get("reasoning_content") or "").strip()
            if not content and not alt:
                failures.append(f"{prefix}empty LLM response (content and raw)")
            continue
        if key == "modes_include":
            modes = {m.get("id") for m in (data.get("modes") or []) if isinstance(m, dict)}
            missing = [m for m in expected if m not in modes]
            if missing:
                failures.append(f"{prefix}missing modes {missing}")
            continue
        if key == "result_intent":
            actual = data.get("intent")
            if actual != expected:
                failures.append(f"{prefix}intent={actual!r} != {expected!r}")
            continue
        if key == "answer_contains":
            answer = str((data.get("result") or {}).get("answer") or data.get("answer") or "")
            if expected not in answer:
                failures.append(f"{prefix}answer missing {expected!r}")
            continue

        if key == "model_contains":
            actual = str(data.get("model") or "")
            if expected not in actual:
                failures.append(f"{prefix}model {actual!r} does not contain {expected!r}")
            continue
        actual = data.get(key)
        if actual != expected:
            failures.append(f"{prefix}{key}={actual!r} != {expected!r}")


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    expect = case.get("expect") or {}
    endpoint = case.get("endpoint", "orchestrator")
    method = case.get("method", "GET").upper()
    path = case.get("path", "")
    body = case.get("body")
    timeout = float(case.get("timeout", 120))
    failures: list[str] = []
    t0 = time.perf_counter()

    setup = case.get("setup")
    if setup:
        setup_method = setup.get("method", "POST").upper()
        setup_path = setup.get("path", "")
        setup_body = setup.get("body")
        setup_url = f"{ORCHESTRATOR_URL}{setup_path}"
        if setup_method == "GET":
            setup_status, setup_data = _http("GET", setup_url, timeout=10)
        else:
            setup_status, setup_data = _http(
                setup_method, setup_url, setup_body, timeout=10
            )
        setup_expect = setup.get("expect") or {"http_status": 200}
        if setup_status != setup_expect.get("http_status", 200):
            failures.append(
                f"setup HTTP {setup_status} != {setup_expect.get('http_status', 200)}"
            )
        _check_expect(setup_data, setup_expect, failures, prefix="setup ")

    if endpoint == "litellm":
        url = f"{LITELLM_URL}{path}"
    else:
        url = f"{ORCHESTRATOR_URL}{path}"

    if method == "GET":
        status, data = _http("GET", url, timeout=timeout)
    else:
        status, data = _http(method, url, body, timeout=timeout)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    exp_status = expect.get("http_status", 200)
    if status != exp_status:
        failures.append(f"HTTP {status} != {exp_status}")

    _check_expect(data, expect, failures)

    return {
        "id": case["id"],
        "name": case.get("name"),
        "category": case.get("category"),
        "ok": len(failures) == 0,
        "failures": failures,
        "elapsed_ms": elapsed_ms,
        "http_status": status,
        "active_mode": data.get("active_mode") if isinstance(data, dict) else None,
        "model": data.get("model") if isinstance(data, dict) else None,
        "compute_mode": data.get("compute_mode") if isinstance(data, dict) else None,
    }


def _restore_mode(mode: str) -> None:
    status, _ = _http("POST", f"{ORCHESTRATOR_URL}/v1/compute/mode", {"mode": mode}, timeout=10)
    if status != 200:
        print(f"Warnung: Restore auf {mode!r} fehlgeschlagen (HTTP {status})", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute-Modus / LLM-Routing Testcases")
    parser.add_argument("--id", dest="case_id", help="Einzelner Case")
    parser.add_argument("--skip-llm", action="store_true", help="Nur Modus-API, ohne LLM-Calls")
    parser.add_argument("--no-restore", action="store_true", help="Am Ende nicht auf sovereign zurücksetzen")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not CASES_DIR.is_dir():
        print(f"Keine Testcases in {CASES_DIR}", file=sys.stderr)
        return 2

    cases = _load_cases(case_id=args.case_id, skip_llm=args.skip_llm)
    if not cases:
        print("Keine Testcases gefunden.", file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    for case in cases:
        result = _run_case(case)
        results.append(result)
        if not args.json:
            status = "OK  " if result["ok"] else "FAIL"
            extra = ""
            if result.get("active_mode"):
                extra = f" mode={result['active_mode']}"
            elif result.get("model"):
                extra = f" model={result['model']}"
            print(f"{status} {result['id']} ({result['elapsed_ms']}ms){extra}")
            if result["failures"]:
                for failure in result["failures"]:
                    print(f"       · {failure}")
        if not result["ok"] and args.fail_fast:
            break

    if not args.no_restore:
        _restore_mode(RESTORE_MODE)

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "orchestrator": ORCHESTRATOR_URL,
        "litellm": LITELLM_URL,
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"\n{summary['passed']}/{summary['total']} passed, {summary['failed']} failed")

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
