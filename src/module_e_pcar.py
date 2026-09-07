"""
Module E: Procurement Cost-at-Risk Engine (Dummy Implementation for Phase 1)

This module calculates the Procurement Cost-at-Risk (PCaR) in financial terms
based on the Monte Carlo production drop distribution and calibration constants.
"""

import time
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Sourced from UN Comtrade (India Imports HS 8542, 2022 Full Year: $16.12B USD @ 83.0 INR/USD = ₹1,33,814.34 Crore)
DEFAULT_COMTRADE_HS8542_BASELINE_CRORE = 133814.34

# Sourced OEM Profiles: SIAM FY2023-24 Passenger Vehicle Market Shares & Component Chain Dependencies
# Formula: Company Base Spend = Industry Baseline × Market Share (%) × Chain Dependency Ratio (%)
OEM_PROFILES = {
    "Maruti Suzuki": {
        "market_share": 0.417,         # SIAM FY24: 41.7% Passenger Vehicle market share
        "dependency_ratio": 0.38,      # Estimated BOM share of microcontrollers / ECU ICs in powertrain & cabin
        "description": "India's largest automaker; high-volume mass-market PV"
    },
    "Hyundai India": {
        "market_share": 0.146,         # SIAM FY24: 14.6% PV market share
        "dependency_ratio": 0.42,      # High electronics penetration (ADAS, digital cockpit, dual displays)
        "description": "Second largest PV maker; higher electronic component density"
    },
    "Tata Motors": {
        "market_share": 0.139,         # SIAM FY24: 13.9% PV market share (plus EV leadership ~70% EV share)
        "dependency_ratio": 0.45,      # High EV inverter/BMS and connected telematics exposure
        "description": "EV market leader (~70% EV share); high semiconductor intensity"
    },
    "Mahindra": {
        "market_share": 0.112,         # SIAM FY24: 11.2% PV (SUV market leader)
        "dependency_ratio": 0.44,      # Advanced electronic architecture in modern SUV platforms
        "description": "SUV market leader; heavily impacted in 2021 chip crisis"
    },
    "Entire Indian Automotive Industry": {
        "market_share": 1.000,
        "dependency_ratio": 1.00,
        "description": "Macro-level aggregate Indian automotive semiconductor import exposure"
    }
}

# OEM Revenue Realization Assumptions (FY2023-24 Baseline)
# NOTE: These values are assumed industry-average realizations based on 
# publicly reported FY23-24 revenue and vehicle volume data from annual reports.
# They are modeled estimates for academic demonstration, not certified audited figures.
OEM_REALIZATION_LAKH_PER_UNIT = {
    "Maruti Suzuki": 6.2,    # Mass-market PV segment blend
    "Tata Motors": 8.8,      # Commercial vehicle + PV blend
    "Mahindra": 11.4,        # SUV / higher ASP vehicle blend
    "Hyundai India": 7.9,    # Mid-market PV segment blend
    "Industry Average": 7.5  # Weighted industry average (default)
}

def calculate_pcar(
    mc_samples: np.ndarray,
    baseline_revenue_crore: float = DEFAULT_COMTRADE_HS8542_BASELINE_CRORE,
    company_name: str = "Maruti Suzuki"
) -> dict:
    """
    Calculates Procurement Cost-at-Risk (PCaR) metrics based on simulated production drop samples
    calibrated to India's real semiconductor/IC import baseline, scaled to the company level.
    
    Formula:
      Company Base = Industry_Baseline (₹1,33,814 Cr) × Market_Share% × Chain_Dependency%
      Company Loss = Production_Drop% × Company Base × Stochastic_Premium_Multiplier U[1.3, 2.8]
    
    Args:
        mc_samples: Numpy array of simulated production drop percentages (or MonteCarloResult dict).
        baseline_revenue_crore: Baseline semiconductor import turnover in Crore INR 
                                (Default: ₹1,33,814.34 Crore from UN Comtrade HS 8542).
        company_name: Target OEM ("Maruti Suzuki", "Hyundai India", "Tata Motors", "Mahindra",
                      or "Entire Indian Automotive Industry").
        
    Returns:
        A dictionary of company-allocated financial risk metrics in Crore INR.
    """
    logger.info(f"Calculating PCaR metrics for enterprise: {company_name}...")
    
    # Simulate processing time
    time.sleep(0.1)
    
    # Handle dict or MonteCarloResult input gracefully
    if isinstance(mc_samples, dict) and "samples" in mc_samples:
        samples_array = np.asarray(mc_samples["samples"])
    else:
        samples_array = np.asarray(mc_samples)
    
    # Resolve company allocation factors
    profile = OEM_PROFILES.get(company_name, OEM_PROFILES["Maruti Suzuki"])
    market_share = profile["market_share"]
    dependency_ratio = profile["dependency_ratio"]
    effective_base_crore = baseline_revenue_crore * market_share * dependency_ratio
    
    # Convert percentage drop to fraction
    drop_fractions = samples_array / 100.0
    
    # Generate stochastic Spot Premium Multiplier (between 1.3 and 2.8)
    premium_multiplier_samples = np.random.uniform(low=1.3, high=2.8, size=len(samples_array))
    
    # Formula: Company Loss = Production_Drop% * Effective_Company_Base * Premium_Multiplier
    loss_samples = drop_fractions * effective_base_crore * premium_multiplier_samples
    
    metrics = {
        "company_name": company_name,
        "market_share_pct": round(market_share * 100, 1),
        "dependency_ratio_pct": round(dependency_ratio * 100, 1),
        "effective_base_crore": float(round(effective_base_crore, 2)),
        "industry_baseline_crore": float(round(baseline_revenue_crore, 2)),
        "mean_loss_crore": float(np.mean(loss_samples)),
        "median_loss_crore": float(np.median(loss_samples)),
        "pcar_95_crore": float(np.percentile(loss_samples, 95)),
        "pcar_99_crore": float(np.percentile(loss_samples, 99)),
        "worst_case_loss_crore": float(np.max(loss_samples)),
        "allocation_formula": "Industry_Baseline (₹1,33,814 Cr) × Market_Share% × Chain_Dependency% × Production_Drop% × Premium_Multiplier",
        "_loss_samples": loss_samples,
    }
    
    logger.info(f"Calculated PCaR 95% for {company_name}: ₹{metrics['pcar_95_crore']:,.0f} Crore (Base: ₹{effective_base_crore:,.0f} Cr)")
    return metrics


SUPPORTED_OEM_COMPANIES = ["Maruti Suzuki", "Tata Motors", "Mahindra", "Hyundai India"]

COMPANY_SYNONYMS = {
    "maruti suzuki": "Maruti Suzuki",
    "maruti": "Maruti Suzuki",
    "msil": "Maruti Suzuki",
    "tata motors": "Tata Motors",
    "tata": "Tata Motors",
    "tml": "Tata Motors",
    "mahindra": "Mahindra",
    "m&m": "Mahindra",
    "mahindra & mahindra": "Mahindra",
    "hyundai india": "Hyundai India",
    "hyundai": "Hyundai India",
    "hmil": "Hyundai India",
}


def calculate_pcar_by_company(
    company_name: str,
    macro_pcar_result: dict
) -> dict:
    """
    Calculates company-specific Procurement Cost-at-Risk (PCaR) from macro/aggregate industry PCaR.
    
    Formula (identical to macro formulation scaled by company allocation factors):
      Company Base Spend = Industry Baseline × Market Share (%) × Dependency Ratio (%)
      Company Loss = Macro Loss × Market Share (%) × Dependency Ratio (%)
    
    Args:
        company_name: Target automaker. Must be one of:
                      ['Maruti Suzuki', 'Tata Motors', 'Mahindra', 'Hyundai India'].
        macro_pcar_result: Return dictionary from macro-level calculate_pcar()
                           (e.g., company_name='Entire Indian Automotive Industry').
    
    Returns:
        A dictionary containing company-specific PCaR metrics, market share, dependency ratio,
        and VaR percentiles (95% and 99%).
    """
    # 1. Normalize and validate company name
    norm_key = str(company_name).strip().lower()
    canonical_name = COMPANY_SYNONYMS.get(norm_key)
    if not canonical_name:
        for sup in SUPPORTED_OEM_COMPANIES:
            if sup.lower() == norm_key:
                canonical_name = sup
                break
    if not canonical_name:
        raise ValueError(
            f"Unsupported company '{company_name}'. "
            f"Must be one of {SUPPORTED_OEM_COMPANIES}."
        )

    # 2. Retrieve OEM profile allocation parameters
    profile = OEM_PROFILES[canonical_name]
    market_share = profile["market_share"]
    dependency_ratio = profile["dependency_ratio"]
    allocation_factor = market_share * dependency_ratio

    # 3. Retrieve baseline turnover
    industry_baseline = float(
        macro_pcar_result.get(
            "industry_baseline_crore",
            macro_pcar_result.get("effective_base_crore", DEFAULT_COMTRADE_HS8542_BASELINE_CRORE)
        )
    )
    effective_company_base = industry_baseline * allocation_factor

    # 4. Calculate company PCaR using the SAME formula as macro PCaR
    # If raw macro loss samples are available, derive empirical percentiles directly:
    if "_loss_samples" in macro_pcar_result and macro_pcar_result["_loss_samples"] is not None:
        macro_samples = np.asarray(macro_pcar_result["_loss_samples"])
        company_samples = macro_samples * allocation_factor
        mean_loss = float(np.mean(company_samples))
        median_loss = float(np.median(company_samples))
        pcar_95 = float(np.percentile(company_samples, 95))
        pcar_99 = float(np.percentile(company_samples, 99))
        worst_case = float(np.max(company_samples))
    else:
        # Scale scalar macro percentiles by the exact linear factor (market_share * dependency_ratio)
        macro_mean = float(macro_pcar_result.get("mean_loss_crore", 0.0))
        macro_median = float(macro_pcar_result.get("median_loss_crore", macro_mean))
        macro_p95 = float(macro_pcar_result.get("pcar_95_crore", 0.0))
        macro_p99 = float(macro_pcar_result.get("pcar_99_crore", 0.0))
        macro_worst = float(macro_pcar_result.get("worst_case_loss_crore", macro_p99))

        mean_loss = macro_mean * allocation_factor
        median_loss = macro_median * allocation_factor
        pcar_95 = macro_p95 * allocation_factor
        pcar_99 = macro_p99 * allocation_factor
        worst_case = macro_worst * allocation_factor
        company_samples = None

    metrics = {
        "company_name": canonical_name,
        "market_share_pct": round(market_share * 100, 1),
        "dependency_ratio_pct": round(dependency_ratio * 100, 1),
        "allocation_factor": round(allocation_factor, 4),
        "effective_base_crore": float(round(effective_company_base, 2)),
        "industry_baseline_crore": float(round(industry_baseline, 2)),
        "mean_loss_crore": float(round(mean_loss, 2)),
        "median_loss_crore": float(round(median_loss, 2)),
        "pcar_95_crore": float(round(pcar_95, 2)),
        "pcar_99_crore": float(round(pcar_99, 2)),
        "worst_case_loss_crore": float(round(worst_case, 2)),
        "allocation_formula": "Industry_Baseline (₹1,33,814 Cr) × Market_Share% × Chain_Dependency% × Production_Drop% × Premium_Multiplier",
        "macro_reference": {
            "macro_mean_loss_crore": float(round(macro_pcar_result.get("mean_loss_crore", 0.0), 2)),
            "macro_pcar_95_crore": float(round(macro_pcar_result.get("pcar_95_crore", 0.0), 2)),
            "macro_pcar_99_crore": float(round(macro_pcar_result.get("pcar_99_crore", 0.0), 2)),
        }
    }
    if company_samples is not None:
        metrics["_loss_samples"] = company_samples

    logger.info(
        f"Calculated Company PCaR for {canonical_name}: "
        f"95% VaR = ₹{metrics['pcar_95_crore']:,.0f} Cr (Base: ₹{effective_company_base:,.0f} Cr)"
    )
    return metrics

