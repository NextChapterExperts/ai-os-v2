"""Google Cloud Platform (GCP) Compute Engine VM Management für AI-OS v2 Appliance.

Verwaltet das automatisierte Erstellen, Auflisten, Stoppen und Löschen
von dedizierten Kunden-VMs in Google Cloud (z.B. Frankfurt europe-west3).
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("gcp_vm_manager")

GCLOUD_BIN = os.environ.get("GCLOUD_BIN", "/home/peter/.local/share/google-cloud-sdk/bin/gcloud")
DEFAULT_PROJECT = os.environ.get("GCP_PROJECT", "strong-zephyr-505611-k4")
DEFAULT_ZONE = os.environ.get("GCP_ZONE", "europe-west3-a")
DEFAULT_MACHINE_TYPE = os.environ.get("GCP_MACHINE_TYPE", "e2-standard-4")


def _run_gcloud(args: list[str]) -> dict[str, Any] | list[Any] | str:
    """Führt einen gcloud-Befehl aus und gibt das JSON-Ergebnis zurück."""
    env = os.environ.copy()
    sdk_bin_dir = Path(GCLOUD_BIN).parent
    env["PATH"] = f"{sdk_bin_dir}:{env.get('PATH', '')}"

    cmd = [GCLOUD_BIN] + args
    log.info("Running gcloud command: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        log.error("gcloud error (code %d): %s", res.returncode, res.stderr)
        raise RuntimeError(f"gcloud Fehler: {res.stderr.strip() or res.stdout.strip()}")

    output = res.stdout.strip()
    if not output:
        return {}
    try:
        return json.loads(output)
    except Exception:
        return output


def list_customer_vms(project: str = DEFAULT_PROJECT) -> list[dict[str, Any]]:
    """Gibt alle laufenden und gestoppten Kunden-VMs im Projekt zurück."""
    try:
        raw = _run_gcloud(["compute", "instances", "list", f"--project={project}", "--format=json"])
        if isinstance(raw, list):
            vms = []
            for item in raw:
                # Extrahiere relevante Felder
                name = item.get("name", "")
                zone = item.get("zone", "").split("/")[-1]
                status = item.get("status", "UNKNOWN")
                machine_type = item.get("machineType", "").split("/")[-1]
                nat_ip = "—"
                for iface in item.get("networkInterfaces", []):
                    for access in iface.get("accessConfigs", []):
                        if "natIP" in access:
                            nat_ip = access["natIP"]
                labels = item.get("labels", {})
                vms.append({
                    "name": name,
                    "zone": zone,
                    "status": status,
                    "machine_type": machine_type,
                    "ip_address": nat_ip,
                    "console_url": f"http://{nat_ip}:8090" if nat_ip != "—" else None,
                    "tenant_id": labels.get("aios_tenant", name.replace("aios-", "")),
                    "created_at": item.get("creationTimestamp", ""),
                })
            return vms
        return []
    except Exception as exc:
        log.warning("Konnte VMs nicht auflisten: %s", exc)
        return []


def create_customer_vm(
    tenant_id: str,
    company_name: str,
    admin_email: str,
    *,
    project: str = DEFAULT_PROJECT,
    zone: str = DEFAULT_ZONE,
    machine_type: str = DEFAULT_MACHINE_TYPE,
) -> dict[str, Any]:
    """Erstellt eine neue, isolierte Kunden-VM in Google Cloud."""
    sanitized_tenant = re.sub(r"[^a-z0-9\-]", "", tenant_id.lower().replace("_", "-"))
    instance_name = f"aios-{sanitized_tenant}"

    # Startup-Script für automatische Zero-Touch Installation
    startup_script = f"""#!/bin/bash
set -e
echo "🚀 Initialisiere AI-OS v2 Kunden-VM für {company_name} ({tenant_id})..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get update && apt-get install -y git curl docker.io docker-compose python3 python3-venv nodejs

# AI-OS v2 Repository klonen
mkdir -p /opt
if [ ! -d "/opt/ai-os-v2" ]; then
  git clone https://github.com/NextChapterExperts/ai-os-v2.git /opt/ai-os-v2
fi

# Console Web installieren & starten
cd /opt/ai-os-v2/core/console-web
npm install --legacy-peer-deps
nohup ./node_modules/.bin/next dev -p 8090 -H 0.0.0.0 > /tmp/console.log 2>&1 &

echo "✅ System-Setup abgeschlossen für {company_name}!"
"""

    args = [
        "compute",
        "instances",
        "create",
        instance_name,
        f"--project={project}",
        f"--zone={zone}",
        f"--machine-type={machine_type}",
        "--image-family=ubuntu-2404-lts-amd64",
        "--image-project=ubuntu-os-cloud",
        "--boot-disk-size=50GB",
        "--boot-disk-type=pd-balanced",
        f"--labels=aios_tenant={sanitized_tenant},env=production",
        f"--metadata=startup-script={startup_script},company-name={company_name},admin-email={admin_email}",
        "--tags=http-server,https-server,aios-console",
        "--format=json",
    ]

    raw = _run_gcloud(args)
    log.info("VM '%s' erfolgreich in GCP erstellt: %s", instance_name, raw)

    # Firewall Rule für Port 8090/8091 sicherstellen
    try:
        _run_gcloud([
            "compute",
            "firewall-rules",
            "create",
            "allow-aios-console",
            f"--project={project}",
            "--allow=tcp:8090,tcp:8091,tcp:80,tcp:443",
            "--source-ranges=0.0.0.0/0",
            "--description=Allow global access to AI-OS Console and Orchestrator",
        ])
    except Exception:
        pass

    # Status der frisch erstellten VM abrufen
    vms = list_customer_vms(project)
    matched = next((v for v in vms if v["name"] == instance_name), None)

    return {
        "status": "created",
        "instance_name": instance_name,
        "tenant_id": tenant_id,
        "company_name": company_name,
        "zone": zone,
        "machine_type": machine_type,
        "ip_address": matched["ip_address"] if matched else "pending",
        "console_url": matched["console_url"] if matched else None,
    }


def start_customer_vm(instance_name: str, zone: str = DEFAULT_ZONE, project: str = DEFAULT_PROJECT) -> dict[str, Any]:
    """Startet eine pausierte Kunden-VM wieder auf."""
    _run_gcloud(["compute", "instances", "start", instance_name, f"--project={project}", f"--zone={zone}"])
    return {"status": "started", "instance_name": instance_name}


def stop_customer_vm(instance_name: str, zone: str = DEFAULT_ZONE, project: str = DEFAULT_PROJECT) -> dict[str, Any]:
    """Stoppt eine Kunden-VM, um Rechenkosten einzusparen (0 € Compute-Kosten während Pause)."""
    _run_gcloud(["compute", "instances", "stop", instance_name, f"--project={project}", f"--zone={zone}"])
    return {"status": "stopped", "instance_name": instance_name}


def delete_customer_vm(instance_name: str, zone: str = DEFAULT_ZONE, project: str = DEFAULT_PROJECT) -> dict[str, Any]:
    """Löscht eine Kunden-VM vollständig aus Google Cloud."""
    _run_gcloud(["compute", "instances", "delete", instance_name, f"--project={project}", f"--zone={zone}", "--quiet"])
    return {"status": "deleted", "instance_name": instance_name}

