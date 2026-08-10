"""Compute-Modi und LiteLLM-Konfiguration."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPUTE_CONFIG = REPO_ROOT / "config" / "compute.yaml"
LITELLM_URL = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "192.168.178.116")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen2.5-coder:32b")
VLLM_HOST = os.environ.get("VLLM_HOST", "192.168.178.116")
VLLM_PORT = os.environ.get("VLLM_PORT", "8001")
VLLM_MODEL = os.environ.get("VLLM_DEFAULT_MODEL", "/workspace/model")
DEFAULT_COMPUTE_MODE = os.environ.get("DEFAULT_COMPUTE_MODE", "sovereign")
MODE_STATE_PATH = Path(
    os.environ.get(
        "AIOS_COMPUTE_MODE_PATH",
        "/opt/ai-os/memory/state/compute-mode.json",
    )
)

MODE_TO_OLLAMA_MODEL = {
    "auto": "qwen2.5-coder:14b",
    "sovereign": "qwen2.5-coder:14b",
    "sovereign_r1": "deepseek-r1:32b",
    "sovereign_coder": "qwen2.5-coder:14b",
    "sovereign_nemo": "mistral-nemo:12b",
    "sovereign_hermes": "hermes3:8b",
    "sovereign_vision": "llama3.2-vision:11b",
}


def resolve_auto_model(prompt_text: str = "") -> str:
    """Smart Auto-Router: Analysiert den Prompt & wählt das optimale Monster-Modell."""
    lower = prompt_text.lower()

    if any(k in lower for k in ("bild", "pdf", "ocr", "foto", "dokument", "image", "analyse bild")):
        return "llama3.2-vision:11b"
    if any(k in lower for k in ("code", "script", "skript", "python", "javascript", "json", "sql", "html", "function", "bug", "refactor", "class")):
        return "qwen2.5-coder:14b"
    if any(k in lower for k in ("warum", "analysiere", "logik", "reasoning", "beweise", "erkläre im detail", "vergleiche", "berechne", "strategie")):
        return "deepseek-r1:32b"
    if any(k in lower for k in ("mail", "email", "e-mail", "blog", "zusammenfassung", "entwurf", "text", "schreibe")):
        return "mistral-nemo:12b"
    return "qwen2.5-coder:14b"





@lru_cache(maxsize=1)
def load_compute_config() -> dict[str, Any]:
    if COMPUTE_CONFIG.is_file():
        with COMPUTE_CONFIG.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "modes": {
            "sovereign": {"default_model": "ai-os-sovereign", "label": "Lokal (LAN)"},
        },
        "default_mode": DEFAULT_COMPUTE_MODE,
    }


def read_active_mode() -> str | None:
    if not MODE_STATE_PATH.is_file():
        return None
    try:
        data = json.loads(MODE_STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    active = data.get("mode") or data.get("active_mode")
    return str(active).strip() if active else None


def set_active_mode(mode: str) -> str:
    cfg = load_compute_config()
    modes = cfg.get("modes") or {}
    chosen = mode.strip()
    if chosen not in modes:
        raise ValueError(f"unknown compute mode: {chosen}")
    MODE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODE_STATE_PATH.write_text(
        json.dumps(
            {
                "mode": chosen,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return chosen


def get_mode(mode: str | None = None) -> str:
    cfg = load_compute_config()
    modes = cfg.get("modes") or {}
    if mode is not None and str(mode).strip():
        chosen = str(mode).strip()
    else:
        chosen = (
            read_active_mode()
            or DEFAULT_COMPUTE_MODE
            or cfg.get("default_mode")
            or "sovereign"
        )
    if chosen not in modes:
        return cfg.get("default_mode") or "sovereign"
    return chosen


def model_for_mode(mode: str | None = None) -> str:
    cfg = load_compute_config()
    mode_key = get_mode(mode)
    modes = cfg.get("modes") or {}
    entry = modes.get(mode_key) or {}
    return str(entry.get("default_model") or "ai-os-sovereign")


def ollama_chat_url() -> str:
    return f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"


def vllm_chat_url() -> str:
    return f"http://{VLLM_HOST}:{VLLM_PORT}/v1/chat/completions"



def list_compute_modes() -> list[dict[str, Any]]:
    cfg = load_compute_config()
    active = get_mode(None)
    config_default = (
        DEFAULT_COMPUTE_MODE or cfg.get("default_mode") or "sovereign"
    )
    out = []
    for key, meta in (cfg.get("modes") or {}).items():
        out.append(
            {
                "id": key,
                "default_model": meta.get("default_model"),
                "label": meta.get("label", key),
                "description": meta.get("description", ""),
                "is_active": key == active,
                "is_config_default": key == config_default,
            }
        )
    return out


def compute_mode_snapshot() -> dict[str, Any]:
    active_mode = get_mode(None)
    cfg = load_compute_config()
    config_default = (
        DEFAULT_COMPUTE_MODE or cfg.get("default_mode") or "sovereign"
    )
    modes_cfg = cfg.get("modes") or {}
    meta = modes_cfg.get(active_mode) or {}
    return {
        "active_mode": active_mode,
        "active_model": model_for_mode(active_mode),
        "active_label": meta.get("label", active_mode),
        "active_description": meta.get("description", ""),
        "config_default_mode": config_default,
        "updated_at": None
        if not MODE_STATE_PATH.is_file()
        else _mode_state_updated_at(),
        "modes": list_compute_modes(),
    }


def _mode_state_updated_at() -> str | None:
    try:
        data = json.loads(MODE_STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    updated = data.get("updated_at")
    return str(updated) if updated else None
