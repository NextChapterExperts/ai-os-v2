"""Google-Kalender-Teilnehmerlisten → strukturierte Personen (E-Mail, Name, Domain)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", re.UNICODE)

FREE_EMAIL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "outlook.com",
        "hotmail.com",
        "live.com",
        "yahoo.com",
        "yahoo.de",
        "icloud.com",
        "me.com",
        "gmx.de",
        "gmx.net",
        "web.de",
        "t-online.de",
        "proton.me",
        "protonmail.com",
        "aol.com",
        "mail.de",
    }
)


@dataclass
class ParsedParticipant:
    email: str
    name: str
    domain: str
    person_id: str
    org_id: str | None = None
    org_name: str | None = None
    company_website: str | None = None
    linkedin_url: str | None = None
    role: str | None = None
    status: str = "new"  # new | existing | updated
    existing_node_id: str | None = None
    notes: str = field(default_factory=str)

    def to_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "name": self.name,
            "domain": self.domain,
            "person_id": self.person_id,
            "org_id": self.org_id,
            "org_name": self.org_name,
            "company_website": self.company_website,
            "linkedin_url": self.linkedin_url,
            "role": self.role,
            "status": self.status,
            "existing_node_id": self.existing_node_id,
            "notes": self.notes,
        }


def _slugify(value: str) -> str:
    s = value.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def person_id_from_email(email: str) -> str:
    local = email.split("@", 1)[0]
    return f"person:{_slugify(local)}"


def org_id_from_domain(domain: str) -> str:
    return f"org:{_slugify(domain.replace('.', '-'))}"


def org_name_from_domain(domain: str) -> str:
    stem = domain.split(".", 1)[0]
    if stem in {"mail", "smtp", "corp", "group"} and "." in domain:
        stem = domain.split(".")[0]
    return stem.replace("-", " ").title()


def _name_from_local_part(local: str) -> str:
    local = local.replace(".", " ").replace("_", " ").replace("-", " ")
    parts = [p for p in local.split() if p and not p.isdigit()]
    if not parts:
        return local
    return " ".join(p.capitalize() for p in parts)


def _name_before_email(line: str, email: str) -> str | None:
    idx = line.lower().find(email.lower())
    if idx <= 0:
        return None
    prefix = line[:idx].strip(" \t•-*—–|,;:")
    prefix = re.sub(r"\([^)]*$", "", prefix).strip()
    if not prefix or "@" in prefix:
        return None
    if len(prefix) > 80:
        return None
    return prefix


def _extract_name_for_email(line: str, email: str) -> str:
    angle = re.match(r"^(.+?)\s*<" + re.escape(email) + r">\s*$", line, re.I)
    if angle:
        return angle.group(1).strip().strip('"').strip("'")

    paren = re.match(r"^(.+?)\s*\(" + re.escape(email) + r"\)\s*$", line, re.I)
    if paren:
        return paren.group(1).strip()

    before = _name_before_email(line, email)
    if before:
        return before

    local = email.split("@", 1)[0]
    return _name_from_local_part(local)


def parse_participant_list(raw: str) -> list[ParsedParticipant]:
    """Extrahiert E-Mails aus Google-Kalender-/Meet-Kopien (mehrzeilig, gemischt)."""
    if not raw or not raw.strip():
        return []

    seen: set[str] = set()
    out: list[ParsedParticipant] = []

    for line in raw.replace(";", "\n").splitlines():
        line = line.strip()
        if not line:
            continue
        for match in EMAIL_RE.finditer(line):
            email = match.group(0).lower()
            if email in seen:
                continue
            seen.add(email)

            domain = email.split("@", 1)[1]
            name = _extract_name_for_email(line, email)
            org_id = None
            org_name = None
            if domain not in FREE_EMAIL_DOMAINS:
                org_id = org_id_from_domain(domain)
                org_name = org_name_from_domain(domain)

            out.append(
                ParsedParticipant(
                    email=email,
                    name=name,
                    domain=domain,
                    person_id=person_id_from_email(email),
                    org_id=org_id,
                    org_name=org_name,
                )
            )

    return out
