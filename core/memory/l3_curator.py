"""L3-Curator — stabile Fakten aus L2 Archival → OrgClaim (G) + Letta Core (L3).

Pipeline (09-COMPANY-BRAIN.md §12.2):
  L2 Archival (7d) → LLM Fact-Extraktion → confidence-Filter → Dedup
  → OrgClaim DP-Commit (nur textuelle Claims, GREEN)
  → Claims mit supports_refs → Pending (Human-Gate)
  → Profil-Fakten → Letta Core Memory (human-Block)

Roh-Chat wird nie direkt zu org:Claim (P18).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from fastembed import TextEmbedding

from core.memory_gateway.client import chat_completion
from core.memory_gateway.letta_client import (
    get_or_create_agent,
    is_available as letta_available,
    list_archival,
)
from core.orchestrator.dataproducts import OrgClaim
from core.orchestrator.db import get_connection
from core.orchestrator.dp_service import commit_dataproduct

log = logging.getLogger("l3_curator")

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "memory-curator.yaml"
STATE_DIR = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory")) / "state"
PROCESSED_STATE = Path(
    os.environ.get("L3_CURATOR_STATE", str(STATE_DIR / "l3-curator-processed.json"))
)
PENDING_STATE = Path(
    os.environ.get("L3_PENDING_CLAIMS", str(STATE_DIR / "l3-pending-claims.json"))
)

EMBED_MODEL = os.environ.get(
    "SEARCH_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

_EXTRACTION_SYSTEM = """Du bist der L3-Curator des AI-OS Company Brain.
Extrahiere aus den Episoden NUR stabile, überprüfbare Fakten über Projekte,
Entscheidungen, Architektur oder den Nutzer — keine TODOs, keine Höflichkeiten.

Antworte NUR mit JSON (kein Markdown):
{
  "claims": [
    {"text": "...", "confidence": 0.85, "supports_refs": []}
  ],
  "profile_facts": [
    {"key": "rolle", "value": "...", "confidence": 0.9}
  ]
}

Regeln:
- confidence 0.0–1.0; unter 0.5 weglassen
- supports_refs nur bei klarem Bezug zu Offering/Decision/Engagement (external_id)
- Leere Arrays wenn nichts Relevantes
- Deutsch"""

_embedder: TextEmbedding | None = None


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "claim_min_confidence": 0.7,
        "profile_min_confidence": 0.75,
        "dedup_cosine_threshold": 0.95,
        "max_claims_per_run": 50,
        "episode_lookback_days": 7,
        "max_episodes_per_run": 40,
    }


def _cfg(key: str, default: Any) -> Any:
    return _load_config().get(key, default)


def _get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=EMBED_MODEL)
    return _embedder


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _claim_id(text: str) -> str:
    digest = hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]
    return f"claim-{digest}"


def _parse_episode_ts(text: str) -> datetime | None:
    match = re.search(r"\[(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?)\]", text or "")
    if not match:
        return None
    raw = match.group(1)
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(f"{raw}T12:00:00").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _recent_episodes(tenant_id: str, days: int, max_episodes: int) -> list[dict[str, Any]]:
    if not letta_available():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = list_archival(tenant_id, max_items=500)
    recent = []
    for row in rows:
        ts = row.get("episode_ts") or _parse_episode_ts(str(row.get("text") or ""))
        if ts and ts < cutoff:
            continue
        recent.append(row)
    recent.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return recent[:max_episodes]


def _existing_claim_texts(tenant_id: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT payload->>'text' AS text
            FROM kg_nodes
            WHERE tenant_id = %s AND node_type = 'org:Claim'
            """,
            (tenant_id,),
        ).fetchall()
    return [str(r["text"]) for r in rows if r.get("text")]


def _is_duplicate(text: str, existing_texts: list[str], threshold: float) -> bool:
    if not existing_texts:
        return False
    embedder = _get_embedder()
    vec = list(embedder.embed([text]))[0].tolist()
    for batch_start in range(0, len(existing_texts), 32):
        batch = existing_texts[batch_start : batch_start + 32]
        for ev in embedder.embed(batch):
            if _cosine(vec, ev.tolist()) >= threshold:
                return True
    return False


def _parse_extraction(raw: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"claims": [], "profile_facts": []}
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return {"claims": [], "profile_facts": []}
    return {
        "claims": data.get("claims") or [],
        "profile_facts": data.get("profile_facts") or [],
    }


async def _extract_facts(episodes: list[dict[str, Any]], tenant_id: str) -> dict[str, Any]:
    if not episodes:
        return {"claims": [], "profile_facts": []}

    blocks = []
    for ep in episodes[:25]:
        text = str(ep.get("text") or "").strip()
        if text:
            blocks.append(text[:600])
    context = "\n---\n".join(blocks)

    result = await chat_completion(
        [
            {"role": "system", "content": _EXTRACTION_SYSTEM},
            {
                "role": "user",
                "content": f"Episoden (L2 Archival):\n{context[:12000]}",
            },
        ],
        tenant_id=tenant_id,
        produced_by="l3-curator",
        max_tokens=900,
        temperature=0.1,
        persist=False,
    )
    return _parse_extraction(result.get("content") or "")


def _append_core_memory(tenant_id: str, lines: list[str]) -> dict[str, Any]:
    from core.memory_gateway.letta_client import append_core_human

    return append_core_human(tenant_id, "\n".join(lines))


def get_pending_claims() -> list[dict[str, Any]]:
    return list(_load_json(PENDING_STATE).get("claims") or [])


async def run_l3_curate(
    tenant_id: str = "nextchapter",
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """L3-Curator-Lauf — extrahiert Fakten, committet Claims, aktualisiert Core."""
    cfg = _load_config()
    days = int(_cfg("episode_lookback_days", 7))
    max_eps = int(_cfg("max_episodes_per_run", 40))
    min_claim_conf = float(_cfg("claim_min_confidence", 0.7))
    min_profile_conf = float(_cfg("profile_min_confidence", 0.75))
    dedup_threshold = float(_cfg("dedup_cosine_threshold", 0.95))
    max_claims = int(_cfg("max_claims_per_run", 50))

    processed_state = _load_json(PROCESSED_STATE)
    processed_ids: set[str] = set(processed_state.get("episode_ids") or [])
    pending_state = _load_json(PENDING_STATE)
    pending: list[dict[str, Any]] = list(pending_state.get("claims") or [])

    episodes = _recent_episodes(tenant_id, days, max_eps)
    if force:
        new_episodes = episodes
    else:
        new_episodes = [e for e in episodes if str(e.get("id")) not in processed_ids]

    if not new_episodes:
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "episodes_seen": len(episodes),
            "episodes_new": 0,
            "claims_committed": 0,
            "claims_pending": len(pending),
            "profile_lines": 0,
            "dry_run": dry_run,
        }

    extracted = await _extract_facts(new_episodes, tenant_id)
    existing_texts = _existing_claim_texts(tenant_id)
    committed: list[str] = []
    skipped_dup = 0
    skipped_low = 0
    gated: list[dict[str, Any]] = []

    for raw_claim in extracted.get("claims") or []:
        if len(committed) >= max_claims:
            break
        if not isinstance(raw_claim, dict):
            continue
        text = str(raw_claim.get("text") or "").strip()
        if len(text) < 12:
            continue
        try:
            confidence = float(raw_claim.get("confidence", 0))
        except (TypeError, ValueError):
            continue
        if confidence < min_claim_conf:
            skipped_low += 1
            continue

        supports = [str(r) for r in (raw_claim.get("supports_refs") or []) if r]
        if supports:
            gated.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "supports_refs": supports,
                    "status": "pending_human_gate",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            continue

        if _is_duplicate(text, existing_texts + committed, dedup_threshold):
            skipped_dup += 1
            continue

        claim_id = _claim_id(text)
        dp = OrgClaim(
            tenant_id=tenant_id,
            produced_by="memory-agent/l3-curator",
            workflow_run_id=f"l3-curator-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            claim_id=claim_id,
            text=text[:500],
            confidence=round(confidence, 3),
            valid_from=date.today(),
            asserts_from_ref=f"agent-run:l3-curator",
        )

        if dry_run:
            committed.append(text)
            existing_texts.append(text)
            continue

        try:
            commit_dataproduct(dp)
            committed.append(claim_id)
            existing_texts.append(text)
        except Exception as exc:
            log.warning("Claim-Commit fehlgeschlagen (%s): %s", claim_id, exc)

    profile_lines: list[str] = []
    for fact in extracted.get("profile_facts") or []:
        if not isinstance(fact, dict):
            continue
        key = str(fact.get("key") or "").strip()
        value = str(fact.get("value") or "").strip()
        if not key or not value:
            continue
        try:
            conf = float(fact.get("confidence", 0))
        except (TypeError, ValueError):
            continue
        if conf < min_profile_conf:
            continue
        profile_lines.append(f"- {key}: {value}")

    core_result: dict[str, Any] | None = None
    if profile_lines and not dry_run:
        core_result = _append_core_memory(tenant_id, profile_lines)

    if gated:
        pending.extend(gated)
        pending_state["claims"] = pending[-200:]
        if not dry_run:
            _save_json(PENDING_STATE, pending_state)

    for ep in new_episodes:
        eid = str(ep.get("id") or "")
        if eid:
            processed_ids.add(eid)

    if not dry_run:
        processed_state["episode_ids"] = sorted(processed_ids)[-2000:]
        processed_state["last_run"] = datetime.now(timezone.utc).isoformat()
        _save_json(PROCESSED_STATE, processed_state)

    return {
        "ok": True,
        "tenant_id": tenant_id,
        "dry_run": dry_run,
        "episodes_seen": len(episodes),
        "episodes_new": len(new_episodes),
        "claims_committed": len(committed),
        "claim_ids": committed,
        "claims_gated": len(gated),
        "claims_skipped_duplicate": skipped_dup,
        "claims_skipped_low_confidence": skipped_low,
        "claims_pending_total": len(pending_state.get("claims") or pending),
        "profile_lines": len(profile_lines),
        "core_memory": core_result,
        "extracted_preview": {
            "claims": len(extracted.get("claims") or []),
            "profile_facts": len(extracted.get("profile_facts") or []),
        },
    }
