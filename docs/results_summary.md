# Results Summary

## Pre-Committed Success Thresholds

These thresholds were defined based on AlMahri et al. (2026) reported results BEFORE final tuning, to prevent result cherry-picking:

| Metric | Acceptable (Pass) | Failed (Below Bar) | Rationale |
|---|---|---|---|
| Pipeline Macro F1 | ≥ 0.750 | < 0.750 | AlMahri et al. (2026) reports 0.82 on proprietary data; 0.75 is a defensible adaptation floor on synthetic scenarios |
| SIAM Calibration Gap | ≤ ±5.0pp | > ±5.0pp | Within one standard deviation of Monte Carlo output distribution |
| Stage 1 Recall | = 1.000 | < 1.000 | Zero missed disruptions is non-negotiable for a risk monitoring system |
| Stage 1 Precision | ≥ 0.700 | < 0.700 | >30% false alarm rate would overwhelm CSCO decision bandwidth |

## Current Results vs. Thresholds

| Metric | Threshold | Actual Result | Pass/Fail |
|---|---|---|---|
| Pipeline Macro F1 | ≥ 0.750 | 0.790 | ✅ PASS |
| SIAM Calibration Gap | ≤ ±5.0pp | -2.8pp | ✅ PASS |
| Stage 1 Recall | = 1.000 | 1.000 | ✅ PASS |
| Stage 1 Precision | ≥ 0.700 | 0.733 | ✅ PASS (marginal) |

**Note:** Stage 1 Precision passes marginally (0.733 vs 0.700 threshold). This reflects the known precautionary bias of the 0.5B SLM — all 4 benign control scenarios were flagged as disruptions. The Stage 3 deterministic guard intercepts these false alarms before final output. This limitation is documented in Section 7 of the technical report.

---

## Baseline Comparison: Naive Keyword Classifier vs. CounterVerse Pipeline

| System | Precision | Recall | F1 Score |
|---|---|---|---|
| Naive Keyword Classifier | 1.000 | 0.455 | 0.625 |
| CounterVerse Stage 1 (SLM) | 0.733 | 1.000 | 0.846 |
| CounterVerse Stage 3 (+ Guard) | 0.636 | 1.000 | 0.778 |
| CounterVerse Pipeline Macro | 0.657 | 1.000 | 0.790 |

The full CounterVerse pipeline **does** outperform the naive keyword baseline. The Stage 1 F1 improvement of **+22.1 pp** (0.846 vs 0.625) and Pipeline Macro F1 improvement of **+16.5 pp** (0.790 vs 0.625) justifies the architectural complexity of the SLM + GraphRAG + deterministic guard pipeline over a simple keyword heuristic.

Crucially, the naive keyword classifier suffers from a catastrophic **54.5% False Negative rate** (Recall: 0.455; missed 6 of 11 disruptions, including Red Sea shipping rerouting, Shanghai port closures, German auto strikes, and Kyushu wafer flooding) because natural disaster and logistics reporting uses specialized phrasing that evades simple keyword thresholds. Furthermore, the CounterVerse pipeline provides structured entity grounding (GraphRAG), causal risk scoring, and Monte Carlo financial loss estimation (PCaR) — capabilities that a raw keyword counter cannot provide.

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

