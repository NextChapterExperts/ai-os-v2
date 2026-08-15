"""Tenant Provisioning & Lifecycle Management für AI-OS v2 Multi-Tenant Appliance.

Erlaubt das automatische, isolierte Anlegen neuer Kunden-Mandanten (Säule 1)
mit eigenem Company Brain, Dateisystem-Ordner und neutralem Profil.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
from core.orchestrator.dataproducts import OrgEnterpriseProfile
from core.orchestrator.enterprise_profile_store import save_enterprise_profile

log = logging.getLogger("tenant_provisioning")

REPO_ROOT = Path(os.environ.get("AIOS_ROOT", Path(__file__).resolve().parent.parent.parent))
CUSTOMERS_DIR = REPO_ROOT / "customers"


def _sanitize_tenant_id(tenant_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "", tenant_id.strip().lower())
    if not cleaned:
        raise ValueError("Ungültige tenant_id")
    return cleaned


def list_tenants() -> list[str]:
    """Gibt alle im Dateisystem existierenden Mandanten zurück."""
    if not CUSTOMERS_DIR.exists():
        return []
    return sorted([p.name for p in CUSTOMERS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")])


def provision_tenant(
    tenant_id: str,
    company_name: str,
    *,
    brand_name: str | None = None,
    industry: str | None = None,
    founder_or_owner: str | None = None,
    website: str | None = None,
    tax_id: str | None = None,
    hourly_rates: dict[str, float] | None = None,
    core_services: list[str] | None = None,
    standard_payment_days: int = 14,
) -> dict[str, Any]:
    """Erstellt einen neuen, vollständig isolierten Mandanten mit neutralem Company Brain."""
    t_id = _sanitize_tenant_id(tenant_id)
    tenant_dir = CUSTOMERS_DIR / t_id
    knowledge_dir = tenant_dir / "knowledge"

    # 1. Verzeichnisstruktur erstellen
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # 2. Neutrales Mandanten-Profil (SSOT) anlegen
    profile = OrgEnterpriseProfile(
        tenant_id=t_id,
        produced_by="tenant-provisioning",
        enterprise_id=f"org:enterprise:{t_id}",
        legal_name=company_name.strip(),
        brand_name=(brand_name or company_name).strip(),
        tax_id=tax_id or "",
        website=website or "",
        industry=industry or "Allgemeine Dienstleistungen & Beratung",
        description=f"Plattform-Instanz für {company_name}.",
        founder_or_owner=founder_or_owner or "Geschäftsführung",
        hourly_rates=hourly_rates or {
            "standard_consultant": 120.0,
            "senior_expert": 160.0,
            "assistant": 40.0,
        },
        team_members=[
            {
                "name": founder_or_owner or "Administrator",
                "role": "Mandanten-Administrator",
                "type": "angestellter",
                "skills": ["Plattform-Management", "Fachanwendung"],
            }
        ],
        core_services=core_services or [
            "Mandantenspezifische Fachberatung",
            "Digitale Prozessunterstützung",
        ],
        standard_terms={
            "payment_terms_days": standard_payment_days,
            "travel_policy": "Reisekosten nach Beleg oder Standardpauschale",
        },
        path=f"customers/{t_id}/knowledge/00-company-profile.yaml",
    )

    # 3. Profil im Dateisystem und Knowledge Graph speichern
    save_res = save_enterprise_profile(profile, commit_to_graph=True)

    # 4. Mandanten-Konfiguration (config.json) anlegen
    config_file = tenant_dir / "config.json"
    config_data = {
        "tenant_id": t_id,
        "company_name": company_name,
        "created_at": "2026-08-15",
        "active": True,
        "enabled_agents": ["research-agent", "email-invoices", "meetings-agent"],
        "max_users": 10,
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    log.info("Tenant '%s' erfolgreich provisioniert in %s", t_id, tenant_dir)

    return {
        "status": "provisioned",
        "tenant_id": t_id,
        "company_name": company_name,
        "tenant_dir": str(tenant_dir),
        "knowledge_dir": str(knowledge_dir),
        "profile_save_status": save_res.get("status"),
        "config_path": str(config_file),
    }
