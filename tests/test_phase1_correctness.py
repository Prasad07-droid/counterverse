# tests/test_phase1_correctness.py
"""
Tests for Phase 1 Correctness Fixes:
1. SIAM backtest json import & precomputed path usage.
2. Grounding graph overlay persistence & base graph hash integrity.
3. PCaR seed isolation and removal of mock sleep.
4. Report grounding mapping from ground_entities() output.
5. Stripping 10,000 samples from API report responses & field name separation.
"""

import json
import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import patch

from api.main import app, get_siam_backtest
from src.grounding_graph import (
    build_grounding_graph,
    get_grounding_graph,
    save_graph_overlay,
    load_graph_overlay,
    ground_entities,
    _compute_graph_hash,
    EXPECTED_GRAPH_HASH,
)
from src.module_e_pcar import calculate_pcar, calculate_pcar_custom_bom
from src.module_d_mc import run_monte_carlo, MonteCarloResult
from src.module_i_report import build_report_data, generate_report


# ── Fix 1: SIAM backtest precomputed path ────────────────────────
@pytest.mark.anyio
async def test_siam_backtest_precomputed_file_path_used():
    """Verify that get_siam_backtest() loads from file without NameError or recomputation."""
    res = await get_siam_backtest()
    assert isinstance(res, dict)
    assert "metrics" in res or "results" in res or "status" in res


def test_siam_backtest_uses_json_load():
    """Verify json.load is invoked on the file path when it exists."""
    with patch("api.main.json.load", return_value={"test": "mock_siam"}) as mock_json_load:
        import asyncio
        res = asyncio.run(get_siam_backtest())
        assert res == {"test": "mock_siam"}
        mock_json_load.assert_called_once()


# ── Fix 2: Graph overlay persistence round-trip ─────────────────
def test_graph_overlay_persistence_roundtrip():
    """Test save and load overlay to a custom file without corrupting base graph hash."""
    base_G = build_grounding_graph()
    base_hash = _compute_graph_hash(base_G)
    assert base_hash == EXPECTED_GRAPH_HASH

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Add custom node to a clone of base graph
        G = base_G.copy()
        G.add_node("CustomSupplierX", type="company", custom=True, country="India")
        G.add_edge("CustomSupplierX", "ECU", relationship="supplies_to", custom=True, edge_confidence=0.95)

        saved_path = save_graph_overlay(G, path=tmp_path)
        assert Path(saved_path).exists()

        # Load overlay into fresh base graph
        fresh_G = build_grounding_graph()
        assert not fresh_G.has_node("CustomSupplierX")

        added = load_graph_overlay(fresh_G, path=tmp_path)
        assert added >= 2
        assert fresh_G.has_node("CustomSupplierX")
        assert fresh_G.has_edge("CustomSupplierX", "ECU")
        assert fresh_G.nodes["CustomSupplierX"]["country"] == "India"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Fix 3: Seed isolation in calculate_pcar ──────────────────────
def test_pcar_seed_isolation():
    """Test that explicit random_seed guarantees deterministic output regardless of global state."""
    samples = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

    # Pollute global state
    np.random.seed(9999)
    res1 = calculate_pcar(samples, random_seed=42)

    np.random.seed(1111)
    res2 = calculate_pcar(samples, random_seed=42)

    assert res1["mean_loss_crore"] == pytest.approx(res2["mean_loss_crore"], rel=1e-7)
    assert res1["pcar_95_crore"] == pytest.approx(res2["pcar_95_crore"], rel=1e-7)


def test_pcar_custom_bom_seed_isolation():
    """Test seed isolation in calculate_pcar_custom_bom."""
    samples = np.array([15.0, 25.0, 35.0])
    bom = [{"component_name": "Integrated Circuits", "hs_code": "8542", "annual_spend_crore": 100.0}]

    np.random.seed(9999)
    res1 = calculate_pcar_custom_bom(samples, bom, random_seed=42, ground_against_graph=False)

    np.random.seed(1111)
    res2 = calculate_pcar_custom_bom(samples, bom, random_seed=42, ground_against_graph=False)

    assert res1["mean_loss_crore"] == pytest.approx(res2["mean_loss_crore"], rel=1e-7)


def test_pcar_no_mock_sleep():
    """Verify that calculate_pcar runs in sub-10ms without artificial sleep(0.1)."""
    import time
    samples = np.array([10.0, 20.0, 30.0])
    t0 = time.perf_counter()
    calculate_pcar(samples, random_seed=42)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.05, f"calculate_pcar took {elapsed}s, expected < 0.05s without sleep"


# ── Fix 4: Grounding mapping from real ground_entities() ────────
def test_report_grounding_mapping_real_output():
    """Verify build_report_data correctly extracts summary and entity attributes from ground_entities()."""
    signal = {
        "headline": "China restricts export of gallium and semiconductor integrated circuits to India",
        "component": "Integrated Circuits",
        "affected_regions": ["China"],
        "companies": ["TSMC"],
    }
    grounding = ground_entities(signal)
    assert "summary" in grounding
    assert grounding["summary"]["verified_count"] >= 1

    report_input = {
        "headline": signal["headline"],
        "signal": signal,
        "grounding": grounding,
        "risk_result": {"risk_score": 0.72},
    }

    report_data = build_report_data(report_input)
    grd = report_data["grounding"]

    assert grd["verified_count"] == grounding["summary"]["verified_count"]
    assert grd["total_entities"] == grounding["summary"]["total_entities"]
    assert grd["verification_rate"] == grounding["summary"]["verification_rate"]
    assert grd["graph_hash"] == EXPECTED_GRAPH_HASH
    assert grd["total_nodes"] > 20
    assert grd["total_edges"] > 30

    # Entity list has canonical names and In-graph status
    entities = grd["entities"]
    assert len(entities) > 0
    in_graph_count = sum(1 for e in entities if e["status"] == "In-graph")
    assert in_graph_count >= 1
    # Check that names are canonical, not fallback "Entity"
    assert any("China" in e["name"] or "Integrated Circuits" in e["name"] for e in entities)


# ── Fix 5: Strip 10,000 raw samples & field name separation ────
def test_generate_report_no_raw_samples_leak():
    """Verify 10,000 raw samples array is stripped from mc_stats and data, and fields match."""
    # Create realistic MC result with 10,000 samples
    samples = np.random.normal(loc=25.0, scale=5.0, size=10000)
    mc = MonteCarloResult(samples=samples, random_seed=42)

    signal = {
        "headline": "Semiconductor foundry outage triggers production halts",
        "component": "Integrated Circuits",
        "severity": 3,
        "duration_days": 45,
    }
    pcar_metrics = calculate_pcar(mc, company_name="Maruti Suzuki", random_seed=42)

    full_result = {
        "headline": signal["headline"],
        "signal": signal,
        "mc_result": mc,
        "pcar_metrics": pcar_metrics,
        "target_oem": "Maruti Suzuki",
    }

    report = generate_report(full_result)

    # 1. Samples must not be leaked into mc_stats or data
    assert "samples" not in report["mc_stats"]
    assert "samples" not in report["data"].get("mc_stats", {})
    assert "histogram" in report["mc_stats"]
    assert len(report["mc_stats"]["histogram"]["counts"]) == 20

    # 2. Field name separation
    assert "pcar_metrics" in report
    assert report["pcar_metrics"]["mean_loss_crore"] > 0
    assert "recommendation" in report
    assert "options_ranked" in report["recommendation"]
    # Backward compatibility key carries recommendation
    assert "options_ranked" in report["pcar"]
