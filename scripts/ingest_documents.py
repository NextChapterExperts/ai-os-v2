#!/usr/bin/env python3
"""scripts/ingest_documents.py — Automatisierter Ingestion Runner für Dokumente, Verträge & PDFs."""

import sys
import os
import argparse
import httpx
from pathlib import Path

def ingest_file(file_path: str, tenant_id: str = "default", orchestrator_url: str = "http://127.0.0.1:8091"):
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        print(f"❌ Datei nicht gefunden: {file_path}")
        return False
        
    print(f"📄 Ingestiere Datei: {p.name} ({p.stat().st_size} Bytes) für Mandant '{tenant_id}'...")
    url = f"{orchestrator_url}/v1/ingest/file"
    
    try:
        with open(p, "rb") as f:
            files = {"file": (p.name, f, "application/octet-stream")}
            data = {"tenant_id": tenant_id}
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, files=files, data=data)
                if res.status_code == 200:
                    res_json = res.json()
                    chunks = res_json.get("chunks_created", res_json.get("chunks", 1))
                    print(f"✅ Erfolgreich verarbeitet: {chunks} semantische Chunks in L3/L4 Memory integriert.")
                    return True
                else:
                    print(f"❌ Ingestion fehlgeschlagen: HTTP {res.status_code} — {res.text}")
                    return False
    except Exception as e:
        print(f"❌ Fehler bei Ingestion: {e}")
        return False

def ingest_directory(dir_path: str, tenant_id: str = "default", orchestrator_url: str = "http://127.0.0.1:8091"):
    p = Path(dir_path)
    if not p.exists() or not p.is_dir():
        print(f"❌ Verzeichnis nicht gefunden: {dir_path}")
        sys.exit(1)
        
    valid_exts = {".pdf", ".md", ".txt", ".json", ".csv", ".docx"}
    files = [f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in valid_exts]
    
    print(f"\n📂 Starte Batch-Ingestion für Verzeichnis: {dir_path}")
    print(f"📊 Gefundene Dokumente: {len(files)}")
    print("=" * 60)
    
    success_count = 0
    for f in files:
        if ingest_file(str(f), tenant_id, orchestrator_url):
            success_count += 1
            
    print("=" * 60)
    print(f"✨ Abgeschlossen: {success_count}/{len(files)} Dokumente erfolgreich im Company Brain indexiert.\n")

def main():
    parser = argparse.ArgumentParser(description="AI-OS Document Ingestion Runner")
    parser.add_argument("path", help="Pfad zu einer Datei oder einem Ordner für den Ingest")
    parser.add_argument("--tenant", default="default", help="Mandanten-ID (Standard: default)")
    parser.add_argument("--url", default=os.getenv("ORCHESTRATOR_URL", "http://127.0.0.1:8091"), help="Orchestrator URL")
    
    args = parser.parse_args()
    
    target = Path(args.path)
    if target.is_dir():
        ingest_directory(str(target), args.tenant, args.url)
    else:
        ingest_file(str(target), args.tenant, args.url)

if __name__ == "__main__":
    main()
