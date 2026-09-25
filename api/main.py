# -*- coding: utf-8 -*-
"""
CounterVerse FastAPI REST Backend
=================================
Provides headless access to the full CounterVerse pipeline for
enterprise integration, CI/CD, and automated supply chain monitoring.

Endpoints:
  POST /api/v1/analyze-headline  — Full pipeline: SLM → GraphRAG → Risk → Directive
  POST /api/v1/simulate-risk     — Monte Carlo simulation with custom parameters
  POST /api/v1/calculate-pcar    — PCaR for predefined OEM or custom BOM
  GET  /api/v1/health            — System status, GPU, graph integrity

Launch:
  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# ── Path setup ──
_API_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _API_DIR.parent
for p in [str(_PROJECT_ROOT), str(_API_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Project imports ──
from src.grounding_graph import (
    get_grounding_graph,
    get_graph_summary,
    ground_entities,
    verify_graph_integrity,
    _compute_graph_hash,
)
from src.module_c_causal import (
    simulate_causal_impact,
    calculate_deterministic_risk_score,
    compute_cost_adjusted_recommendation,
)
from src.module_d_mc import run_monte_carlo
from src.module_e_pcar import (
    calculate_pcar,
    calculate_pcar_by_company,
    calculate_pcar_custom_bom,
    OEM_PROFILES,
    SUPPORTED_OEM_COMPANIES,
)
from src.data_sources import (
    SOURCED_HS8542_BASELINE_CRORE,
    USD_INR_RATE,
)

logger = logging.getLogger("counterverse.api")

# ── SLM availability check ──
SLM_AVAILABLE = False
_SLM_SKIP_REASON = "Not loaded"
try:
    import torch
    _HAS_GPU = torch.cuda.is_available()
except ImportError:
    _HAS_GPU = False

if _HAS_GPU:
    try:
        from src.module_b_slm import extract_signal, extract_signal_with_grounding
        SLM_AVAILABLE = True
        _SLM_SKIP_REASON = None
    except (ImportError, RuntimeError, OSError) as e:
        _SLM_SKIP_REASON = str(e)
else:
    _SLM_SKIP_REASON = "No CUDA GPU available"

# Import fast heuristic always
try:
    from src.module_b_slm import extract_signal_fast
except ImportError:
    extract_signal_fast = None


# ════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE SCHEMAS
# ════════════════════════════════════════════════════════════════

class HeadlineRequest(BaseModel):
    """Request body for /analyze-headline."""
    headline: str = Field(..., min_length=5, max_length=500, description="News headline text")
    engine: str = Field(
        default="fast",
        description="Inference engine: 'fast' (rule-based heuristic) or 'slm' (Qwen2.5 GPU inference)"
    )
    company: str = Field(
        default="Maruti Suzuki",
        description="Target OEM for PCaR calculation"
    )
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo sample count")

class HeadlineResponse(BaseModel):
    """Response for /analyze-headline."""
    headline: str
    engine_used: str
    signal: Dict[str, Any]
    grounding: Dict[str, Any]
    risk_score: float
    risk_label: str
    csco_directive: str
    pcar_metrics: Dict[str, Any]
    pipeline_time_ms: float

class SimulateRequest(BaseModel):
    """Request body for /simulate-risk."""
    event_type: str = Field(default="supply_disruption", description="Disruption event type")
    severity: int = Field(default=3, ge=1, le=5, description="Severity level (1-5)")
    duration_days: int = Field(default=30, ge=1, le=365, description="Expected disruption duration")
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo draws")
    random_seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")

class SimulateResponse(BaseModel):
    """Response for /simulate-risk."""
    risk_score: float
    risk_label: str
    probabilities: Dict[str, Any]
    mc_stats: Dict[str, float]
    simulation_config: Dict[str, Any]
    pipeline_time_ms: float

class PcarRequest(BaseModel):
    """Request body for /calculate-pcar."""
    company: str = Field(
        default="Maruti Suzuki",
        description="Target OEM or 'Entire Indian Automotive Industry' for aggregate"
    )
    risk_score: float = Field(default=0.65, ge=0.0, le=1.0, description="Input risk score")
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo draws")
    custom_baseline_crore: Optional[float] = Field(
        default=None,
        description="Custom BOM baseline in Crore INR (overrides UN Comtrade default)"
    )

class PcarResponse(BaseModel):
    """Response for /calculate-pcar."""
    company_name: str
    effective_base_crore: float
    mean_loss_crore: float
    pcar_95_crore: float
    pcar_99_crore: float
    worst_case_loss_crore: float
    market_share_pct: Optional[float] = None
    dependency_ratio_pct: Optional[float] = None
    pipeline_time_ms: float

class BOMComponentItem(BaseModel):
    """Line item in a Custom Bill of Materials."""
    component_name: str = Field(..., description="Component / part name")
    hs_code: str = Field(default="8542", description="HS Code (e.g. 8542 for Semiconductors)")
    annual_spend_crore: float = Field(..., gt=0, description="Annual procurement spend in ₹ Crore")

class CustomBOMRequest(BaseModel):
    """Request body for /calculate-custom-bom."""
    company_name: str = Field(default="Custom Enterprise OEM", description="Company or division name")
    components: List[BOMComponentItem] = Field(..., min_length=1, description="List of BOM line items")
    risk_score: float = Field(default=0.65, ge=0.0, le=1.0, description="Input risk score")
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo draws")
    ground_against_graph: bool = Field(default=True, description="Verify components against GraphRAG")

class CustomBOMResponse(BaseModel):
    """Response for /calculate-custom-bom."""
    company_name: str
    effective_base_crore: float
    component_count: int
    mean_loss_crore: float
    pcar_95_crore: float
    pcar_99_crore: float
    worst_case_loss_crore: float
    component_grounding: List[Dict[str, Any]]
    pipeline_time_ms: float

class HealthResponse(BaseModel):
    """Response for /health."""
    status: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    slm_available: bool
    slm_skip_reason: Optional[str] = None
    graph_nodes: int
    graph_edges: int
    graph_integrity: bool
    graph_hash: str
    baseline_crore: float
    usd_inr_rate: float
    version: str


# ════════════════════════════════════════════════════════════════
# APP CONSTRUCTION
# ════════════════════════════════════════════════════════════════

app = FastAPI(
    title="CounterVerse API",
    description=(
        "Causal AI supply chain disruption simulator for Indian automotive semiconductors. "
        "Headline → GraphRAG → Risk Score → Monte Carlo → Procurement Cost at Risk (PCaR)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════

@app.post("/api/v1/analyze-headline", response_model=HeadlineResponse)
async def analyze_headline(req: HeadlineRequest):
    """
    Full pipeline: Headline → SLM Signal Extraction → GraphRAG Grounding →
    Deterministic Risk Score → Monte Carlo → PCaR Financial Quantification.
    """
    t0 = time.perf_counter()

    # 1. Signal extraction
    engine_used = req.engine
    if req.engine == "slm" and SLM_AVAILABLE:
        try:
            signal = extract_signal(req.headline, engine="slm")
        except Exception as e:
            logger.warning(f"SLM inference failed: {e}. Falling back to fast.")
            signal = extract_signal_fast(req.headline) if extract_signal_fast else _fallback_signal(req.headline)
            engine_used = "fast (fallback)"
    elif extract_signal_fast:
        signal = extract_signal_fast(req.headline)
        engine_used = "fast"
    else:
        signal = _fallback_signal(req.headline)
        engine_used = "fallback"

    # 2. GraphRAG grounding
    grounding = ground_entities(signal)

    # 3. Deterministic risk scoring
    risk_result = calculate_deterministic_risk_score(signal)
    risk_score = risk_result.get("risk_score", 0.5)

    # Risk label
    if risk_score >= 0.60:
        risk_label = "HIGH"
    elif risk_score >= 0.45:
        risk_label = "MEDIUM"
    else:
        risk_label = "LOW"

    # 4. Monte Carlo → PCaR
    probabilities = simulate_causal_impact(signal)
    mc_result = run_monte_carlo(probabilities, n_samples=req.mc_samples)

    # 5. PCaR calculation
    macro_pcar = calculate_pcar(mc_result, company_name="Entire Indian Automotive Industry")
    if req.company in ("Macro (aggregate)", "Entire Indian Automotive Industry"):
        pcar_metrics = _sanitize_pcar(macro_pcar)
    else:
        try:
            company_pcar = calculate_pcar_by_company(req.company, macro_pcar)
            pcar_metrics = _sanitize_pcar(company_pcar)
        except (ValueError, KeyError):
            pcar_metrics = _sanitize_pcar(calculate_pcar(mc_result, company_name=req.company))

    # 6. CSCO directive
    mean_crore = float(pcar_metrics.get("mean_loss_crore", pcar_metrics.get("pcar_mean_crore", 0.0)))
    directive_result = compute_cost_adjusted_recommendation(
        risk_score=risk_score,
        pcar_mean_crore=mean_crore
    )
    csco_directive = directive_result.get("recommendation", directive_result.get("cost_adjusted_best", "Monitor & Maintain"))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return HeadlineResponse(
        headline=req.headline,
        engine_used=engine_used,
        signal=_safe_dict(signal),
        grounding=grounding,
        risk_score=round(risk_score, 4),
        risk_label=risk_label,
        csco_directive=csco_directive,
        pcar_metrics=pcar_metrics,
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.post("/api/v1/simulate-risk", response_model=SimulateResponse)
async def simulate_risk(req: SimulateRequest):
    """
    Runs Monte Carlo simulation with custom parameters.
    Returns risk distribution statistics without requiring a headline.
    """
    t0 = time.perf_counter()

    # Build a synthetic signal from parameters
    synthetic_signal = {
        "event_type": req.event_type,
        "severity": req.severity,
        "duration_days": req.duration_days,
        "recovery_time_days": max(30, req.duration_days // 2),
        "affected_regions": ["China", "Taiwan"],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive", "Semiconductors"],
        "companies": [],
    }

    risk_result = calculate_deterministic_risk_score(synthetic_signal)
    risk_score = risk_result.get("risk_score", 0.5)

    if risk_score >= 0.60:
        risk_label = "HIGH"
    elif risk_score >= 0.45:
        risk_label = "MEDIUM"
    else:
        risk_label = "LOW"

    probabilities = simulate_causal_impact(synthetic_signal)
    mc_result = run_monte_carlo(
        probabilities,
        n_samples=req.mc_samples,
        random_seed=req.random_seed,
    )

    mc_stats = {
        "mean_drop_pct": mc_result["mean_drop"],
        "median_drop_pct": mc_result["median_drop"],
        "p95_drop_pct": mc_result["p95_drop"],
        "p99_drop_pct": mc_result["p99_drop"],
        "n_samples": mc_result["n_samples"],
    }

    # Remove numpy arrays for JSON serialization
    prob_safe = {k: v for k, v in probabilities.items() if k != "_risk_meta" and not isinstance(v, dict)}

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return SimulateResponse(
        risk_score=round(risk_score, 4),
        risk_label=risk_label,
        probabilities=prob_safe,
        mc_stats=mc_stats,
        simulation_config={
            "event_type": req.event_type,
            "severity": req.severity,
            "duration_days": req.duration_days,
            "mc_samples": req.mc_samples,
            "random_seed": req.random_seed,
        },
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.post("/api/v1/calculate-pcar", response_model=PcarResponse)
async def calculate_pcar_endpoint(req: PcarRequest):
    """
    Calculate Procurement Cost at Risk for a specific OEM or custom baseline.
    """
    t0 = time.perf_counter()

    # Build minimal signal for the requested risk score
    synthetic_signal = {
        "event_type": "supply_disruption",
        "severity": max(1, min(5, int(req.risk_score * 5) + 1)),
        "duration_days": 60,
        "recovery_time_days": 45,
        "affected_regions": ["China"],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive"],
        "companies": [],
    }

    probabilities = simulate_causal_impact(synthetic_signal)
    mc_result = run_monte_carlo(probabilities, n_samples=req.mc_samples)

    baseline = req.custom_baseline_crore or SOURCED_HS8542_BASELINE_CRORE

    if req.company in ("Entire Indian Automotive Industry", "Macro (aggregate)"):
        pcar = calculate_pcar(mc_result, baseline_revenue_crore=baseline, company_name="Entire Indian Automotive Industry")
    else:
        macro_pcar = calculate_pcar(mc_result, baseline_revenue_crore=baseline, company_name="Entire Indian Automotive Industry")
        try:
            pcar = calculate_pcar_by_company(req.company, macro_pcar)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown company: '{req.company}'. Supported: {SUPPORTED_OEM_COMPANIES}"
            )

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return PcarResponse(
        company_name=pcar.get("company_name", req.company),
        effective_base_crore=pcar.get("effective_base_crore", 0.0),
        mean_loss_crore=round(pcar.get("mean_loss_crore", 0.0), 2),
        pcar_95_crore=round(pcar.get("pcar_95_crore", 0.0), 2),
        pcar_99_crore=round(pcar.get("pcar_99_crore", 0.0), 2),
        worst_case_loss_crore=round(pcar.get("worst_case_loss_crore", 0.0), 2),
        market_share_pct=pcar.get("market_share_pct"),
        dependency_ratio_pct=pcar.get("dependency_ratio_pct"),
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.post(
    "/api/v1/calculate-custom-bom",
    response_model=CustomBOMResponse,
    tags=["Procurement Cost-at-Risk"],
    summary="Compute enterprise PCaR from a custom Bill of Materials (BOM) with GraphRAG grounding"
)
async def calculate_custom_bom(req: CustomBOMRequest):
    """
    Computes enterprise-specific Procurement Cost-at-Risk (PCaR) from an OEM's
    custom Bill of Materials (component name, HS code, annual spend in ₹ Crore).
    
    Validates each line item against the supply-chain grounding graph and replaces
    the aggregate UN Comtrade macro baseline with the enterprise's actual BOM spend.
    """
    t0 = time.perf_counter()
    components_raw = [c.model_dump() for c in req.components]

    # Run Monte Carlo simulation based on input risk
    dummy_signal = {
        "event_type": "supply_disruption",
        "severity": min(5, max(1, int(req.risk_score * 5) + 1)),
        "duration_days": 30,
        "recovery_time_days": 30,
        "affected_regions": ["Taiwan", "East Asia"],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive"],
        "companies": [req.company_name],
    }
    probs = simulate_causal_impact(dummy_signal)
    mc_result = run_monte_carlo(probs, n_samples=req.mc_samples)

    try:
        custom_pcar = calculate_pcar_custom_bom(
            mc_samples=mc_result,
            bom_components=components_raw,
            company_name=req.company_name,
            ground_against_graph=req.ground_against_graph,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return CustomBOMResponse(
        company_name=custom_pcar.get("company_name", req.company_name),
        effective_base_crore=float(custom_pcar.get("effective_base_crore", custom_pcar.get("total_baseline_crore", 0.0))),
        component_count=int(custom_pcar.get("component_count", custom_pcar.get("num_components", len(components_raw)))),
        mean_loss_crore=round(float(custom_pcar.get("mean_loss_crore", 0.0)), 2),
        pcar_95_crore=round(float(custom_pcar.get("pcar_95_crore", 0.0)), 2),
        pcar_99_crore=round(float(custom_pcar.get("pcar_99_crore", 0.0)), 2),
        worst_case_loss_crore=round(float(custom_pcar.get("worst_case_loss_crore", 0.0)), 2),
        component_grounding=custom_pcar.get("component_grounding", custom_pcar.get("grounding_results", [])),
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """System health check: GPU, SLM, graph integrity, baselines."""
    G = get_grounding_graph()
    integrity = verify_graph_integrity(G)
    graph_hash = _compute_graph_hash(G)

    gpu_name = None
    if _HAS_GPU:
        try:
            import torch
            gpu_name = torch.cuda.get_device_name(0)
        except Exception:
            pass

    return HealthResponse(
        status="healthy" if integrity else "degraded",
        gpu_available=_HAS_GPU,
        gpu_name=gpu_name,
        slm_available=SLM_AVAILABLE,
        slm_skip_reason=_SLM_SKIP_REASON,
        graph_nodes=G.number_of_nodes(),
        graph_edges=G.number_of_edges(),
        graph_integrity=integrity,
        graph_hash=graph_hash,
        baseline_crore=float(SOURCED_HS8542_BASELINE_CRORE),
        usd_inr_rate=USD_INR_RATE,
        version="1.0.0",
    )


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def _fallback_signal(headline: str) -> dict:
    """Minimal signal when no SLM or heuristic is available."""
    return {
        "event_type": "supply_disruption",
        "severity": 3,
        "duration_days": 30,
        "recovery_time_days": 30,
        "affected_regions": [],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive", "Semiconductors"],
        "companies": [],
        "headline": headline,
        "engine": "api_fallback",
    }


def _sanitize_pcar(pcar: dict) -> dict:
    """Remove numpy arrays from PCaR result for JSON serialization."""
    return {k: v for k, v in pcar.items() if k != "_loss_samples"}


def _safe_dict(d: Any) -> dict:
    """Ensure dict output even for non-dict returns."""
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if not hasattr(v, '__array__') or isinstance(v, (int, float, str, bool, list))}
    return {"raw": str(d)}
