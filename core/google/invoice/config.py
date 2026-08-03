"""Rechnungs-Konfiguration — Tenant-Default + Override."""

from __future__ import annotations

import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_DEFAULT = _REPO / "config" / "invoice.yaml"


def invoice_config_path(tenant_id: str | None = None) -> Path:
    env = os.getenv("AIOS_INVOICE_CONFIG", "").strip()
    if env:
        return Path(env)
    if tenant_id:
        tenant_cfg = _REPO / "customers" / tenant_id / "config" / "invoice.yaml"
        if tenant_cfg.is_file():
            return tenant_cfg
    return _DEFAULT


def load_invoice_config(tenant_id: str | None = None) -> dict:
    path = invoice_config_path(tenant_id)
    if not path.is_file():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
