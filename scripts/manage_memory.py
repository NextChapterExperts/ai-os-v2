#!/usr/bin/env python3
"""scripts/manage_memory.py — CLI-Tool für Memory-Storage, L1-L5 Schichten & Health."""

import sys
import os
import argparse
import httpx
import json

def fmt_bytes(b: int) -> str:
    if b >= 1024 ** 3:
        return f"{b / (1024 ** 3):.2f} GB"
    if b >= 1024 ** 2:
        return f"{b / (1024 ** 2):.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b} B"

def show_storage_status(orchestrator_url: str = "http://127.0.0.1:8091"):
    print("\n🧠 AI-OS 5-Layer Memory Storage Status")
    print("=" * 65)
    
    url = f"{orchestrator_url}/v1/memory/storage"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url)
            if res.status_code != 200:
                print(f"❌ Fehler beim Abfragen des Speichers: HTTP {res.status_code}")
                sys.exit(1)
            
            data = res.json()
            vm = data.get("vm", {})
            total = vm.get("totalBytes", 0)
            used = vm.get("usedBytes", 0)
            free = vm.get("freeBytes", 0)
            percent = vm.get("usedPercent", 0.0)
            
            print(f"🖥️  System-Festplatte:")
            print(f"   Gesamt:    {fmt_bytes(total)}")
            print(f"   Belegt:    {fmt_bytes(used)} ({percent:.1f}%)")
            print(f"   Frei:      {fmt_bytes(free)}")
            print("-" * 65)
            
            stacks = data.get("stacks", [])
            print(f"📚 Memory-Schichten (Stacks):")
            for s in stacks:
                label = s.get("label", s.get("id", "Unbekannt"))
                bytes_cnt = s.get("bytes", 0)
                detail = s.get("detail", "")
                print(f"   • {label:<25} : {fmt_bytes(bytes_cnt):>10}  ({detail})")
                
            total_memory = data.get("memoryStacksTotalBytes", 0)
            print("-" * 65)
            print(f"✨ Gesamtes AI-OS Gedächtnisvolumen: {fmt_bytes(total_memory)}\n")
            
    except Exception as e:
        print(f"❌ Verbindungsfehler zu Orchestrator ({orchestrator_url}): {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI-OS Memory Storage Manager")
    parser.add_argument("--url", default=os.getenv("ORCHESTRATOR_URL", "http://127.0.0.1:8091"), help="Orchestrator URL")
    parser.add_argument("--status", action="store_true", default=True, help="Zeige aktuellen Speicherstatus")
    
    args = parser.parse_args()
    show_storage_status(args.url)

if __name__ == "__main__":
    main()
