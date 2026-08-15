"""Enterprise Profile Store — Verwaltung der kanonischen Unternehmens-Identität (Company Brain Root)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .dataproducts import OrgEnterpriseProfile

log = logging.getLogger("enterprise_profile_store")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TENANT = "nextchapter"

# Cache
_PROFILE_CACHE: dict[str, OrgEnterpriseProfile] = {}


def _profile_path_for_tenant(tenant_id: str) -> Path:
    tenant_dir = REPO_ROOT / "customers" / tenant_id / "knowledge"
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir / "00-company-profile.yaml"


def _default_nextchapter_profile(tenant_id: str = DEFAULT_TENANT) -> OrgEnterpriseProfile:
    return OrgEnterpriseProfile(
        tenant_id=tenant_id,
        produced_by="enterprise-admin",
        enterprise_id=f"org:enterprise:{tenant_id}",
        legal_name="Next Chapter Experts / Peter Schuler",
        brand_name="NextChapterExperts",
        tax_id="DE345678901",
        website="https://nextchapterexperts.de",
        industry="KI-Consulting, Autonome Agentensysteme & Enterprise AI Architectures",
        description=(
            "Beratung, Konzeption und Implementierung maßgeschneiderter KI-Betriebssysteme, "
            "Multi-Agenten-Architekturen und BTP/GenAI-Integrationen für den Mittelstand und Enterprises."
        ),
        founder_or_owner="Peter Schuler (Senior AI System Architect & Founder)",
        hourly_rates={
            "senior_ai_architect": 180.0,
            "ai_consultant": 140.0,
            "working_student_minijobber": 45.0,
            "workshop_day_rate": 2200.0,
        },
        team_members=[
            {
                "name": "Peter Schuler",
                "role": "Senior AI System Architect & Founder",
                "type": "freelancer",
                "skills": ["AI-OS v2", "LangGraph", "Docker", "FastAPI", "SAP BTP AI", "Enterprise Architecture"],
            },
            {
                "name": "Studentischer Mitarbeiter",
                "role": "Working Student / Mini-Jobber",
                "type": "minijobber",
                "skills": ["Python Data Pipelines", "FastEmbed", "Research & Testing", "Web Ingestion"],
            },
        ],
        core_services=[
            "AI-OS VM Appliance Setup & Betrieb",
            "Fachagenten & Workflow-Entwicklung (LangGraph, n8n)",
            "Company Brain & Graph-RAG Wissensmanagement",
            "KI-Strategie- & Architektur-Workshops",
        ],
        standard_terms={
            "payment_terms_days": 14,
            "travel_policy": "Reisekosten 0,70 €/km oder Bahnfahrt 1. Klasse, Reisezeit 50% Stundensatz",
        },
        path=f"customers/{tenant_id}/knowledge/00-company-profile.yaml",
    )


def get_enterprise_profile(tenant_id: str = DEFAULT_TENANT) -> OrgEnterpriseProfile:
    """Lädt das Unternehmensprofil für den Mandanten (aus Cache oder YAML-Datei)."""
    if tenant_id in _PROFILE_CACHE:
        return _PROFILE_CACHE[tenant_id]

    yaml_file = _profile_path_for_tenant(tenant_id)
    if yaml_file.is_file():
        try:
            with yaml_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            data["tenant_id"] = tenant_id
            profile = OrgEnterpriseProfile.model_validate(data)
            _PROFILE_CACHE[tenant_id] = profile
            return profile
        except Exception:
            log.exception("Fehler beim Laden von %s, nutze Standard-Profil", yaml_file)

    # Initial-Seed anlegen
    profile = _default_nextchapter_profile(tenant_id)
    save_enterprise_profile(profile, commit_to_graph=False)
    _PROFILE_CACHE[tenant_id] = profile
    return profile


def save_enterprise_profile(
    profile: OrgEnterpriseProfile,
    commit_to_graph: bool = True,
) -> dict[str, Any]:
    """Speichert das Unternehmensprofil in der kanonischen YAML-Datei und optional im Graph."""
    tenant_id = profile.tenant_id or DEFAULT_TENANT
    yaml_file = _profile_path_for_tenant(tenant_id)

    profile_dict = profile.model_dump(
        mode="json",
        exclude={"produced_by", "workflow_run_id"},
    )
    profile_dict["path"] = f"customers/{tenant_id}/knowledge/00-company-profile.yaml"

    # 1. In YAML-Datei schreiben (Kanonischer K-Store)
    with yaml_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(profile_dict, f, allow_unicode=True, sort_keys=False)

    _PROFILE_CACHE[tenant_id] = profile

    commit_res: dict[str, Any] = {}
    if commit_to_graph:
        from .dp_service import commit_dataproduct

        commit_res = commit_dataproduct(profile)

    return {
        "status": "saved",
        "tenant_id": tenant_id,
        "path": str(yaml_file),
        "graph_commit": commit_res,
        "profile": profile_dict,
    }
