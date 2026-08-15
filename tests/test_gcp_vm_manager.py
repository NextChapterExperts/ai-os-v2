"""Tests für GCP VM Management & Appliance Provisioning."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.gcp_vm_manager import (
    list_customer_vms,
    create_customer_vm,
    stop_customer_vm,
    delete_customer_vm,
)
from core.orchestrator.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_customer_vms_empty(monkeypatch):
    monkeypatch.setattr("core.orchestrator.gcp_vm_manager._run_gcloud", lambda args: [])
    vms = list_customer_vms("strong-zephyr-505611-k4")
    assert isinstance(vms, list)
    assert len(vms) == 0


def test_list_customer_vms_with_instances(monkeypatch):
    mock_data = [
        {
            "name": "aios-kanzlei-schmidt",
            "zone": "projects/strong-zephyr-505611-k4/zones/europe-west3-a",
            "status": "RUNNING",
            "machineType": "projects/strong-zephyr-505611-k4/machineTypes/e2-standard-4",
            "networkInterfaces": [
                {
                    "accessConfigs": [{"natIP": "34.141.123.45"}]
                }
            ],
            "labels": {"aios_tenant": "kanzlei_schmidt"},
            "creationTimestamp": "2026-08-15T12:00:00Z",
        }
    ]
    monkeypatch.setattr("core.orchestrator.gcp_vm_manager._run_gcloud", lambda args: mock_data)
    vms = list_customer_vms("strong-zephyr-505611-k4")
    assert len(vms) == 1
    assert vms[0]["name"] == "aios-kanzlei-schmidt"
    assert vms[0]["ip_address"] == "34.141.123.45"
    assert vms[0]["console_url"] == "http://34.141.123.45:8090"
    assert vms[0]["status"] == "RUNNING"


def test_gcp_api_endpoints(client, monkeypatch):
    monkeypatch.setattr(
        "core.orchestrator.gcp_vm_manager._run_gcloud",
        lambda args: [{"name": "aios-test", "status": "RUNNING", "networkInterfaces": []}],
    )

    # 1. GET /v1/platform/gcp/vms
    get_res = client.get("/v1/platform/gcp/vms")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["status"] == "ok"
    assert len(data["vms"]) == 1

    # 2. POST create
    monkeypatch.setattr(
        "core.orchestrator.gcp_vm_manager.create_customer_vm",
        lambda **kwargs: {"status": "created", "instance_name": "aios-demo", "ip_address": "34.141.1.2"},
    )
    post_res = client.post(
        "/v1/platform/gcp/vms/create",
        json={"tenant_id": "demo", "company_name": "Demo AG"},
    )
    assert post_res.status_code == 200
    assert post_res.json()["result"]["status"] == "created"

    # 3. POST stop
    monkeypatch.setattr(
        "core.orchestrator.gcp_vm_manager.stop_customer_vm",
        lambda instance_name, **kwargs: {"status": "stopped", "instance_name": instance_name},
    )
    stop_res = client.post(
        "/v1/platform/gcp/vms/stop",
        json={"instance_name": "aios-demo"},
    )
    assert stop_res.status_code == 200
    assert stop_res.json()["result"]["status"] == "stopped"

    # 4. POST start
    monkeypatch.setattr(
        "core.orchestrator.gcp_vm_manager.start_customer_vm",
        lambda instance_name, **kwargs: {"status": "started", "instance_name": instance_name},
    )
    start_res = client.post(
        "/v1/platform/gcp/vms/start",
        json={"instance_name": "aios-demo"},
    )
    assert start_res.status_code == 200
    assert start_res.json()["result"]["status"] == "started"

    # 5. DELETE
    monkeypatch.setattr(
        "core.orchestrator.gcp_vm_manager.delete_customer_vm",
        lambda instance_name, **kwargs: {"status": "deleted", "instance_name": instance_name},
    )
    del_res = client.delete("/v1/platform/gcp/vms/aios-demo")
    assert del_res.status_code == 200
    assert del_res.json()["result"]["status"] == "deleted"

