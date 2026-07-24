"""Calendar MCP stub — merges with seed meetings_today when empty."""

from __future__ import annotations

from typing import Any

from ..brain_store import meetings_today


async def list_today(tenant_id: str) -> dict[str, Any]:
    seeded = meetings_today()
    return {
        "status": "stub" if not seeded else "seed",
        "status_note": (
            "Calendar-MCP Stub — nutzt Seed `meetings_today` "
            "bis MCP calendar angebunden ist."
        ),
        "meetings": seeded,
        "tenant_id": tenant_id,
    }
