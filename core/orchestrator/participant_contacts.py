"""Teilnehmer → Kontakte (Graph): Lookup, Web-Anreicherung, DP-Commit."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote, unquote

import httpx

from .dataproducts import OrgOrganization, OrgPerson
from .dp_service import commit_dataproduct
from .kg_search import lookup_person_by_email
from .participant_parse import ParsedParticipant, parse_participant_list

log = logging.getLogger("orchestrator.participant_contacts")

LINKEDIN_RE = re.compile(r"https?://(?:[\w.-]+\.)?linkedin\.com/in/[\w%-]+/?", re.I)
DUCK_TIMEOUT = 8.0
WEB_TIMEOUT = 5.0


def _merge_person_fields(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, val in incoming.items():
        if val is None or val == "":
            continue
        if not merged.get(key):
            merged[key] = val
    return merged


async def _probe_website(domain: str) -> str | None:
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}"
        try:
            async with httpx.AsyncClient(
                timeout=WEB_TIMEOUT, follow_redirects=True, headers={"User-Agent": "AI-OS/1.0"}
            ) as client:
                res = await client.head(url)
                if res.status_code < 400:
                    return f"{res.url.scheme}://{res.url.host}"
        except httpx.HTTPError:
            continue
    return f"https://{domain}"


async def _find_linkedin(name: str, org_name: str | None) -> str | None:
    parts = [f'"{name}"', "site:linkedin.com/in"]
    if org_name:
        parts.append(org_name)
    query = " ".join(parts)
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    try:
        async with httpx.AsyncClient(
            timeout=DUCK_TIMEOUT, follow_redirects=True, headers={"User-Agent": "AI-OS/1.0"}
        ) as client:
            res = await client.get(url)
            res.raise_for_status()
            for match in LINKEDIN_RE.finditer(res.text):
                link = unquote(match.group(0).rstrip("/"))
                if "/in/" in link.lower():
                    return link
    except httpx.HTTPError as exc:
        log.debug("LinkedIn-Suche fehlgeschlagen für %s: %s", name, exc)
    return None


async def enrich_participants(
    participants: list[ParsedParticipant],
    *,
    find_linkedin: bool = True,
    probe_websites: bool = True,
) -> list[ParsedParticipant]:
    async def enrich_one(p: ParsedParticipant) -> ParsedParticipant:
        notes: list[str] = []
        if probe_websites and p.org_id and p.domain:
            website = await _probe_website(p.domain)
            if website:
                p.company_website = website
                notes.append(f"Website: {website}")
        if find_linkedin and p.name:
            linkedin = await _find_linkedin(p.name, p.org_name)
            if linkedin:
                p.linkedin_url = linkedin
                notes.append(f"LinkedIn: {linkedin}")
        if notes:
            p.notes = "; ".join(notes)
        return p

    return list(await asyncio.gather(*(enrich_one(p) for p in participants)))


def attach_existing_status(tenant_id: str, participants: list[ParsedParticipant]) -> None:
    for p in participants:
        hit = lookup_person_by_email(tenant_id, p.email)
        if hit is None:
            p.status = "new"
            continue
        p.status = "existing"
        p.existing_node_id = hit["id"]
        payload = hit.get("payload") or {}
        if payload.get("name"):
            p.name = str(payload["name"])
        if payload.get("role"):
            p.role = str(payload["role"])
        if payload.get("linkedin_url"):
            p.linkedin_url = str(payload["linkedin_url"])
        if payload.get("company_website"):
            p.company_website = str(payload["company_website"])
        if payload.get("org_ref"):
            p.org_id = str(payload["org_ref"])


def build_summary(participants: list[ParsedParticipant]) -> str:
    if not participants:
        return "Keine E-Mail-Adressen erkannt."
    lines = [f"{len(participants)} Teilnehmer erkannt:"]
    for p in participants:
        bits = [p.name, f"<{p.email}>"]
        if p.org_name:
            bits.append(f"({p.org_name})")
        if p.linkedin_url:
            bits.append(f"LinkedIn: {p.linkedin_url}")
        if p.company_website:
            bits.append(f"Web: {p.company_website}")
        bits.append(f"[{p.status}]")
        lines.append(" · ".join(bits))
    return "\n".join(lines)


async def process_participant_raw(
    tenant_id: str,
    raw: str,
    *,
    enrich: bool = False,
) -> dict[str, Any]:
    parsed = parse_participant_list(raw)
    attach_existing_status(tenant_id, parsed)
    if enrich and parsed:
        parsed = await enrich_participants(parsed)
    return {
        "participants": [p.to_dict() for p in parsed],
        "summary": build_summary(parsed),
        "count": len(parsed),
    }


def commit_participants(
    tenant_id: str,
    items: list[dict[str, Any]],
    *,
    produced_by: str = "meetings-panel",
    workflow_run_id: str | None = None,
) -> dict[str, Any]:
    orgs_done: set[str] = set()
    persons: list[dict[str, Any]] = []
    errors: list[str] = []

    for item in items:
        email = str(item.get("email") or "").lower().strip()
        if not email:
            continue
        name = str(item.get("name") or email.split("@")[0])
        person_id = str(item.get("person_id") or f"person:{email.split('@')[0]}")
        org_id = item.get("org_id")
        org_name = item.get("org_name")

        if org_id and org_id not in orgs_done:
            orgs_done.add(org_id)
            try:
                commit_dataproduct(
                    OrgOrganization(
                        tenant_id=tenant_id,
                        produced_by=produced_by,
                        workflow_run_id=workflow_run_id,
                        org_id=str(org_id),
                        name=str(org_name or org_id.replace("org:", "")),
                        kind="partner",
                        website=item.get("company_website"),
                    )
                )
            except Exception as exc:
                errors.append(f"Org {org_id}: {exc}")

        existing = lookup_person_by_email(tenant_id, email)
        payload_in = {
            "person_id": person_id,
            "name": name,
            "email": email,
            "role": item.get("role"),
            "linkedin_url": item.get("linkedin_url"),
            "company_website": item.get("company_website"),
            "org_ref": org_id,
        }
        if existing:
            payload_in = _merge_person_fields(existing.get("payload") or {}, payload_in)

        try:
            result = commit_dataproduct(
                OrgPerson(
                    tenant_id=tenant_id,
                    produced_by=produced_by,
                    workflow_run_id=workflow_run_id,
                    person_id=str(payload_in["person_id"]),
                    name=str(payload_in["name"]),
                    role=payload_in.get("role"),
                    email=str(payload_in.get("email") or email),
                    linkedin_url=payload_in.get("linkedin_url"),
                    company_website=payload_in.get("company_website"),
                    org_ref=payload_in.get("org_ref"),
                )
            )
            persons.append(
                {
                    "person_id": payload_in["person_id"],
                    "email": email,
                    "name": payload_in["name"],
                    "node_id": result.get("node_id"),
                    "status": "existing" if existing else "created",
                }
            )
        except Exception as exc:
            errors.append(f"{email}: {exc}")

    display = ", ".join(p["name"] for p in persons)
    participant_refs = [p["person_id"] for p in persons]
    return {
        "persons": persons,
        "participant_refs": participant_refs,
        "participants_display": display,
        "errors": errors,
    }


def participants_display_from_items(items: list[dict[str, Any]]) -> str:
    names: list[str] = []
    for item in items:
        name = str(item.get("name") or "").strip()
        email = str(item.get("email") or "").strip()
        if name:
            names.append(name)
        elif email:
            names.append(email)
    return ", ".join(names)
