"""core/orchestrator/releases.py — System Release & Audit History Registry."""

from typing import Any

PLATFORM_RELEASES: list[dict[str, Any]] = [
    {
        "version": "v1.0.0",
        "tag": "v1.0.0-core-appliance",
        "date": "2026-08-15",
        "title": "AI-OS Core Platform Appliance Initial Release",
        "description": "Erste offizielle Verteilung der autarken Core Platform Appliance mit 5-Layer Memory Modell und Docker Stack.",
        "changes": [
            "Autarkes Distributions-Projekt virgi-platform-dist",
            "5-Schichten-Memory-Modell (L1 Working Memory bis L5 Enterprise Core)",
            "Hybrid Graph-RAG mit Reciprocal Rank Fusion",
            "Unternehmensprofil-Verwaltung (/company) mit dynamischem Mandanten-Support",
            "Sovereign Multi-Stage Dockerfile & Docker Compose Setup",
            "CLI-Toolbox: search_company_brain, manage_memory, ingest_documents, manage_company_profile",
            "Plattform-Auditlog & Revisionssicherheit"
        ],
        "git_commit": "bd2a74c"
    }
]

def get_platform_releases() -> list[dict[str, Any]]:
    return PLATFORM_RELEASES
