#!/usr/bin/env python3
"""scripts/manage_company_profile.py — CLI-Tool für Unternehmens-Profil & Identität."""

import sys
import os
import argparse
import httpx
import json
import yaml

def get_profile(tenant_id: str = "default", orchestrator_url: str = "http://127.0.0.1:8091"):
    url = f"{orchestrator_url}/v1/company/profile?tenant_id={tenant_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url)
            if res.status_code != 200:
                print(f"❌ Fehler beim Laden des Profils: HTTP {res.status_code}")
                sys.exit(1)
                
            data = res.json().get("profile", {})
            print(f"\n🏢 Unternehmensprofil für Mandant: '{tenant_id}'")
            print("=" * 60)
            print(yaml.dump(data, allow_unicode=True, default_flow_style=False))
            print("=" * 60)
    except Exception as e:
        print(f"❌ Fehler bei Verbindung zu Orchestrator: {e}")
        sys.exit(1)

def set_profile_from_file(file_path: str, tenant_id: str = "default", orchestrator_url: str = "http://127.0.0.1:8091"):
    p = os.path.expanduser(file_path)
    if not os.path.exists(p):
        print(f"❌ Datei nicht gefunden: {p}")
        sys.exit(1)
        
    with open(p, "r", encoding="utf-8") as f:
        if p.endswith(".json"):
            data = json.load(f)
        else:
            data = yaml.safe_load(f)
            
    url = f"{orchestrator_url}/v1/company/profile?tenant_id={tenant_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(url, json=data)
            if res.status_code == 200:
                print(f"✅ Profil für Mandant '{tenant_id}' erfolgreich aktualisiert!")
            else:
                print(f"❌ Speichern fehlgeschlagen: HTTP {res.status_code} — {res.text}")
    except Exception as e:
        print(f"❌ Fehler bei Verbindung zu Orchestrator: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI-OS Company Profile CLI")
    parser.add_argument("--tenant", default="default", help="Mandanten-ID (Standard: default)")
    parser.add_argument("--url", default=os.getenv("ORCHESTRATOR_URL", "http://127.0.0.1:8091"), help="Orchestrator URL")
    parser.add_argument("--show", action="store_true", help="Profil anzeigen")
    parser.add_argument("--update-from", help="Pfad zu YAML/JSON Datei mit neuem Profil")
    
    args = parser.parse_args()
    
    if args.update_from:
        set_profile_from_file(args.update_from, args.tenant, args.url)
    else:
        get_profile(args.tenant, args.url)

if __name__ == "__main__":
    main()
