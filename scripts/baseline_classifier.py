"""
Naive Keyword Classifier Baseline for CounterVerse
Provides a pure heuristic keyword-counting baseline to benchmark against the Agentic SLM pipeline.
"""

import json
from pathlib import Path

def naive_keyword_classifier(headline: str) -> dict:
    """
    Naive baseline: counts disruption-related keywords.
    Threshold >= 2 keywords = disruption detected.
    No ML, no graph, no SLM — pure keyword heuristic.
    """
    DISRUPTION_KEYWORDS = [
        "shortage", "disruption", "halt", "closure", "ban", "restrict",
        "delay", "block", "suspend", "crisis", "supply", "chip", 
        "semiconductor", "export", "import", "sanction", "strike",
        "earthquake", "flood", "shutdown", "cutoff", "scarcity"
    ]
    headline_lower = headline.lower()
    matched = [k for k in DISRUPTION_KEYWORDS if k in headline_lower]
    is_disruption = len(matched) >= 2
    return {
        "is_disruption": is_disruption,
        "matched_keywords": matched,
        "keyword_count": len(matched),
        "confidence": min(len(matched) / 5.0, 1.0)
    }

def evaluate_naive_baseline(scenarios_path: Path = None):
    if scenarios_path is None:
        scenarios_path = Path(__file__).resolve().parent.parent / "data" / "synthesized_scenarios.json"
    
    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    
    print(f"{'ID':<8} | {'Ground Truth':<12} | {'Predicted':<12} | {'Matches':<8} | Headline")
    print("-" * 80)
    for s in scenarios:
        res = naive_keyword_classifier(s["headline"])
        gt = s["ground_truth"]["is_disruption"]
        pred = res["is_disruption"]
        
        if gt and pred:
            tp += 1
            status = "TP"
        elif not gt and pred:
            fp += 1
            status = "FP"
        elif not gt and not pred:
            tn += 1
            status = "TN"
        else:
            fn += 1
            status = "FN"
            
        print(f"{s['id']:<8} | {str(gt):<12} | {str(pred):<12} | {status:<8} | {s['headline'][:50]}...")
        
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    print("\n--- Naive Baseline Performance on 15 Scenarios ---")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn
    }

if __name__ == "__main__":
    evaluate_naive_baseline()
