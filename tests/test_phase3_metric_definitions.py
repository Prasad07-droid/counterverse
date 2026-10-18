# -*- coding: utf-8 -*-
"""
Tests for Phase 3: Metric Definitions & Centralized Thresholds
==============================================================
Covers:
  - docs/metric_definitions.md existence and core sections
  - Centralized risk thresholds (0.60 / 0.45) in module_c_causal, module_i_report, and api/main
  - classify_risk_band behavior
  - /api/v1/simulate accepting mc_samples and seed
  - metric_version and assumptions fields in PCaR and report responses
"""

from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.module_c_causal import (
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
    classify_risk_band,
)
from src.module_e_pcar import (
    METRIC_VERSION,
    PCAR_ASSUMPTIONS,
    calculate_pcar,
    calculate_pcar_by_company,
    calculate_pcar_custom_bom,
)
from src.module_i_report import generate_report


@pytest.fixture
def client():
    return TestClient(app)


# ── 1. Documentation Verification ──

def test_metric_definitions_documentation_exists():
    """docs/metric_definitions.md must exist and contain required metric explanations."""
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "metric_definitions.md"
    assert doc_path.exists(), "docs/metric_definitions.md was not created"

    content = doc_path.read_text(encoding="utf-8")
    assert "PCaR(q)" in content
    assert "extra_procurement_cost_" in content
    assert "spot-market surge premium" in content or "spot market surge premium" in content
    assert "ordinal multi-criteria prioritization index" in content or "ordinal prioritization index" in content
    assert "NOT an empirical probability" in content or "NOT a probability" in content
    assert "Model-Assigned Heuristics" in content or "model-assigned" in content
    assert "Uniform[1.3, 2.8]" in content
    assert "133,814.34" in content or "133814.34" in content


# ── 2. Centralized Risk Thresholds ──

def test_centralized_risk_thresholds():
    """Verify threshold constants and classification behavior."""
    assert RISK_THRESHOLD_HIGH == 0.60
    assert RISK_THRESHOLD_MEDIUM == 0.45

    assert classify_risk_band(0.75) == "HIGH"
    assert classify_risk_band(0.60) == "HIGH"
    assert classify_risk_band(0.599) == "MEDIUM"
    assert classify_risk_band(0.45) == "MEDIUM"
    assert classify_risk_band(0.449) == "LOW"
    assert classify_risk_band(0.10) == "LOW"


# ── 3. /api/v1/simulate Accepts mc_samples and seed ──

def test_simulate_endpoint_accepts_mc_samples_and_seed(client):
    """POST /api/v1/simulate must respect mc_samples and seed passed in payload."""
    payload = {
        "signal": {
            "event_type": "supply_disruption",
            "severity": 3,
            "duration_days": 30,
            "recovery_time_days": 30,
            "affected_regions": ["China"],
            "component": "Integrated Circuits",
            "impacted_industries": ["Automotive"],
            "companies": ["Maruti Suzuki"],
        },
        "mc_samples": 5000,
        "seed": 99,
    }
    resp = client.post("/api/v1/simulate", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "simulation_config" in data
    assert data["simulation_config"]["mc_samples"] == 5000
    assert data["simulation_config"]["random_seed"] == 99
    assert data["mc_stats"]["n_samples"] == 5000
    assert "metric_version" in data
    assert data["metric_version"] == "2.0.0"
    assert "assumptions" in data
    assert "pcar_definition" in data["assumptions"]


def test_simulate_endpoint_reproducibility(client):
    """Calling /api/v1/simulate with the same seed must produce bit-identical results."""
    payload = {
        "signal": {
            "event_type": "supply_disruption",
            "severity": 4,
            "duration_days": 45,
            "recovery_time_days": 30,
            "affected_regions": ["Taiwan"],
            "component": "Integrated Circuits",
            "impacted_industries": ["Automotive"],
            "companies": [],
        },
        "mc_samples": 2000,
        "seed": 12345,
    }
    resp1 = client.post("/api/v1/simulate", json=payload)
    resp2 = client.post("/api/v1/simulate", json=payload)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["mc_stats"] == resp2.json()["mc_stats"]
    assert resp1.json()["pcar"]["pcar_95_crore"] == resp2.json()["pcar"]["pcar_95_crore"]


# ── 4. metric_version and assumptions in PCaR Responses ──

def test_pcar_module_includes_metric_version_and_assumptions():
    """Module E functions must include metric_version and assumptions dicts."""
    samples = np.array([5.0, 10.0, 15.0])

    macro = calculate_pcar(samples, company_name="Entire Indian Automotive Industry", random_seed=42)
    assert macro["metric_version"] == METRIC_VERSION
    assert "assumptions" in macro
    assert macro["assumptions"]["spot_premium_distribution"] == "Uniform[1.3, 2.8] (spot market surge premium included)"

    company = calculate_pcar_by_company("Maruti Suzuki", macro)
    assert company["metric_version"] == METRIC_VERSION
    assert "assumptions" in company

    bom = calculate_pcar_custom_bom(
        samples,
        bom_components=[{"component_name": "ECU IC", "hs_code": "8542", "annual_spend_crore": 100.0}],
        company_name="Test OEM",
        random_seed=42,
    )
    assert bom["metric_version"] == METRIC_VERSION
    assert "assumptions" in bom


def test_api_pcar_endpoints_include_metric_version_and_assumptions(client):
    """API endpoints /calculate-pcar and /calculate-custom-bom must return metric_version & assumptions."""
    # /calculate-pcar
    resp1 = client.post(
        "/api/v1/calculate-pcar",
        json={"company": "Tata Motors", "risk_score": 0.65, "mc_samples": 500},
    )
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["metric_version"] == "2.0.0"
    assert d1["assumptions"] is not None
    assert "risk_score_interpretation" in d1["assumptions"]

    # /calculate-custom-bom
    resp2 = client.post(
        "/api/v1/calculate-custom-bom",
        json={
            "company_name": "Custom Auto Corp",
            "components": [{"component_name": "MCU", "hs_code": "8542", "annual_spend_crore": 150.0}],
            "risk_score": 0.5,
            "mc_samples": 500,
        },
    )
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["metric_version"] == "2.0.0"
    assert d2["assumptions"] is not None


# ── 5. metric_version and assumptions in Decision Support Report ──

def test_report_includes_metric_version_and_assumptions(client):
    """generate_report and /generate-report must return metric_version and assumptions."""
    pipeline_dummy = {
        "headline": "Semiconductor Fab Bottleneck in Taiwan Impacts Auto Production",
        "engine_used": "fast",
        "target_oem": "Maruti Suzuki",
        "signal": {
            "event_type": "supply_disruption",
            "component": "Integrated Circuits",
            "region": "Taiwan",
            "severity_pct": 60.0,
            "severity_level": "HIGH",
            "duration_days": 45,
            "confidence": 0.88,
        },
        "risk_result": {"risk_score": 0.68, "risk_level": "HIGH", "factors": {}},
        "risk_score": 0.68,
        "risk_label": "HIGH",
        "mc_result": {"mean_drop": 18.2, "median_drop": 16.5, "p95_drop": 27.4, "p99_drop": 32.1, "n_samples": 1000},
        "pcar_metrics": {
            "effective_base_crore": 21200.0,
            "mean_loss_crore": 3800.0,
            "median_loss_crore": 3400.0,
            "pcar_95_crore": 5700.0,
            "pcar_99_crore": 6800.0,
            "worst_case_loss_crore": 7500.0,
            "extra_procurement_cost_p95_crore": 1800.0,
        },
    }

    rep = generate_report(pipeline_dummy)
    assert "metric_version" in rep
    assert rep["metric_version"] == "2.0.0"
    assert "assumptions" in rep
    assert "formula" in rep["assumptions"]

    # Endpoint test
    resp = client.post(
        "/api/v1/generate-report",
        json={"headline": "Critical Gallium Export Controls Limit Indian Chip Packaging", "oem": "Tata Motors"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric_version"] == "2.0.0"
    assert data["assumptions"] is not None
