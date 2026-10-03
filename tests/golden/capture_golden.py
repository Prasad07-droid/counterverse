"""Capture deterministic pre-hardening behavior for regression protection.

Run from the repository root with a stable interpreter hash seed:
    PYTHONHASHSEED=0 python tests/golden/capture_golden.py --write

The hash seed is explicit because the current severity/duration extractor uses
Python's process-randomized hash(). Changing that implementation is Tier C and
is intentionally outside this safety-net commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_sources import SIAM_2021_GROUND_TRUTH
from src.grounding_graph import (
    _compute_graph_hash,
    get_graph_summary,
    get_grounding_graph,
    verify_graph_integrity,
)
from src.module_b_slm import extract_signal
from src.module_c_causal import (
    calculate_deterministic_risk_score,
    compute_cost_adjusted_recommendation,
    simulate_causal_impact,
)
from src.module_d_mc import run_monte_carlo
from src.module_e_pcar import calculate_pcar, calculate_pcar_by_company

GOLDEN_DIR = Path(__file__).resolve().parent
SCENARIOS_PATH = PROJECT_ROOT / "data" / "synthesized_scenarios.json"
EVALUATION_PATH = PROJECT_ROOT / "data" / "evaluation_results.json"
SCENARIO_GOLDEN_PATH = GOLDEN_DIR / "pipeline_outputs.json"
EVALUATION_GOLDEN_PATH = GOLDEN_DIR / "evaluation_results.json"

PCAR_EXISTING_KEYS = (
    "company_name",
    "market_share_pct",
    "dependency_ratio_pct",
    "allocation_factor",
    "effective_base_crore",
    "industry_baseline_crore",
    "mean_loss_crore",
    "median_loss_crore",
    "pcar_95_crore",
    "pcar_99_crore",
    "worst_case_loss_crore",
    "allocation_formula",
    "macro_reference",
)


def _json_safe(value: Any) -> Any:
    """Convert NumPy values while preserving current scalar precision."""
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _existing_pcar_fields(result: dict) -> dict:
    """Snapshot only keys that existed before additive hardening changes."""
    return {
        key: _json_safe(result[key])
        for key in PCAR_EXISTING_KEYS
        if key in result
    }


def _mc_summary(result: dict) -> dict:
    return {
        "distribution_source": result["distribution_source"],
        "random_seed": result["random_seed"],
        "mean_drop": result["mean_drop"],
        "median_drop": result["median_drop"],
        "p95_drop": result["p95_drop"],
        "p99_drop": result["p99_drop"],
        "n_samples": result["n_samples"],
    }


def _run_pipeline(signal: dict, n_samples: int = 10_000) -> dict:
    risk = calculate_deterministic_risk_score(signal)
    probabilities = simulate_causal_impact(signal)
    mc_result = run_monte_carlo(probabilities, n_samples=n_samples, random_seed=42)
    macro_pcar = calculate_pcar(
        mc_result,
        company_name="Entire Indian Automotive Industry",
    )
    company_pcars = {
        company: _existing_pcar_fields(calculate_pcar_by_company(company, macro_pcar))
        for company in ("Maruti Suzuki", "Tata Motors", "Mahindra", "Hyundai India")
    }
    maruti_mean = company_pcars["Maruti Suzuki"]["mean_loss_crore"]
    cost_adjusted = compute_cost_adjusted_recommendation(
        risk_score=risk["risk_score"],
        pcar_mean_crore=maruti_mean,
    )
    return {
        "risk_score": risk["risk_score"],
        "risk_class": risk["risk_level"],
        "threshold_directive": risk["recommended_action"],
        "cost_adjusted_directive": cost_adjusted["recommendation"],
        "monte_carlo": _mc_summary(mc_result),
        "pcar": {
            "macro": _existing_pcar_fields(macro_pcar),
            "companies": company_pcars,
        },
    }


def _capture_siam_backtests() -> dict:
    config = SIAM_2021_GROUND_TRUTH["simulation_benchmark_config"]
    data_signal = {
        "event_type": config["event_type"],
        "severity": config["severity"],
        "duration_days": config["duration_days"],
        "recovery_time_days": config["recovery_time_days"],
        "affected_regions": ["China", "Taiwan"],
        "component": config["component"],
        "impacted_industries": ["Automotive", "Semiconductors"],
        "companies": [],
    }
    data_probabilities = simulate_causal_impact(data_signal)
    data_mc = run_monte_carlo(data_probabilities, n_samples=10_000, random_seed=42)
    data_target = float(config["target_actual_pct"])

    # This second signal mirrors the current dashboard's separately defined case.
    dashboard_signal = {
        "affected_node": "Semiconductor Fab",
        "component": "semiconductor",
        "event_type": "Raw material shortage",
        "severity": 3,
        "severity_pct": 85,
        "duration_days": 90,
        "region": "Taiwan",
    }
    dashboard_probabilities = simulate_causal_impact(dashboard_signal)
    dashboard_mc = run_monte_carlo(
        dashboard_probabilities,
        n_samples=10_000,
        random_seed=42,
    )
    dashboard_target = 41.2

    return {
        "data_source_case": {
            "target_actual_pct": data_target,
            **_mc_summary(data_mc),
            "p95_gap_pp": data_mc["p95_drop"] - data_target,
        },
        "dashboard_case": {
            "target_actual_pct": dashboard_target,
            **_mc_summary(dashboard_mc),
            "mean_gap_pp": dashboard_mc["mean_drop"] - dashboard_target,
            "p95_gap_pp": dashboard_mc["p95_drop"] - dashboard_target,
        },
    }


def build_snapshot() -> dict:
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError(
            "Golden capture requires PYTHONHASHSEED=0 because current extraction "
            "uses Python hash() for severity and duration."
        )

    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    captured_scenarios = []
    for scenario in scenarios:
        signal = extract_signal(
            scenario["headline"],
            simulate_delay=False,
            engine="fast",
        )
        # Match the existing evaluation harness input to deterministic risk scoring.
        signal["headline"] = scenario["headline"]
        captured_scenarios.append(
            {
                "id": scenario["id"],
                "headline": scenario["headline"],
                "signal": _json_safe(signal),
                **_run_pipeline(signal),
            }
        )

    graph = get_grounding_graph()
    evaluation_bytes = EVALUATION_PATH.read_bytes()
    return {
        "metadata": {
            "schema_version": 1,
            "engine": "fast",
            "python_hash_seed": 0,
            "monte_carlo_seed": 42,
            "monte_carlo_samples": 10_000,
            "evaluation_results_sha256": hashlib.sha256(evaluation_bytes).hexdigest(),
        },
        "graph": {
            "hash": _compute_graph_hash(graph),
            "integrity": verify_graph_integrity(graph),
            "summary": get_graph_summary(),
        },
        "siam_backtests": _capture_siam_backtests(),
        "scenarios": captured_scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the snapshot and evaluation-results copy into tests/golden/.",
    )
    args = parser.parse_args()
    snapshot = build_snapshot()
    serialized = json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

    if args.write:
        SCENARIO_GOLDEN_PATH.write_text(serialized, encoding="utf-8")
        EVALUATION_GOLDEN_PATH.write_bytes(EVALUATION_PATH.read_bytes())
        print(f"Wrote {SCENARIO_GOLDEN_PATH}")
        print(f"Wrote {EVALUATION_GOLDEN_PATH}")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
