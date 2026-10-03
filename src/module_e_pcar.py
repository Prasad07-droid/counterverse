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
    company_name: str = "Maruti Suzuki",
    baseline_output_value_crore: float = None,
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
        baseline_output_value_crore: Optional annual output-value baseline for the selected
                                     scope. When omitted, lost-output-value keys are returned
                                     as None rather than inferred from procurement spend.

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
    
    # Existing protected metric: total stressed procurement exposure.
    loss_samples = drop_fractions * effective_base_crore * premium_multiplier_samples

    # Additive decomposition: only the premium above the baseline price is an
    # extra procurement cost. This reuses the exact existing random draws.
    extra_procurement_cost_samples = (
        drop_fractions * effective_base_crore * (premium_multiplier_samples - 1.0)
    )

    # Procurement spend is not an output/revenue baseline. Do not relabel it as
    # lost output. Compute this metric only when a caller supplies that baseline.
    lost_output_value_samples = None
    if baseline_output_value_crore is not None:
        if baseline_output_value_crore < 0:
            raise ValueError("baseline_output_value_crore must be non-negative")
        output_scope_factor = market_share if company_name != "Entire Indian Automotive Industry" else 1.0
        effective_output_value_crore = baseline_output_value_crore * output_scope_factor
        lost_output_value_samples = drop_fractions * effective_output_value_crore

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
        "extra_procurement_cost_mean_crore": float(np.mean(extra_procurement_cost_samples)),
        "extra_procurement_cost_median_crore": float(np.median(extra_procurement_cost_samples)),
        "extra_procurement_cost_p95_crore": float(np.percentile(extra_procurement_cost_samples, 95)),
        "extra_procurement_cost_p99_crore": float(np.percentile(extra_procurement_cost_samples, 99)),
        "extra_procurement_cost_worst_case_crore": float(np.max(extra_procurement_cost_samples)),
        "lost_output_value_mean_crore": (
            float(np.mean(lost_output_value_samples)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_median_crore": (
            float(np.median(lost_output_value_samples)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_p95_crore": (
            float(np.percentile(lost_output_value_samples, 95)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_p99_crore": (
            float(np.percentile(lost_output_value_samples, 99)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_worst_case_crore": (
            float(np.max(lost_output_value_samples)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_status": (
            "calculated_from_caller_supplied_output_baseline"
            if lost_output_value_samples is not None
            else "not_calculated_missing_output_value_baseline"
        ),
        "allocation_formula": "Industry_Baseline (₹1,33,814 Cr) × Market_Share% × Chain_Dependency% × Production_Drop% × Premium_Multiplier",
        "_loss_samples": loss_samples,
        "_extra_procurement_cost_samples": extra_procurement_cost_samples,
        "_lost_output_value_samples": lost_output_value_samples,
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

    # Additive procurement-premium decomposition, scaled with the same company
    # procurement allocation factor as the protected PCaR metrics.
    macro_extra_samples = macro_pcar_result.get("_extra_procurement_cost_samples")
    if macro_extra_samples is not None:
        company_extra_samples = np.asarray(macro_extra_samples) * allocation_factor
        extra_metrics = {
            "extra_procurement_cost_mean_crore": float(round(np.mean(company_extra_samples), 2)),
            "extra_procurement_cost_median_crore": float(round(np.median(company_extra_samples), 2)),
            "extra_procurement_cost_p95_crore": float(round(np.percentile(company_extra_samples, 95), 2)),
            "extra_procurement_cost_p99_crore": float(round(np.percentile(company_extra_samples, 99), 2)),
            "extra_procurement_cost_worst_case_crore": float(round(np.max(company_extra_samples), 2)),
        }
    else:
        company_extra_samples = None
        extra_metrics = {
            key: (
                float(round(macro_pcar_result.get(key, 0.0) * allocation_factor, 2))
                if macro_pcar_result.get(key) is not None else None
            )
            for key in (
                "extra_procurement_cost_mean_crore",
                "extra_procurement_cost_median_crore",
                "extra_procurement_cost_p95_crore",
                "extra_procurement_cost_p99_crore",
                "extra_procurement_cost_worst_case_crore",
            )
        }

    # Lost output is separate from procurement exposure and scales by company
    # market share only. It remains unavailable unless the macro call received
    # an explicit output-value baseline.
    macro_output_samples = macro_pcar_result.get("_lost_output_value_samples")
    if macro_output_samples is not None:
        company_output_samples = np.asarray(macro_output_samples) * market_share
        output_metrics = {
            "lost_output_value_mean_crore": float(round(np.mean(company_output_samples), 2)),
            "lost_output_value_median_crore": float(round(np.median(company_output_samples), 2)),
            "lost_output_value_p95_crore": float(round(np.percentile(company_output_samples, 95), 2)),
            "lost_output_value_p99_crore": float(round(np.percentile(company_output_samples, 99), 2)),
            "lost_output_value_worst_case_crore": float(round(np.max(company_output_samples), 2)),
            "lost_output_value_status": "calculated_from_caller_supplied_output_baseline",
        }
    else:
        company_output_samples = None
        output_metrics = {
            "lost_output_value_mean_crore": None,
            "lost_output_value_median_crore": None,
            "lost_output_value_p95_crore": None,
            "lost_output_value_p99_crore": None,
            "lost_output_value_worst_case_crore": None,
            "lost_output_value_status": "not_calculated_missing_output_value_baseline",
        }

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
    metrics.update(extra_metrics)
    metrics.update(output_metrics)
    if company_samples is not None:
        metrics["_loss_samples"] = company_samples
    if company_extra_samples is not None:
        metrics["_extra_procurement_cost_samples"] = company_extra_samples
    if company_output_samples is not None:
        metrics["_lost_output_value_samples"] = company_output_samples

    logger.info(
        f"Calculated Company PCaR for {canonical_name}: "
        f"95% VaR = ₹{metrics['pcar_95_crore']:,.0f} Cr (Base: ₹{effective_company_base:,.0f} Cr)"
    )
    return metrics


# ════════════════════════════════════════════════════════════════
# PHASE 4: CUSTOM BOM UPLOAD — PCaR for Any Company
# ════════════════════════════════════════════════════════════════

import csv
import io
import json as _json


def parse_bom_csv(csv_content: str) -> list:
    """
    Parses CSV BOM content into a list of component dicts.
    Expected CSV columns: component_name, hs_code, annual_spend_crore
    
    Returns:
        List of dicts with keys: component_name, hs_code, annual_spend_crore
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    components = []
    for row in reader:
        try:
            components.append({
                "component_name": row.get("component_name", row.get("name", "")).strip(),
                "hs_code": row.get("hs_code", row.get("hs", "")).strip(),
                "annual_spend_crore": float(row.get("annual_spend_crore", row.get("spend_crore", row.get("spend", 0)))),
            })
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping invalid BOM row: {row} — {e}")
            continue
    return components


def parse_bom_json(json_content: str) -> list:
    """
    Parses JSON BOM content into a list of component dicts.
    Expected JSON: [{"component_name": ..., "hs_code": ..., "annual_spend_crore": ...}, ...]

    Returns:
        List of dicts with keys: component_name, hs_code, annual_spend_crore
    """
    try:
        data = _json.loads(json_content)
    except _json.JSONDecodeError as e:
        logger.error(f"Invalid BOM JSON: {e}")
        return []

    if isinstance(data, dict):
        data = data.get("components", data.get("bom", [data]))
    if not isinstance(data, list):
        return []

    components = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            components.append({
                "component_name": item.get("component_name", item.get("name", "")).strip(),
                "hs_code": str(item.get("hs_code", item.get("hs", ""))).strip(),
                "annual_spend_crore": float(item.get("annual_spend_crore", item.get("spend_crore", item.get("spend", 0)))),
            })
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping invalid BOM item: {item} — {e}")
            continue
    return components


def calculate_pcar_custom_bom(
    mc_samples: np.ndarray,
    bom_components: list,
    company_name: str = "Custom Enterprise",
    ground_against_graph: bool = True,
    baseline_output_value_crore: float = None,
) -> dict:
    """
    Calculates Procurement Cost-at-Risk using a custom Bill of Materials.
    
    Each BOM component specifies its annual procurement spend in Crore INR.
    The total BOM baseline replaces the default UN Comtrade macro baseline,
    enabling PCaR calculation for ANY company with known procurement data.
    
    If ground_against_graph is True, each component is verified against the
    GraphRAG grounding graph for entity validation.
    
    Args:
        mc_samples: Monte Carlo production drop samples (np.ndarray or MonteCarloResult).
        bom_components: List of dicts with keys:
            - component_name: str
            - hs_code: str (e.g. "8542")
            - annual_spend_crore: float
        company_name: Label for the custom enterprise.
        ground_against_graph: Whether to verify components against the graph.
        baseline_output_value_crore: Optional output-value baseline. Lost-output
                                     metrics remain None when it is omitted.

    Returns:
        dict with PCaR metrics plus component-level grounding results.
    """
    logger.info(f"Calculating Custom BOM PCaR for '{company_name}' ({len(bom_components)} components)...")

    if not bom_components:
        raise ValueError("BOM component list is empty. Provide at least one component.")

    # Handle dict or MonteCarloResult input
    if isinstance(mc_samples, dict) and "samples" in mc_samples:
        samples_array = np.asarray(mc_samples["samples"])
    else:
        samples_array = np.asarray(mc_samples)

    # Calculate total BOM baseline
    total_baseline_crore = sum(c.get("annual_spend_crore", 0) for c in bom_components)
    if total_baseline_crore <= 0:
        raise ValueError(f"Total BOM baseline is ₹{total_baseline_crore} Cr — must be positive.")

    # GraphRAG grounding (optional)
    grounding_results = []
    if ground_against_graph:
        try:
            from src.grounding_graph import resolve_entity, get_grounding_graph
            G = get_grounding_graph()
            for comp in bom_components:
                canonical = resolve_entity(comp["component_name"])
                grounding_results.append({
                    "component": comp["component_name"],
                    "hs_code": comp["hs_code"],
                    "spend_crore": comp["annual_spend_crore"],
                    "canonical_name": canonical,
                    "graph_verified": canonical is not None and G.has_node(canonical),
                })
        except ImportError:
            logger.warning("GraphRAG grounding unavailable — skipping BOM verification.")

    # Monte Carlo loss calculation (same formula as calculate_pcar)
    drop_fractions = samples_array / 100.0
    premium_multiplier_samples = np.random.uniform(low=1.3, high=2.8, size=len(samples_array))
    loss_samples = drop_fractions * total_baseline_crore * premium_multiplier_samples
    extra_procurement_cost_samples = (
        drop_fractions * total_baseline_crore * (premium_multiplier_samples - 1.0)
    )
    lost_output_value_samples = None
    if baseline_output_value_crore is not None:
        if baseline_output_value_crore < 0:
            raise ValueError("baseline_output_value_crore must be non-negative")
        lost_output_value_samples = drop_fractions * baseline_output_value_crore

    # Component-level loss allocation
    component_pcars = []
    for comp in bom_components:
        comp_share = comp["annual_spend_crore"] / total_baseline_crore if total_baseline_crore > 0 else 0
        comp_losses = loss_samples * comp_share
        component_pcars.append({
            "component_name": comp["component_name"],
            "hs_code": comp["hs_code"],
            "annual_spend_crore": comp["annual_spend_crore"],
            "share_pct": round(comp_share * 100, 2),
            "mean_loss_crore": float(round(np.mean(comp_losses), 2)),
            "pcar_95_crore": float(round(np.percentile(comp_losses, 95), 2)),
            "pcar_99_crore": float(round(np.percentile(comp_losses, 99), 2)),
        })

    metrics = {
        "company_name": company_name,
        "bom_type": "custom",
        "total_baseline_crore": float(round(total_baseline_crore, 2)),
        "effective_base_crore": float(round(total_baseline_crore, 2)),
        "num_components": len(bom_components),
        "component_count": len(bom_components),
        "mean_loss_crore": float(round(np.mean(loss_samples), 2)),
        "mean_loss_pct": float(round((np.mean(loss_samples) / total_baseline_crore) * 100, 2)) if total_baseline_crore > 0 else 0.0,
        "median_loss_crore": float(round(np.median(loss_samples), 2)),
        "pcar_95_crore": float(round(np.percentile(loss_samples, 95), 2)),
        "pcar_95_pct": float(round((np.percentile(loss_samples, 95) / total_baseline_crore) * 100, 2)) if total_baseline_crore > 0 else 0.0,
        "pcar_99_crore": float(round(np.percentile(loss_samples, 99), 2)),
        "worst_case_loss_crore": float(round(np.max(loss_samples), 2)),
        "worst_case_pct": float(round((np.max(loss_samples) / total_baseline_crore) * 100, 2)) if total_baseline_crore > 0 else 0.0,
        "extra_procurement_cost_mean_crore": float(round(np.mean(extra_procurement_cost_samples), 2)),
        "extra_procurement_cost_median_crore": float(round(np.median(extra_procurement_cost_samples), 2)),
        "extra_procurement_cost_p95_crore": float(round(np.percentile(extra_procurement_cost_samples, 95), 2)),
        "extra_procurement_cost_p99_crore": float(round(np.percentile(extra_procurement_cost_samples, 99), 2)),
        "extra_procurement_cost_worst_case_crore": float(round(np.max(extra_procurement_cost_samples), 2)),
        "lost_output_value_mean_crore": (
            float(round(np.mean(lost_output_value_samples), 2)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_median_crore": (
            float(round(np.median(lost_output_value_samples), 2)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_p95_crore": (
            float(round(np.percentile(lost_output_value_samples, 95), 2)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_p99_crore": (
            float(round(np.percentile(lost_output_value_samples, 99), 2)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_worst_case_crore": (
            float(round(np.max(lost_output_value_samples), 2)) if lost_output_value_samples is not None else None
        ),
        "lost_output_value_status": (
            "calculated_from_caller_supplied_output_baseline"
            if lost_output_value_samples is not None
            else "not_calculated_missing_output_value_baseline"
        ),
        "component_pcars": component_pcars,
        "grounding_results": grounding_results,
        "component_grounding": grounding_results,
        "allocation_formula": "BOM_Baseline × Production_Drop% × Premium_Multiplier U[1.3, 2.8]",
        "_loss_samples": loss_samples,
        "_extra_procurement_cost_samples": extra_procurement_cost_samples,
        "_lost_output_value_samples": lost_output_value_samples,
    }

    logger.info(
        f"Custom BOM PCaR for {company_name}: "
        f"95% VaR = ₹{metrics['pcar_95_crore']:,.0f} Cr (Base: ₹{total_baseline_crore:,.0f} Cr)"
    )
    return metrics


