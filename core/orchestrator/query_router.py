"""Query-Router (deterministisch, P4) — 09-COMPANY-BRAIN.md §12.1.

Entscheidet PRO FRAGE, welche Speicher-Schichten befragt werden, bevor
gesucht wird — Code, kein LLM. Verhindert Doppel-Suche (L1 + Graph fuer
"was gilt") und falsche Schicht (L1 statt Graph fuer Geltungsfragen).

Umsetzungsstand: `use_g`, `use_k_resolve`, `use_l1` werden von
`handlers/unified_search.py` tatsaechlich ausgewertet. `use_letta` und
`use_sk` sind im Plan bereits vorgesehen (Spec-Vollstaendigkeit), haben
aber noch keinen Verbraucher — Letta-Anbindung und Skill-Store sind noch
nicht gebaut (siehe docs/13-IST-STAND.md "Noch geplant").
"""

from __future__ import annotations

from pydantic import BaseModel


class SearchPlan(BaseModel):
    use_g: bool = False  # Knowledge Graph
    use_k_resolve: bool = False  # Datei nach Node-ID laden
    use_l1: bool = False  # Qdrant (content + raw-files)
    use_letta: bool = False  # Archival / Core — noch kein Verbraucher
    use_sk: bool = False  # Skills — noch kein Verbraucher
    use_a: bool = False  # Audit (Operator)
    max_l1: int = 5
    max_graph_nodes: int = 20
    hops: int = 2


# (Keyword-Set, Plan) — erste Regel, deren Keywords in der Frage vorkommen, gewinnt.
INTENT_RULES: list[tuple[set[str], SearchPlan]] = [
    (
        {"decision", "entscheidung", "gilt", "policy", "offering", "regel", "zuständig"},
        SearchPlan(use_g=True, use_k_resolve=True, use_l1=False, use_letta=False),
    ),
    (
        {"ähnlich", "wie blog", "recherche", "quellen"},
        SearchPlan(use_l1=True, use_g=True, use_sk=True, max_l1=5),
    ),
    (
        {"gestern", "letzte woche", "besprochen", "erinnerst"},
        SearchPlan(use_letta=True, use_g=False, use_l1=False),
    ),
    (
        {"wie haben wir", "skill", "ablauf", "verfahren"},
        SearchPlan(use_sk=True, use_g=False, use_l1=True, max_l1=3),
    ),
]

# Letta nur wenn Episodic-Keywords — nie Default-Hot-Path.
DEFAULT_PLAN = SearchPlan(use_g=True, use_l1=True, use_sk=True, max_l1=5)


def route_query(query: str) -> SearchPlan:
    lower = (query or "").strip().lower()
    if not lower:
        return DEFAULT_PLAN
    for keywords, plan in INTENT_RULES:
        if any(kw in lower for kw in keywords):
            return plan
    return DEFAULT_PLAN
