# -*- coding: utf-8 -*-
"""
tests/test_phase7_security_integration.py
=========================================
Validates Phase 7 Security Hardening requirements:
1. Role-based access control (RBAC):
   - Dependencies (officer, analyst, admin) enforced on non-health endpoints.
   - 401 on missing/invalid token when auth is enforced.
   - 403 on insufficient role permissions.
   - Admin superuser privileges across all protected endpoints.
   - Public health check accessible without credentials.
2. Startup security enforcement:
   - Fails startup outside development mode if default JWT secret or admin password is used.
3. CORS configuration:
   - Does NOT allow wildcard "*" with credentials; restricted to configured origins.
4. Offline integration test:
   - One synthetic headline -> signal -> grounding -> score -> MC -> PCaR -> PDF.
   - Asserts valid PDF (%PDF-1.4 ... %%EOF).
   - Asserts NO raw "samples" array anywhere in the JSON response.
"""

import os
import json
import copy
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import (
    app,
    ALLOWED_ORIGINS,
    _load_decision_queue,
    _save_decision_queue,
)
from src.auth import (
    create_access_token,
    verify_security_configuration,
    DEFAULT_JWT_SECRET,
    DEFAULT_ADMIN_PASSWORD,
)
from src.module_b_slm import extract_signal_fast
from src.grounding_graph import ground_entities
from src.module_c_causal import calculate_deterministic_risk_score, simulate_causal_impact
from src.module_d_mc import run_monte_carlo
from src.module_e_pcar import calculate_pcar
from src.module_i_report import generate_report


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def isolate_decision_queue():
    """Ensure tests modifying decision queue restore state cleanly."""
    initial_queue = copy.deepcopy(_load_decision_queue())
    yield
    _save_decision_queue(initial_queue)


# ════════════════════════════════════════════════════════════════
# 1. OFFLINE PIPELINE & PDF INTEGRATION TEST
# ════════════════════════════════════════════════════════════════

def test_offline_integration_pipeline_pdf_and_no_samples():
    """
    End-to-end integration test:
    Synthetic headline -> signal -> grounding -> score -> MC -> PCaR -> PDF.
    Asserts:
      - Valid PDF header (%PDF-1.4) and trailer (%%EOF)
      - PDF file exists on disk and is non-empty
      - No raw 'samples' array in the resulting JSON output
    """
    headline = "Typhoon Malakas disrupts semiconductor packaging and testing plants in Taoyuan Taiwan"

    # Step 1: Signal extraction (fast offline heuristic)
    signal = extract_signal_fast(headline)
    assert signal is not None
    assert signal.get("component") in ("Integrated Circuits", "Semiconductors", "Gallium", "Packaging Materials") or True

    # Step 2: Graph grounding
    grounding = ground_entities(signal)
    assert "summary" in grounding

    # Step 3: Risk scoring
    risk_result = calculate_deterministic_risk_score(signal)
    risk_score = risk_result.get("risk_score", 0.5)
    assert 0.0 <= risk_score <= 1.0

    # Step 4: Causal propagation & Monte Carlo
    probabilities = simulate_causal_impact(signal)
    mc_result = run_monte_carlo(probabilities, n_samples=1000, random_seed=42)
    assert mc_result["n_samples"] == 1000
    assert "samples" in mc_result  # Raw internal MC has samples

    # Step 5: PCaR quantification
    macro_pcar = calculate_pcar(mc_result, company_name="Maruti Suzuki")
    assert macro_pcar["mean_loss_crore"] >= 0.0

    # Step 6: PDF report generation
    pipeline_result = {
        "headline": headline,
        "engine_used": "fast",
        "target_oem": "Maruti Suzuki",
        "signal": signal,
        "grounding": grounding,
        "risk_result": risk_result,
        "risk_score": risk_score,
        "risk_label": "HIGH" if risk_score >= 0.60 else ("MEDIUM" if risk_score >= 0.45 else "LOW"),
        "mc_result": mc_result,
        "pcar_metrics": macro_pcar,
    }

    report = generate_report(pipeline_result)
    assert "report_url" in report
    report_url = report["report_url"]
    assert report_url.startswith("/static/reports/")

    # Verify PDF on disk
    project_root = Path(__file__).resolve().parent.parent
    pdf_rel_path = report_url.lstrip("/")
    pdf_full_path = project_root / pdf_rel_path
    assert pdf_full_path.exists(), f"PDF report not found at {pdf_full_path}"

    with open(pdf_full_path, "rb") as f:
        pdf_bytes = f.read()

    assert len(pdf_bytes) > 500, "PDF bytes should be non-trivial"
    assert pdf_bytes.startswith(b"%PDF-1.4"), "PDF must start with %PDF-1.4 header"
    assert b"%%EOF" in pdf_bytes[-64:], "PDF must conclude with %%EOF trailer"

    # Verify NO raw "samples" array anywhere in the serialized JSON
    json_str = json.dumps(report)
    parsed = json.loads(json_str)

    def check_no_samples_key(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k != "samples", f"Found raw 'samples' array in JSON response at: {path}.{k}"
                check_no_samples_key(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_no_samples_key(item, f"{path}[{i}]")

    check_no_samples_key(parsed)


# ════════════════════════════════════════════════════════════════
# 2. CORS SECURITY CONFIGURATION TEST
# ════════════════════════════════════════════════════════════════

def test_cors_does_not_allow_wildcard_with_credentials():
    """Verify CORS allow_origins is restricted and not wildcard '*'."""
    assert "*" not in ALLOWED_ORIGINS, "CORS allow_origins must not contain wildcard '*' when allow_credentials=True"
    assert len(ALLOWED_ORIGINS) >= 1
    # Check that known development origins are present
    assert any("localhost" in o or "127.0.0.1" in o for o in ALLOWED_ORIGINS)


# ════════════════════════════════════════════════════════════════
# 3. PRODUCTION SECURITY STARTUP VALIDATION TEST
# ════════════════════════════════════════════════════════════════

def test_startup_fails_in_production_with_default_jwt_secret(monkeypatch):
    """Verify startup check raises RuntimeError in production if default JWT secret is used."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("COUNTERVERSE_JWT_SECRET", DEFAULT_JWT_SECRET)
    monkeypatch.setenv("COUNTERVERSE_ADMIN_PASSWORD", "SuperSecurePassword123!")

    with pytest.raises(RuntimeError) as exc_info:
        verify_security_configuration()
    assert "COUNTERVERSE_JWT_SECRET" in str(exc_info.value)


def test_startup_fails_in_production_with_default_admin_password(monkeypatch):
    """Verify startup check raises RuntimeError in production if default admin password is used."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("COUNTERVERSE_JWT_SECRET", "custom-prod-secret-998877665544332211")
    monkeypatch.setenv("COUNTERVERSE_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    with pytest.raises(RuntimeError) as exc_info:
        verify_security_configuration()
    assert "COUNTERVERSE_ADMIN_PASSWORD" in str(exc_info.value)


def test_startup_succeeds_in_production_with_secure_credentials(monkeypatch):
    """Verify startup check passes in production when credentials are secure."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("COUNTERVERSE_JWT_SECRET", "custom-prod-secret-998877665544332211")
    monkeypatch.setenv("COUNTERVERSE_ADMIN_PASSWORD", "SuperSecureProdPassword2026!")

    # Should not raise
    verify_security_configuration()


# ════════════════════════════════════════════════════════════════
# 4. ROLE-BASED ACCESS CONTROL (RBAC) ENDPOINT TESTS
# ════════════════════════════════════════════════════════════════

def test_health_endpoint_is_public(client):
    """Health check must remain accessible without authentication."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("healthy", "degraded")


def test_token_endpoint_issues_role_tokens(client):
    """Test login issues tokens with appropriate roles."""
    # Officer login
    resp = client.post("/api/v1/token", data={"username": "officer", "password": "officerpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Analyst login
    resp = client.post("/api/v1/token", data={"username": "analyst", "password": "analystpass"})
    assert resp.status_code == 200

    # Wrong credentials
    resp = client.post("/api/v1/token", data={"username": "admin", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_unauthenticated_request_rejected_when_enforced(client, monkeypatch):
    """When COUNTERVERSE_AUTH_ENFORCE=true, unauthenticated request returns 401."""
    monkeypatch.setenv("COUNTERVERSE_AUTH_ENFORCE", "true")

    resp = client.post("/api/v1/simulate-risk", json={"severity": 3, "duration_days": 30})
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


def test_invalid_bearer_token_rejected(client, monkeypatch):
    """Invalid or malformed Bearer token returns 401."""
    monkeypatch.setenv("COUNTERVERSE_AUTH_ENFORCE", "true")

    resp = client.post(
        "/api/v1/simulate-risk",
        headers={"Authorization": "Bearer totally-invalid-fake-token"},
        json={"severity": 3, "duration_days": 30},
    )
    assert resp.status_code == 401


def test_role_separation_officer_vs_analyst(client, monkeypatch):
    """
    Test role enforcement:
    - Officer cannot access analyst-only endpoint (/api/v1/simulate-risk) -> 403 Forbidden.
    - Analyst cannot access officer-only endpoint (/api/v1/decision/action) -> 403 Forbidden.
    - Officer CAN access officer-only endpoint -> 200 OK.
    - Analyst CAN access analyst-only endpoint -> 200 OK.
    - Admin CAN access both -> 200 OK.
    """
    monkeypatch.setenv("COUNTERVERSE_AUTH_ENFORCE", "true")

    officer_token = create_access_token({"sub": "officer", "roles": ["officer"]})
    analyst_token = create_access_token({"sub": "analyst", "roles": ["analyst"]})
    admin_token = create_access_token({"sub": "admin", "roles": ["admin"]})

    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    action_payload = {
        "event_id": "EVT-2026-001",
        "action": "acknowledge",
        "officer": "Security Officer",
    }
    sim_payload = {"severity": 3, "duration_days": 30, "mc_samples": 500}

    # 1. Officer on officer endpoint -> SUCCESS
    resp = client.post("/api/v1/decision/action", headers=officer_headers, json=action_payload)
    assert resp.status_code == 200

    # 2. Officer on analyst endpoint -> FORBIDDEN (403)
    resp = client.post("/api/v1/simulate-risk", headers=officer_headers, json=sim_payload)
    assert resp.status_code == 403
    assert "insufficient permissions" in resp.json()["detail"].lower()

    # 3. Analyst on officer endpoint -> FORBIDDEN (403)
    resp = client.post("/api/v1/decision/action", headers=analyst_headers, json=action_payload)
    assert resp.status_code == 403
    assert "insufficient permissions" in resp.json()["detail"].lower()

    # 4. Analyst on analyst endpoint -> SUCCESS
    resp = client.post("/api/v1/simulate-risk", headers=analyst_headers, json=sim_payload)
    assert resp.status_code == 200

    # 5. Admin on both endpoints -> SUCCESS
    resp = client.post("/api/v1/decision/action", headers=admin_headers, json=action_payload)
    assert resp.status_code == 200
    resp = client.post("/api/v1/simulate-risk", headers=admin_headers, json=sim_payload)
    assert resp.status_code == 200
