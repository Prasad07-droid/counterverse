"""Global sensitivity analysis for the documented deterministic risk index.

This is an offline analysis utility. It does not import or modify pipeline
functions, thresholds, graph data, or runtime configuration.

Method:
- Baseline inputs mirror the current severity-2 China IC branch in
  ``src/module_c_causal.py``.
- Asserted component values (EB, DC, TC, ED) and all formula weights are jointly
  perturbed by independent Uniform[-20%, +20%] multipliers.
- Weights are renormalized to sum to one for each draw.
- DR is held at the protected 0.560 code output. It is only partially
  data-informed; this script does not reinterpret it as wholly empirical.
- A one-at-a-time tornado chart accompanies the joint simulation.

The results are a robustness analysis of assumptions, not a confidence interval
and not a forecast.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON_PATH = PROJECT_ROOT / "data" / "sensitivity_results.json"
DEFAULT_PLOT_PATH = PROJECT_ROOT / "data" / "outputs" / "sensitivity_tornado.png"

FACTOR_ORDER = ("EB", "DR", "DC", "TC", "ED")
BASE_VALUES = {
    "EB": 0.85,
    "DR": 0.560,
    "DC": 0.95,
    "TC": 0.80,
    "ED": 0.75,
}
BASE_WEIGHTS = {
    "EB": 0.35,
    "DR": 0.25,
    "DC": 0.20,
    "TC": 0.10,
    "ED": 0.10,
}
ASSERTED_VALUE_KEYS = ("EB", "DC", "TC", "ED")
PERTURBATION_FRACTION = 0.20
RANDOM_SEED = 42
N_DRAWS = 10_000


def classify(score: float) -> str:
    """Use existing protected thresholds without changing pipeline code."""
    if score >= 0.60:
        return "HIGH"
    if score >= 0.45:
        return "MEDIUM"
    return "LOW"


def score(values: Dict[str, float], weights: Dict[str, float]) -> float:
    return float(sum(values[key] * weights[key] for key in FACTOR_ORDER))


def normalized_weights(raw_weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(raw_weights.values())
    return {key: raw_weights[key] / total for key in FACTOR_ORDER}


def one_at_a_time_tornado() -> list[dict]:
    """Calculate low/high score effects for each asserted input and weight."""
    rows: list[dict] = []
    baseline = score(BASE_VALUES, BASE_WEIGHTS)

    for key in ASSERTED_VALUE_KEYS:
        low_values = dict(BASE_VALUES)
        high_values = dict(BASE_VALUES)
        low_values[key] = max(0.0, BASE_VALUES[key] * (1.0 - PERTURBATION_FRACTION))
        high_values[key] = min(1.0, BASE_VALUES[key] * (1.0 + PERTURBATION_FRACTION))
        low_score = score(low_values, BASE_WEIGHTS)
        high_score = score(high_values, BASE_WEIGHTS)
        rows.append(
            {
                "parameter": key,
                "kind": "asserted_factor_value",
                "low_score": round(low_score, 6),
                "high_score": round(high_score, 6),
                "low_delta": round(low_score - baseline, 6),
                "high_delta": round(high_score - baseline, 6),
            }
        )

    for key in FACTOR_ORDER:
        low_raw = dict(BASE_WEIGHTS)
        high_raw = dict(BASE_WEIGHTS)
        low_raw[key] *= 1.0 - PERTURBATION_FRACTION
        high_raw[key] *= 1.0 + PERTURBATION_FRACTION
        low_score = score(BASE_VALUES, normalized_weights(low_raw))
        high_score = score(BASE_VALUES, normalized_weights(high_raw))
        rows.append(
            {
                "parameter": f"weight_{key}",
                "kind": "formula_weight",
                "low_score": round(low_score, 6),
                "high_score": round(high_score, 6),
                "low_delta": round(low_score - baseline, 6),
                "high_delta": round(high_score - baseline, 6),
            }
        )

    return sorted(
        rows,
        key=lambda row: max(abs(row["low_delta"]), abs(row["high_delta"])),
        reverse=True,
    )


def joint_perturbation(n_draws: int = N_DRAWS, seed: int = RANDOM_SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    scores = np.empty(n_draws, dtype=float)

    for idx in range(n_draws):
        values = dict(BASE_VALUES)
        for key in ASSERTED_VALUE_KEYS:
            multiplier = rng.uniform(
                1.0 - PERTURBATION_FRACTION,
                1.0 + PERTURBATION_FRACTION,
            )
            values[key] = float(np.clip(BASE_VALUES[key] * multiplier, 0.0, 1.0))

        raw_weights = {
            key: BASE_WEIGHTS[key]
            * rng.uniform(1.0 - PERTURBATION_FRACTION, 1.0 + PERTURBATION_FRACTION)
            for key in FACTOR_ORDER
        }
        scores[idx] = score(values, normalized_weights(raw_weights))

    return scores


def build_results(n_draws: int = N_DRAWS, seed: int = RANDOM_SEED) -> dict:
    baseline_score = score(BASE_VALUES, BASE_WEIGHTS)
    samples = joint_perturbation(n_draws=n_draws, seed=seed)
    labels, counts = np.unique([classify(item) for item in samples], return_counts=True)
    class_counts = {label: 0 for label in ("LOW", "MEDIUM", "HIGH")}
    class_counts.update({str(label): int(count) for label, count in zip(labels, counts)})

    return {
        "analysis": "joint_uniform_perturbation_of_asserted_values_and_formula_weights",
        "disclaimer": "Robustness analysis of assumptions; not a confidence interval and not a forecast.",
        "baseline_case": "severity-2 China integrated-circuit branch",
        "baseline_values": BASE_VALUES,
        "baseline_weights": BASE_WEIGHTS,
        "baseline_score": round(baseline_score, 6),
        "baseline_class": classify(baseline_score),
        "dependency_ratio_note": "DR is fixed at the protected 0.560 output and is partially data-informed; C_upstream and W_unhedged remain assumptions in branches where they apply.",
        "joint_analysis": {
            "random_seed": seed,
            "draws": n_draws,
            "perturbation": "independent Uniform[-20%, +20%] multipliers",
            "weight_handling": "renormalized to sum to 1 after perturbation",
            "mean_score": round(float(np.mean(samples)), 6),
            "std_score": round(float(np.std(samples)), 6),
            "min_score": round(float(np.min(samples)), 6),
            "p05_score": round(float(np.percentile(samples, 5)), 6),
            "median_score": round(float(np.median(samples)), 6),
            "p95_score": round(float(np.percentile(samples, 95)), 6),
            "max_score": round(float(np.max(samples)), 6),
            "class_counts": class_counts,
            "class_rates": {
                key: round(value / n_draws, 6) for key, value in class_counts.items()
            },
        },
        "tornado": one_at_a_time_tornado(),
    }


def write_tornado_plot(rows: Iterable[dict], output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(rows)
    labels = [row["parameter"] for row in rows][::-1]
    low = [row["low_delta"] for row in rows][::-1]
    high = [row["high_delta"] for row in rows][::-1]
    y_pos = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(y_pos, low, color="#0ea5e9", label="-20%")
    ax.barh(y_pos, high, color="#f97316", label="+20%")
    ax.axvline(0.0, color="#111827", linewidth=1)
    ax.set_yticks(y_pos, labels)
    ax.set_xlabel("Change in risk score from baseline")
    ax.set_title("CounterVerse one-at-a-time sensitivity tornado")
    ax.legend()
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--plot-output", type=Path, default=DEFAULT_PLOT_PATH)
    parser.add_argument("--draws", type=int, default=N_DRAWS)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    results = build_results(n_draws=args.draws, seed=args.seed)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_tornado_plot(results["tornado"], args.plot_output)
    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.plot_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
