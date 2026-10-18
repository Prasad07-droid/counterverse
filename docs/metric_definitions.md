# CounterVerse — Quantitative Metric Definitions & Modeling Assumptions

**Document Version:** 2.0.0 (Audited)  
**Target Domain:** Indian Automotive Microcontroller / Integrated Circuit Supply Chain (HS 8542 / HS 8112)  
**System Scope:** Scenario simulation and operational decision support (not predictive forecasting, causal discovery, or audited financial accounting).

---

## 1. Executive Summary & Purpose

This document provides formal, code-aligned mathematical definitions and scenario modeling assumptions for all quantitative metrics emitted by CounterVerse (FastAPI backend, React/Vite dashboard, and Streamlit decision-support interfaces).

All formulas documented below reflect the **active repository code** in [`src/module_c_causal.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_c_causal.py), [`src/module_d_mc.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_d_mc.py), [`src/module_e_pcar.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_e_pcar.py), and [`src/module_i_report.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_i_report.py).

---

## 2. Procurement Cost-at-Risk (PCaR)

### 2.1 Mathematical Formulation

For quantile $q \in (0, 1)$ (typically $q = 0.95$ for 95% Value-at-Risk or $q = 0.99$ for 99% VaR), PCaR(q) represents the $q$-th empirical percentile of total stressed procurement financial exposure across $N$ Monte Carlo draws ($N \ge 10{,}000$):

$$\text{PCaR}(q) = \text{Quantile}_q(\mathbf{L})$$

where the loss vector $\mathbf{L} = (L_1, L_2, \dots, L_N)$ has sample elements:

$$L_i = \left(\frac{D_i}{100}\right) \times B_{\text{effective}} \times M_i$$

with:
- **$D_i \in [0, 100]$:** Simulated automotive production/dispatch drop percentage draw from Monte Carlo step.
- **$B_{\text{effective}}$:** Effective enterprise procurement baseline in Crore INR ($\text{₹ Cr}$):
  $$B_{\text{effective}} = B_{\text{industry}} \times \alpha_{\text{market\_share}} \times \delta_{\text{dependency}}$$
  - $B_{\text{industry}} = \text{₹}1{,}33{,}814.34\text{ Cr}$ / ₹133,814.34 Crore (133814.34 Cr) (UN Comtrade 2022 Full Year India Imports for HS 8542 @ 83.0 INR/USD).
  - $\alpha_{\text{market\_share}}$: OEM passenger vehicle market share (SIAM FY24 baseline).
  - $\delta_{\text{dependency}}$: Estimated bill-of-materials share of microcontrollers / ECU ICs in powertrain & electronic architectures (heuristic proxy 0.38–0.45).
- **$M_i \sim \text{Uniform}[1.3, 2.8]$ (Uniform[1.3, 2.8]):** Stochastic spot-market surge premium multiplier drawn for draw $i$.

### 2.2 Critical Distinction: Spot Premium is Included in $\text{PCaR}$

> [!IMPORTANT]
> Because $M_i \ge 1.3$, **$\text{PCaR}(q)$ includes the spot market surge premium**. It is NOT just the replacement value of the missing parts at standard contract cost; it measures the total cash needed to secure emergency allocation during an industry-wide shortage.

---

## 3. Premium Decomposition (`extra_procurement_cost_*`)

To maintain complete transparency between baseline disrupted value and emergency spot surcharge, CounterVerse computes an additive decomposition:

$$\mathbf{L}_{\text{extra}, i} = \left(\frac{D_i}{100}\right) \times B_{\text{effective}} \times (M_i - 1.0)$$

$$\text{Baseline Disrupted Spend}_i = \left(\frac{D_i}{100}\right) \times B_{\text{effective}} \times 1.0$$

Therefore, for every draw $i$:
$$L_i = \text{Baseline Disrupted Spend}_i + \mathbf{L}_{\text{extra}, i}$$

The reported metric $\text{extra\_procurement\_cost\_p95\_crore}$ is:
$$\text{Quantile}_{0.95}(\mathbf{L}_{\text{extra}})$$

---

## 4. Lost Output Value ($\text{lost\_output\_value\_*}$)

### 4.1 Strict Independence from Procurement Exposure

Lost output value (finished vehicle revenue lost due to curtailed assembly) is an order of magnitude larger than component procurement spend. CounterVerse enforces strict mathematical independence between procurement cost and lost vehicle output:

$$\mathbf{L}_{\text{output}, i} = \left(\frac{D_i}{100}\right) \times B_{\text{output}} \times \alpha_{\text{market\_share}}$$

### 4.2 Honesty Rule on Missing Baselines

If the caller does **not** provide an explicit `baseline_output_value_crore`:
- `lost_output_value_mean_crore = None`
- `lost_output_value_p95_crore = None`
- `lost_output_value_p99_crore = None`
- `lost_output_value_status = "not_calculated_missing_output_value_baseline"`

CounterVerse **never** infers lost vehicle turnover from component trade data.

---

## 5. Deterministic Risk Score ($\text{risk\_score}$)

### 5.1 Ordinal Prioritization Index, NOT a Probability

> [!CAUTION]
> The metric `risk_score` $\in [0.0, 1.0]$ is an **ordinal multi-criteria prioritization index**, NOT an empirical probability of failure, survival, or default. A score of 0.65 does NOT mean a 65% chance of supply disruption; it means the scenario sits in the 65th percentile of the structured risk rubric.

### 5.2 Deterministic Multi-Factor Formula

Adapted from AlMahri et al. (2026), Section 3.2.5:

$$R = 0.35 \cdot E_B + 0.25 \cdot D_R + 0.20 \cdot C_D + 0.10 \cdot T_C + 0.10 \cdot E_D$$

| Factor Symbol | Factor Name | Weight | Definition in CounterVerse |
| :--- | :--- | :---: | :--- |
| $E_B$ | Exposure Breadth | 0.35 | Geographical & supplier concentration of the affected node |
| $D_R$ | Dependency Ratio | 0.25 | Share of Tier-1 / OEM systems dependent on this node |
| $C_D$ | Downstream Criticality | 0.20 | Centrality of node to active Indian assembly plants |
| $T_C$ | Tier-1 Centrality | 0.10 | Degree centrality of direct Tier-1 harness/ECU suppliers |
| $E_D$ | Exposure Depth | 0.10 | Normalized disruption severity & duration duration scale |

### 5.3 Centralized Ordinal Risk Bands

Threshold constants are centralized in `src.module_c_causal`:
- **`HIGH`:** $R \ge 0.60$ (`RISK_THRESHOLD_HIGH = 0.60`)
  - Directive: Qualify Dual Source / Immediate Executive Escalation
- **`MEDIUM`:** $0.45 \le R < 0.60$ (`RISK_THRESHOLD_MEDIUM = 0.45`)
  - Directive: Increase Safety Stock Buffer & Active Weekly Monitoring
- **`LOW`:** $R < 0.45$
  - Directive: Maintain Standard Operations & Routine Watch

---

## 6. 4-State Posterior Probabilities

The causal propagation engine reports 4 discrete supply disruption states:
1. `High (>15%)`
2. `Medium (5-15%)`
3. `Low (<5%)`
4. `None`

### 6.1 Epistemic Character: Model-Assigned Heuristics

> [!NOTE]
> These state probabilities are **model-assigned Bayesian heuristic priors** anchored to the deterministic risk score $R$. They are NOT empirically calibrated frequentist transition probabilities derived from multi-year industrial telemetry.

---

## 7. Monte Carlo Drop Distributions

Production drop samples $D_i$ are simulated in [`src/module_d_mc.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_d_mc.py) using Beta distributions whose shape parameters $(\alpha, \beta)$ are calibrated to the shock's extracted severity and expected duration.

- **Calibrated Scenario Assumptions:** The shape parameters are hand-calibrated against historical crisis benchmarks (e.g., SIAM 2021 chip shortage 37.46% YoY drop benchmark).
- **Not Econometrically Fitted:** They are not maximum-likelihood econometric estimates. Users should treat the Monte Carlo distribution as an exploratory stress-testing tool.

---

## 8. Currency, Vintage, and Scope Invariants

| Parameter | Value | Source / Rationale |
| :--- | :--- | :--- |
| Base Currency | INR ($\text{₹ Crore}$) | Operational standard for Indian automotive industry |
| FX Rate | $83.00\text{ INR/USD}$ | Audited baseline rate for 2022-2024 modeling period |
| Trade Baseline | $\text{₹}1{,}33{,}814.34\text{ Cr}$ | UN Comtrade 2022 Full Year India Imports (HS 8542) |
| Minor Metals Baseline | $\text{₹}72.48\text{ Cr}$ | UN Comtrade 2022 Full Year India Imports (HS 8112) |
| Market Shares | SIAM FY2023-24 | Maruti Suzuki: 41.7%, Hyundai: 14.6%, Tata: 13.9%, M&M: 11.2% |
| Metric Version | `2.0.0` | Sourced data provenance and isolated random state |
