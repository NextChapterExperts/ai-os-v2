"""Tests für Projekt-Erkennung aus Kalender-Titeln."""

from core.google.meetings.project_parse import (
    extract_projects_from_titles,
    list_discovered_projects,
    match_engagement_ids,
    parse_project_from_title,
    resolve_project_from_title,
)


def test_parse_project_bracket():
    project, title = parse_project_from_title("[Launchpad] Weekly Sync")
    assert project == "Launchpad"
    assert title == "Weekly Sync"


def test_parse_project_dash():
    project, title = parse_project_from_title("Launchpad - Kundenreview")
    assert project == "Launchpad"
    assert title == "Kundenreview"


def test_parse_project_colon():
    project, title = parse_project_from_title("AI-OS v2: Architektur-Review")
    assert project == "AI-OS v2"
    assert title == "Architektur-Review"


def test_parse_project_slash():
    project, _ = parse_project_from_title("PBD/RedRays")
    assert "PBD" in project


def test_parse_austausch_mit():
    project, _ = parse_project_from_title("Austausch mit SAP BAIP Abteilung")
    assert "SAP BAIP" in project


def test_parse_no_project():
    project, title = parse_project_from_title("Allgemeines Standup")
    assert project == ""
    assert title == "Allgemeines Standup"


def test_match_engagement_by_project_name():
    engagements = [{"id": "eng-x", "title": "Launchpad — MVP Phase"}]
    assert match_engagement_ids("Launchpad", engagements) == ["eng-x"]


def test_batch_extract_sync_titles():
    titles = [
        "Sync 1",
        "Sync 2",
        "Sync 3",
        "Launch Review",
        "SAP BAIP Austausch",
        "Austausch mit SAP BAIP Abteilung",
        "Prototyp KI SAP Lizenzen",
        "[Launchpad] Weekly",
        "Launchpad - Roadmap",
    ]
    mapping = extract_projects_from_titles(titles)
    assert mapping.get("Austausch mit SAP BAIP Abteilung") == "SAP BAIP"
    assert mapping.get("[Launchpad] Weekly") == "Launchpad"
    assert mapping.get("Launchpad - Roadmap") == "Launchpad"
    discovered = list_discovered_projects(titles)
    assert "SAP BAIP" in discovered
    assert "Launchpad" in discovered


def test_resolve_launch_prefix_cluster():
    titles = ["Launch Review", "Launch Planning", "Launch Demo"]
    from core.google.meetings.project_parse import build_project_catalog

    catalog = build_project_catalog(titles)
    project, _ = resolve_project_from_title("Launch Review", catalog)
    assert project == "Launch"
