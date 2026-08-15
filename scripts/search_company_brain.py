#!/usr/bin/env python3
"""scripts/search_company_brain.py — CLI-Suche im 5-Layer Memory & Wissensgraphen."""

import sys
import os
import argparse
import httpx
import json

def search_company_brain(query: str, tenant_id: str = "default", orchestrator_url: str = "http://127.0.0.1:8091"):
    print(f"\n🔍 Suche im Unternehmenswissen für Mandant: '{tenant_id}'")
    print(f"🔎 Suchbegriff: '{query}'")
    print("=" * 60)
    
    url = f"{orchestrator_url}/v1/memory/search"
    payload = {
        "query": query,
        "tenant_id": tenant_id,
        "include_graph": True,
        "limit": 10
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(url, json=payload)
            if res.status_code != 200:
                print(f"❌ Fehler bei der Suche: HTTP {res.status_code} — {res.text}")
                sys.exit(1)
            
            data = res.json()
            results = data.get("results", [])
            print(f"✨ Gefundene Treffer: {len(results)}\n")
            
            for idx, item in enumerate(results, 1):
                title = item.get("title") or item.get("id") or "Dokument/Eintrag"
                source = item.get("source") or item.get("layer") or "Memory"
                snippet = item.get("content") or item.get("snippet") or item.get("text") or ""
                score = item.get("score", 0.0)
                
                print(f"[{idx}] {title} (Quelle: {source} | Score: {score:.2f})")
                if snippet:
                    print(f"    {snippet[:200]}...")
                print("-" * 60)
                
    except Exception as e:
        print(f"❌ Verbindungsfehler zu Orchestrator ({orchestrator_url}): {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI-OS Company Brain Knowledge Search")
    parser.add_argument("query", help="Suchbegriff oder Frage an das Unternehmenswissen")
    parser.add_argument("--tenant", default="default", help="Mandanten-ID (Standard: default)")
    parser.add_argument("--url", default=os.getenv("ORCHESTRATOR_URL", "http://127.0.0.1:8091"), help="Orchestrator URL")
    
    args = parser.parse_args()
    search_company_brain(args.query, args.tenant, args.url)

if __name__ == "__main__":
    main()
