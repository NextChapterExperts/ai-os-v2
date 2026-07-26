"""DataProducts & Knowledge Graph Schema Tests."""

from __future__ import annotations

from datetime import date
import os
import sys

import pytest
from pydantic import ValidationError

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.dataproducts import (
    DP_CLASS_BY_NODE_TYPE,
    NODE_TYPE_BY_CLASS,
    OrgClaim,
    OrgDecision,
    OrgEngagement,
    OrgKnowledgeAsset,
    OrgMeeting,
    OrgOffering,
    OrgOrganization,
    OrgPerson,
    OrgPolicy,
)
from core.orchestrator.dp_service import _edges_for, _node_type_and_external_id, _ingest_recommended


def test_dataproduct_class_mappings():
    assert len(NODE_TYPE_BY_CLASS) == 9
    assert len(DP_CLASS_BY_NODE_TYPE) == 9
    assert DP_CLASS_BY_NODE_TYPE["org:Offering"] == OrgOffering
    assert DP_CLASS_BY_NODE_TYPE["org:Claim"] == OrgClaim


def test_org_offering_validation():
    offering = OrgOffering(
        tenant_id="nextchapter",
        produced_by="test",
        offering_id="offering:test-1",
        name="Test Offering",
        kind="consulting",
        summary="A test offering summary",
    )
    assert offering.storage_target == ["G", "K"]
    assert _ingest_recommended(offering) is False

    with pytest.raises(ValidationError):
        OrgOffering(
            tenant_id="nextchapter",
            produced_by="test",
            offering_id="offering:test-2",
            name="Invalid Kind",
            kind="invalid_kind",  # type: ignore
        )


def test_org_organization_validation():
    org = OrgOrganization(
        tenant_id="nextchapter",
        produced_by="test",
        org_id="org:partner-1",
        name="Partner Org",
        kind="partner",
        website="https://partner.example.com",
    )
    assert _ingest_recommended(org) is False
    assert org.storage_target == ["G"]


def test_org_person_validation():
    person = OrgPerson(
        tenant_id="nextchapter",
        produced_by="test",
        person_id="person:peter",
        name="Peter",
        role="CEO",
        email="peter@example.com",
        org_ref="org:nextchapter",
    )
    assert person.email == "peter@example.com"
    edges = _edges_for(person)
    assert len(edges) == 0  # OrgPerson uses payload org_ref, edges handled via other nodes


def test_org_engagement_edges():
    eng = OrgEngagement(
        tenant_id="nextchapter",
        produced_by="test",
        engagement_id="eng:ai-os",
        title="AI-OS Project",
        status="active",
        org_ref="org:client-1",
        offering_ref="offering:consulting-1",
    )
    edges = _edges_for(eng)
    assert ("about", "out", "org:client-1") in edges
    assert ("about", "out", "offering:consulting-1") in edges


def test_org_meeting_edges():
    meeting = OrgMeeting(
        tenant_id="nextchapter",
        produced_by="test",
        meeting_id="meet-001",
        title="Sprint Sync",
        held_at="2026-07-26T10:00:00Z",
        attendee_refs=["person:peter", "person:alice"],
        about_refs=["eng:ai-os"],
    )
    edges = _edges_for(meeting)
    assert ("attended_by", "out", "person:peter") in edges
    assert ("attended_by", "out", "person:alice") in edges
    assert ("about", "out", "eng:ai-os") in edges


def test_org_decision_edges():
    dec = OrgDecision(
        tenant_id="nextchapter",
        produced_by="test",
        decision_id="dec:001",
        title="Use Postgres Graph",
        status="active",
        decided_at=date(2026, 7, 26),
        summary="Decided to use Postgres as single source of truth for Knowledge Graph.",
        meeting_ref="meet-001",
        about_refs=["offering:consulting-1"],
    )
    edges = _edges_for(dec)
    assert ("decided_in", "out", "meet-001") in edges
    assert ("about", "out", "offering:consulting-1") in edges


def test_org_policy_edges():
    pol = OrgPolicy(
        tenant_id="nextchapter",
        produced_by="test",
        policy_id="policy:pii",
        title="PII Protection Policy",
        scope="global",
        applies_to_refs=["org:nextchapter"],
    )
    edges = _edges_for(pol)
    assert ("applies_to", "out", "org:nextchapter") in edges


def test_org_knowledge_asset_published():
    asset_unpub = OrgKnowledgeAsset(
        tenant_id="nextchapter",
        asset_id="asset:readme",
        title="README",
        path="README.md",
        kind="document",
        published=False,
    )
    assert _ingest_recommended(asset_unpub) is False

    asset_pub = OrgKnowledgeAsset(
        tenant_id="nextchapter",
        asset_id="asset:readme-pub",
        title="Published README",
        path="README.md",
        kind="document",
        published=True,
    )
    assert _ingest_recommended(asset_pub) is True


def test_org_claim_validation():
    claim = OrgClaim(
        tenant_id="nextchapter",
        claim_id="claim-001",
        text="AI-OS Memory Gate uses Postgres Graph for SSOT.",
        confidence=0.95,
        asserts_from_ref="agent-run:test",
        supports_refs=["offering:consulting-1"],
    )
    assert claim.confidence == 0.95
    edges = _edges_for(claim)
    assert ("asserts", "in", "agent-run:test") in edges
    assert ("supports", "out", "offering:consulting-1") in edges

    with pytest.raises(ValidationError):
        OrgClaim(
            tenant_id="nextchapter",
            claim_id="claim-invalid",
            text="Invalid confidence",
            confidence=1.5,  # > 1.0 invalid
        )
