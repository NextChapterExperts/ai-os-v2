"""Letta L2 Archival Memory — episodisches Gedächtnis pro Tenant (Phase 2-Vorbereitung).

Schreibt und liest Episoden über die Letta REST-API (:8283). Der Orchestrator
läuft auf dem Host (systemd), Letta im Docker-Container mit published Port —
deshalb wird `LETTA_HOST=letta` automatisch auf 127.0.0.1 gemappt.

Agent-State: `/opt/ai-os/memory/state/letta-agents.json` (tenant_id → agent_id).
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_PORT

log = logging.getLogger("letta_client")

LETTA_PORT = os.environ.get("LETTA_PORT", "8283")
LETTA_ENABLED = os.environ.get("LETTA_ENABLED", "true").lower() not in ("0", "false", "no")
LETTA_STATE_PATH = Path(
    os.environ.get("LETTA_AGENTS_STATE", "/opt/ai-os/memory/state/letta-agents.json")
)
LETTA_EMBED_MODEL = os.environ.get("LETTA_EMBED_MODEL", "nomic-embed-text:latest")
LETTA_EMBED_DIM = int(os.environ.get("LETTA_EMBED_DIM", "768"))
TIMEOUT = float(os.environ.get("LETTA_TIMEOUT", "5.0"))

_EPISODE_TS = re.compile(r"\[(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?)\]")


def letta_base_url() -> str:
    explicit = os.environ.get("LETTA_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = os.environ.get("LETTA_HOST", "127.0.0.1")
    if host == "letta":
        # Orchestrator auf Host, nicht im Compose-Netz
        host = "127.0.0.1"
    return f"http://{host}:{LETTA_PORT}"


def _ollama_endpoint() -> str:
    return f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"


def _request(method: str, path: str, payload: dict | None = None) -> Any:
    url = f"{letta_base_url()}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
        if not raw:
            return None
        return json.loads(raw)


def is_available() -> bool:
    if not LETTA_ENABLED:
        return False
    try:
        _request("GET", "/v1/agents/?limit=1")
        return True
    except Exception:
        log.debug("Letta nicht erreichbar unter %s", letta_base_url(), exc_info=True)
        return False


def _load_state() -> dict[str, str]:
    if not LETTA_STATE_PATH.is_file():
        return {}
    try:
        data = json.loads(LETTA_STATE_PATH.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in (data or {}).items()}
    except Exception:
        log.warning("Letta-Agent-State unlesbar: %s", LETTA_STATE_PATH, exc_info=True)
        return {}


def _save_state(state: dict[str, str]) -> None:
    LETTA_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LETTA_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _agent_name(tenant_id: str) -> str:
    slug = re.sub(r"[^\w\-]+", "-", tenant_id.strip().lower()).strip("-") or "default"
    return f"aios-{slug}"


def _find_agent_by_name(name: str) -> str | None:
    try:
        agents = _request("GET", "/v1/agents/") or []
        for agent in agents:
            if agent.get("name") == name:
                return str(agent["id"])
    except Exception:
        log.debug("Letta-Agent-Suche fehlgeschlagen", exc_info=True)
    return None


def _create_agent(tenant_id: str) -> str:
    name = _agent_name(tenant_id)
    payload = {
        "name": name,
        "description": f"AI-OS Company Brain episodic L2 ({tenant_id})",
        "memory": {
            "memory": {
                "human": {
                    "label": "human",
                    "value": f"Tenant: {tenant_id}. NCE First-Party DEV-VM.",
                    "limit": 4000,
                },
                "persona": {
                    "label": "persona",
                    "value": "AI-OS Memory Agent — speichert Episoden ins Archival Memory.",
                    "limit": 2000,
                },
            }
        },
        "llm_config": {
            "model": OLLAMA_MODEL,
            "model_endpoint_type": "ollama",
            "model_endpoint": _ollama_endpoint(),
            "context_window": 32000,
        },
        "embedding_config": {
            "embedding_endpoint_type": "ollama",
            "embedding_endpoint": _ollama_endpoint(),
            "embedding_model": LETTA_EMBED_MODEL,
            "embedding_dim": LETTA_EMBED_DIM,
        },
    }
    agent = _request("POST", "/v1/agents/", payload)
    return str(agent["id"])


def get_or_create_agent(tenant_id: str) -> str | None:
    if not LETTA_ENABLED:
        return None
    state = _load_state()
    if tenant_id in state:
        try:
            _request("GET", f"/v1/agents/{state[tenant_id]}")
            return state[tenant_id]
        except Exception:
            log.info("Letta-Agent %s für %s ungültig — neu anlegen", state[tenant_id], tenant_id)

    name = _agent_name(tenant_id)
    agent_id = _find_agent_by_name(name)
    if not agent_id:
        try:
            agent_id = _create_agent(tenant_id)
            log.info("Letta-Agent angelegt: %s (%s)", name, agent_id)
        except Exception:
            log.exception("Letta-Agent für %s konnte nicht angelegt werden", tenant_id)
            return None

    state[tenant_id] = agent_id
    _save_state(state)
    return agent_id


def format_archival_episode(
    prompt: str,
    source: str,
    answer_preview: str,
    *,
    decision: str = "",
    open_items: str = "",
    ts: datetime | None = None,
) -> str:
    when = (ts or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M")
    theme = prompt[:80].replace("\n", " ")
    dec = decision or f"Quelle={source[:60]}"
    opn = open_items or "—"
    prev = answer_preview[:120].replace("\n", " ")
    return f"[{when}] THEMA: {theme} | ENTSCHEIDUNG: {dec} | OFFEN: {opn} | ANTWORT: {prev}"


def insert_archival(tenant_id: str, text: str, *, agent_id: str | None = None) -> dict[str, Any]:
    if not LETTA_ENABLED or not text.strip():
        return {"success": False, "error": "disabled_or_empty"}
    aid = agent_id or get_or_create_agent(tenant_id)
    if not aid:
        return {"success": False, "error": "no_agent"}
    try:
        result = _request("POST", f"/v1/agents/{aid}/archival", {"text": text})
        passage_id = None
        if isinstance(result, list) and result:
            passage_id = result[0].get("id")
        elif isinstance(result, dict):
            passage_id = result.get("id")
        return {"success": True, "agent_id": aid, "passage_id": passage_id, "error": None}
    except Exception as exc:
        log.warning("Letta insert_archival fehlgeschlagen: %s", exc)
        return {"success": False, "error": str(exc), "agent_id": aid}


def insert_episode(
    tenant_id: str,
    prompt: str,
    source: str,
    answer_preview: str,
    *,
    agent_id: str | None = None,
) -> dict[str, Any]:
    episode = format_archival_episode(prompt, source, answer_preview)
    return insert_archival(tenant_id, episode, agent_id=agent_id)


def append_core_human(tenant_id: str, addition: str) -> dict[str, Any]:
    """L3: Text an den human-Block in Letta Core Memory anhängen."""
    if not LETTA_ENABLED or not addition.strip():
        return {"success": False, "error": "disabled_or_empty"}
    aid = get_or_create_agent(tenant_id)
    if not aid:
        return {"success": False, "error": "no_agent"}
    try:
        current = _request("GET", f"/v1/agents/{aid}/memory")
        human = (
            (current.get("memory") or {}).get("human", {}).get("value")
            or f"Tenant: {tenant_id}."
        )
        if addition.strip() in human:
            return {"success": True, "skipped": True, "agent_id": aid}
        new_val = f"{human.rstrip()}\n{addition.strip()}".strip()[:3900]
        _request("PATCH", f"/v1/agents/{aid}/memory", {"human": new_val})
        return {"success": True, "agent_id": aid, "error": None}
    except Exception as exc:
        log.warning("append_core_human fehlgeschlagen: %s", exc)
        return {"success": False, "error": str(exc), "agent_id": aid}


def _parse_episode_ts(text: str) -> datetime | None:
    match = _EPISODE_TS.search(text or "")
    if not match:
        return None
    raw = match.group(1)
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(f"{raw}T12:00:00").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _content_tokens(query: str) -> list[str]:
    stop = {
        "was", "haben", "wir", "gemacht", "besprochen", "erinnerst", "du", "sie",
        "gestern", "heute", "woche", "letzte", "diese", "vorletzte", "noch",
        "wie", "wo", "wann", "wer", "warum", "bitte", "mal", "denn",
    }
    return [t for t in re.split(r"\W+", query.lower()) if len(t) >= 3 and t not in stop]


def _keyword_match(text: str, query: str) -> bool:
    tokens = _content_tokens(query)
    if not tokens:
        return True
    lower_text = text.lower()
    return any(t in lower_text for t in tokens)


def list_archival(
    tenant_id: str,
    *,
    limit: int = 100,
    max_items: int = 2000,
    agent_id: str | None = None,
) -> list[dict[str, Any]]:
    if not LETTA_ENABLED:
        return []
    aid = agent_id or get_or_create_agent(tenant_id)
    if not aid:
        return []
    fetch_limit = min(max(max_items, limit), 500)
    try:
        rows = _request("GET", f"/v1/agents/{aid}/archival?limit={fetch_limit}") or []
        out: list[dict[str, Any]] = []
        for row in rows:
            text = str(row.get("text") or "")
            out.append(
                {
                    "id": row.get("id"),
                    "text": text,
                    "created_at": row.get("created_at"),
                    "episode_ts": _parse_episode_ts(text),
                    "agent_id": aid,
                }
            )
        return out[:max_items]
    except Exception:
        log.debug("Letta list_archival fehlgeschlagen", exc_info=True)
        return []


def search_archival(
    tenant_id: str,
    query: str,
    *,
    count: int = 10,
    start: str | None = None,
    end: str | None = None,
    agent_id: str | None = None,
) -> list[dict[str, Any]]:
    """Archival-Episoden suchen (Keyword + optional Zeitfenster).

    Die aktuelle Letta-Version (:8283) hat keinen dedizierten Search-Endpoint;
    wir listen paginiert und filtern clientseitig. Bei wachsendem Archiv kann
    später auf Letta-Semantic-Search umgestellt werden.
    """
    rows = list_archival(tenant_id, limit=count, max_items=max(count * 20, 500), agent_id=agent_id)
    if not rows:
        return []

    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if start else None
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None
    time_filtered = bool(start_dt or end_dt)

    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        text = row["text"]
        if time_filtered:
            ts = row.get("episode_ts")
            if not ts:
                continue
            if start_dt and ts < start_dt:
                continue
            if end_dt and ts >= end_dt:
                continue
        elif query.strip() and not _keyword_match(text, query):
            continue

        score = 0.9
        if query.strip() and _keyword_match(text, query):
            score = 0.95
        if time_filtered and row.get("created_at"):
            score += 0.01
        scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:count]]
