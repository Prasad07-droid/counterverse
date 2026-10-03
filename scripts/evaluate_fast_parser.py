#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/evaluate_fast_parser.py
===============================
Evaluates the Fast Deterministic Parser (and optionally Qwen2.5-0.5B-Instruct SLM)
across:
  1. The original 15 synthesized scenarios (data/synthesized_scenarios.json)
  2. The new 30 held-out adversarial scenarios (data/heldout_adversarial_scenarios.json)

Computes Precision, Recall, and F1 across four evaluation stages:
  - Stage 1: Disruption Monitoring (Relevance Filtering)
  - Stage 2: Classification (Disruption Type & Component Matching)
  - Stage 3: Risk Manager Agent (Deterministic Risk Level)
  - Stage 4: CSCO Decision (Strategic Directive Alignment)

Outputs structured evaluation metrics to data/evaluation_fast_parser.json.
Existing data/evaluation_results.json remains untouched.
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.module_b_slm import extract_signal_fast, extract_signal
from src.module_c_causal import calculate_deterministic_risk_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_fast_parser")


def safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def calculate_metrics(tp: int, fp: int, fn: int) -> dict:
    prec = safe_div(tp, tp + fp)
    rec = safe_div(tp, tp + fn)
    f1 = safe_div(2 * prec * rec, prec + rec)
    return {"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)}


def evaluate_scenario_set(
    scenarios: List[Dict[str, Any]],
    engine_name: str = "fast",
    extractor_func = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Evaluates a list of scenarios and returns:
    (table_5_metrics, detailed_results, misclassifications)
    """
    stage1_tp = stage1_fp = stage1_fn = stage1_tn = 0
    stage2_tp = stage2_fp = stage2_fn = 0
    stage3_tp = stage3_fp = stage3_fn = 0
    stage4_tp = stage4_fp = stage4_fn = 0

    detailed_results = []
    misclassifications = []

    for sc in scenarios:
        sc_id = sc["id"]
        headline = sc["headline"]
        gt = sc["ground_truth"]
        category = sc.get("category", "unspecified")

        # Ingest signal
        if extractor_func:
            signal = extractor_func(headline)
        elif engine_name == "slm":
            signal = extract_signal(headline, simulate_delay=False, engine="slm")
        else:
            signal = extract_signal_fast(headline)

        signal["headline"] = headline

        # Stage 1: Relevance Filtering
        pred_is_disruption = bool(signal.get("is_disruption", False))
        gt_is_disruption = bool(gt.get("is_disruption", False))

        if gt_is_disruption and pred_is_disruption:
            stage1_tp += 1
        elif not gt_is_disruption and pred_is_disruption:
            stage1_fp += 1
        elif gt_is_disruption and not pred_is_disruption:
            stage1_fn += 1
        else:
            stage1_tn += 1

        # Stage 2: Disruption Type & Component Matching (conditioned on actual disruptions)
        if gt_is_disruption:
            pred_type = str(signal.get("disruption_type", "")).strip().lower()
            gt_type = str(gt.get("disruption_type", "")).strip().lower()
            type_match = (pred_type == gt_type)

            pred_comp = str(signal.get("component", "")).strip().lower()
            gt_comp = str(gt.get("component", "")).strip().lower()
            comp_match = (gt_comp in pred_comp or pred_comp in gt_comp)

            if type_match and comp_match:
                stage2_tp += 1
            elif type_match or comp_match:
                stage2_tp += 1  # partial match
            else:
                stage2_fp += 1

        # Stage 3 & 4: Risk Scoring & Decision Alignment
        if pred_is_disruption:
            risk_meta = calculate_deterministic_risk_score(signal)
            pred_risk_level = risk_meta["risk_level"]
            pred_risk_score = risk_meta["risk_score"]

            if gt_is_disruption:
                if pred_risk_level == gt["expected_risk_level"]:
                    stage3_tp += 1
                    stage4_tp += 1
                else:
                    stage3_fp += 1
                    stage4_fp += 1
            else:
                stage3_fp += 1
                stage4_fp += 1
        else:
            pred_risk_level = "LOW"
            pred_risk_score = 0.0
            if not gt_is_disruption:
                stage3_tp += 1
                stage4_tp += 1
            else:
                stage3_fn += 1
                stage4_fn += 1

        # Match assessment
        relevance_match = (pred_is_disruption == gt_is_disruption)
        pred_type_clean = signal.get("disruption_type", "None")
        type_match_clean = (str(pred_type_clean).lower() == str(gt["disruption_type"]).lower())
        risk_match = (pred_risk_level == gt["expected_risk_level"])
        overall_match = relevance_match and (type_match_clean or not gt_is_disruption) and risk_match

        res_entry = {
            "id": sc_id,
            "headline": headline,
            "category": category,
            "gt_disruption": gt_is_disruption,
            "pred_disruption": pred_is_disruption,
            "gt_type": gt["disruption_type"],
            "pred_type": pred_type_clean,
            "pred_risk_score": pred_risk_score,
            "pred_risk_level": pred_risk_level,
            "gt_risk_level": gt["expected_risk_level"],
            "match": "YES" if overall_match else "NO",
            "engine": signal.get("engine", engine_name)
        }
        detailed_results.append(res_entry)

        if not overall_match:
            reasons = []
            if not relevance_match:
                reasons.append(f"Relevance error: expected is_disruption={gt_is_disruption}, got {pred_is_disruption}")
            if gt_is_disruption and not type_match_clean:
                reasons.append(f"Disruption type error: expected '{gt['disruption_type']}', got '{pred_type_clean}'")
            if not risk_match:
                reasons.append(f"Risk level error: expected '{gt['expected_risk_level']}', got '{pred_risk_level}' ({pred_risk_score:.3f})")

            misclassifications.append({
                "id": sc_id,
                "headline": headline,
                "expected": f"{gt['disruption_type']} ({gt['expected_risk_level']}) [disruption={gt_is_disruption}]",
                "predicted": f"{pred_type_clean} ({pred_risk_level}) [disruption={pred_is_disruption}]",
                "risk_score": pred_risk_score,
                "diagnostic_reasons": reasons
            })

    # Metrics computation
    m_disruption = calculate_metrics(stage1_tp, stage1_fp, stage1_fn)
    m_class = calculate_metrics(stage2_tp, stage2_fp, stage2_fn)
    m_risk = calculate_metrics(stage3_tp, stage3_fp, stage3_fn)
    m_csco = calculate_metrics(stage4_tp, stage4_fp, stage4_fn)

    macro_prec = round((m_disruption["precision"] + m_class["precision"] + m_risk["precision"] + m_csco["precision"]) / 4, 3)
    macro_rec = round((m_disruption["recall"] + m_class["recall"] + m_risk["recall"] + m_csco["recall"]) / 4, 3)
    macro_f1 = round((m_disruption["f1"] + m_class["f1"] + m_risk["f1"] + m_csco["f1"]) / 4, 3)

    table_5 = {
        "disruption_monitoring": m_disruption,
        "classification": m_class,
        "risk_manager": m_risk,
        "csco_decision": m_csco,
        "macro_average": {
            "precision": macro_prec,
            "recall": macro_rec,
            "f1": macro_f1
        }
    }

    return table_5, detailed_results, misclassifications


def print_table(title: str, metrics: Dict[str, Any]):
    print("\n" + "=" * 65)
    print(f" {title.upper()}")
    print("=" * 65)
    print(f"{'Stage / Agent':<26} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10}")
    print("-" * 65)
    for stage_key, label in [
        ("disruption_monitoring", "Disruption Monitoring"),
        ("classification", "Classification"),
        ("risk_manager", "Risk Manager"),
        ("csco_decision", "CSCO Decision"),
        ("macro_average", "Macro Average")
    ]:
        m = metrics[stage_key]
        print(f"{label:<26} | {m['precision']:<10.3f} | {m['recall']:<10.3f} | {m['f1']:<10.3f}")
    print("=" * 65)


def main():
    synthesized_path = _PROJECT_ROOT / "data" / "synthesized_scenarios.json"
    heldout_path = _PROJECT_ROOT / "data" / "heldout_adversarial_scenarios.json"

    if not synthesized_path.exists():
        print(f"Error: {synthesized_path} not found.")
        return
    if not heldout_path.exists():
        print(f"Error: {heldout_path} not found.")
        return

    with open(synthesized_path, "r", encoding="utf-8") as f:
        scenarios_15 = json.load(f)

    with open(heldout_path, "r", encoding="utf-8") as f:
        scenarios_30 = json.load(f)

    all_scenarios = scenarios_15 + scenarios_30

    print(f"Loaded {len(scenarios_15)} original scenarios and {len(scenarios_30)} held-out adversarial scenarios.")

    # 1. Evaluate Fast Deterministic Parser on original 15
    print("\n[1/4] Evaluating Fast Deterministic Parser on Original 15 Scenarios...")
    fast_m15, fast_det15, fast_misc15 = evaluate_scenario_set(
        scenarios_15, engine_name="fast", extractor_func=extract_signal_fast
    )
    print_table("Fast Parser — Original 15 Scenarios", fast_m15)

    # 2. Evaluate Fast Deterministic Parser on new 30 held-out
    print("\n[2/4] Evaluating Fast Deterministic Parser on 30 Held-Out Adversarial Scenarios...")
    fast_m30, fast_det30, fast_misc30 = evaluate_scenario_set(
        scenarios_30, engine_name="fast", extractor_func=extract_signal_fast
    )
    print_table("Fast Parser — 30 Held-Out Scenarios", fast_m30)

    # 3. Check local Qwen SLM availability
    qwen_available = False
    qwen_m30 = None
    qwen_det30 = None
    qwen_misc30 = None

    try:
        import torch
        if torch.cuda.is_available():
            from src.module_b_slm import get_slm_model
            model_res = get_slm_model(timeout_seconds=20)
            if model_res is not None:
                qwen_available = True
    except Exception as e:
        logger.warning(f"Could not load local Qwen SLM: {e}")

    if qwen_available:
        print("\n[3/4] Running Qwen2.5-0.5B-Instruct on 30 Held-Out Scenarios (Local GPU bf16)...")
        qwen_m30, qwen_det30, qwen_misc30 = evaluate_scenario_set(
            scenarios_30, engine_name="slm"
        )
        print_table("Qwen2.5-0.5B SLM — 30 Held-Out Scenarios", qwen_m30)
    else:
        print("\n[3/4] Skipping Qwen SLM evaluation on 30 held-out scenarios (CUDA or weights unavailable).")

    # 4. Print Misclassified Cases Summary
    print("\n" + "=" * 95)
    print(f" MISCLASSIFICATION DIAGNOSTICS (Fast Parser on 30 Held-Out: {len(fast_misc30)} cases)")
    print("=" * 95)
    for m in fast_misc30:
        print(f"ID: {m['id']} | Headline: \"{m['headline'][:65]}...\"")
        print(f"  Expected : {m['expected']}")
        print(f"  Predicted: {m['predicted']} (Score: {m['risk_score']:.3f})")
        for r in m["diagnostic_reasons"]:
            print(f"  -> Reason: {r}")
        print("-" * 95)

    # 5. Output to data/evaluation_fast_parser.json
    output_data = {
        "evaluation_timestamp": str(Path(__file__).stat().st_mtime),
        "fast_parser_evaluation": {
            "original_15_scenarios": {
                "n_samples": len(scenarios_15),
                "metrics": fast_m15,
                "misclassifications_count": len(fast_misc15),
                "misclassifications": fast_misc15,
            },
            "heldout_30_scenarios": {
                "n_samples": len(scenarios_30),
                "metrics": fast_m30,
                "misclassifications_count": len(fast_misc30),
                "misclassifications": fast_misc30,
            }
        },
        "qwen_slm_evaluation": {
            "status": "completed" if qwen_available else "skipped_unavailable",
            "heldout_30_scenarios": {
                "n_samples": len(scenarios_30) if qwen_available else 0,
                "metrics": qwen_m30,
                "misclassifications_count": len(qwen_misc30) if qwen_misc30 else 0,
                "misclassifications": qwen_misc30 or [],
            } if qwen_available else None
        }
    }

    out_file = _PROJECT_ROOT / "data" / "evaluation_fast_parser.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nSaved evaluation results to {out_file}")


if __name__ == "__main__":
    main()
