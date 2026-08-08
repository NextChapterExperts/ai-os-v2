"""Projekt/Engagement aus Kalender-Titeln ableiten (deterministisch, kein LLM).

Sammelt Titel aus vergangenen + geplanten Terminen und erkennt Projekte über:
- Struktur im Titel ([Projekt], Projekt - Titel, Projekt/Titel, …)
- Abgleich mit Engagements/Offerings im Company Brain
- Wiederkehrende Präfixe über viele Titel (Häufigkeitsanalyse)
- Typische Meeting-Formulierungen („Austausch mit SAP BAIP …“)
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# Meeting-Typ-Wörter — kein Projektname, wenn der Rest nur aus diesen besteht
_MEETING_TYPE_WORDS = frozenset({
    "sync", "standup", "stand-up", "review", "retro", "retrospektive", "kickoff",
    "workshop", "call", "meeting", "termin", "austausch", "abstimmung", "weekly",
    "daily", "monthly", "check-in", "checkin", "update", "planung", "besprechung",
    "interview", "demo", "präsentation", "presentation", "fokus", "focus",
})

# Generische Titel ohne Projektbezug
_GENERIC_TITLES = frozenset({
    "privates treffen", "focus time", "block", "ooo", "out of office",
})


def parse_project_from_title(title: str) -> tuple[str, str]:
    """Strukturelle Erkennung: (projekt_label, anzeige_titel)."""
    t = (title or "").strip()
    if not t or t.lower() in _GENERIC_TITLES:
        return "", t

    bracket = re.match(r"^\[([^\]]{1,48})\]\s*(.*)$", t)
    if bracket:
        project = bracket.group(1).strip()
        rest = (bracket.group(2) or "").strip()
        return project, rest or t

    slash = re.match(r"^([^/|]{2,48})/([^/|]{2,80})$", t)
    if slash:
        left = slash.group(1).strip()
        right = slash.group(2).strip()
        if left and right and not _looks_like_meeting_type_only(left):
            return f"{left}/{right.split()[0]}" if " " in right else f"{left}/{right}", t

    for sep in (" — ", " – ", " - ", " | ", ": "):
        if sep in t:
            prefix, rest = t.split(sep, 1)
            prefix = prefix.strip()
            rest = rest.strip()
            if prefix and rest and len(prefix) <= 48 and not _looks_like_meeting_type_only(prefix):
                return prefix, rest

    mit = re.match(
        r"^(?:Austausch|Meeting|Call|Sync|Termin|Workshop)\s+(?:mit\s+)?(.+?)"
        r"(?:\s+(?:Abteilung|Team|Gruppe|Department))?\s*$",
        t,
        re.IGNORECASE,
    )
    if mit:
        subject = mit.group(1).strip()
        if subject and len(subject) >= 3:
            return _normalize_project_label(subject), t

    return "", t


def _looks_like_meeting_type_only(text: str) -> bool:
    words = re.findall(r"[a-zA-ZäöüÄÖÜß0-9]+", text.lower())
    if not words:
        return True
    return all(w in _MEETING_TYPE_WORDS or w.isdigit() for w in words)


def _normalize_project_label(label: str) -> str:
    s = re.sub(r"\s+", " ", label.strip())
    return s[:48]


def known_project_labels(
    engagements: list[dict[str, Any]] | None = None,
    offerings: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Bekannte Projekt-Labels aus Company Brain (längste zuerst für Substring-Match)."""
    labels: set[str] = set()
    for eng in engagements or []:
        title = str(eng.get("title") or "").strip()
        if not title:
            continue
        for part in re.split(r"[—–|:]", title):
            part = part.strip()
            if part and len(part) >= 3:
                labels.add(part)
        eid = str(eng.get("id") or "")
        if eid.startswith("eng-"):
            slug = eid[4:].replace("-", " ").title()
            if len(slug) >= 3:
                labels.add(slug)
    for off in offerings or []:
        title = str(off.get("title") or off.get("name") or "").strip()
        if title and len(title) >= 3:
            labels.add(title)
    return sorted(labels, key=lambda x: (-len(x), x.lower()))


def _prefix_candidates(titles: list[str], min_count: int = 2) -> list[str]:
    """Häufige Titel-Präfixe (z. B. „Launch Review“, „SAP BAIP“)."""
    counts: Counter[str] = Counter()
    for title in titles:
        t = (title or "").strip()
        if not t:
            continue
        words = t.split()
        for n in range(min(4, len(words)), 0, -1):
            prefix = " ".join(words[:n])
            if len(prefix) < 4 or _looks_like_meeting_type_only(prefix):
                continue
            counts[prefix] += 1
    return [p for p, c in counts.most_common() if c >= min_count]


def build_project_catalog(
    titles: list[str],
    *,
    engagements: list[dict[str, Any]] | None = None,
    offerings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Katalog aus allen Titeln (vergangen + geplant) aufbauen."""
    clean_titles = [str(t or "").strip() for t in titles if str(t or "").strip()]
    known = known_project_labels(engagements, offerings)
    prefixes = _prefix_candidates(clean_titles)
    structural: dict[str, str] = {}
    for title in clean_titles:
        project, _ = parse_project_from_title(title)
        if project:
            structural[title] = project
    return {
        "known": known,
        "prefixes": prefixes,
        "structural": structural,
        "titles": clean_titles,
    }


def resolve_project_from_title(
    title: str,
    catalog: dict[str, Any] | None = None,
    *,
    engagements: list[dict[str, Any]] | None = None,
    offerings: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """Beste Projekt-Zuordnung + Anzeige-Titel."""
    t = (title or "").strip()
    if not t:
        return "", t

    if catalog and t in catalog.get("structural", {}):
        project = catalog["structural"][t]
        _, display = parse_project_from_title(t)
        return project, display or t

    project, display = parse_project_from_title(t)
    if project:
        return project, display

    cat = catalog or build_project_catalog([t], engagements=engagements, offerings=offerings)
    tl = t.lower()

    for label in cat.get("known", known_project_labels(engagements, offerings)):
        if label.lower() in tl:
            return label, t

    for prefix in cat.get("prefixes", []):
        if t.lower().startswith(prefix.lower()) and len(prefix) >= 4:
            return prefix, t

    # Einzelwort-Projekt am Anfang: „Launch Review“ → Launch (wenn Launch in ≥2 Titeln)
    first = t.split()[0] if t.split() else ""
    if first and len(first) >= 4 and not _looks_like_meeting_type_only(first):
        all_titles = cat.get("titles", [t])
        if sum(1 for ot in all_titles if ot.lower().startswith(first.lower())) >= 2:
            return first, t

    return "", t


def extract_projects_from_titles(
    titles: list[str],
    *,
    engagements: list[dict[str, Any]] | None = None,
    offerings: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    """Alle Titel → {original_titel: projekt_label}."""
    catalog = build_project_catalog(titles, engagements=engagements, offerings=offerings)
    out: dict[str, str] = {}
    for title in catalog["titles"]:
        project, _ = resolve_project_from_title(title, catalog)
        if project:
            out[title] = project
    return out


def list_discovered_projects(
    titles: list[str],
    *,
    engagements: list[dict[str, Any]] | None = None,
    offerings: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Eindeutige Projekt-Labels aus einer Titelliste."""
    mapping = extract_projects_from_titles(titles, engagements=engagements, offerings=offerings)
    return sorted(set(mapping.values()), key=str.lower)


def match_engagement_ids(project: str, engagements: list[dict[str, Any]]) -> list[str]:
    if not project:
        return []
    needle = project.lower()
    matched: list[str] = []
    for eng in engagements:
        eid = str(eng.get("id") or "").strip()
        etitle = str(eng.get("title") or "").lower()
        if not eid:
            continue
        if needle in etitle or etitle.split("—")[0].strip() in needle or needle in etitle.split("—")[0].lower():
            matched.append(eid)
    return matched
