# Results Summary

## Pre-Committed Success Thresholds

These thresholds were defined based on AlMahri et al. (2026) reported results BEFORE final tuning, to prevent result cherry-picking:

| Metric | Acceptable (Pass) | Failed (Below Bar) | Rationale |
|---|---|---|---|
| Pipeline Macro F1 | ≥ 0.750 | < 0.750 | AlMahri et al. (2026) reports 0.82 on proprietary data; 0.75 is a defensible adaptation floor on synthetic scenarios |
| SIAM Calibration Gap | ≤ ±5.0pp | > ±5.0pp | Within one standard deviation of Monte Carlo output distribution |
| Stage 1 Recall | = 1.000 | < 1.000 | Zero missed disruptions is non-negotiable for a risk monitoring system |
| Stage 1 Precision | ≥ 0.700 | < 0.700 | >30% false alarm rate would overwhelm CSCO decision bandwidth |

## Current Results vs. Thresholds (Phase 6 Post-Upgrade)

| Metric | Threshold | Phase 0 Baseline | Phase 6 Result | Pass/Fail | Delta |
|---|---|---|---|---|---|
| **Pipeline Macro F1** | ≥ 0.750 | 0.812 | **0.933** | ✅ PASS | +0.121 |
| **SIAM Calibration Gap** | ≤ ±5.0pp | -2.8pp | **-2.8pp** | ✅ PASS | 0.0pp |
| **Stage 1 Recall** | = 1.000 | 1.000 | **1.000** | ✅ PASS | 0.000 |
| **Stage 1 Precision** | ≥ 0.700 | 0.733 | **1.000** | ✅ PASS | +0.267 |
| **Stage 1 Specificity** | ≥ 80.0% | 0.0% | **100.0%** | ✅ PASS | +100.0% |

**Note on Precautionary Bias Resolution:** In Phase 0, Stage 1 Precision passed marginally (0.733 vs 0.700 threshold) because all 4 benign control scenarios were falsely flagged as disruptions (0.0% specificity). Following Phase 3 prompt hardening with few-shot benign contrastive examples and mandatory `confidence_reason` attribution, Stage 1 achieves **100.0% specificity** (all 4 benign events rejected) and **1.000 precision** without sacrificing 100% recall.

---

## Table 5: Multi-Agent Pipeline Scorecard (AlMahri et al. 2026 Format)

*Engine: Local Qwen2.5-0.5B-Instruct on GPU (bfloat16) across 15 Synthesized Benchmark Scenarios (11 True Disruption / 4 Benign Control).*

| Agent / Stage | Precision | Recall | F1 Score | Phase 0 Base F1 | Delta vs. Base | Regression Status |
|---|---|---|---|---|---|---|
| **Disruption Monitoring (Stage 1)** | 1.000 | 1.000 | **1.000** | 0.846 | +0.154 | ✅ PASS |
| **Entity & Type Classification (Stage 2)** | 0.909 | 1.000 | **0.952** | 0.778 | +0.174 | ✅ PASS |
| **Risk Manager Deterministic (Stage 3)** | 0.800 | 1.000 | **0.889** | 0.778 | +0.111 | ✅ PASS |
| **CSCO Decision Strategy (Stage 4)** | 0.800 | 1.000 | **0.889** | 0.846 | +0.043 | ✅ PASS |
| **Pipeline Macro Average** | **0.877** | **1.000** | **0.933** | **0.812** | **+0.121** | ✅ **ALL PASS** |

### Confusion Matrix Summary (Disruption Detection):
- **True Positives (TP):** 11 / 11 actual disruptions detected
- **False Positives (FP):** 0 / 4 benign events falsely triggered
- **False Negatives (FN):** 0 / 11 disruptions missed
- **True Negatives (TN):** 4 / 4 benign events correctly filtered
- **Specificity (False Alarm Rejection):** **100.0%** (up from 0.0% in Phase 0)

---

## Baseline Comparison: Naive Keyword Classifier vs. CounterVerse Pipeline

| System | Precision | Recall | F1 Score | Specificity |
|---|---|---|---|---|
| Naive Keyword Classifier | 1.000 | 0.455 | 0.625 | 100.0% |
| CounterVerse Stage 1 (Phase 0 Baseline) | 0.733 | 1.000 | 0.846 | 0.0% |
| CounterVerse Full Pipeline (Phase 0 Baseline) | 0.684 | 1.000 | 0.812 | 0.0% (raw SLM) |
| **CounterVerse Stage 1 (Phase 6 Post-Upgrade)** | **1.000** | **1.000** | **1.000** | **100.0%** |
| **CounterVerse Full Pipeline (Phase 6 Post-Upgrade)** | **0.877** | **1.000** | **0.933** | **100.0%** |

The hardened CounterVerse pipeline decisively outperforms the naive keyword baseline across all dimensions. While the naive keyword classifier achieves high precision on trivial strings, it suffers from a catastrophic **54.5% False Negative rate** (Recall: 0.455; missing 6 of 11 disruptions, including Red Sea maritime reroutes, Shanghai port congestions, and Kyushu silicon wafer floods) because multi-tier supply chain disruptions use specialized industry phrasing. In contrast, CounterVerse achieves **100% Recall** while maintaining **100% Specificity** and **0.933 Pipeline Macro F1**.

---

### Phase History & Run Notes


- Phase 0: GPU smoke test logs go in `docs/environment.md`.
- Phase 3: per-field F1 (zero-shot vs fine-tuned if approved).
- Phase 4: `check_model()` + three ±20% robustness plots (not confidence intervals).
- Phase 5: three scenario histograms + PCaR table, all parameters tagged ASSUMPTION.

This system does **not** report statistical forecasts of future IIP.

---

## Domain Expert Sanity Check (Pending)

**Status:** Not yet completed.

**Plan:** Share the dashboard with one person with real automotive procurement or supply chain management exposure. Ask:
1. Does the CSCO directive logic match how a real risk manager would respond to a Tier-1 semiconductor shortage signal?
2. Is anything in the causal chain assumptions obviously wrong to an industry insider?
3. Does the 90-day disruption duration for the 2021 scenario match real procurement timelines?

**Why this matters:** No amount of additional code closes the gap between academic modeling assumptions and real procurement behavior. One informal domain-expert conversation is more valuable than additional algorithmic complexity for this specific gap.

**To be updated:** Record feedback here after conversation, even informally. Format: [Expert background] + [Key feedback points] + [Any assumption flagged as unrealistic].

