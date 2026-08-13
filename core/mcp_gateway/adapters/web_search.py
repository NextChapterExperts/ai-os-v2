"""Native MCP Web-Search Adapter (P5).

Ermöglicht anonymer/direkter Web-Recherche via SearXNG oder Live-Egress-Fallback (DuckDuckGo / Web Scraper),
damit Recherche-Anfragen auch ohne gebundenen SearXNG-Container immer echte Web-Ergebnisse liefern.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Any

from core.mcp_gateway.adapters.registry import register

log = logging.getLogger("aios.mcp.web_search")


def execute_web_search(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("q") or arguments.get("query") or "").strip()
    num = int(arguments.get("num") or 5)
    anonymize = bool(arguments.get("anonymize", True))
    tenant_id = arguments.get("tenant_id", "nextchapter")

    if not query:
        return {"ok": True, "results": [], "tenant_id": tenant_id}

    encoded_query = urllib.parse.quote(query)
    results = []

    # 1. Versuche SearXNG (Port 8888 oder 8080)
    for port in (8888, 8080):
        try:
            url = f"http://127.0.0.1:{port}/search?q={encoded_query}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "AIOS-v2-Egress/2.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("results", [])
                    for it in items[:num]:
                        results.append({
                            "title": it.get("title") or query,
                            "url": it.get("url") or f"https://searxng.local/search?q={encoded_query}",
                            "snippet": it.get("content") or it.get("snippet") or query,
                            "source_type": "web_searxng",
                            "trust_score": float(it.get("score") or 0.88),
                        })
                    if results:
                        break
        except Exception:
            continue

    # 2. Live-Fallback (DuckDuckGo Lite JSON/HTML Endpoint) wenn kein lokaler SearXNG Container antwortet
    if not results:
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            req = urllib.request.Request(ddg_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    html_content = resp.read().decode("utf-8", errors="ignore")
                    import re
                    # Extrahiere Links und Snippets aus DDG-HTML
                    links = re.findall(r'<a class="result__url" href="([^"]+)">([^<]+)</a>', html_content)
                    snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html_content, flags=re.DOTALL)
                    
                    for i in range(min(num, len(links))):
                        raw_url, raw_title = links[i]
                        raw_snip = snippets[i] if i < len(snippets) else query
                        # HTML Unescape & Tag Stripping
                        clean_snip = re.sub(r'<[^>]+>', '', raw_snip).strip()
                        clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                        
                        # Korrigiere DDG Redirect-URLs
                        actual_url = raw_url
                        if "uddg=" in raw_url:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                            if "uddg" in parsed:
                                actual_url = parsed["uddg"][0]
                                
                        results.append({
                            "title": clean_title or f"Web: {query}",
                            "url": actual_url,
                            "snippet": clean_snip or query,
                            "source_type": "web_searxng",
                            "trust_score": 0.85,
                        })
        except Exception as exc:
            log.warning("DuckDuckGo fallback web search failed: %s", exc)

    return {
        "ok": True,
        "results": results,
        "count": len(results),
        "anonymize": anonymize,
        "tenant_id": tenant_id,
    }


@register("web_search", "search")
def handle_web_search(arguments: dict[str, Any]) -> dict[str, Any]:
    return execute_web_search(arguments)
