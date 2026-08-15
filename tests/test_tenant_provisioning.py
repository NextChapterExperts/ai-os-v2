"""Tests für Tenant Provisioning & Multi-Tenant Isolation (Säule 1)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.tenant_provisioning import provision_tenant, list_tenants
from core.orchestrator.enterprise_profile_store import get_enterprise_profile
from core.orchestrator.context_resolution import resolve_context
from core.orchestrator.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_tenants():
    tenants = list_tenants()
    assert isinstance(tenants, list)
    assert "nextchapter" in tenants


def test_provision_new_tenant_lifecycle(tmp_path, monkeypatch):
    test_tenant_id = "test_acme_corp"
    customers_dir = tmp_path / "customers"
    monkeypatch.setattr("core.orchestrator.tenant_provisioning.CUSTOMERS_DIR", customers_dir)
    monkeypatch.setattr(
        "core.orchestrator.enterprise_profile_store._profile_path_for_tenant",
        lambda t: customers_dir / t / "knowledge" / "00-company-profile.yaml",
    )
    monkeypatch.setattr("core.orchestrator.enterprise_profile_store._PROFILE_CACHE", {})

    res = provision_tenant(
        tenant_id=test_tenant_id,
        company_name="ACME Industrial Robotics GmbH",
        industry="Automatisierung & Robotik",
        founder_or_owner="Dr. Erika Musterfrau",
        hourly_rates={"robotics_engineer": 175.0, "technician": 90.0},
    )

    assert res["status"] == "provisioned"
    assert res["tenant_id"] == test_tenant_id

    # Verzeichnisse prüfen
    assert (customers_dir / test_tenant_id / "knowledge" / "00-company-profile.yaml").exists()
    assert (customers_dir / test_tenant_id / "config.json").exists()

    # Profil laden & verifizieren
    profile = get_enterprise_profile(test_tenant_id)
    assert profile.legal_name == "ACME Industrial Robotics GmbH"
    assert profile.industry == "Automatisierung & Robotik"
    assert profile.hourly_rates["robotics_engineer"] == 175.0
    assert "NextChapter" not in profile.legal_name

    # Context Resolution prüfen
    monkeypatch.setattr(
        "core.orchestrator.context_resolution.get_enterprise_profile",
        lambda t: profile if t == test_tenant_id else get_enterprise_profile(t),
    )
    bundle = resolve_context("ask", test_tenant_id, {"query": "Welche Stundensätze haben wir?"})
    assert "enterprise" in bundle
    assert bundle["enterprise"]["legal_name"] == "ACME Industrial Robotics GmbH"
    assert bundle["enterprise"]["hourly_rates"]["robotics_engineer"] == 175.0


def test_tenant_api_endpoints(client, tmp_path, monkeypatch):
    customers_dir = tmp_path / "customers"
    monkeypatch.setattr("core.orchestrator.tenant_provisioning.CUSTOMERS_DIR", customers_dir)
    monkeypatch.setattr(
        "core.orchestrator.enterprise_profile_store._profile_path_for_tenant",
        lambda t: customers_dir / t / "knowledge" / "00-company-profile.yaml",
    )
    monkeypatch.setattr("core.orchestrator.enterprise_profile_store._PROFILE_CACHE", {})

    # 1. Provision via POST
    post_res = client.post(
        "/v1/platform/tenant/provision",
        json={
            "tenant_id": "kanzlei_schmidt",
            "company_name": "Kanzlei Schmidt & Kollegen",
            "industry": "Wirtschafts- und Arbeitsrecht",
            "founder_or_owner": "RA Thomas Schmidt",
        },
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["status"] == "ok"
    assert data["result"]["tenant_id"] == "kanzlei_schmidt"

    # 2. List via GET
    get_res = client.get("/v1/platform/tenants")
    assert get_res.status_code == 200
    tenants = get_res.json()["tenants"]
    assert "kanzlei_schmidt" in tenants
