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

---

## Enterprise-Level (Company) PCaR Allocation Methodology

### Problem & Scoping Formulation
The aggregate UN Comtrade HS 8542 baseline (₹1,33,814 Crore, 2022) reflects total Indian import turnover of electronic integrated circuits across the entire automotive sector. Evaluating an individual automaker (e.g. Maruti Suzuki or Tata Motors) against the entire national trade flow overestimates single-enterprise exposure.

### Allocation Mathematical Formula & Boundedness Proof
Individual enterprise exposure is scaled down deterministically using official SIAM market share figures and component BOM dependency ratios:

$$\text{Company Exposed Base} = \text{Macro Baseline (₹1,33,814 Cr)} \times \text{Company Market Share (\%)} \times \text{Chain Dependency Ratio (\%)} $$

$$\text{Company PCaR} = \text{Simulated Production Drop (\%)} \times \text{Company Exposed Base} \times U[1.3, 2.8] $$

### Sourced Empirical Parameters & Dependency Ratio Disclosures (SIAM FY2023-24 Baseline)

| Enterprise / OEM | PV Market Share (%) | Share Basis | Chain Dependency (%) | Dependency Ratio Status | Basis & BOM Rationale | Allocated Sourcing Base | Allocation Ratio |
|---|---|---|---|---|---|---|---|
| **Maruti Suzuki** | 41.7% | SIAM FY24 official disclosures | 38% | **Heuristic Assignment (pending OEM procurement expert validation)** | Mass-market PV blend; dual-sensor ECUs. Domain-informed proxy, NOT an audited OEM BOM disclosure. | ₹21,192 Cr | 15.85% |
| **Hyundai India** | 14.6% | SIAM FY24 official disclosures | 42% | **Heuristic Assignment (pending OEM procurement expert validation)** | Higher electronics intensity (ADAS, digital cockpit). Domain-informed proxy, NOT an audited OEM BOM disclosure. | ₹8,206 Cr | 6.13% |
| **Tata Motors** | 13.9% | SIAM FY24 official disclosures | 45% | **Heuristic Assignment (pending OEM procurement expert validation)** | EV market leadership (~70% EV share); heavy inverter/BMS exposure. Domain-informed proxy, NOT an audited OEM BOM disclosure. | ₹8,370 Cr | 6.26% |
| **Mahindra & Mahindra** | 11.2% | SIAM FY24 official disclosures | 44% | **Heuristic Assignment (pending OEM procurement expert validation)** | Premium SUV platform architecture; multi-microcontroller ECUs. Domain-informed proxy, NOT an audited OEM BOM disclosure. | ₹6,594 Cr | 4.93% |
| **Subtotal (4 Named OEMs)** | **81.4%** | SIAM FY24 | **Weighted 40.7%** | **Combined Heuristic** | Major passenger vehicle manufacturers | **₹44,362 Cr** | **33.16%** |
| **Entire Indian Industry** | 100.0% | Macro UN Comtrade aggregate | 100% | Measured Trade Baseline | National aggregate import turnover (HS 8542) | ₹1,33,814 Cr | 100.00% |

#### Methodological Clarification: Algebraic Boundedness vs. Empirical Accuracy
Summing the allocated exposure across all four named OEMs yields:
$$\sum_{i=1}^{4} \text{Allocation Ratio}_i = 15.85\% + 6.13\% + 6.26\% + 4.93\% = 33.16\%$$

Consequently:
$$\sum_{i=1}^{4} \text{Company PCaR}_i \approx 0.3316 \times \text{Macro PCaR} < \text{Macro PCaR}$$

> [!WARNING]
> **Algebraic Consistency vs. Empirical Accuracy:**  
> The fact that individual company allocations sum to 33.16% ($\le 1.0$) guarantees **algebraic internal consistency by construction**, because the formula is mathematically structured to scale down from the macro baseline ($\text{Macro} \times \text{Share} \times \text{Dependency}$).  
> **It does NOT guarantee empirical ground-truth accuracy.**  
> While market shares (41.7%, 14.6%, etc.) are verified from official SIAM FY24 filings, the dependency ratios (0.38, 0.42, 0.45, 0.44) are analyst-estimated heuristic proxies reflecting relative electronics intensity across vehicle segments, not certified audited OEM Bill of Materials (BOM) disclosures. Until validated through proprietary OEM procurement interviews or confidential enterprise ERP telemetry, these remain domain-asserted modeling assumptions (matching the status of EB, DC, and TC constants in Section 4.2).

The remaining ~66.84% (₹89,452 Cr) represents non-covered passenger vehicle manufacturers (Kia, Toyota, Honda, MG, Volkswagen), commercial vehicles (Tata CV, Ashok Leyland), two-wheelers, tractors, and unexposed non-semiconductor electronic components. This relationship is verified in unit test `test_company_level_pcar_internal_consistency()`.

---

## Auto-Extracted Parameter Derivation & Seeded Determinism

To replace manual UI sliders while maintaining rigorous reproducibility, `src/module_b_slm.py` extracts disruption simulation parameters directly from unstructured headlines using deterministic taxonomy mappings and seeded pseudo-random number generation (PRNG):

### 1. Node & Event Taxonomy Mapping

- **`affected_node`**: Mapped from headline keywords to `ALLOWED_AFFECTED_NODES`:
  - `"Raw Material Supplier"`: keywords like *raw material, mine, mining, refinery, gallium, germanium, lithium, cobalt*
  - `"Port/Logistics"`: keywords like *port, dock, dockworker, container, terminal, shipping, maritime, freight, red sea, suez*
  - `"Tier-1 Supplier"`: keywords like *supplier, plant, factory, powertrain, brake, tier-1*
  - `"Tier-2 Supplier"`: keywords like *battery, cell, sub-tier, tier-2*
  - `"Semiconductor Fab"`: keywords like *fab, foundry, wafer, lithography, semiconductor, chip, microcontroller, ecu*
  - `"Assembly Hub"`: keywords like *assembly, oem, automaker, vehicle*
  - *Fallback:* Defaults strictly to `"Tier-1 Supplier"`.
- **`event_type`**: Mapped from headline keywords to `ALLOWED_EVENT_TYPES`:
  - `"Port closure"`: *port closure, closure, closed*
  - `"Export ban/restriction"`: *export ban, export control, controls, ban, restrict, tariff, quota*
  - `"Factory shutdown"`: *shutdown, shut down, halt, strike, walkout, fire, explosion*
  - `"Natural disaster"`: *earthquake, flood, floods, typhoon, tsunami, hurricane, storm, disaster*
  - `"Geopolitical sanction"`: *sanction, trade war, geopolitical, embargo*
  - `"Raw material shortage"`: *shortage, deficit, curb*
  - `"Logistics delay"`: *delay, congestion, reroute, bottleneck, disrupt*
  - `"Demand shock"`: *demand, sales, earnings, recession*
  - *Fallback:* Defaults strictly to `"Logistics delay"`.

### 2. Seeded PRNG Determinism (`hash(headline)`)

To guarantee that the exact same headline produces identical disruption severity and duration across separate invocations without state persistence, parameters are seeded via:
```python
rng = random.Random(hash(headline))
```

Severity and duration ranges are governed by the classified disruption level:

| Disruption Severity Level | `is_disruption` | `severity_pct` Range | `duration_days` Range |
|---|---|---|---|
| **CRITICAL** | `True` | $80\% - 95\%$ | $60 - 90$ days |
| **HIGH** | `True` | $60\% - 79\%$ | $30 - 59$ days |
| **MEDIUM** | `True` | $35\% - 59\%$ | $15 - 29$ days |
| **LOW** | `True` | $10\% - 30\%$ | $5 - 14$ days |
| **Benign / Non-Disruptive** | `False` | $0\%$ | $1 - 7$ days |

All parameters are strictly bounded: $0 \le \text{severity\_pct} \le 100$ and $1 \le \text{duration\_days} \le 90$. This guarantees schema integrity and determinism across all evaluation and testing pipelines.



