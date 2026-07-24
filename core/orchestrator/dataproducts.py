"""Company-Brain-DataProducts (org:*) — siehe docs/03-DATENPRODUKTE.md.

Minimal-Set fuer Phase 2 (Platform-Gate-Vorstufe): nur die Company-Brain-
Klassen, nicht der volle Blog/Email/Kalender-Catalog (Fach-Agenten, Phase 4,
gesperrt bis Platform-Gate). Vollstaendige Pydantic-Definitionen laut Doku;
`storage_target`/`ingest_recommended` sind hier bewusst als Klassen-Defaults
hinterlegt, nicht vom Aufrufer waehlbar (P4 — Speicherziel ist Code, kein
LLM-Entscheid).
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar, Literal

from pydantic import BaseModel, Field


class DataProduct(BaseModel):
    tenant_id: str
    produced_by: str
    workflow_run_id: str | None = None

    storage_target: ClassVar[list[str]] = ["G"]
    ingest_recommended: ClassVar[bool] = False


class OrgOffering(DataProduct):
    storage_target: ClassVar[list[str]] = ["G", "K"]

    offering_id: str
    name: str
    kind: Literal["training", "consulting", "product"]
    summary: str | None = None


class OrgOrganization(DataProduct):
    storage_target: ClassVar[list[str]] = ["G"]

    org_id: str
    name: str
    kind: Literal["customer", "partner", "university", "internal"]


class OrgPerson(DataProduct):
    storage_target: ClassVar[list[str]] = ["G"]

    person_id: str
    name: str
    role: str | None = None
    email: str | None = None


class OrgEngagement(DataProduct):
    storage_target: ClassVar[list[str]] = ["G", "K"]

    engagement_id: str
    title: str
    status: Literal["pipeline", "active", "closed"]
    org_ref: str | None = None
    offering_ref: str | None = None


class OrgMeeting(DataProduct):
    storage_target: ClassVar[list[str]] = ["G"]

    meeting_id: str
    title: str
    held_at: str
    attendee_refs: list[str] = Field(default_factory=list)
    source_ref: str | None = None
    about_refs: list[str] = Field(default_factory=list)


class OrgDecision(DataProduct):
    storage_target: ClassVar[list[str]] = ["G", "K"]

    decision_id: str
    title: str
    status: Literal["proposed", "active", "superseded"]
    decided_at: date | None = None
    summary: str
    meeting_ref: str | None = None
    about_refs: list[str] = Field(default_factory=list)
    supersedes_ref: str | None = None


class OrgPolicy(DataProduct):
    storage_target: ClassVar[list[str]] = ["G", "K"]

    policy_id: str
    title: str
    scope: str
    applies_to_refs: list[str] = Field(default_factory=list)


class OrgKnowledgeAsset(DataProduct):
    produced_by: str = "ingest-agent"
    storage_target: ClassVar[list[str]] = ["G", "K"]

    asset_id: str
    title: str
    path: str
    kind: str
    documents_refs: list[str] = Field(default_factory=list)
    # ingest_recommended ist bei KnowledgeAsset kein Klassen-Fixwert, sondern
    # haengt vom einzelnen Asset ab ("nur wenn published" — 09-COMPANY-BRAIN §4).
    published: bool = False
    # Beantwortet Abnahmefrage 5 (09-COMPANY-BRAIN §8): pro documents_ref-Ziel
    # (z.B. ein Offering) darf hoechstens ein Asset canonical=True sein.
    canonical: bool = False


class OrgClaim(DataProduct):
    produced_by: str = "memory-agent"
    storage_target: ClassVar[list[str]] = ["G"]

    claim_id: str
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: date | None = None
    valid_to: date | None = None
    asserts_from_ref: str | None = None
    supports_refs: list[str] = Field(default_factory=list)


# node_type-Praefix + external_id-Feld je DP-Klasse (§3.1 09-COMPANY-BRAIN.md)
NODE_TYPE_BY_CLASS: dict[type[DataProduct], tuple[str, str]] = {
    OrgOffering: ("org:Offering", "offering_id"),
    OrgOrganization: ("org:Organization", "org_id"),
    OrgPerson: ("org:Person", "person_id"),
    OrgEngagement: ("org:Engagement", "engagement_id"),
    OrgMeeting: ("org:Meeting", "meeting_id"),
    OrgDecision: ("org:Decision", "decision_id"),
    OrgPolicy: ("org:Policy", "policy_id"),
    OrgKnowledgeAsset: ("org:KnowledgeAsset", "asset_id"),
    OrgClaim: ("org:Claim", "claim_id"),
}

DP_CLASS_BY_NODE_TYPE: dict[str, type[DataProduct]] = {
    node_type: cls for cls, (node_type, _) in NODE_TYPE_BY_CLASS.items()
}
