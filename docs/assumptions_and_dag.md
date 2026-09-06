# Assumptions and DAG citations

Phase 4 fills every CPT cell with `# SOURCE:` or `# ASSUMPTION:`.

Until then: **no CPT numbers in code.** Do not copy calibration anecdotes into the dashboard as if they were estimated from a large sample.

Fixed DAG: see `.cursorrules`. Do not add/remove edges without written approval.

Placeholder calibration facts (cite when used):

- Maruti production Sep 2020 → Sep 2021: 166,086 → 81,278 (51.1%), from coverage of MSI regulatory filing (see `data/raw/oem_production/SOURCE.md`). Re-file the BSE PDF before treating as locked.
- Tata Motors Q2 FY22 loss ₹4,442 crore — **re-cite the original results release** in Phase 4; do not use until the PDF URL is in this file.

---

## Independence of Calibration and Validation

This section documents whether any input variable feeding the Bayesian priors or severity classification in the September 2021 SIAM scenario was set with knowledge of the actual outcome (41.2% worst-month capacity drop; 54.0% Maruti Suzuki peak drop).

| Variable | Source | Set Before/After Knowing Outcome | Circular? |
|---|---|---|---|
| Disrupted Node (Tier-1 Semiconductor) | AlMahri §3.2 architecture | Before — fixed by architecture | No |
| Shock Magnitude (Level 3 / Severe) | Calibrated to match 2021 event severity | After — set with outcome knowledge | Yes |
| Disruption Duration (90 days) | Calibrated to Q3-Q4 2021 crisis timeline | After — set with outcome knowledge | Yes |
| DR formula weights (UN Comtrade 2022) | UN Comtrade official data | Before — fixed by data vintage | No |
| EB/DC/TC/ED asserted constants | Domain lookup table | Before — fixed by domain mapping | No |
| Monte Carlo distribution shape (Beta) | Standard supply chain literature | Before — not event-specific | No |

**Conclusion:** Shock Magnitude and Disruption Duration were set with reference to the known event. The -2.8pp match therefore demonstrates calibration plausibility, not predictive accuracy on unseen data. This is explicitly labeled as a Calibration Case Study in the dashboard UI. A genuine held-out validation would require a second independently occurring event (e.g., 2024 Red Sea shipping disruption impact on Indian auto imports) with parameters set blind to the outcome.

---

## Risk Formula Weight Provenance & Sensitivity Analysis

### Weight Provenance Table

| Variable | Weight | Basis | Empirically Measured? |
|---|---|---|---|
| EB (Exposure Breadth) | 35% | Domain assertion — AlMahri §3.2.5 | No — asserted constant |
| DR (Dependency Ratio) | 25% | UN Comtrade bilateral trade shares | YES — real measured data |
| DC (Downstream Criticality) | 20% | Domain assertion — automotive ECU literature | No — asserted constant |
| TC (Tier-1 Centrality) | 10% | Graph degree centrality (NetworkX) | Partial — topological, not economic |
| ED (Exposure Depth) | 10% | Tier depth normalized (Tier/4.0) | Partial — structural, not economic |

**Summary: 75% of formula weight rests on domain-asserted constants, 25% on empirically measured trade data (DR). This is a known limitation acknowledged in AlMahri et al. (2026) for domain-adapted implementations.**

### Sensitivity Analysis (±20% perturbation on each asserted constant)

Scores computed via formula: $\text{Risk} = 0.35 \cdot \text{EB} + 0.25 \cdot \text{DR} + 0.20 \cdot \text{DC} + 0.10 \cdot \text{TC} + 0.10 \cdot \text{ED}$  
With DR fixed at 0.560 (China ICs, Comtrade-measured), baseline score is 0.752 (HIGH).

| Variable Perturbed | Direction | New Score | Classification Change? |
|---|---|---|---|
| EB (0.85 baseline) | +20% → 0.85*1.2=1.02 capped at 1.0 | 0.805 (HIGH) | No |
| EB (0.85 baseline) | -20% → 0.85*0.8=0.68 | 0.693 (HIGH) | No |
| DC (0.95 baseline) | +20% → capped at 1.0 | 0.762 (HIGH) | No |
| DC (0.95 baseline) | -20% → 0.76 | 0.715 (HIGH) | No |
| TC (0.75 baseline) | +20% → 0.90 | 0.767 (HIGH) | No |
| TC (0.75 baseline) | -20% → 0.60 | 0.738 (HIGH) | No |
| ED (0.50 baseline) | +20% → 0.60 | 0.762 (HIGH) | No |
| ED (0.50 baseline) | -20% → 0.40 | 0.742 (HIGH) | No |

**Finding:** A ±20% perturbation on any single asserted constant is **not** sufficient to flip the classification from HIGH to MEDIUM. All perturbed scores remain $\ge 0.693$, solidly maintaining the HIGH risk classification ($\ge 0.60$).

---

## OEM Realization Assumptions

| OEM | Realization (₹ Lakh/Unit) | Segment Mix Rationale | Source Basis |
|---|---|---|---|
| Maruti Suzuki | 6.2 | Entry/compact PV dominant | FY24 Annual Report implied ASP |
| Hyundai India | 7.9 | Mid-size SUV & premium hatch | Industry estimates |
| Tata Motors | 8.8 | PV + heavy commercial blend | Consolidated investor presentation |
| Mahindra | 11.4 | Premium SUV dominant | FY24 analyst presentation |
| Industry Average | 7.5 | Weighted baseline | Default used in aggregate PCaR |

*Note: Individual OEM realizations are disclosed modeling assumptions 
for comparative analysis. The core pipeline uses the aggregate ₹7.5 Lakh/unit 
industry average.*


