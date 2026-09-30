"""Evaluate human-labeled held-out headlines without touching the 15-scenario harness.

The script compares three extraction modes on ``data/labeled/test``:
1. naive regex/keyword baseline,
2. CounterVerse fast extractor,
3. Qwen SLM when CUDA is available and ``--include-qwen`` is requested.

It reports binary disruption metrics with deterministic bootstrap 95% intervals.
Rows are eligible only after two annotators agree or an adjudicated label is
provided. Empty and disputed rows are never silently treated as negative labels.

This script intentionally leaves ``scripts/evaluate_pipeline.py`` unchanged.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_classifier import naive_keyword_classifier
from src.module_b_slm import extract_signal

DEFAULT_DEV_PATH = PROJECT_ROOT / "data" / "labeled" / "dev" / "annotations.csv"
DEFAULT_TEST_PATH = PROJECT_ROOT / "data" / "labeled" / "test" / "annotations.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "heldout_evaluation_results.json"
BOOTSTRAP_SEED = 42
BOOTSTRAP_RESAMPLES = 1_000

TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}


def parse_optional_bool(value: str) -> Optional[bool]:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"Unrecognized boolean label: {value!r}")


def load_consensus_rows(path: Path) -> tuple[list[dict], dict]:
    """Load rows with adjudication or two-annotator agreement."""
    if not path.exists():
        raise FileNotFoundError(path)

    eligible: list[dict] = []
    counts = {
        "rows_total": 0,
        "rows_eligible": 0,
        "rows_empty": 0,
        "rows_disputed_unadjudicated": 0,
    }
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            counts["rows_total"] += 1
            headline = (row.get("headline") or "").strip()
            if not headline:
                counts["rows_empty"] += 1
                continue

            adjudicated = parse_optional_bool(row.get("adjudicated_is_disruption", ""))
            ann1 = parse_optional_bool(row.get("annotator_1_is_disruption", ""))
            ann2 = parse_optional_bool(row.get("annotator_2_is_disruption", ""))

            if adjudicated is not None:
                label = adjudicated
                label_source = "adjudicated"
            elif ann1 is not None and ann2 is not None and ann1 == ann2:
                label = ann1
                label_source = "two_annotator_agreement"
            elif ann1 is None or ann2 is None:
                counts["rows_empty"] += 1
                continue
            else:
                counts["rows_disputed_unadjudicated"] += 1
                continue

            eligible.append(
                {
                    "scenario_id": (row.get("scenario_id") or "").strip(),
                    "headline": headline,
                    "is_disruption": label,
                    "label_source": label_source,
                }
            )
            counts["rows_eligible"] += 1

    return eligible, counts


def confusion_metrics(y_true: Iterable[bool], y_pred: Iterable[bool]) -> dict:
    pairs = list(zip(y_true, y_pred))
    tp = sum(truth and pred for truth, pred in pairs)
    fp = sum((not truth) and pred for truth, pred in pairs)
    tn = sum((not truth) and (not pred) for truth, pred in pairs)
    fn = sum(truth and (not pred) for truth, pred in pairs)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    accuracy = (tp + tn) / len(pairs) if pairs else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "specificity": round(specificity, 6),
        "accuracy": round(accuracy, 6),
        "f1": round(f1, 6),
    }


def bootstrap_intervals(
    y_true: list[bool],
    y_pred: list[bool],
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    """Paired nonparametric bootstrap percentile intervals."""
    if not y_true:
        return {}
    rng = np.random.default_rng(seed)
    metric_names = ("precision", "recall", "specificity", "accuracy", "f1")
    samples = {name: [] for name in metric_names}
    y_true_arr = np.asarray(y_true, dtype=bool)
    y_pred_arr = np.asarray(y_pred, dtype=bool)

    for _ in range(resamples):
        indices = rng.integers(0, len(y_true_arr), size=len(y_true_arr))
        metrics = confusion_metrics(y_true_arr[indices], y_pred_arr[indices])
        for name in metric_names:
            samples[name].append(metrics[name])

    return {
        name: {
            "low": round(float(np.percentile(values, 2.5)), 6),
            "high": round(float(np.percentile(values, 97.5)), 6),
        }
        for name, values in samples.items()
    }


def qwen_availability() -> tuple[bool, str]:
    try:
        import torch
    except ImportError:
        return False, "torch is not installed"
    if not torch.cuda.is_available():
        return False, "CUDA GPU is not available; CPU-Qwen is out of scope"
    return True, "available"


def evaluate_model(
    name: str,
    rows: list[dict],
    predictor: Callable[[str], bool],
    bootstrap_resamples: int,
) -> dict:
    y_true = [row["is_disruption"] for row in rows]
    y_pred = [bool(predictor(row["headline"])) for row in rows]
    return {
        "name": name,
        "status": "evaluated",
        "n": len(rows),
        "metrics": confusion_metrics(y_true, y_pred),
        "bootstrap_95pct": bootstrap_intervals(
            y_true,
            y_pred,
            resamples=bootstrap_resamples,
            seed=BOOTSTRAP_SEED,
        ),
        "predictions": [
            {
                "scenario_id": row["scenario_id"],
                "truth": truth,
                "prediction": prediction,
            }
            for row, truth, prediction in zip(rows, y_true, y_pred)
        ],
    }


def run_ablation(
    rows: list[dict],
    include_qwen: bool = False,
    bootstrap_resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict:
    results = {
        "naive_regex": evaluate_model(
            "naive_regex",
            rows,
            lambda headline: naive_keyword_classifier(headline)["is_disruption"],
            bootstrap_resamples,
        ),
        "fast_extractor": evaluate_model(
            "fast_extractor",
            rows,
            lambda headline: extract_signal(
                headline,
                simulate_delay=False,
                engine="fast",
            )["is_disruption"],
            bootstrap_resamples,
        ),
    }

    available, reason = qwen_availability()
    if include_qwen and available:
        results["qwen"] = evaluate_model(
            "qwen",
            rows,
            lambda headline: extract_signal(
                headline,
                simulate_delay=False,
                engine="slm",
            )["is_disruption"],
            bootstrap_resamples,
        )
    else:
        results["qwen"] = {
            "name": "qwen",
            "status": "not_run",
            "reason": reason if not available else "pass --include-qwen to run GPU inference",
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", type=Path, default=DEFAULT_DEV_PATH)
    parser.add_argument("--test", type=Path, default=DEFAULT_TEST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--include-qwen", action="store_true")
    parser.add_argument("--bootstrap-resamples", type=int, default=BOOTSTRAP_RESAMPLES)
    args = parser.parse_args()

    dev_rows, dev_counts = load_consensus_rows(args.dev)
    test_rows, test_counts = load_consensus_rows(args.test)
    if not test_rows:
        print(
            "No eligible held-out test rows. Complete both annotator columns "
            "and adjudicate disagreements before evaluation."
        )
        print(json.dumps({"dev": dev_counts, "test": test_counts}, indent=2))
        return 0

    payload = {
        "protocol": "human_labeled_heldout_ablation",
        "disclaimer": "Held-out evaluation, not a forecast. Confidence intervals are bootstrap intervals over the labeled sample.",
        "dev_label_counts": dev_counts,
        "test_label_counts": test_counts,
        "bootstrap": {
            "method": "paired nonparametric percentile bootstrap",
            "confidence_level": 0.95,
            "resamples": args.bootstrap_resamples,
            "random_seed": BOOTSTRAP_SEED,
        },
        "ablation": run_ablation(
            test_rows,
            include_qwen=args.include_qwen,
            bootstrap_resamples=args.bootstrap_resamples,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
