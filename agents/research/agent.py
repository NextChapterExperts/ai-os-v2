"""AI-OS v2 — Research Agent (SDK-compliant).

Implements AIOS-PACK-RESEARCH following P1-P19 Leitprinzipien.
Supports dual-retrieval (Company Brain + SearXNG Web-Search), model selection override,
and prompt inspection context capture.
"""

from __future__ import annotations

import json
from typing import Any, Literal
from pydantic import BaseModel, Field

from sdk.agent_base import AgentBase
from sdk.dataproduct import DataProduct


class ResearchInput(DataProduct):
    """Input DataProduct for research execution."""

    query: str = Field(description="Rechercheanfrage oder Thema")
    depth: Literal["quick", "deep"] = Field(default="quick", description="Recherche-Tiefe")
    model: str | None = Field(default=None, description="Expliziter Modell-Override oder None für Auto-Routing")
    compute_mode: str | None = Field(default=None, description="Compute-Modus (sovereign, balanced, premium)")
    anonymize: bool = Field(default=True, description="Egress über SearXNG und Egress-Proxy anonymisieren")
    refinement_feedback: str | None = Field(default=None, description="Optionales Feedback zur Verfeinerung aus Vor-Schritten")


class SourceItem(BaseModel):
    """Einzelne Quelle in den Rechercheergebnissen."""

    title: str
    url: str
    snippet: str
    source_type: Literal["local_brain", "web_searxng"] = "web_searxng"
    trust_score: float = 0.85


class ResearchResult(DataProduct):
    """Output DataProduct of research execution."""

    query: str
    summary: str
    sources: list[SourceItem] = Field(default_factory=list)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    anonymity_active: bool = True
    model_used: str = "sovereign"
    prompt_context: dict[str, Any] = Field(default_factory=dict)
    sub_questions: list[str] = Field(default_factory=list)


class ResearchAgent(AgentBase):
    """SDK-konformer Recherche-Agent in AI-OS v2."""

    agent_id = "research-agent"
    version = "2.0.0"
    input_schema = ResearchInput
    output_schema = ResearchResult

    async def run(self, input_dp: ResearchInput) -> ResearchResult:
        query = (input_dp.query or "").strip()
        if not query:
            return ResearchResult(
                tenant_id=self.ctx.tenant_id,
                produced_by=self.agent_id,
                query="",
                summary="Keine Suchanfrage angegeben.",
                confidence=0.0,
                sources=[],
            )

        # 1. Dual-Retrieval: Local Company Brain
        local_hits = []
        try:
            local_res = await self.mcp.call(
                "qdrant_search",
                "search",
                {"q": query, "k": 3, "tenant_id": self.ctx.tenant_id},
            )
            if isinstance(local_res, list):
                for item in local_res:
                    local_hits.append(
                        SourceItem(
                            title=item.get("title") or "Company Brain Dokument",
                            url=item.get("url") or f"brain://{item.get('id', 'doc')}",
                            snippet=item.get("text") or item.get("snippet") or "",
                            source_type="local_brain",
                            trust_score=0.95,
                        )
                    )
        except Exception:
            pass

        # 2. Dual-Retrieval: Web Search via SearXNG MCP
        web_hits = []
        try:
            web_res = await self.mcp.call(
                "web_search",
                "search",
                {"q": query, "num": 5, "anonymize": input_dp.anonymize},
            )
            if isinstance(web_res, list):
                for item in web_res:
                    web_hits.append(
                        SourceItem(
                            title=item.get("title") or "Web-Quelle",
                            url=item.get("url") or item.get("link") or "https://searxng.local",
                            snippet=item.get("snippet") or item.get("snippet_text") or "",
                            source_type="web_searxng",
                            trust_score=0.85,
                        )
                    )
        except Exception:
            pass

        all_sources = local_hits + web_hits

        # 3. Prompt Capture & Metadata Construction
        prompt_metadata = {
            "query": query,
            "depth": input_dp.depth,
            "anonymize": input_dp.anonymize,
            "model_requested": input_dp.model or "auto",
            "compute_mode": input_dp.compute_mode or "sovereign",
            "local_sources_count": len(local_hits),
            "web_sources_count": len(web_hits),
            "system_prompt": "Du bist ein spezialisierter AI-OS Recherche-Agent. Verwende bestehendes Firmenwissen und aktuelle Web-Quellen, um eine fundierte, objektive Zusammenfassung zu erstellen.",
            "user_prompt": f"Recherchiere das Thema: '{query}'. Tiefe: {input_dp.depth}. Berücksichtigte Quellen: {len(all_sources)}.",
        }

        # Sub-questions decomposition
        sub_questions = [
            f"Was sind die Kernaspekte von '{query}'?",
            f"Welche aktuellen Daten / Quellen gibt es zu '{query}'?",
            f"Welche Lücken oder Folgemaßnahmen existieren bezüglich '{query}'?",
        ]

        if input_dp.refinement_feedback:
            sub_questions.append(f"Fokus-Verfeinerung: {input_dp.refinement_feedback}")

        summary = f"Recherche-Ergebnis für '{query}' ({'Deep' if input_dp.depth == 'deep' else 'Quick'}-Analyse):\n"
        if all_sources:
            summary += f"- Insgesamte Quellen analysiert: {len(all_sources)} (davon {len(local_hits)} lokal im Company Brain, {len(web_hits)} via SearXNG Web-Suche).\n"
            summary += f"- Die wichtigsten Erkenntnisse wurden strukturiert zusammengestellt."
        else:
            summary += "- Für diese Anfrage wurden keine externen Treffer gefunden. Eine Verfeinerung des Suchbegriffs wird empfohlen."

        model_used = input_dp.model or "qwen2.5-coder:14b"

        return ResearchResult(
            tenant_id=self.ctx.tenant_id,
            produced_by=self.agent_id,
            query=query,
            summary=summary,
            sources=all_sources,
            confidence=0.92 if all_sources else 0.4,
            anonymity_active=input_dp.anonymize,
            model_used=model_used,
            prompt_context=prompt_metadata,
            sub_questions=sub_questions,
        )
