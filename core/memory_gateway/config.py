"""Compute-Modi und LiteLLM-Konfiguration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPUTE_CONFIG = REPO_ROOT / "config" / "compute.yaml"
LITELLM_URL = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "192.168.178.64")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen3.6-64k:latest")
DEFAULT_COMPUTE_MODE = os.environ.get("DEFAULT_COMPUTE_MODE", "sovereign")
MODE_STATE_PATH = Path(
    os.environ.get(
        "AIOS_COMPUTE_MODE_PATH",
        "/opt/ai-os/memory/state/compute-mode.json",
    )
)


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


def get_mode(mode: str | None = None) -> str:
    cfg = load_compute_config()
    chosen = (mode or DEFAULT_COMPUTE_MODE or cfg.get("default_mode") or "sovereign").strip()
    modes = cfg.get("modes") or {}
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


def list_compute_modes() -> list[dict[str, Any]]:
    cfg = load_compute_config()
    default = get_mode(None)
    out = []
    for key, meta in (cfg.get("modes") or {}).items():
        out.append(
            {
                "id": key,
                "default_model": meta.get("default_model"),
                "label": meta.get("label", key),
                "description": meta.get("description", ""),
                "is_default": key == default,
            }
        )
    return out
