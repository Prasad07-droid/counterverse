# -*- coding: utf-8 -*-
"""
tests/test_phase6_two_modes.py
==============================
Validates Phase 6 backend support for Two Modes (Decision Mode & Analyst Mode):
- GET /api/v1/decision/events returns ranked queue with risk bands, exposure ranges, and human-in-the-loop policy.
- POST /api/v1/decision/action executes and records timestamped acknowledge, assign, comment, resolve actions.
- Human-in-the-loop governance: never auto-execute purchases or supplier changes.
"""

import pytest
import copy
from fastapi.testclient import TestClient
from api.main import app, _load_decision_queue, _save_decision_queue

client = TestClient(app)

@pytest.fixture(autouse=True)
def isolate_decision_queue():
    initial_queue = copy.deepcopy(_load_decision_queue())
    yield
    _save_decision_queue(initial_queue)



def test_get_decision_events():
    """Verify decision events endpoint returns ranked queue with policy."""
    response = client.get("/api/v1/decision/events")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Never auto-execute" in data["policy"]
    assert "events" in data
    assert len(data["events"]) >= 3

    first_event = data["events"][0]
    assert "id" in first_event
    assert "headline" in first_event
    assert "risk_band" in first_event
    assert "component" in first_event
    assert "oem" in first_event
    assert "p95_exposure_range" in first_event
    assert "recommended_action" in first_event
    assert "audit_trail" in first_event
    assert isinstance(first_event["audit_trail"], list)


def test_decision_action_acknowledge_and_assign():
    """Verify acknowledge and assign workflow actions."""
    # 1. Acknowledge
    ack_res = client.post(
        "/api/v1/decision/action",
        json={
            "event_id": "EVT-2026-001",
            "action": "acknowledge",
            "officer": "Lead Triage Officer",
            "notes": "Verified threat via UN Comtrade",
        },
    )
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["success"] is True
    assert ack_data["status"] == "ACKNOWLEDGED"

    latest_audit = ack_data["audit_trail"][-1]
    assert latest_audit["action"] == "acknowledge"
    assert latest_audit["actor"] == "Lead Triage Officer"
    assert "timestamp" in latest_audit

    # 2. Assign
    assign_res = client.post(
        "/api/v1/decision/action",
        json={
            "event_id": "EVT-2026-001",
            "action": "assign",
            "officer": "Semiconductor Procurement Desk",
            "notes": "Assigned for dual-sourcing RFQ",
        },
    )
    assert assign_res.status_code == 200
    assign_data = assign_res.json()
    assert assign_data["status"] == "IN_REVIEW"
    assert assign_data["assigned_to"] == "Semiconductor Procurement Desk"


def test_decision_action_comment_and_resolve():
    """Verify comment and resolve workflow actions."""
    # 1. Comment
    comment_res = client.post(
        "/api/v1/decision/action",
        json={
            "event_id": "EVT-2026-003",
            "action": "comment",
            "officer": "Logistics Lead",
            "notes": "Air charter quotes secured at ₹8.2 Cr",
        },
    )
    assert comment_res.status_code == 200
    comment_data = comment_res.json()
    latest_audit = comment_data["audit_trail"][-1]
    assert latest_audit["action"] == "comment"
    assert "Air charter quotes" in latest_audit["notes"]

    # 2. Resolve
    resolve_res = client.post(
        "/api/v1/decision/action",
        json={
            "event_id": "EVT-2026-003",
            "action": "resolve",
            "officer": "CSCO",
            "notes": "Manual PO authorized for air charter; disruption mitigated",
        },
    )
    assert resolve_res.status_code == 200
    resolve_data = resolve_res.json()
    assert resolve_data["status"] == "RESOLVED"


def test_decision_action_invalid_inputs():
    """Verify 404 for unknown event and 400 for unknown action."""
    res_404 = client.post(
        "/api/v1/decision/action",
        json={
            "event_id": "NON-EXISTENT-ID",
            "action": "acknowledge",
            "officer": "Officer A",
        },
    )
    assert res_404.status_code == 404

    res_400 = client.post(
        "/api/v1/decision/action",
        json={
            "event_id": "EVT-2026-001",
            "action": "auto_execute_purchase",  # Policy forbids auto-executing
            "officer": "Bot",
        },
    )
    assert res_400.status_code == 400
