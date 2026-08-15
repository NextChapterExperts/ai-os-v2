"""Tests for Enterprise Profile DataProduct, Context Bundle Integration, and API Endpoints."""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.dataproducts import OrgEnterpriseProfile, NODE_TYPE_BY_CLASS
from core.orchestrator.enterprise_profile_store import (
    get_enterprise_profile,
    save_enterprise_profile,
    _default_nextchapter_profile,
)
from core.orchestrator.context_resolution import resolve_context
from core.orchestrator.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_org_enterprise_profile_schema():
    profile = OrgEnterpriseProfile(
        tenant_id="nextchapter",
        produced_by="test",
        legal_name="Next Chapter Experts / Peter Schuler",
        brand_name="NextChapterExperts",
        tax_id="DE123456789",
        website="https://nextchapterexperts.de",
        industry="KI-Consulting",
        hourly_rates={"senior_ai_architect": 180.0, "student": 45.0},
        team_members=[
            {"name": "Peter Schuler", "role": "Senior AI Architect", "type": "freelancer"},
            {"name": "Student", "role": "Working Student", "type": "minijobber"},
        ],
    )
    assert profile.legal_name == "Next Chapter Experts / Peter Schuler"
    assert profile.hourly_rates["senior_ai_architect"] == 180.0
    assert len(profile.team_members) == 2
    assert NODE_TYPE_BY_CLASS[OrgEnterpriseProfile] == ("org:EnterpriseProfile", "enterprise_id")


def test_enterprise_profile_store_get_and_save(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.orchestrator.enterprise_profile_store._profile_path_for_tenant",
        lambda t: tmp_path / f"00-company-profile-{t}.yaml",
    )
    monkeypatch.setattr("core.orchestrator.enterprise_profile_store._PROFILE_CACHE", {})

    profile = get_enterprise_profile("tenant_test")
    assert profile is not None
    assert profile.brand_name == "NextChapterExperts"
    assert "senior_ai_architect" in profile.hourly_rates

    # Update profile
    profile.legal_name = "Peter Schuler AI Engineering"
    profile.hourly_rates["senior_ai_architect"] = 195.0
    res = save_enterprise_profile(profile, commit_to_graph=False)
    assert res["status"] == "saved"

    # Clear cache and reload
    monkeypatch.setattr("core.orchestrator.enterprise_profile_store._PROFILE_CACHE", {})
    reloaded = get_enterprise_profile("tenant_test")
    assert reloaded.legal_name == "Peter Schuler AI Engineering"
    assert reloaded.hourly_rates["senior_ai_architect"] == 195.0


def test_context_bundle_contains_enterprise_slice():
    bundle = resolve_context("ask", "nextchapter", {"query": "Welche Stundensätze bieten wir?"})
    assert "enterprise" in bundle
    ent = bundle["enterprise"]
    assert "legal_name" in ent
    assert "hourly_rates" in ent
    assert "team_members" in ent
    assert ent["hourly_rates"]["senior_ai_architect"] >= 100.0


def test_company_profile_api_endpoints(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "core.orchestrator.enterprise_profile_store._profile_path_for_tenant",
        lambda t: tmp_path / f"00-company-profile-{t}.yaml",
    )
    monkeypatch.setattr("core.orchestrator.enterprise_profile_store._PROFILE_CACHE", {})

    # 1. GET
    resp = client.get("/v1/company/profile?tenant_id=test_api")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["profile"]["brand_name"] == "NextChapterExperts"

    # 2. POST (Update)
    updated_payload = data["profile"]
    updated_payload["brand_name"] = "NextChapter AI Systems"
    updated_payload["hourly_rates"]["workshop_day_rate"] = 2800.0

    post_resp = client.post("/v1/company/profile?tenant_id=test_api", json=updated_payload)
    assert post_resp.status_code == 200
    post_data = post_resp.json()
    assert post_data["status"] == "ok"

    # 3. Verify GET reflects change
    monkeypatch.setattr("core.orchestrator.enterprise_profile_store._PROFILE_CACHE", {})
    get_resp2 = client.get("/v1/company/profile?tenant_id=test_api")
    assert get_resp2.status_code == 200
    assert get_resp2.json()["profile"]["brand_name"] == "NextChapter AI Systems"
    assert get_resp2.json()["profile"]["hourly_rates"]["workshop_day_rate"] == 2800.0
